"""Build the executed notebook, figures, report and portable submission archive."""
from __future__ import annotations

import contextlib
import io
import json
import os
from pathlib import Path
import shutil
import zipfile
from xml.sax.saxutils import escape

os.environ.setdefault('MPLCONFIGDIR', '/private/tmp/dic2-matplotlib')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, MaxNLocator
import nbformat
import numpy as np
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output'
SUB = ROOT / 'submission'
PDF = ROOT / 'output/pdf'
FONT = 'DIC2Chinese'
pdfmetrics.registerFont(TTFont(FONT, '/System/Library/Fonts/Supplemental/Arial Unicode.ttf'))
INK = colors.HexColor('#1b3130')
GREEN = colors.HexColor('#247962')
MUTED = colors.HexColor('#62736d')
styles = {key: ParagraphStyle(key, fontName=FONT, fontSize=size, leading=leading,
                              textColor=INK, wordWrap='CJK', spaceAfter=space)
          for key, size, leading, space in [('title', 26, 38, 22), ('h1', 18, 27, 15),
                                            ('h2', 12, 19, 10), ('body', 10, 16, 9),
                                            ('small', 8.2, 12.5, 7), ('cell', 8, 12, 0)]}
WIDTH = A4[0] - 92


def para(text, kind='body'):
    return Paragraph(escape(str(text)).replace('\n', '<br/>'), styles[kind])


def f(x, digits=2):
    return '—' if x is None else f'{x:,.{digits}f}'


def table(headers, rows, widths=None):
    data = [[para(x, 'cell') for x in headers]] + [[para(x, 'cell') for x in row] for row in rows]
    t = Table(data, colWidths=widths or [WIDTH / len(headers)] * len(headers), repeatRows=1, hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e9f0e5')),
                           ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                           ('TOPPADDING', (0, 0), (-1, -1), 7), ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
                           ('LINEBELOW', (0, 0), (-1, -1), .3, colors.HexColor('#dce2d9'))]))
    return t


def footer(c, doc):
    c.setStrokeColor(colors.HexColor('#dce2d9'))
    c.line(46, 42, A4[0] - 46, 42)
    c.setFont(FONT, 8)
    c.setFillColor(MUTED)
    c.drawString(46, 27, 'DIC2 | 魏柏勝 7114056191 | Regression Studio')
    c.drawRightString(A4[0] - 46, 27, str(doc.page))


def selected(d):
    return d['records'][d['selected_index']]


def figures(d):
    figdir = OUT / 'figures'
    figdir.mkdir(exist_ok=True)
    plt.rcParams.update({'font.size': 9, 'axes.spines.top': False, 'axes.spines.right': False,
                         'axes.labelcolor': '#1b3130', 'text.color': '#1b3130'})
    fig, axs = plt.subplots(1, 2, figsize=(8.1, 3.2))
    palette = ['#247962', '#c58446', '#617aa0', '#9975a0', '#8b9b43']
    methods = ['Lasso', 'Forward SFS', 'RFE', 'Elastic Net', 'Exhaustive']
    for method, color in zip(methods, palette):
        rr = [r for r in d['records'] if r['method'] == method]
        for ax, metric in zip(axs, ['cv_rmse', 'test_rmse']):
            ax.plot([r['k'] for r in rr], [r[metric] for r in rr], '-o', lw=1.2, ms=3,
                    label=method, color=color, alpha=.85)
            ax.set_xlabel('Number of encoded features (k)')
            ax.set_ylabel('RMSE')
            ax.grid(alpha=.15)
    axs[0].set_title('Training CV (selection criterion)')
    axs[1].set_title('Holdout test (evaluation only)')
    axs[1].legend(fontsize=7)
    s = selected(d)
    axs[0].scatter([s['k']], [s['cv_rmse']], s=80, marker='*', color='#1b3130', zorder=20)
    fig.suptitle(d['name'], fontsize=12)
    fig.tight_layout()
    path = figdir / f'{d["key"]}_progression.png'
    fig.savefig(path, dpi=180, facecolor='white')
    plt.close(fig)
    fig, axs = plt.subplots(1, 2, figsize=(8.1, 3.0))
    actual = np.array([r['actual'] for r in s['residuals']])
    pred = np.array([r['predicted'] for r in s['residuals']])
    axs[0].scatter(actual, pred, s=15, color='#247962', alpha=.7)
    limits = [min(actual.min(), pred.min()), max(actual.max(), pred.max())]
    axs[0].plot(limits, limits, '--', color='#c58446')
    axs[0].set(xlabel='Actual', ylabel='Predicted', title='Holdout predictions')
    axs[1].scatter(pred, actual - pred, s=15, color='#247962', alpha=.7)
    axs[1].axhline(0, color='#c58446', linestyle='--')
    axs[1].set(xlabel='Predicted', ylabel='Actual - predicted', title='Holdout residuals')
    for ax in axs:
        ax.grid(alpha=.15)
        ax.xaxis.set_major_locator(MaxNLocator(4))
        ax.yaxis.set_major_locator(MaxNLocator(4))
        if d['key'] == 'startup':
            ax.xaxis.set_major_formatter(FuncFormatter(lambda x, pos: f'{x/1000:g}k'))
            ax.yaxis.set_major_formatter(FuncFormatter(lambda x, pos: f'{x/1000:g}k'))
    fig.tight_layout()
    fig.savefig(figdir / f'{d["key"]}_diagnostics.png', dpi=180, facecolor='white')
    plt.close(fig)


def fig(name, height=205):
    return Image(str(OUT / 'figures' / name), width=WIDTH, height=height)


def coefficient_table(d):
    rows = []
    for c in selected(d)['coefficients']:
        p = '<0.0001' if c['p'] is not None and c['p'] < .0001 else f(c['p'], 4)
        rows.append([c['name'], f(c['estimate'], 4), f(c['se'], 4), p,
                     f'[{f(c["ci_low"], 3)}, {f(c["ci_high"], 3)}]', f(c['vif'])])
    return table(['特徵', 'β', 'SE', 'p', '95% CI', 'VIF'], rows,
                 [104, 74, 66, 57, 151, WIDTH - 452])


def report(data):
    PDF.mkdir(exist_ok=True)
    startup, boston = data['startup'], data['boston']
    s, b = selected(startup), selected(boston)
    story = []
    def p(text, kind='body'):
        story.append(para(text, kind))
    def heading(number, title):
        p(f'{number} / {title}', 'h1')
    def page():
        story.append(PageBreak())
    p('AIoT / 課堂作業 DIC2', 'small')
    p('50 Startups\n多元線性迴歸與特徵選擇', 'title')
    p('主要繳交題目：50 Startups\n延伸題目：Boston Housing（套用同一工作流程）\n加分：兩題下拉切換 + 任意 CSV / 公開網址載入')
    p('魏柏勝 / 7114056191\n2026 年 10 月 14 日\n使用 Codex 協助實作、分析與驗證', 'small')
    story.append(Spacer(1, 16))
    story.append(table(['50 Startups 選定模型', '保留測試結果'],
                       [['方法 / 特徵數', f'{s["method"]} / k = {s["k"]}'],
                        ['CV RMSE（訓練資料）', f(s['cv_rmse'])],
                        ['Test RMSE / MAE（USD）', f'{f(s["test_rmse"])} / {f(s["test_mae"])}'],
                        ['Test R²', f(s['test_r2'], 4)],
                        ['特徵', '、'.join(s['features'])]], [170, WIDTH - 170]))
    p('模型依訓練集的交叉驗證誤差選定。測試資料在選擇完成後才用於評估；未利用測試 RMSE 挑選特徵或強迫重現老師示範的最佳 k。')
    p('作業要求來源：使用者提供的 iLearning PDF（3 頁）。兩題都完成，主要報告採 50 Startups；Boston 的結果與重用方式另附於後續章節。', 'small')
    page()
    heading('01', '50 Startups：問題、資料與前處理')
    p('商業問題：根據新創公司的各項支出與所在地，預測 Profit。此分析尋找可解釋的預測關係；係數不被解讀為支出增加造成獲利增加的因果效果。')
    story.append(table(['欄位', '含義與處理'], [['R&D Spend', '研發支出，數值，USD'], ['Administration', '行政支出，數值，USD'],
                         ['Marketing Spend', '行銷支出，數值，USD'], ['State', 'California / Florida / New York；以 California 為參考類別'],
                         ['Profit', '預測目標，獲利，USD']], [125, WIDTH - 125]))
    p(f'資料有 {startup["n"]} 列，{startup["quality"]["missing_cells"]} 個缺失儲存格、{startup["quality"]["duplicates"]} 列完全重複。類別編碼後共有 5 個候選特徵：3 個支出與 2 個 State 虛擬變數。')
    p('固定 80/20 切分：訓練 40 筆、測試 10 筆，random_state=0。先切分，才依訓練資料決定類別與缺失填補值。數值缺失填訓練中位數，類別缺失標為 (missing)；本資料無缺失。')
    p('Lasso / Elastic Net 的排序係數以訓練資料標準化後估計。正則化強度由 5-fold CV 調整；Elastic Net 同時調整 L1 比例。RFE 以標準化係數逐步刪除特徵，避免比較不同單位的原始係數。')
    p('每個方法對 k=1…5 產生特徵子集後，以 OLS 重估，並用相同 5 折計算 CV RMSE。前進選擇與窮舉也以此分數作選擇依據。以最低訓練 CV 分數選定方法與 k；相同子集與分數優先選較小 k，再依固定方法順序決定標籤。')
    p('CV 分數是調參與子集選擇的依據，包含選擇造成的樂觀偏差；本報告以保留測試集作最後的一次泛化評估，未把 CV 分數宣稱為無偏評估。', 'small')
    page()
    heading('02', '50 Startups：方法比較與簡約模型')
    rows=[]
    for method in ['Lasso', 'Forward SFS', 'RFE', 'Elastic Net', 'Exhaustive']:
        candidate=min((r for r in startup['records'] if r['method']==method), key=lambda r:r['cv_rmse'])
        rows.append([method, candidate['k'], f(candidate['cv_rmse']), f(candidate['test_rmse']), f(candidate['test_r2'],4)])
    story.append(table(['方法', 'CV 選定 k', 'CV RMSE', 'Test RMSE', 'Test R²'], rows, [104,70,110,110,WIDTH-394]))
    story.append(fig('startup_progression.png'))
    p(f'選定模型：{s["method"]}，k={s["k"]}，特徵為 {"、".join(s["features"])}。保留測試 RMSE={f(s["test_rmse"])} USD；完整 5 特徵 OLS 的 RMSE={f(startup["baseline"]["test_rmse"])} USD；訓練平均值基準 RMSE={f(startup["mean_baseline_test_rmse"])} USD。')
    two=next(r for r in startup['records'] if r['method']=='Lasso' and r['k']==2)
    p(f'與老師示範的比較：在相同 80/20、seed=0 條件下，Lasso 排序的 k=2（{"、".join(two["features"])}）測試 RMSE 為 {f(two["test_rmse"])}。這是可檢視的候選模型；即使其測試表現較好，也不回頭用保留測試資料改選模型。')
    p('增加特徵能提高訓練擬合度，卻不保證降低新資料誤差。以本切分觀察到的曲線討論簡約性與過度擬合風險，不能把單次 10 筆測試結果當成所有切分的必然結論。', 'small')
    page()
    heading('03', '50 Startups：係數、統計與誤差')
    equation='Profit = '+f(s['coefficients'][0]['estimate'],4)+''.join(f' {"-" if c["estimate"]<0 else "+"} {f(abs(c["estimate"]),4)} × [{c["name"]}]' for c in s['coefficients'][1:])
    p(equation)
    story.append(coefficient_table(startup))
    p(f'訓練 R²={f(s["train_r2"],4)}；訓練調整 R²={f(s["train_adjusted_r2"],4)}。整體 F={f(s["f"])}，p={s["f_p"]:.3g}。以上為訓練 OLS 統計量；p 值、95% 係數區間屬特徵選擇後的探索性推論，未作選擇偏差校正。', 'small')
    a=s['anova']
    story.append(table(['ANOVA 來源', 'SS', 'df', 'MS'], [['迴歸',f(a['regression_ss']),a['model_df'],f(a['regression_ss']/a['model_df'])],['殘差',f(a['residual_ss']),a['residual_df'],f(a['residual_ss']/a['residual_df'])],['總計',f(a['total_ss']),a['model_df']+a['residual_df'],'—']], [90,150,45,WIDTH-285]))
    story.append(fig('startup_diagnostics.png',180))
    worst=s['residuals'][0]
    p(f'最大絕對誤差：原始第 {worst["row"]} 筆，實際 {f(worst["actual"])}、預測 {f(worst["predicted"])}、殘差 {f(worst["residual"])} USD。完整 10 筆預測另附 CSV。殘差定義為真實值減預測值。', 'small')
    page()
    heading('04', 'Boston Housing：直接重用工作流程')
    p('第二題無須另寫一套分析程式。regression_workflow.py 的 load_dataset 切換來源與目標，其他 prepare → choose_paths → fit_record → export 流程完全共用。執行 --dataset boston，即可重跑相同的資料準備、五方法比較、評估與匯出。')
    p(f'使用 scikit-learn 1.1.3 保存的原始 CSV，共 {boston["n"]} 列、13 個候選特徵，目標為 MEDV（1970 年代地區住宅價格中位數，單位：千美元）。資料缺失 {boston["quality"]["missing_cells"]} 個、完全重複 {boston["quality"]["duplicates"]} 列。訓練 {boston["train_n"]}、測試 {boston["test_n"]}；切分與 CV 種子和第一題相同。')
    story.append(table(['CV 選定模型', '結果'], [['方法 / k',f'{b["method"]} / {b["k"]}'],['特徵','、'.join(b['features'])],['CV RMSE',f(b['cv_rmse'],4)],['Test RMSE / MAE',f'{f(b["test_rmse"],4)} / {f(b["test_mae"],4)}'],['Test R²',f(b['test_r2'],4)],['完整 OLS / 平均值基準 RMSE',f'{f(boston["baseline"]["test_rmse"],4)} / {f(boston["mean_baseline_test_rmse"],4)}']], [145,WIDTH-145]))
    story.append(fig('boston_progression.png',210))
    p('k 的範圍自動由編碼後特徵數決定，因此第一題是 1–5，第二題是 1–13；窮舉搜尋真的枚舉 2^13−1=8,191 個非空子集，以訓練 CV 分數比較。', 'small')
    page()
    heading('05', 'Boston Housing：解釋與限制')
    story.append(coefficient_table(boston))
    p(f'訓練調整 R²={f(b["train_adjusted_r2"],4)}；整體 F={f(b["f"])}，p={b["f_p"]:.3g}。各係數代表控制所選其他特徵後的線性關聯。VIF 用於檢視共線性，不能把高擬合度當成係數穩定或因果證據。', 'small')
    story.append(fig('boston_diagnostics.png',175))
    p('資料限制：MEDV 有 50 的上限，最高價位樣本的誤差可能受截尾與非線性影響；資料年代、地區與單次隨機切分也限制外推。B 欄位源自有爭議的種族相關設計；本作業保留指定資料以重現課堂迴歸練習，不將結果用於現代房價或政策判斷。', 'small')
    p('方法限制：線性模型不能充分表示所有非線性關係；特徵選擇後的傳統檢定是探索性分析。更完整的延伸可使用重複切分或巢狀 CV，但不以反覆查看本次保留測試資料來調整模型。', 'small')
    page()
    heading('06', '加分功能：兩題切換與自訂 Dataset')
    story.append(table(['加分項目', '已實作方式'], [['+1：下拉選單呈現兩題','選擇 50 Startups / Boston Housing，資料筆數、特徵上限、圖表、係數與預測表單同步切換。'],['+2：任意輸入 Dataset','支援本機 CSV 及公開 CSV URL；選擇數值目標後，在 Web Worker 實際重新訓練 OLS 與特徵選擇方法。']], [140,WIDTH-140]))
    p('操作：點「載入自訂資料」→ 上傳 CSV 或貼網址 → 載入 → 選數值目標欄位 → 開始分析。可直接使用老師指定的 50_Startups.csv 網址，也可使用隨包的範例資料。', 'small')
    for filename, caption in [('startup-desktop.png','內建 50 Startups：兩題選單、方法與評估指標。'),('custom-desktop.png','自訂資料：載入 CSV、選目標與實際完成重新分析。')]:
        path=OUT/'screenshots'/filename
        if path.exists():
            story.append(Image(str(path),width=420,height=420*700/1280))
            p(caption,'small')
    p('支援範圍：CSV 至多 5 MB / 5,000 列 / 16 個編碼特徵；瀏覽器窮舉上限 12 特徵與 1,000 列，超限時明確停用該方法。目標缺失列排除，常數特徵移除；數值以訓練中位數填補，類別以訓練集合編碼。未知測試類別回到全零參考編碼。', 'small')
    page()
    heading('07', '重現、查核與繳交')
    p('建議繳交：7114056191_DIC2.zip。內容包含本報告、已執行 Notebook、同一套 Python 工作流程、兩題原始資料、結果 CSV、完整互動網站與操作說明。此為以 50 Startups 為主題的完整繳交包，Boston 作延伸與加分展示。')
    p('重新分析：在解壓後的資料夾執行 python -m pip install -r project/requirements.txt，再執行 python project/regression_workflow.py --dataset all。第二題重用：python project/regression_workflow.py --dataset boston。', 'small')
    p('預覽加分網站：python -m http.server 8765 --directory site；開啟 http://localhost:8765/。內建結果來自 Python 的真實分析；自訂資料使用 JavaScript。兩者的亂數演算法與正則化搜尋網格不同，固定種子仍可能產生不同子集，介面有明確註記。', 'small')
    deployment_path = OUT / 'deployment.json'
    deployment = json.loads(deployment_path.read_text()) if deployment_path.exists() else {}
    if deployment.get('status') == 'success':
        p(f'GitHub Pages：已於 {deployment["verified_date"]} 部署成功。公開成果：{deployment["dic2_url"]}；個人首頁：{deployment["home_url"]}。首頁導覽與 Coursework 均有 DIC2 入口，DIC2 頁首可返回首頁。正式網站上的兩題切換、CSV 上傳與老師指定 URL 已通過實際瀏覽器驗證。', 'small')
    else:
        p('GitHub Pages：已備妥原 IoT 儲存庫的部署整合，網站將發布至 /IoT/DIC2/。需完成發布後再使用公開網址繳交。', 'small')
    qa=OUT/'verification.json'
    if qa.exists():
        checks=json.loads(qa.read_text())
        p('驗證紀錄：'+checks['summary'], 'small')
    p('來源與參考', 'h2')
    refs=[('課堂範例','https://huanchen1107.github.io/AIoT-DIC2-MultipleLR/'),('50 Startups 原始資料',startup['source']),('Boston 原始資料',boston['source']),('Boston 資料背景與棄用說明','https://scikit-learn.org/1.1/modules/generated/sklearn.datasets.load_boston.html'),('SequentialFeatureSelector 官方文件','https://scikit-learn.org/stable/modules/generated/sklearn.feature_selection.SequentialFeatureSelector.html')]
    if deployment.get('status') == 'success':
        refs.insert(0, ('本作業公開成果', deployment['dic2_url']))
    for label,url in refs:
        story.append(Paragraph(escape(label)+': <link href="'+escape(url)+'" color="#247962">'+escape(url)+'</link>',styles['small']))
    p('原始資料的 SHA-256 存於 output/data_sha256.json。套件版本固定於 project/requirements.txt；圖、指標、係數與網站結果均由同一份分析輸出產生。沒有複製老師的模型常數作為自己的計算結果。', 'small')
    path=PDF/'7114056191_DIC2_report.pdf'
    doc=SimpleDocTemplate(str(path),pagesize=A4,rightMargin=46,leftMargin=46,topMargin=44,bottomMargin=58,
                          title='DIC2 - 50 Startups and Boston Housing',author='魏柏勝 7114056191')
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    return path


def notebook(data):
    nb=nbformat.v4.new_notebook()
    nb.metadata={'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},
                 'language_info':{'name':'python','version':'3.12'}}
    nb.cells=[nbformat.v4.new_markdown_cell('# DIC2：50 Startups（主要）與 Boston Housing\n魏柏勝 / 7114056191\n\nCRISP-DM 工作流程；兩題共用 `regression_workflow.py`。本 Notebook 的顯示結果已實際執行。完整重訓由最後的重現指令執行。'),
              nbformat.v4.new_code_cell("from pathlib import Path\nimport json\nimport pandas as pd\nROOT = Path.cwd()\nif not (ROOT / 'output').exists():\n    ROOT = ROOT.parent if (ROOT.parent / 'output').exists() else ROOT / 'DIC2'\nresults = {key: json.loads((ROOT / 'output' / f'{key}_results.json').read_text()) for key in ['startup', 'boston']}\nprint('Loaded real Python analysis artifacts:', ', '.join(results))"),
              nbformat.v4.new_markdown_cell('## 1. 資料理解與前處理\n先切分 80/20（seed=0），再由訓練資料決定中位數與類別。50 Startups 的 State 使用 California 作參考類別，編碼後共 5 特徵；Boston 共 13 特徵，目標 MEDV 為歷史千美元。'),
              nbformat.v4.new_code_cell("for key, r in results.items():\n    print(key, 'rows=', r['n'], 'train=', r['train_n'], 'test=', r['test_n'], 'features=', r['encoded_p'])\n    print('quality:', r['quality'])"),
              nbformat.v4.new_markdown_cell('## 2. 模型選擇與評估\n五種方法產生子集，每個子集重估 OLS。方法與 k 依訓練 5-fold CV 的 RMSE 選定；test RMSE 僅用於評估。Lasso / Elastic Net 在此是排序方法，最終預測器都是 OLS。CV 選擇分數不是無偏泛化誤差。'),
              nbformat.v4.new_code_cell("for key, r in results.items():\n    best = r['records'][r['selected_index']]\n    print('\\n', r['name'], r['selection'])\n    print('CV RMSE:', best['cv_rmse'], 'Test RMSE:', best['test_rmse'], 'Test MAE:', best['test_mae'], 'Test R2:', best['test_r2'])\n    print('Full OLS test RMSE:', r['baseline']['test_rmse'])\n    print(pd.DataFrame(r['records'])[['method','k','cv_rmse','test_rmse','test_r2']].to_string(index=False))"),
              nbformat.v4.new_markdown_cell('## 3. 選定模型的係數與測試殘差\n95% 係數區間與 p 值來自訓練 OLS；因先作特徵選擇，視為探索性推論。殘差定義為實際值減預測值。'),
              nbformat.v4.new_code_cell("for key, r in results.items():\n    best = r['records'][r['selected_index']]\n    print('\\n', r['name'])\n    print(pd.DataFrame(best['coefficients']).to_string(index=False))\n    print(pd.DataFrame(best['residuals']).head(5).to_string(index=False))"),
              nbformat.v4.new_markdown_cell('## 4. 第二題直接套用工作流程\n下面顯示同一套流程的核心函式；`--dataset boston` 只更換資料來源與目標，保留資料準備、子集選擇、評估、匯出步驟。完整兩題可執行 `python project/regression_workflow.py --dataset all`。'),
              nbformat.v4.new_code_cell("import importlib.util, inspect\nspec = importlib.util.spec_from_file_location('regression_workflow', ROOT / 'project' / 'regression_workflow.py')\nworkflow = importlib.util.module_from_spec(spec)\nspec.loader.exec_module(workflow)\nprint(inspect.getsource(workflow.run_dataset))"),
              nbformat.v4.new_markdown_cell('## 5. 加分展示與限制\n透過 `python -m http.server 8765 --directory site` 開啟網站。下拉選單切換兩題；自訂 CSV / URL 會在瀏覽器重新分析。Browser JavaScript 與 Python 的亂數演算法及參數網格不同，結果不強求相同。Boston 資料具有年代、MEDV 上限與 B 欄位的爭議限制，僅作課堂練習。')]
    # Execute every code cell in a shared namespace; retain actual stdout and errors.
    ns={'__name__':'__dic2_notebook__'}
    cwd=Path.cwd()
    os.chdir(ROOT)
    try:
        count=0
        for cell in nb.cells:
            if cell.cell_type!='code':
                continue
            count+=1
            buf=io.StringIO()
            with contextlib.redirect_stdout(buf):
                exec(compile(cell.source,'DIC2_notebook','exec'),ns)
            cell.execution_count=count
            cell.outputs=[nbformat.v4.new_output('stream',name='stdout',text=buf.getvalue())]
    finally:
        os.chdir(cwd)
    nbformat.validate(nb)
    nbformat.write(nb, ROOT/'7114056191_DIC2.ipynb')


def package(pdf):
    SUB.mkdir(exist_ok=True)
    path=SUB/'7114056191_DIC2.zip'
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as archive:
        for folder in ['site','data','project','output']:
            for source in sorted((ROOT/folder).rglob('*')):
                if source.is_file() and '__pycache__' not in source.parts:
                    archive.write(source, '7114056191_DIC2/'+str(source.relative_to(ROOT)))
        for name in ['README.md','WORKFLOW.md','7114056191_DIC2.ipynb']:
            source=ROOT/name
            if source.exists():
                archive.write(source,'7114056191_DIC2/'+name)
        archive.write(pdf,'7114056191_DIC2/7114056191_DIC2_report.pdf')
        submission_text = SUB / 'iLearning_submission.txt'
        if submission_text.exists():
            archive.write(submission_text, '7114056191_DIC2/submission/iLearning_submission.txt')
    print(path)


def main():
    data={k:json.loads((OUT/f'{k}_results.json').read_text()) for k in ['startup','boston']}
    for d in data.values():
        figures(d)
    notebook(data)
    pdf=report(data)
    package(pdf)
    print(pdf)


if __name__=='__main__':
    main()
