'use strict';
const $=id=>document.getElementById(id);
const escaped=x=>String(x).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmt=(x,d=2)=>Number.isFinite(x)?x.toLocaleString('en-US',{minimumFractionDigits:d,maximumFractionDigits:d}):'—';
const statFmt=(x,d=2)=>Number.isFinite(x)&&Math.abs(x)>=1e7?x.toExponential(2):fmt(x,d);
const pFmt=x=>x===null||x===undefined?'—':x<.0001?'<0.0001':fmt(x,4);
const DESCRIPTIONS={Lasso:'L1 正則化係數排序：由訓練 CV 選擇強度，取前 k 個特徵，再以 OLS 重估。','Forward SFS':'從空模型開始，每一步加入讓訓練 CV RMSE 最低的特徵。',RFE:'以標準化 OLS 係數，逐步刪除貢獻最小的特徵，直到剩下 k 個。','Elastic Net':'L1 + L2 正則化係數排序：由訓練 CV 選強度與混合比例，再以 OLS 重估。',Exhaustive:'固定 k，列舉所有特徵組合，以訓練 CV RMSE 選擇最佳子集。'};
let datasets=window.DIC2_RESULTS,dataset,method,k,currentRecord,pendingCSV,pendingName,sourceURL='',busy=false;
if(!datasets||!datasets.startup){document.querySelector('main').textContent='分析資料尚未生成。請先執行 Python 工作流程以建立 results.js。';throw Error('Missing results.js');}
function methods(){return [...new Set(dataset.records.map(r=>r.method))];}
function record(){return dataset.records.find(r=>r.method===method&&r.k===k)||dataset.records.find(r=>r.method===method);}
function chooseDataset(key){dataset=datasets[key];const best=dataset.records[dataset.selected_index];method=best.method;k=best.k;$('problem').value=key;$('feature-count').max=dataset.encoded_p;$('feature-count').value=k;draw();}
function draw(){
  currentRecord=record();if(!currentRecord)return;const r=currentRecord;k=r.k;$('feature-count').value=k;
  $('dataset-meta').textContent=`${dataset.n} 筆資料 · ${dataset.encoded_p} 個特徵\n訓練 ${dataset.train_n} / 測試 ${dataset.test_n}`;$('dataset-meta').style.whiteSpace='pre-line';
  $('methods').replaceChildren();for(const name of methods()){const b=document.createElement('button');b.textContent=name;b.className=name===method?'active':'';b.setAttribute('aria-pressed',String(name===method));b.onclick=()=>{method=name;draw();};$('methods').append(b);}
  $('k-label').textContent=k;$('feature-max').textContent=`1–${dataset.encoded_p} 個特徵`;$('method-note').textContent=DESCRIPTIONS[method];
  const s=dataset.records[dataset.selected_index];$('selection-notice').textContent=`訓練 CV 選定：${s.method} / k = ${s.k}（CV RMSE ${fmt(s.cv_rmse)}）。目前：${method} / k = ${k}。測試曲線只供觀察，不作模型選擇。`;
  $('metric-rmse').textContent=fmt(r.test_rmse);$('metric-r2').textContent=fmt(r.test_r2,4);$('metric-mae').textContent=fmt(r.test_mae);$('metric-adjr2').textContent=fmt(r.train_adjusted_r2,4);$('metric-unit').textContent=dataset.unit;
  $('equation-text').textContent=dataset.target+' = '+fmt(r.coefficients[0].estimate,4)+r.coefficients.slice(1).map(c=>` ${c.estimate<0?'−':'+'} ${fmt(Math.abs(c.estimate),4)} × [${c.name}]`).join('');
  $('active-features').replaceChildren(...r.features.map(f=>{let s=document.createElement('span');s.textContent=f;return s;}));
  $('coefficient-body').innerHTML=r.coefficients.map(c=>`<tr><td>${escaped(c.name)}</td><td>${fmt(c.estimate,4)}</td><td>${fmt(c.se,4)}</td><td>${statFmt(c.t,3)}</td><td>${escaped(pFmt(c.p))}</td><td>[${fmt(c.ci_low,3)}, ${fmt(c.ci_high,3)}]</td><td>${fmt(c.vif,2)}</td></tr>`).join('');
  $('f-stat').textContent=`F ${statFmt(r.f,2)} · p ${pFmt(r.f_p)}`;
  const a=r.anova;$('anova').innerHTML=`<table><thead><tr><th>來源</th><th>SS</th><th>df</th><th>MS</th></tr></thead><tbody><tr><td>迴歸</td><td>${fmt(a.regression_ss)}</td><td>${a.model_df}</td><td>${fmt(a.regression_ss/a.model_df)}</td></tr><tr><td>殘差</td><td>${fmt(a.residual_ss)}</td><td>${a.residual_df}</td><td>${fmt(a.residual_ss/a.residual_df)}</td></tr><tr><td>總計</td><td>${fmt(a.total_ss)}</td><td>${a.model_df+a.residual_df}</td><td>—</td></tr></tbody></table>`;
  $('residual-body').innerHTML=r.residuals.slice(0,10).map(t=>`<tr><td>#${t.row}</td><td>${fmt(t.actual)}</td><td>${fmt(t.predicted)}</td><td>${t.residual>0?'+':''}${fmt(t.residual)}</td><td>${fmt(t.absolute_error)}</td></tr>`).join('');
  $('residual-count').textContent=`顯示 ${Math.min(10,r.residuals.length)} / ${r.residuals.length} 筆，依絕對誤差由大到小排序。可下載完整測試預測。`;
  if(dataset.key==='custom'){$('methodology').textContent=`自訂資料：訓練 ${dataset.train_n} 筆、測試 ${dataset.test_n} 筆；5-fold 訓練 CV。JavaScript 固定亂數種子 0 / 42，其亂數演算法與 Python 內建兩題不同；自訂分析使用較小的正則化參數網格。排除 ${dataset.quality.excluded_target_rows} 筆無目標資料；移除常數欄位：${dataset.quality.removed_constant_columns.join('、')||'無'}。${dataset.skipped.join('；')}`;}
  else $('methodology').textContent=`內建資料：Python train_test_split(test_size=0.2, random_state=0)；5-fold 訓練 CV（shuffle=True, random_state=42）。類別與缺失處理由訓練資料決定，特徵與 k 依訓練 CV 選擇，最後以 ${dataset.test_n} 筆保留測試資料評估。CV 是模型選擇依據，獨立評估以 test 指標為準。`;
  if(/^https?:/.test(dataset.source)){$('data-source').href=dataset.source;$('data-source').hidden=false;}else $('data-source').hidden=true;
  renderCharts(r);renderPredictor(r);
}
function renderCharts(r){
  const series=dataset.records.filter(v=>v.method===method),W=500,H=248,L=63,R=15,T=16,B=46;let values=series.flatMap(v=>[v.test_rmse,v.cv_rmse]);let lo=Math.min(...values),hi=Math.max(...values),pad=(hi-lo)*.15||Math.max(1,hi*.1);lo=Math.max(0,lo-pad);hi+=pad;const x=j=>L+(j-1)/Math.max(1,dataset.encoded_p-1)*(W-L-R),y=v=>T+(hi-v)/(hi-lo)*(H-T-B);
  let grid='';for(let i=0;i<=4;i++){let v=lo+(hi-lo)*i/4,yy=y(v);grid+=`<line x1="${L}" y1="${yy}" x2="${W-R}" y2="${yy}" stroke="#e5eae2"/><text x="${L-8}" y="${yy+3}" text-anchor="end">${fmt(v,0)}</text>`;}
  let ticks='';series.forEach(v=>ticks+=`<text x="${x(v.k)}" y="${H-B+19}" text-anchor="middle">${v.k}</text>`);
  let lines=['cv_rmse','test_rmse'].map((name,i)=>{let color=i?'#247962':'#c58446';let pts=series.map(v=>`${x(v.k)},${y(v[name])}`).join(' ');return `<polyline points="${pts}" fill="none" stroke="${color}" stroke-width="2" ${i?'':'stroke-dasharray="5 4"'}/>`+series.map(v=>`<circle cx="${x(v.k)}" cy="${y(v[name])}" r="${v.k===k?5:2.7}" fill="${color}"><title>k=${v.k}; ${name}: ${fmt(v[name])}</title></circle>`).join('');}).join('');
  $('rmse-chart').innerHTML=`<svg viewBox="0 0 ${W} ${H}" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">${grid}${lines}${ticks}<text x="${W/2}" y="${H-7}" text-anchor="middle">Number of features (k)</text></svg>`;
  let vals=r.residuals.flatMap(v=>[v.actual,v.predicted]),min=Math.min(...vals),max=Math.max(...vals),pd=(max-min)*.08||1;min-=pd;max+=pd;const sx=v=>L+(v-min)/(max-min)*(W-L-R),sy=v=>T+(max-v)/(max-min)*(H-T-B);grid='';for(let i=0;i<=4;i++){let v=min+(max-min)*i/4;grid+=`<line x1="${L}" y1="${sy(v)}" x2="${W-R}" y2="${sy(v)}" stroke="#e5eae2"/><text x="${L-8}" y="${sy(v)+3}" text-anchor="end">${fmt(v,0)}</text><text x="${sx(v)}" y="${H-B+19}" text-anchor="middle">${fmt(v,0)}</text>`;}
  const dots=r.residuals.map(v=>`<circle cx="${sx(v.actual)}" cy="${sy(v.predicted)}" r="3.6" fill="#247962" opacity=".68"><title>Row ${v.row}; actual ${fmt(v.actual)}; predicted ${fmt(v.predicted)}</title></circle>`).join('');
  $('scatter-chart').innerHTML=`<svg viewBox="0 0 ${W} ${H}" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">${grid}<line x1="${sx(min)}" y1="${sy(min)}" x2="${sx(max)}" y2="${sy(max)}" stroke="#c58446" stroke-dasharray="4 4"/>${dots}<text x="${W/2}" y="${H-7}" text-anchor="middle">Actual</text><text x="12" y="${H/2}" transform="rotate(-90,12,${H/2})" text-anchor="middle">Predicted</text></svg>`;
}
function renderPredictor(r){
  const form=$('predictor-form');form.replaceChildren();dataset.specs.forEach((s,i)=>{if(!r.features.some(f=>f===s.name||(s.type==='category'&&s.levels.some(level=>f===s.name+'='+level))))return;const div=document.createElement('div'),label=document.createElement('label');label.textContent=s.name;label.htmlFor='predict-'+i;let input;
    if(s.type==='category'){input=document.createElement('select');for(const level of s.levels){let o=document.createElement('option');o.value=level;o.textContent=level+(level===s.levels[0]?'（參考類別）':'');input.append(o);}}
    else{input=document.createElement('input');input.type='number';input.step='any';input.value=s.median;input.required=true;}
    input.id='predict-'+i;input.dataset.spec=i;input.addEventListener('input',predict);div.append(label,input);form.append(div);
  });form.onsubmit=e=>e.preventDefault();$('prediction-label').textContent=`預測 ${dataset.target}（${dataset.unit}）`;predict();
}
function predict(){
  let beta=currentRecord.coefficients[0].estimate,warning=false,valid=true;for(const c of currentRecord.coefficients.slice(1)){const s=dataset.specs.find(s=>s.name===c.name||(s.type==='category'&&s.levels.some(l=>c.name===s.name+'='+l))),i=dataset.specs.indexOf(s),input=$('predict-'+i);let v;
    if(s.type==='category')v=+(c.name===s.name+'='+input.value);
    else{if(input.value.trim()===''||!Number.isFinite(Number(input.value)))valid=false;v=Number(input.value);if(v<s.min||v>s.max)warning=true;}
    beta+=c.estimate*v;
  }$('prediction-output').textContent=valid?fmt(beta):'請輸入有效數值';$('prediction-warning').textContent=valid?(warning?'輸入超出訓練資料範圍，屬外插預測。':'OLS 點預測；不是保證值，也不是預測區間。'):'';
}
function status(message,error=false){$('import-status').textContent=message;$('import-status').className=error?'error':'loading';}
function stageCSV(text,name){pendingCSV=null;$('target-controls').hidden=true;const parsed=DIC2_ENGINE.parseCSV(text);pendingCSV=parsed;pendingName=name;$('target').replaceChildren(...parsed.numericTargets.map(h=>{let o=document.createElement('option');o.value=h;o.textContent=h;return o;}));$('target').value=parsed.numericTargets.includes('Profit')?'Profit':parsed.numericTargets.includes('MEDV')?'MEDV':parsed.numericTargets.at(-1);$('csv-preview').textContent=`${parsed.rows.length} 列 · ${parsed.headers.length} 欄：${parsed.headers.join('、')}`;$('target-controls').hidden=false;status('資料已讀取。確認目標欄位後按「開始分析」。');}
function setBusy(value){busy=value;for(const id of ['analyze-custom','load-url','csv-file','target'])$(id).disabled=value;}
$('problem').onchange=e=>chooseDataset(e.target.value);$('feature-count').oninput=e=>{k=Number(e.target.value);draw();};$('restore-best').onclick=()=>chooseDataset(dataset.key);
$('toggle-import').onclick=()=>{const open=$('import-panel').hidden;$('import-panel').hidden=!open;$('toggle-import').setAttribute('aria-expanded',String(open));};
$('example-url').onclick=()=>{$('csv-url').value='https://raw.githubusercontent.com/Avik-Jain/100-Days-Of-ML-Code/master/datasets/50_Startups.csv';$('csv-url').focus();};
$('csv-file').onchange=async e=>{const file=e.target.files[0];if(!file)return;sourceURL='';try{if(file.size>5*1024*1024)throw Error('檔案超過 5 MB。');stageCSV(await file.text(),file.name);}catch(err){pendingCSV=null;$('target-controls').hidden=true;status(err.message,true);}};
$('load-url').onclick=async()=>{const url=$('csv-url').value.trim();pendingCSV=null;$('target-controls').hidden=true;try{if(!/^https?:\/\//i.test(url))throw Error('請輸入完整的 HTTP 或 HTTPS CSV 網址。');setBusy(true);status('正在讀取公開網址…');const response=await fetch(url,{signal:AbortSignal.timeout(20000),credentials:'omit'});if(!response.ok)throw Error(`網址回應 HTTP ${response.status}。`);if(Number(response.headers.get('content-length'))>5*1024*1024)throw Error('資料超過 5 MB。');const text=await response.text();if(new Blob([text]).size>5*1024*1024)throw Error('資料超過 5 MB。');stageCSV(text,new URL(url).pathname.split('/').at(-1)||'URL dataset');sourceURL=url;}catch(err){status(`${err.message} 網址可能受 CORS 或網路限制，請改用 CSV 檔案上傳。`,true);}finally{setBusy(false);}};
$('analyze-custom').onclick=()=>{if(!pendingCSV||busy)return;setBusy(true);status('正在以訓練資料選擇特徵並重新估計模型…');let worker;try{worker=new Worker('worker.js');}catch(err){setBusy(false);status('請透過本機 HTTP 預覽或 GitHub Pages 開啟此頁，才能執行自訂分析。',true);return;}worker.onmessage=e=>{setBusy(false);worker.terminate();if(e.data.error){status(e.data.error,true);return;}const result=e.data.result;result.source=sourceURL||result.source;datasets.custom=result;if(!$('problem').querySelector('option[value="custom"]')){const o=document.createElement('option');o.value='custom';$('problem').append(o);}$('problem').querySelector('option[value="custom"]').textContent='03 / 自訂資料 — '+result.name;chooseDataset('custom');status(`已完成 ${result.n} 筆資料的實際分析。訓練 CV 選定 ${result.selection.method} / k=${result.selection.k}。${result.skipped.join('；')}`);};worker.onerror=()=>{setBusy(false);worker.terminate();status('分析引擎無法啟動，請確認使用 HTTP 網站而非直接開啟檔案。',true);};worker.postMessage({parsed:pendingCSV,target:$('target').value,name:pendingName});};
$('download-results').onclick=()=>{const headers=['row','actual','predicted','residual','absolute_error'],text=[headers.join(','),...currentRecord.residuals.map(r=>headers.map(h=>r[h]).join(','))].join('\r\n');const url=URL.createObjectURL(new Blob([text],{type:'text/csv;charset=utf-8'})),a=document.createElement('a');a.href=url;a.download=`${dataset.key}_${method.replace(/\s/g,'_')}_k${k}_predictions.csv`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
chooseDataset('startup');
