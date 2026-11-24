import FreeCAD as A,Part,sys,os,json,hashlib,math
from pathlib import Path
from dataclasses import asdict
sys.path.insert(0,'/worker')
from active_bundle import public_specs,right_measure,slab
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def open_doc(name):return A.openDocument(name)
def shape(d):
 b=[o for o in d.Objects if o.TypeId=='PartDesign::Body']
 if len(b)!=1:raise ValueError('expected one body')
 return b[0].Shape
def tree(d):return [(o.Name,o.TypeId) for o in d.Objects]
def inspect(d,p,text,c):
 v,q=public_specs(text)
 s=shape(d)
 if s.isNull() or not s.isValid() or len(s.Solids)!=1:raise ValueError('invalid solid')
 if any(set(o.State)&{'Invalid','Error','Touched'} for o in d.Objects):raise ValueError('invalid feature state')
 r=right_measure(d,q[c['constraint_id']],text,sha(p),slab)
 # The profile identity is independently supported by the BRep witness. Here
 # verify the declared parametric feature owns the same measured support edges.
 f=d.getObject(c['feature']);sk=d.getObject(c['profile'])
 valid=f and sk and f.TypeId=='PartDesign::Pocket' and sk.TypeId=='Sketcher::SketchObject' and f.Profile[0].Name==sk.Name
 if not valid:raise ValueError('parametric dependency missing')
 pts=sorted({(round(float(p.Point.x),6),round(float(-p.Point.z),6)) for e in sk.Shape.Edges for p in e.Vertexes})
 seg=r['mapping'][0]['support_segments'] if r['mapping'] else []
 matched=sorted({tuple(round(v,6) for v in p) for e in seg for p in e})
 if pts!=matched or len(pts)!=3:raise ValueError('profile does not uniquely match BRep support')
 x,y=c['base_left'];w,h=c['base_length'],c['height']
 bases=[v for v in pts if abs(v[1]-y)<1e-5]
 apex=[v for v in pts if abs(v[1]-y-h)<1e-5]
 bounds=s.BoundBox
 other=dict(base_ok=bases==[(round(x,6),round(y,6)),(round(x+w,6),round(y,6))],
   height_ok=len(apex)==1,thickness_ok=abs(bounds.YLength-c['thickness'])<1e-6,
   right_vertex_ok=len(apex)==1 and c['corner'] in ('left','right') and abs(apex[0][0]-(x+(w if c['corner']=='right' else 0)))<1e-5,
   sketch_points=pts)
 return r,other
def diff(a,b,roi):
 s,t=shape(a),shape(b)
 x0,y0,x1,y1=roi
 box=Part.makeBox(x1-x0,20,y1-y0,A.Vector(x0,-5,-y1))
 ds=[s.cut(t),t.cut(s)]
 return [x.Volume for x in ds],[x.cut(box).Volume for x in ds]
mode=sys.argv[1]; text=Path('/in/instruction.md').read_text()
c=json.loads(Path('/in/contract.json').read_text())
old='/in/answer.FCStd'; d=open_doc(old)
r,b=inspect(d,old,text,c)
out=dict(before=r,before_constraints=b)
if mode=='compare':
 p='/app/answer.FCStd'; n=open_doc(p)
 rr,bb=inspect(n,p,text,c)
 dv,external=diff(d,n,c['roi'])
 out.update(after=rr,after_constraints=bb,diff_mm3=dv,outside_mm3=external,tree_same=tree(d)==tree(n))
 # Established contractual checks select the known dimension failure independently
 # of spatial leak, without discarding either check.
 problems=[]
 if rr['status']!='PASS':problems.append('target_fail_or_unknown')
 if not all(bb[k] for k in ('base_ok','height_ok','thickness_ok','right_vertex_ok')):problems.append('retained_constraints_or_vertex')
 if not out['tree_same'] or max(external)>1e-5:problems.append('dependency_or_outside_roi')
 out['problems']=problems
elif mode=='replay':
 p='/app/answer.FCStd';n=open_doc(p)
 x=shape(d);y=shape(n)
 out=dict(replay_valid=y.isValid() and len(y.Solids)==1,tree_same=tree(d)==tree(n),symmetric_diff=[x.cut(y).Volume,y.cut(x).Volume])
 print('E05='+json.dumps(out));sys.exit(0)
print('E05='+json.dumps(out))
