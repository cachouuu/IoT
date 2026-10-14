/* Run: node project/verify_engine.cjs */
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const root=path.resolve(__dirname,'..'),engine=require('../site/engine.js');
const close=(a,b,tol=1e-7)=>assert.ok(Math.abs(a-b)<=tol*Math.max(1,Math.abs(b)),`${a} != ${b}`);
let records=0;
for(const key of ['startup','boston']){
  const d=JSON.parse(fs.readFileSync(path.join(root,'output',key+'_results.json'),'utf8'));
  const csv=engine.parseCSV(fs.readFileSync(path.join(root,'site',key+'.csv'),'utf8'));
  const encode=row=>d.specs.flatMap(s=>{const val=row[csv.headers.indexOf(s.name)];return s.type==='numeric'?[Number(val)]:s.levels.slice(1).map(l=>+(val===l));});
  const X=d.split.train_rows.map(i=>encode(csv.rows[i-1])),y=d.split.train_rows.map(i=>Number(csv.rows[i-1][csv.headers.indexOf(d.target)]));
  for(const r of d.records){const m=engine.ols(X,y,r.subset,true);r.coefficients.forEach((c,i)=>{close(m.beta[i],c.estimate,1e-6);close(m.coefficients[i].se,c.se,1e-6);close(m.coefficients[i].p,c.p,1e-7);close(m.coefficients[i].ci_low,c.ci_low,1e-6);close(m.coefficients[i].ci_high,c.ci_high,1e-6);if(i)close(m.coefficients[i].vif,c.vif,1e-6);});close(m.f,r.f,1e-6);close(m.f_p,r.f_p,1e-6);records++;}
}
assert.deepEqual(engine.parseCSV('\uFEFFx,y\r\n"a,b",1\r\n"a""b",2\r\n').rows,[['a,b','1'],['a"b','2']]);
for(const bad of ['x,x\n1,2','x,y\n1,2,3','x,y\n"broken,1','x,y\na,b'])assert.throws(()=>engine.parseCSV(bad));
close(engine.tP(2.2281388519649385,10),.05,1e-10);
const synthetic=['x,z,target',...Array.from({length:40},(_,i)=>{const z=(i*13)%17;return `${i},${z},${100+2*i+3*z}`;})].join('\n');
const result=engine.analyze(engine.parseCSV(synthetic),'target','Known linear dataset');
const full=result.records.find(r=>r.method==='Forward SFS'&&r.k===2);assert.ok(full.test_rmse<1e-8);close(full.coefficients[0].estimate,100);close(full.coefficients[1].estimate,2);close(full.coefficients[2].estimate,3);
const original=engine.analyze(engine.parseCSV(fs.readFileSync(path.join(root,'site/startup.csv'),'utf8')),'Profit','Original');
assert.ok(Math.abs(original.records[original.selected_index].test_rmse-full.test_rmse)>1000);
const missing=['x,z,target',...Array.from({length:40},(_,i)=>`${i===5?'':i},${(i*13)%17},${i===7?'':100+2*i+3*((i*13)%17)}`)].join('\n');
const cleaned=engine.analyze(engine.parseCSV(missing),'target','Missing data');assert.equal(cleaned.quality.excluded_target_rows,1);assert.equal(cleaned.n,39);
const malicious=engine.parseCSV('x,"<img src=x onerror=alert(1)>",y\n1,2,3\n2,3,4');assert.equal(malicious.headers[1],'<img src=x onerror=alert(1)>');
const check={passed:true,python_subset_comparisons:records,csv_edge_cases:true,known_linear_model:true,missing_target_handling:true};
fs.writeFileSync(path.join(root,'output/engine_verification.json'),JSON.stringify(check,null,2));console.log(check);
