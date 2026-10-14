"""Independent numerical audit against sklearn and statsmodels."""
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
import statsmodels.api as sm
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import KFold, train_test_split

ROOT=Path(__file__).resolve().parents[1]
checks=[]
for key in ['startup','boston']:
    d=json.loads((ROOT/f'output/{key}_results.json').read_text())
    df=pd.read_csv(ROOT/'data/50_Startups.csv') if key=='startup' else pd.read_csv(ROOT/'data/boston_house_prices_original.csv',skiprows=1)
    target=d['target']
    X=pd.get_dummies(df.drop(columns=[target]),drop_first=True,dtype=float)
    X.columns=[str(c).replace('State_','State=') for c in X.columns]
    X=X[d['feature_names']].to_numpy(float)
    y=df[target].to_numpy(float)
    tr,te=train_test_split(np.arange(len(df)),test_size=.2,random_state=0)
    assert set(tr).isdisjoint(te)
    assert d['split']['train_rows']==(tr+1).tolist() and d['split']['test_rows']==(te+1).tolist()
    assert len(d['records'])==5*d['encoded_p']
    for r in d['records']:
        cols=[d['feature_names'].index(n) for n in r['features']]
        model=LinearRegression().fit(X[tr][:,cols],y[tr])
        pred=model.predict(X[te][:,cols])
        np.testing.assert_allclose([r['coefficients'][0]['estimate']]+[c['estimate'] for c in r['coefficients'][1:]],
                                   [model.intercept_]+model.coef_.tolist(),rtol=1e-7,atol=2e-5)
        np.testing.assert_allclose(r['test_rmse'],np.sqrt(np.mean((pred-y[te])**2)),rtol=1e-9)
        np.testing.assert_allclose(r['test_mae'],np.mean(abs(pred-y[te])),rtol=1e-9)
        np.testing.assert_allclose(r['test_r2'],model.score(X[te][:,cols],y[te]),rtol=1e-9)
        cv=[]
        for fit,val in KFold(5,shuffle=True,random_state=42).split(tr):
            m=LinearRegression().fit(X[tr[fit]][:,cols],y[tr[fit]])
            cv.append(np.mean((m.predict(X[tr[val]][:,cols])-y[tr[val]])**2))
        np.testing.assert_allclose(r['cv_rmse'],np.sqrt(np.mean(cv)),rtol=1e-8)
        stat=sm.OLS(y[tr],sm.add_constant(X[tr][:,cols])).fit()
        np.testing.assert_allclose([c['se'] for c in r['coefficients']],stat.bse,rtol=1e-7)
        np.testing.assert_allclose([[c['ci_low'],c['ci_high']] for c in r['coefficients']],stat.conf_int(),rtol=1e-7,atol=1e-5)
        np.testing.assert_allclose(r['anova']['regression_ss']+r['anova']['residual_ss'],r['anova']['total_ss'],rtol=1e-12)
        row_lookup={int(row+1):(actual,p) for row,actual,p in zip(te,y[te],pred)}
        for v in r['residuals']:
            a,p=row_lookup[v['row']]
            np.testing.assert_allclose([v['actual'],v['predicted'],v['residual']],[a,p,a-p],atol=2e-5)
    winner=min(d['records'],key=lambda r:(round(r['cv_rmse'],8),r['k'],['Lasso','Forward SFS','RFE','Elastic Net','Exhaustive'].index(r['method'])))
    assert winner==d['records'][d['selected_index']]
    checks.append(f'{key}: {len(d["records"])} subsets independently verified')
manifest=json.loads((ROOT/'output/data_sha256.json').read_text())
for filename,expected in manifest.items():
    assert hashlib.sha256((ROOT/'data'/filename).read_bytes()).hexdigest()==expected
print('\n'.join(checks))
(ROOT/'output/numerical_verification.json').write_text(json.dumps({'passed':True,'checks':checks,'independent_libraries':['sklearn.LinearRegression','statsmodels.OLS']},indent=2))
