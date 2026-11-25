"""Recalculate saved evidence; does not train or run traffic experiments."""
from pathlib import Path
import hashlib, json

ROOT = Path(__file__).resolve().parents[1]
def read(name):
    return json.loads((ROOT / name).read_text(encoding='utf-8'))
def summarize(pairs):
    fixed = sum(p['fixed'] for p in pairs)
    model = sum(p['model'] for p in pairs)
    return {'pairs': len(pairs), 'fixed_qvs': fixed, 'model_qvs': model,
            'relative_change_percent': 100 * (model / fixed - 1),
            'improved': sum(p['model'] < p['fixed'] for p in pairs),
            'regressed': sum(p['model'] > p['fixed'] for p in pairs),
            'unchanged': sum(p['model'] == p['fixed'] for p in pairs),
            'cases': pairs}

raw = read('evidence/firmware_validation_original.json')
by_key = {}
for row in raw['scenarios']:
    by_key.setdefault((row['scenario'],row['seed']),{})[row['policy']] = row
pairs18 = []
for (scenario,seed), policies in by_key.items():
    f=policies['fixed_balanced']; m=policies['tiny_tree_rules_fallback']
    assert f['seconds']==m['seconds']==600
    assert f['arrived_vehicles']==m['arrived_vehicles']
    pairs18.append({'scenario':scenario,'seed':seed,'fixed':f['queue_vehicle_seconds'],
                    'model':m['queue_vehicle_seconds']})
six=read('evidence/comparison_6pairs_original.json')['pairs']
pairs6=[{'scenario':p['scenario'],'seed':p['seed'],
         'fixed':p['fixed']['queue_vehicle_seconds'],
         'model':p['model']['queue_vehicle_seconds']} for p in six]
a=summarize(pairs18); b=summarize(pairs6)
assert (a['pairs'],a['fixed_qvs'],a['model_qvs'],a['improved'],a['regressed']) == (18,399954,326830,13,5)
assert (b['pairs'],b['fixed_qvs'],b['model_qvs'],b['improved'],b['regressed']) == (6,137493,110395,4,2)
source_checks=[]
for f in read('source_manifest.json')['files']:
    actual=hashlib.sha256((ROOT/f['snapshot']).read_bytes()).hexdigest()
    assert actual==f['sha256'], f['snapshot']
    original=ROOT.parents[1]/f['source']
    original_unchanged=(hashlib.sha256(original.read_bytes()).hexdigest()==actual) if original.exists() else None
    assert original_unchanged is not False, f['source']
    source_checks.append({'snapshot':f['snapshot'],'sha256_match':True,'original_unchanged':original_unchanged})
result={'status':'PASS','kind':'recalculation_of_existing_saved_results',
        'new_training':False,'new_board_run':False,'new_traffic_experiment':False,
        'batches_must_not_be_combined':True,'host_18_pairs':a,'host_6_pairs':b,
        'source_integrity':source_checks}
(ROOT/'evidence/data_audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k not in ('host_18_pairs','host_6_pairs','source_integrity')},ensure_ascii=False))
print('18 pairs:', a['fixed_qvs'],a['model_qvs'],round(a['relative_change_percent'],2))
print('6 pairs:', b['fixed_qvs'],b['model_qvs'],round(b['relative_change_percent'],2))
