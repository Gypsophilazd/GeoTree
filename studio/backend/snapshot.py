import FreeCAD as App, MeshPart, json, hashlib
from pathlib import Path
p=Path('/app/answer.FCStd')
d=App.openDocument(str(p))
steps=[]
bodies=[x for x in d.Objects if x.TypeId=='PartDesign::Body']
for b in bodies:
 for o in b.Group:
  if o.TypeId not in ('PartDesign::Pad','PartDesign::Pocket','PartDesign::Fillet','PartDesign::Chamfer','PartDesign::Revolution','PartDesign::AdditiveLoft'):continue
  s=o.Shape
  if s.isNull() or not s.isValid() or not s.Solids:continue
  mesh=MeshPart.meshFromShape(Shape=s,LinearDeflection=.35,AngularDeflection=.22,Relative=False)
  stem=f'step-{len(steps)}'
  mesh.write('/out/'+stem+'.stl')
  pts,faces=mesh.Topology
  Path('/out/'+stem+'.json').write_text(json.dumps({'v':[[v.x,v.y,v.z] for v in pts],'f':faces}))
  bb=s.BoundBox
  steps.append(dict(name=o.Label,type=o.TypeId,volume=s.Volume,unit='mm³',mesh=stem+'.json',stl=stem+'.stl',valid=True,solids=len(s.Solids),bounds=[bb.XLength,bb.YLength,bb.ZLength]))
assert steps and len(bodies)==1 and len(bodies[0].Shape.Solids)==1 and bodies[0].Shape.isValid() and bodies[0].Tip.TypeId==steps[-1]['type']
Path('/out/steps.json').write_text(json.dumps({'mode':'FEATURE RECONSTRUCTION','steps':steps,'artifact_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'freecad':App.Version()[:3]}))
