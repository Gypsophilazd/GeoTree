"""Fail-closed single-trial gate; not a launcher."""
import argparse,json,math,sys
from pathlib import Path

def gate(root,live=False):
    if (root/'exit').read_text().strip()!='0':raise ValueError('nonzero Harbor CLI exit')
    files=list((root/'jobs'/root.name).glob('*/result.json'))
    if len(files)!=1:raise ValueError('expected exactly one trial result')
    p=files[0];r=json.loads(p.read_text())
    if not isinstance(r,dict) or 'exception_info' not in r:raise ValueError('missing exception status')
    if r['exception_info'] is not None:
        raise ValueError('trial exception: '+str(r['exception_info'].get('exception_type','unknown')))
    if not r.get('finished_at'):raise ValueError('trial not finished')
    tr=p.parent/'agent/trace.jsonl'
    events=[json.loads(x) for x in tr.read_text().splitlines()]
    terminal=[e['data']['status'] for e in events if e['event']=='terminal']
    if terminal not in (['done'],['decision_budget_exhausted'],['cad_budget_exhausted'],['token_soft_budget']):
        raise ValueError('missing or unacceptable terminal status')
    if any(e['event']=='fatal' or (e['event']=='feedback' and (e['data'].get('status') in ('timeout','execution_error') or e['data'].get('task_grounded',{}).get('status')=='ERROR')) for e in events):
        raise ValueError('runtime or tool infrastructure failure')
    if live:
        v=r.get('verifier_result') or {}
        reward=(v.get('rewards') or {}).get('reward')
        if r.get('verifier_environment_mode')!='separate' or type(reward) not in (int,float) or not math.isfinite(reward):
            raise ValueError('missing separate verifier reward')
    return terminal[0]

def main():
    p=argparse.ArgumentParser();p.add_argument('trial_root',type=Path);p.add_argument('--live',action='store_true')
    a=p.parse_args()
    try:st=gate(a.trial_root,a.live)
    except (OSError,ValueError,TypeError,KeyError,AttributeError) as e:
        print(f'REJECT: {e}');return 2
    print(f'ACCEPT: terminal={st}');return 0
if __name__=='__main__':sys.exit(main())
