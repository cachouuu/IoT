"""DIC2: one reusable, training-only model selection workflow for both datasets.

Run from any directory: python regression_workflow.py --dataset all
The holdout is read only after every feature subset and the winning model are fixed.
CV values are selection criteria, not unbiased post-selection error estimates.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
from sklearn.feature_selection import RFE
from sklearn.linear_model import ElasticNet, Lasso, LinearRegression
from sklearn.model_selection import GridSearchCV, KFold, train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from statsmodels.stats.outliers_influence import variance_inflation_factor

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output'
METHODS = ['Lasso', 'Forward SFS', 'RFE', 'Elastic Net', 'Exhaustive']
SOURCE_URLS = {
    'startup': 'https://raw.githubusercontent.com/Avik-Jain/100-Days-Of-ML-Code/master/datasets/50_Startups.csv',
    'boston': 'https://raw.githubusercontent.com/scikit-learn/scikit-learn/1.1.3/sklearn/datasets/data/boston_house_prices.csv',
}


def load_dataset(key):
    if key == 'startup':
        df = pd.read_csv(ROOT / 'data/50_Startups.csv')
        return df, 'Profit', '50 Startups', 'USD', SOURCE_URLS[key]
    df = pd.read_csv(ROOT / 'data/boston_house_prices_original.csv', skiprows=1)
    return df, 'MEDV', 'Boston Housing', '1,000 USD (historical)', SOURCE_URLS[key]


def prepare(df, target, train_ids, test_ids):
    """Fit categories and numeric medians using training rows only."""
    columns, specs, train_cols, test_cols = [], [], [], []
    train, test = df.iloc[train_ids], df.iloc[test_ids]
    for col in df.columns.drop(target):
        if pd.api.types.is_numeric_dtype(df[col]):
            median = float(train[col].median())
            columns.append(col)
            train_cols.append(train[col].fillna(median).to_numpy(float))
            test_cols.append(test[col].fillna(median).to_numpy(float))
            specs.append({'name': col, 'type': 'numeric', 'median': median,
                          'min': float(train[col].min()), 'max': float(train[col].max())})
        else:
            levels = sorted(train[col].fillna('(missing)').astype(str).unique())
            specs.append({'name': col, 'type': 'category', 'levels': levels})
            for level in levels[1:]:
                columns.append(f'{col}={level}')
                train_cols.append((train[col].fillna('(missing)') == level).to_numpy(float))
                test_cols.append((test[col].fillna('(missing)') == level).to_numpy(float))
    return np.column_stack(train_cols), np.column_stack(test_cols), columns, specs


def cv_cache(X, y, folds):
    """Exact OLS CV with per-fold centering/scaling and a subset result cache."""
    cache = {}

    def score(subset):
        key = tuple(sorted(subset))
        if key not in cache:
            fold_mse = []
            for fit, val in folds:
                xf, xv = X[fit][:, key], X[val][:, key]
                mean, scale = xf.mean(0), xf.std(0)
                scale[scale < 1e-12] = 1
                af = np.column_stack([np.ones(len(fit)), (xf - mean) / scale])
                av = np.column_stack([np.ones(len(val)), (xv - mean) / scale])
                beta = np.linalg.lstsq(af, y[fit], rcond=None)[0]
                fold_mse.append(float(np.mean((y[val] - av @ beta) ** 2)))
            cache[key] = (float(np.sqrt(np.mean(fold_mse))),
                          float(np.std(np.sqrt(fold_mse), ddof=1)))
        return cache[key]
    return score


def choose_paths(X, y, columns):
    p = X.shape[1]
    folds = list(KFold(5, shuffle=True, random_state=42).split(X))
    score = cv_cache(X, y, folds)
    paths = {}
    yy = (y - y.mean()) / y.std()
    tuning = {}
    for name, est in [('Lasso', Lasso(max_iter=100000, tol=1e-7)),
                      ('Elastic Net', ElasticNet(max_iter=100000, tol=1e-7))]:
        pipe = make_pipeline(StandardScaler(), est)
        step = 'lasso' if name == 'Lasso' else 'elasticnet'
        grid = {f'{step}__alpha': np.geomspace(0.001, 0.5, 32)}
        if name == 'Elastic Net':
            grid[f'{step}__l1_ratio'] = [0.2, 0.5, 0.8]
        search = GridSearchCV(pipe, grid, cv=folds, scoring='neg_mean_squared_error', n_jobs=1)
        search.fit(X, yy)
        coef = search.best_estimator_[-1].coef_
        ranking = sorted(range(p), key=lambda i: (-abs(coef[i]), columns[i]))
        paths[name] = [tuple(sorted(ranking[:k])) for k in range(1, p + 1)]
        tuning[name] = {'parameters': search.best_params_,
                        'ranking': [columns[i] for i in ranking],
                        'nonzero_regularized_coefficients': int(np.sum(np.abs(coef) > 1e-10)),
                        'note': 'Standardized regularized coefficient ranking; refit each top-k subset with OLS.'}
    forward, chosen = [], []
    for k in range(1, p + 1):
        candidates = [tuple(sorted(chosen + [i])) for i in range(p) if i not in chosen]
        chosen = list(min(candidates, key=lambda s: (score(s)[0], s)))
        forward.append(tuple(chosen))
    paths['Forward SFS'] = forward
    z = StandardScaler().fit_transform(X)
    paths['RFE'] = []
    for k in range(1, p + 1):
        selector = RFE(LinearRegression(), n_features_to_select=k, step=1).fit(z, y)
        paths['RFE'].append(tuple(np.flatnonzero(selector.support_).tolist()))
    paths['Exhaustive'] = []
    for k in range(1, p + 1):
        subsets = itertools.combinations(range(p), k)
        paths['Exhaustive'].append(min(subsets, key=lambda s: (score(s)[0], s)))
    candidates = []
    for method in METHODS:
        for k, subset in enumerate(paths[method], 1):
            rmse, sd = score(subset)
            candidates.append({'method': method, 'k': k, 'subset': list(subset),
                               'cv_rmse': rmse, 'cv_fold_rmse_sd': sd})
    winner = min(candidates, key=lambda r: (round(r['cv_rmse'], 8), r['k'], METHODS.index(r['method'])))
    return candidates, winner, tuning


def finite(x):
    x = float(x)
    return x if np.isfinite(x) else None


def fit_record(row, Xtrain, ytrain, Xtest, ytest, columns, test_ids):
    subset = row['subset']
    names = [columns[i] for i in subset]
    a = sm.add_constant(Xtrain[:, subset], has_constant='add')
    b = sm.add_constant(Xtest[:, subset], has_constant='add')
    model = sm.OLS(ytrain, a).fit()
    pred = model.predict(b)
    residual = ytest - pred
    ci = model.conf_int()
    coeff = []
    for i, name in enumerate(['Intercept'] + names):
        vif = None if i == 0 else finite(variance_inflation_factor(a, i))
        coeff.append({'name': name, 'estimate': finite(model.params[i]),
                      'se': finite(model.bse[i]), 't': finite(model.tvalues[i]),
                      'p': finite(model.pvalues[i]), 'ci_low': finite(ci[i, 0]),
                      'ci_high': finite(ci[i, 1]), 'vif': vif})
    mse = float(np.mean(residual ** 2))
    total = float(np.sum((ytest - ytest.mean()) ** 2))
    metrics = {'test_rmse': np.sqrt(mse), 'test_mae': float(np.mean(abs(residual))),
               'test_r2': 1 - float(np.sum(residual ** 2)) / total,
               'train_r2': finite(model.rsquared), 'train_adjusted_r2': finite(model.rsquared_adj),
               'train_rmse': np.sqrt(float(np.mean(model.resid ** 2))),
               'f': finite(model.fvalue), 'f_p': finite(model.f_pvalue)}
    jb = stats.jarque_bera(model.resid)
    residual_rows = [{'row': int(idx + 1), 'actual': float(actual), 'predicted': float(yp),
                      'residual': float(err), 'absolute_error': float(abs(err))}
                     for idx, actual, yp, err in zip(test_ids, ytest, pred, residual)]
    return {**row, **metrics, 'features': names, 'coefficients': coeff,
            'residuals': sorted(residual_rows, key=lambda r: -r['absolute_error']),
            'diagnostics': {'jarque_bera_p': finite(jb.pvalue),
                            'condition_number': finite(model.condition_number)},
            'anova': {'regression_ss': finite(model.ess), 'residual_ss': finite(model.ssr),
                      'total_ss': finite(model.centered_tss), 'model_df': int(model.df_model),
                      'residual_df': int(model.df_resid)}}


def run_dataset(key):
    start = time.time()
    df, target, name, unit, source = load_dataset(key)
    ids = np.arange(len(df))
    train_ids, test_ids = train_test_split(ids, test_size=0.2, random_state=0)
    Xtrain, Xtest, columns, specs = prepare(df, target, train_ids, test_ids)
    ytrain, ytest = df[target].to_numpy(float)[train_ids], df[target].to_numpy(float)[test_ids]
    print(f'{name}: selecting subsets on {len(train_ids)} training rows...', flush=True)
    candidates, winner, tuning = choose_paths(Xtrain, ytrain, columns)
    # Freeze the choice before the holdout participates in fitting or reporting.
    frozen = {'method': winner['method'], 'k': winner['k'], 'features': [columns[i] for i in winner['subset']]}
    records = [fit_record(r, Xtrain, ytrain, Xtest, ytest, columns, test_ids) for r in candidates]
    selected_index = next(i for i, r in enumerate(records) if r['method'] == winner['method'] and r['k'] == winner['k'])
    baseline = fit_record({'method': 'Full OLS', 'k': len(columns), 'subset': list(range(len(columns))),
                           'cv_rmse': winner['cv_rmse'] if winner['k'] == len(columns) else
                           next(r['cv_rmse'] for r in candidates if r['k'] == len(columns))},
                          Xtrain, ytrain, Xtest, ytest, columns, test_ids)
    mean_prediction = np.full(len(ytest), ytrain.mean())
    result = {'key': key, 'name': name, 'target': target, 'unit': unit, 'n': len(df),
              'train_n': len(train_ids), 'test_n': len(test_ids), 'encoded_p': len(columns),
              'source': source, 'feature_names': columns, 'specs': specs,
              'split': {'seed': 0, 'test_fraction': 0.2, 'cv_folds': 5, 'cv_seed': 42,
                        'train_rows': (train_ids + 1).tolist(), 'test_rows': (test_ids + 1).tolist()},
              'quality': {'missing_cells': int(df.isna().sum().sum()), 'duplicates': int(df.duplicated().sum())},
              'records': records, 'selected_index': selected_index, 'selection': frozen,
              'tuning': tuning, 'baseline': baseline,
              'mean_baseline_test_rmse': float(np.sqrt(np.mean((ytest - mean_prediction) ** 2))),
              'training_target_mean': float(ytrain.mean())}
    OUT.mkdir(exist_ok=True)
    (OUT / f'{key}_results.json').write_text(json.dumps(result, ensure_ascii=False, allow_nan=False, indent=2))
    pd.DataFrame([{k: r[k] for k in ['method', 'k', 'cv_rmse', 'test_rmse', 'test_mae', 'test_r2', 'train_r2', 'train_adjusted_r2']}
                  | {'features': ' | '.join(r['features'])} for r in records]).to_csv(OUT / f'{key}_metrics.csv', index=False)
    selected = records[selected_index]
    pd.DataFrame(selected['coefficients']).to_csv(OUT / f'{key}_coefficients.csv', index=False)
    pd.DataFrame(selected['residuals']).to_csv(OUT / f'{key}_test_predictions.csv', index=False)
    print(f'{name}: {frozen}; test RMSE={selected["test_rmse"]:.4f}, R2={selected["test_r2"]:.4f}; {time.time()-start:.1f}s', flush=True)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset', choices=['startup', 'boston', 'all'], default='all')
    args = parser.parse_args()
    keys = ['startup', 'boston'] if args.dataset == 'all' else [args.dataset]
    for key in keys:
        run_dataset(key)
    results = {k: json.loads((OUT / f'{k}_results.json').read_text()) for k in ['startup', 'boston']
               if (OUT / f'{k}_results.json').exists()}
    (ROOT / 'site/results.js').write_text('window.DIC2_RESULTS = ' + json.dumps(results, ensure_ascii=False, allow_nan=False) + ';\n')
    for key in ['startup', 'boston']:
        df, *_ = load_dataset(key)
        df.to_csv(ROOT / f'site/{key}.csv', index=False)
    manifest = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT / 'data').glob('*.csv'))}
    (OUT / 'data_sha256.json').write_text(json.dumps(manifest, indent=2))


if __name__ == '__main__':
    main()
