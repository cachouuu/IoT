/* Browser-local regression engine. No dataset leaves the browser on file upload. */
(function(root) {
  'use strict';
  const METHODS = ['Lasso', 'Forward SFS', 'RFE', 'Elastic Net', 'Exhaustive'];
  const mean = a => a.reduce((s,x) => s+x,0)/a.length;
  function rng(seed) {return () => {let t=seed+=0x6D2B79F5;t=Math.imul(t^(t>>>15),t|1);t^=t+Math.imul(t^(t>>>7),t|61);return ((t^(t>>>14))>>>0)/4294967296;};}
  function shuffle(a, seed) {a=a.slice();let random=rng(seed);for(let i=a.length-1;i>0;i--){let j=Math.floor(random()*(i+1));[a[i],a[j]]=[a[j],a[i]];}return a;}
  function parseCSV(text) {
    text=text.replace(/^\uFEFF/,'');let rows=[],row=[],cell='',quoted=false;
    for(let i=0;i<text.length;i++) {
      const c=text[i];
      if(c==='"'){if(quoted&&text[i+1]==='"'){cell+='"';i++;}else if(!quoted&&cell.length){throw Error('CSV 引號格式錯誤。');}else quoted=!quoted;}
      else if(c===','&&!quoted){row.push(cell);cell='';}
      else if((c==='\n'||c==='\r')&&!quoted){if(c==='\r'&&text[i+1]==='\n')i++;row.push(cell);if(row.some(x=>x.trim()!==''))rows.push(row);row=[];cell='';}
      else cell+=c;
    }
    if(quoted)throw Error('CSV 引號尚未關閉。');
    row.push(cell);if(row.some(x=>x.trim()!==''))rows.push(row);
    if(rows.length<2)throw Error('CSV 需要欄位名稱與資料列。');
    const headers=rows.shift().map(x=>x.trim());
    if(headers.some(x=>!x)||new Set(headers).size!==headers.length)throw Error('欄位名稱不能空白或重複。');
    if(rows.some(r=>r.length!==headers.length))throw Error('CSV 各列的欄位數不同，請檢查逗號與引號。');
    if(rows.length>5000)throw Error('資料超過 5,000 列，請先取樣再載入。');
    const numericTargets=headers.filter((h,j)=>rows.some(r=>r[j].trim()!==''&&Number.isFinite(Number(r[j])))&&rows.every(r=>r[j].trim()===''||Number.isFinite(Number(r[j]))));
    if(!numericTargets.length)throw Error('沒有可用的數值目標欄位。');
    return {headers,rows,numericTargets};
  }
  function inverse(A){
    const n=A.length,a=A.map((r,i)=>r.concat(Array.from({length:n},(_,j)=>+(i===j))));
    for(let i=0;i<n;i++){
      let pivot=i;for(let j=i+1;j<n;j++)if(Math.abs(a[j][i])>Math.abs(a[pivot][i]))pivot=j;
      if(Math.abs(a[pivot][i])<1e-9)throw Error('特徵存在完全共線性，請移除重複或線性相依欄位。');
      [a[i],a[pivot]]=[a[pivot],a[i]];const z=a[i][i];for(let k=0;k<2*n;k++)a[i][k]/=z;
      for(let j=0;j<n;j++)if(j!==i){const f=a[j][i];for(let k=0;k<2*n;k++)a[j][k]-=f*a[i][k];}
    }return a.map(r=>r.slice(n));
  }
  function logGamma(z){
    const c=[676.5203681218851,-1259.1392167224028,771.32342877765313,-176.61502916214059,12.507343278686905,-.13857109526572012,9.984369578019572e-6,1.5056327351493116e-7];
    if(z<.5)return Math.log(Math.PI)-Math.log(Math.sin(Math.PI*z))-logGamma(1-z);
    z--;let x=.99999999999980993;for(let i=0;i<c.length;i++)x+=c[i]/(z+i+1);let t=z+c.length-.5;return .5*Math.log(2*Math.PI)+(z+.5)*Math.log(t)-t+Math.log(x);
  }
  function betaCF(a,b,x){
    let qab=a+b,qap=a+1,qam=a-1,c=1,d=1-qab*x/qap;const tiny=1e-30;
    if(Math.abs(d)<tiny)d=tiny;d=1/d;let h=d;
    for(let m=1;m<=200;m++){let m2=2*m,aa=m*(b-m)*x/((qam+m2)*(a+m2));d=1+aa*d;if(Math.abs(d)<tiny)d=tiny;c=1+aa/c;if(Math.abs(c)<tiny)c=tiny;d=1/d;h*=d*c;aa=-(a+m)*(qab+m)*x/((a+m2)*(qap+m2));d=1+aa*d;if(Math.abs(d)<tiny)d=tiny;c=1+aa/c;if(Math.abs(c)<tiny)c=tiny;d=1/d;const delta=d*c;h*=delta;if(Math.abs(delta-1)<3e-13)break;}
    return h;
  }
  function ibeta(x,a,b){if(x<=0)return 0;if(x>=1)return 1;let bt=Math.exp(logGamma(a+b)-logGamma(a)-logGamma(b)+a*Math.log(x)+b*Math.log1p(-x));return x<(a+1)/(a+b+2)?bt*betaCF(a,b,x)/a:1-bt*betaCF(b,a,1-x)/b;}
  function tP(t,df){return ibeta(df/(df+t*t),df/2,.5);}
  function tCritical(df){let lo=0,hi=100;for(let i=0;i<60;i++){const mid=(lo+hi)/2;if(tP(mid,df)>.05)lo=mid;else hi=mid;}return (lo+hi)/2;}
  function ols(X,y,subset,details=false){
    const n=X.length,p=subset.length;if(n<=p+1)throw Error('訓練資料列數不足以估計此模型。');
    const mu=subset.map(j=>mean(X.map(r=>r[j]))),sd=subset.map((j,k)=>Math.sqrt(mean(X.map(r=>(r[j]-mu[k])**2)))||1);
    const A=X.map(r=>[1,...subset.map((j,k)=>(r[j]-mu[k])/sd[k])]);
    const gram=Array.from({length:p+1},()=>Array(p+1).fill(0)),xy=Array(p+1).fill(0);
    for(let r=0;r<n;r++)for(let i=0;i<=p;i++){xy[i]+=A[r][i]*y[r];for(let j=0;j<=p;j++)gram[i][j]+=A[r][i]*A[r][j];}
    const inv=inverse(gram),bz=inv.map(r=>r.reduce((s,v,i)=>s+v*xy[i],0));
    const beta=[bz[0]-subset.reduce((s,j,k)=>s+bz[k+1]*mu[k]/sd[k],0),...bz.slice(1).map((v,k)=>v/sd[k])];
    const predict=r=>beta[0]+subset.reduce((s,j,k)=>s+beta[k+1]*r[j],0);
    const result={beta,bz,predict};if(!details)return result;
    const err=y.map((v,i)=>v-predict(X[i])),ss=err.reduce((s,v)=>s+v*v,0),tt=y.reduce((s,v)=>s+(v-mean(y))**2,0),df=n-p-1,sigma=ss/df,tc=tCritical(df);
    let transform=[1,...mu.map((v,k)=>-v/sd[k])];const variances=[transform.reduce((s,v,i)=>s+v*inv[i].reduce((q,w,j)=>q+w*transform[j],0),0),...sd.map((v,k)=>inv[k+1][k+1]/(v*v))];
    result.coefficients=beta.map((v,i)=>{const se=Math.sqrt(Math.max(0,sigma*variances[i])),t=se>0?v/se:0;return {estimate:v,se,t,p:se>0?tP(t,df):null,ci_low:v-tc*se,ci_high:v+tc*se,vif:i?Math.max(1,inv[i][i]*n):null};});
    result.train_r2=tt>0?1-ss/tt:null;result.train_adjusted_r2=tt>0?1-(ss/df)/(tt/(n-1)):null;result.train_rmse=Math.sqrt(ss/n);
    result.f=p&&sigma>0?Math.max(0,(tt-ss)/p/sigma):null;result.f_p=result.f===null?null:ibeta(df/(df+p*result.f),df/2,p/2);
    result.anova={regression_ss:tt-ss,residual_ss:ss,total_ss:tt,model_df:p,residual_df:df};return result;
  }
  function regularized(X,y,alpha,ratio){
    const n=X.length,p=X[0].length,mu=Array.from({length:p},(_,j)=>mean(X.map(r=>r[j]))),sd=mu.map((v,j)=>Math.sqrt(mean(X.map(r=>(r[j]-v)**2)))||1),ym=mean(y),ys=Math.sqrt(mean(y.map(v=>(v-ym)**2)))||1;
    const Z=X.map(r=>r.map((v,j)=>(v-mu[j])/sd[j])),res=y.map(v=>(v-ym)/ys),b=Array(p).fill(0);
    for(let iter=0;iter<2500;iter++){let change=0;for(let j=0;j<p;j++){let dot=0,norm=0;for(let i=0;i<n;i++){dot+=Z[i][j]*(res[i]+Z[i][j]*b[j]);norm+=Z[i][j]**2;}dot/=n;norm/=n;let v=Math.sign(dot)*Math.max(0,Math.abs(dot)-alpha*ratio)/(norm+alpha*(1-ratio));let delta=v-b[j];change=Math.max(change,Math.abs(delta));for(let i=0;i<n;i++)res[i]-=Z[i][j]*delta;b[j]=v;}if(change<1e-6)break;}
    return {b,predict:r=>ym+ys*r.reduce((s,v,j)=>s+b[j]*(v-mu[j])/sd[j],0)};
  }
  function analyze(parsed,target,name){
    const targetJ=parsed.headers.indexOf(target);if(targetJ<0)throw Error('找不到目標欄位。');
    let excluded=0;const valid=[];
    parsed.rows.forEach((r,i)=>{if(r[targetJ].trim()===''||!Number.isFinite(Number(r[targetJ])))excluded++;else valid.push({values:r,row:i+1});});
    if(valid.length<20)throw Error('至少需要 20 列有效數值目標資料。');
    const shuffled=shuffle(valid.map((_,i)=>i),0),testN=Math.ceil(valid.length*.2),testIds=shuffled.slice(0,testN),trainIds=shuffled.slice(testN),specs=[],names=[];
    let removed=[];
    parsed.headers.forEach((h,j)=>{
      if(j===targetJ)return;const values=valid.map(r=>r.values[j].trim());const isNum=values.every(v=>v===''||Number.isFinite(Number(v)));
      if(isNum){const trainVals=trainIds.map(i=>values[i]).filter(v=>v!=='').map(Number).sort((a,b)=>a-b);if(!trainVals.length||trainVals[0]===trainVals[trainVals.length-1]){removed.push(h);return;}const half=Math.floor(trainVals.length/2),med=trainVals.length%2?trainVals[half]:(trainVals[half-1]+trainVals[half])/2;specs.push({name:h,type:'numeric',median:med,min:trainVals[0],max:trainVals.at(-1),j});names.push(h);}
      else{const levels=[...new Set(trainIds.map(i=>values[i]||'(missing)'))].sort();if(levels.length<2){removed.push(h);return;}specs.push({name:h,type:'category',levels,j});levels.slice(1).forEach(level=>names.push(h+'='+level));}
    });
    if(!names.length)throw Error('沒有可使用的變動特徵。');if(names.length>16)throw Error('編碼後超過 16 個特徵，請先移除識別碼或高基數類別欄位。');if(trainIds.length<=names.length+5)throw Error('特徵太多，請增加資料或減少欄位。');
    function encode(r){let a=[];specs.forEach(s=>{const v=r.values[s.j].trim();if(s.type==='numeric')a.push(v===''?s.median:Number(v));else s.levels.slice(1).forEach(l=>a.push(+((v||'(missing)')===l)));});return a;}
    const allX=valid.map(encode),allY=valid.map(r=>Number(r.values[targetJ])),X=trainIds.map(i=>allX[i]),y=trainIds.map(i=>allY[i]),Xt=testIds.map(i=>allX[i]),yt=testIds.map(i=>allY[i]),p=names.length;
    const cvIds=shuffle(X.map((_,i)=>i),42),folds=Array.from({length:5},(_,f)=>{const val=cvIds.filter((v,i)=>i%5===f),fit=cvIds.filter((v,i)=>i%5!==f);return {xf:fit.map(i=>X[i]),yf:fit.map(i=>y[i]),xv:val.map(i=>X[i]),yv:val.map(i=>y[i])};});
    const cache=new Map();function score(sub){const key=sub.slice().sort((a,b)=>a-b).join(',');if(cache.has(key))return cache.get(key);let mse=[];try{for(const f of folds){let m=ols(f.xf,f.yf,sub);mse.push(mean(f.yv.map((v,i)=>(v-m.predict(f.xv[i]))**2)));}}catch(e){cache.set(key,Infinity);return Infinity;}let rmse=Math.sqrt(mean(mse));cache.set(key,rmse);return rmse;}
    const paths={},tuning={};
    for(const method of ['Lasso','Elastic Net']){let best=null;for(const ratio of method==='Lasso'?[1]:[.2,.5,.8])for(const alpha of [.001,.003,.01,.03,.1,.3]){let mse=mean(folds.map(f=>{const m=regularized(f.xf,f.yf,alpha,ratio);return mean(f.yv.map((v,i)=>(v-m.predict(f.xv[i]))**2));}));if(!best||mse<best.mse)best={alpha,ratio,mse};}const fitted=regularized(X,y,best.alpha,best.ratio);const rank=names.map((_,i)=>i).sort((a,b)=>Math.abs(fitted.b[b])-Math.abs(fitted.b[a])||names[a].localeCompare(names[b]));paths[method]=Array.from({length:p},(_,i)=>rank.slice(0,i+1).sort((a,b)=>a-b));tuning[method]=best;}
    let chosen=[];paths['Forward SFS']=[];for(let k=1;k<=p;k++){let next=null,loss=Infinity;for(let j=0;j<p;j++)if(!chosen.includes(j)){let c=[...chosen,j].sort((a,b)=>a-b),s=score(c);if(s<loss){loss=s;next=c;}}if(!next)throw Error('無法估計模型：請移除共線性或重複欄位。');chosen=next;paths['Forward SFS'].push(chosen);}
    let remain=names.map((_,i)=>i);paths.RFE=Array(p);while(remain.length){paths.RFE[remain.length-1]=remain.slice();if(remain.length===1)break;let model=ols(X,y,remain),index=0;for(let j=1;j<remain.length;j++)if(Math.abs(model.bz[j+1])<Math.abs(model.bz[index+1]))index=j;remain.splice(index,1);}
    let skipped=[];if(p<=12&&valid.length<=1000){paths.Exhaustive=Array(p);let bestScore=Array(p).fill(Infinity);for(let mask=1;mask<(1<<p);mask++){let sub=[];for(let j=0;j<p;j++)if(mask&(1<<j))sub.push(j);let loss=score(sub),index=sub.length-1;if(loss<bestScore[index]){bestScore[index]=loss;paths.Exhaustive[index]=sub;}}}else skipped.push('Exhaustive：最多 12 個編碼特徵、1,000 列資料');
    const candidates=[];for(const method of METHODS)if(paths[method])paths[method].forEach((sub,i)=>{if(sub&&Number.isFinite(score(sub)))candidates.push({method,k:i+1,subset:sub,cv_rmse:score(sub)});});
    if(!candidates.length)throw Error('沒有可估計的特徵子集。');const winner=candidates.slice().sort((a,b)=>a.cv_rmse-b.cv_rmse||a.k-b.k||METHODS.indexOf(a.method)-METHODS.indexOf(b.method))[0];
    const records=candidates.map(r=>{const model=ols(X,y,r.subset,true);const residuals=yt.map((v,i)=>({row:valid[testIds[i]].row,actual:v,predicted:model.predict(Xt[i]),residual:v-model.predict(Xt[i]),absolute_error:Math.abs(v-model.predict(Xt[i]))}));let mse=mean(residuals.map(r=>r.residual**2)),total=yt.reduce((s,v)=>s+(v-mean(yt))**2,0);return {...r,features:r.subset.map(j=>names[j]),coefficients:model.coefficients.map((c,i)=>({...c,name:i?names[r.subset[i-1]]:'Intercept'})),test_rmse:Math.sqrt(mse),test_mae:mean(residuals.map(r=>r.absolute_error)),test_r2:total>0?1-mse*yt.length/total:null,train_r2:model.train_r2,train_adjusted_r2:model.train_adjusted_r2,train_rmse:model.train_rmse,f:model.f,f_p:model.f_p,anova:model.anova,residuals:residuals.sort((a,b)=>b.absolute_error-a.absolute_error)};});
    return {key:'custom',name,target,unit:'目標欄位原始單位',n:valid.length,train_n:X.length,test_n:Xt.length,encoded_p:p,specs,feature_names:names,records,selected_index:candidates.indexOf(winner),selection:{method:winner.method,k:winner.k,features:winner.subset.map(j=>names[j])},quality:{excluded_target_rows:excluded,removed_constant_columns:removed},skipped,tuning,split:{seed:0,cv_seed:42,cv_folds:5,test_fraction:.2,train_rows:trainIds.map(i=>valid[i].row),test_rows:testIds.map(i=>valid[i].row)},source:'本機 CSV / 公開網址',engine:'Browser JavaScript (Mulberry32 shuffle; different PRNG from Python built-in analyses)'};
  }
  root.DIC2_ENGINE={parseCSV,analyze,ols,ibeta,tP};
  if(typeof module!=='undefined')module.exports=root.DIC2_ENGINE;
})(typeof self!=='undefined'?self:globalThis);
