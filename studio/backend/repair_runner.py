import ast,json,hashlib,os,re,sys,subprocess,time,shutil
from pathlib import Path
from dataclasses import dataclass,asdict
D=Path(__file__).resolve().parent
from .core import IMAGE
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,x):Path(p).write_text(json.dumps(x,indent=2)+'\n')
def run(c,cmd,save=None):
 a=['docker','run','--rm','--pull','never','--network','none','--cpus','2','--memory','4g','--pids-limit','128','--user','65534:65534','--cap-drop','ALL','--security-opt','no-new-privileges','--read-only','--tmpfs','/app:rw,nosuid,nodev,size=128m,mode=1777','--tmpfs','/tmp:rw,nosuid,nodev,size=64m,mode=1777','-e','HOME=/tmp','-e','QT_QPA_PLATFORM=offscreen','-e','OMP_NUM_THREADS=1','-e','OPENBLAS_NUM_THREADS=1']
 for src,dst in c:
  p=Path(src)
  if p.is_symlink() or not p.exists():raise ValueError('invalid mount')
  a+=['--mount',f'type=bind,source={p.resolve()},target={dst},readonly']
 if save:
  save=Path(save);save.mkdir();save.chmod(0o777)
  a+=['--mount',f'type=bind,source={save.resolve()},target=/out']
 start=time.monotonic()
 res=subprocess.run(a+['--workdir','/app','--entrypoint','/bin/bash',IMAGE,'-ec',cmd],capture_output=True,text=True,timeout=90)
 return dict(rc=res.returncode,wall=time.monotonic()-start,stdout=res.stdout,stderr=res.stderr,mount_names=[x[1] for x in c])
def mounts(case,script=None,baseline=None):
 a=[(D/'repair_worker.py','/worker/check.py'),(D/'active_bundle.py','/worker/active_bundle.py'),
  (case/'instruction.md','/in/instruction.md'),(case/'contract.json','/in/contract.json')]
 if script:a.append((script,'/in/answer.py'))
 if baseline:a.append((baseline,'/in/answer.FCStd'))
 return a
PYTHON='/opt/conda/bin/python -I '
BUILD='cp /in/answer.py /app/answer.py; timeout 45s '+PYTHON+'/app/answer.py; test -s /app/answer.FCStd; '
def data(r):
 if r['rc']!=0:raise ValueError('worker exit '+str(r['rc']))
 rows=[x[4:] for x in r['stdout'].splitlines() if x.startswith('E05=')]
 if len(rows)!=1:raise ValueError('missing geometry acceptance packet')
 return json.loads(rows[0])
def facts(c):
 return {f:sha(c/f) for f in ('answer.py','answer.FCStd','instruction.md','contract.json')}
def parse_contract(c):
 doc=(c/'instruction.md').read_text()
 m=re.search(r'^Repair contract: base left=\(([-.0-9]+),([-.0-9]+)\) mm; base=([.0-9]+) mm; height=([.0-9]+) mm; thickness=([.0-9]+) mm; right angle at (left|right|unspecified) base endpoint; preserve all geometry outside ROI=\(([-.,0-9]+)\)\.$',doc,re.M)
 if not m:raise ValueError('repair contract missing')
 x,y,w,h,t=map(float,m.groups()[:5]);roi=list(map(float,m[7].split(',')))
 v=dict(base_left=[x,y],base_length=w,height=h,thickness=t,corner=m[6],roi=roi,feature='TargetCut',profile='TargetProfile',constraint_id='repair_port')
 if json.loads((c/'contract.json').read_text())!=v:raise ValueError('trusted contract mismatch')
 return v
def edit(src,param,target):
 if not isinstance(target,(int,float)) or isinstance(target,bool) or not -1000<=target<=1000:raise ValueError('bounded literal required')
 tree=ast.parse(src); found=[x for x in tree.body if isinstance(x,ast.Assign) and len(x.targets)==1 and isinstance(x.targets[0],ast.Name) and x.targets[0].id==param and isinstance(x.value,ast.Constant) and type(x.value.value) in (int,float)]
 if len(found)!=1:raise ValueError('nonunique numeric slot')
 x=found[0].value;ls=src.splitlines(keepends=True)
 if x.lineno!=x.end_lineno or not src.isascii():raise ValueError('source span')
 l=ls[x.lineno-1];ls[x.lineno-1]=l[:x.col_offset]+repr(float(target))+l[x.end_col_offset:]
 patched=''.join(ls)
 # Prove that the two syntax trees differ only at the specified numeric slot.
 rhs=str(x.value);x.value=float(target)
 if ast.dump(ast.parse(patched))!=ast.dump(tree):raise ValueError('AST drift')
 return patched,rhs
def certify(c):
 before=run(mounts(c,baseline=c/'answer.FCStd'),PYTHON+'/worker/check.py baseline')
 return before,data(before)
@dataclass(frozen=True)
class RepairProposal:
    operation:str
    parameter:str
    new_value:float
    intent:str
def attempt(c,out,packet,frozen,test_fault=None,certification=None):
 start=time.monotonic()
 out.mkdir();before=facts(c)
 if before!=frozen:raise ValueError('frozen input changed')
 evidence,base=certification if certification else certify(c)
 dump(out/'baseline.json',evidence)
 cc=parse_contract(c)
 envelope=dict(original_sha=before,constraint_id=cc['constraint_id'],fail=base['before'],target_feature=cc['feature'],
    proposal=packet,keep=cc,affected_roi=cc['roi'],test_fault=test_fault)
 dump(out/'proposal.json',envelope)
 def done(status,reason,**kwargs):
  assert facts(c)==before
  rec=dict(status=status,reason=reason,original_unchanged=True,accepted_pair_exists=(out/'accepted').exists(),
    elapsed=time.monotonic()-start,**kwargs)
  dump(out/'result.json',rec);return rec
 if base['before']['status']!='FAIL':return done('REJECTED','no_credible_fail')
 if cc['corner']=='unspecified':return done('UNKNOWN','public vertex unspecified')
 if set(packet)!={'operation','parameter','new_value','intent'}:return done('REJECTED','proposal schema')
 p=RepairProposal(**packet)
 if p.operation!='set_literal' or p.parameter!='APEX_X':return done('REJECTED','operation not allowed')
 try:src,_=edit((c/'answer.py').read_text(),p.parameter,p.new_value)
 except ValueError as e:return done('REJECTED',str(e))
 if test_fault:
  # Test-only mutation after the normal typed patch, never exposed to callers/models.
  src,_=edit(src,test_fault[0],test_fault[1])
 editpath=out/'answer.py';editpath.write_text(src)
 import difflib
 (out/'answer.diff').write_text(''.join(difflib.unified_diff((c/'answer.py').read_text().splitlines(True),src.splitlines(True),fromfile='original',tofile='candidate')))
 rr=run(mounts(c,editpath,c/'answer.FCStd'),BUILD+PYTHON+'/worker/check.py compare; cp /app/answer.FCStd /out/answer.FCStd',out/'staging')
 dump(out/'build.json',rr)
 try:post=data(rr)
 except ValueError as e:return done('REJECTED',str(e),build_wall=rr['wall'])
 if post['problems']:return done('REJECTED','postconditions_failed',geometry=post,build_wall=rr['wall'])
 candidate=out/'staging'/'answer.FCStd'
 rp=run(mounts(c,editpath,candidate),'cp /in/answer.py /app/answer.py; timeout 45s freecadcmd /app/answer.py </dev/null; test -s /app/answer.FCStd; '+PYTHON+'/worker/check.py replay')
 dump(out/'replay.json',rp)
 try:replay=data(rp)
 except ValueError as e:return done('REJECTED','replay:'+str(e),geometry=post)
 if not(replay['replay_valid'] and replay['tree_same'] and max(replay['symmetric_diff'])<1e-5):
  return done('REJECTED','replay_mismatch',geometry=post,replay=replay)
 if test_fault:return done('REJECTED','test injection never publish')
 publish=out/'publish';publish.mkdir()
 for src,f in [(editpath,'answer.py'),(candidate,'answer.FCStd')]:
  shutil.copyfile(src,publish/f);(publish/f).chmod(0o444)
 publish.rename(out/'accepted')
 return done('ACCEPTED','isolated repair and independent replay verified',geometry=post,replay=replay,build_wall=rr['wall'],replay_wall=rp['wall'],
             accepted_sha={f:sha(out/'accepted'/f) for f in ('answer.py','answer.FCStd')})
def rule(cc):
 return dict(operation='set_literal',parameter='APEX_X',new_value=cc['base_left'][0]+(cc['base_length'] if cc['corner']=='right' else 0),intent='align apex to public right-angle endpoint')
