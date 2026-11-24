import FreeCAD as A, math, json, hashlib
from pathlib import Path
d=A.openDocument('/source/answer.FCStd')
r=A.openDocument('/replay/answer.FCStd')
def body(d):
 b,=[x for x in d.Objects if x.TypeId=='PartDesign::Body']
 s=b.Shape
 assert s.isValid() and len(s.Solids)==1
 return s
s=body(d);t=body(r);bb=s.BoundBox
prompt=Path('/source/public.txt').read_text()
holes=[];outer=[]
for f in s.Faces:
 c=f.Surface
 if type(c).__name__!='Cylinder' or abs(abs(c.Axis.z)-1)>1e-6:continue
 u,v,w,z=f.ParameterRange
 if v-u<2*math.pi-1e-5 or abs(f.BoundBox.ZLength-bb.ZLength)>1e-5:continue
 h=f.valueAt((u+v)/2,(w+z)/2)-c.Center
 rd=h-c.Axis*h.dot(c.Axis)
 data=dict(x=c.Center.x,y=c.Center.y,diameter=c.Radius*2)
 (holes if rd.dot(f.normalAt((u+v)/2,(w+z)/2))<0 else outer).append(data)
import re
def num(x):return float(re.search(x+r'([0-9.]+)\s*mm',prompt).group(1))
rows={}
def check(k,expected,actual):
 rows[k]=dict(expected=expected,actual=actual,status='PASS' if abs(expected-actual)<.02 else 'FAIL',tolerance=.02)
check('thickness',num('厚'),bb.ZLength)
if '矩形' in prompt and '圆盘' not in prompt:
 check('length',num('长'),max(bb.XLength,bb.YLength));check('width',num('宽'),min(bb.XLength,bb.YLength))
 check('through_hole_count',4,len(holes))
 for i,h in enumerate(holes):
  check('diameter_'+str(i),num('直径'),h['diameter'])
  check('x_margin_'+str(i),10,min(h['x']-bb.XMin,bb.XMax-h['x']))
  check('y_margin_'+str(i),10,min(h['y']-bb.YMin,bb.YMax-h['y']))
else:
 o,=outer
 check('outer_diameter',num('外径'),o['diameter'])
 center=[h for h in holes if math.hypot(h['x']-o['x'],h['y']-o['y'])<.02]
 bolts=[h for h in holes if h not in center]
 if len(center)==1:check('bore',num('中心开直径'),center[0]['diameter'])
 else:check('center_bore_count',1,len(center))
 check('bolt_count',4,len(bolts))
 ang=sorted(math.atan2(h['y']-o['y'],h['x']-o['x']) for h in bolts)
 for i,h in enumerate(bolts):
  check('bolt_diameter_'+str(i),num('个直径'),h['diameter'])
  check('pitch_radius_'+str(i),num('半径'),math.hypot(h['x']-o['x'],h['y']-o['y']))
 if len(ang)==4:
  for i in range(4):check('angle_spacing_deg_'+str(i),90,math.degrees((ang[(i+1)%4]-ang[i])%(2*math.pi)))
print('E06='+json.dumps({'artifact_sha256':hashlib.sha256(Path('/source/answer.FCStd').read_bytes()).hexdigest(),'public_sha256':hashlib.sha256(prompt.encode()).hexdigest(),'rows':rows,'replay_symmetric_volume_mm3':[s.cut(t).Volume,t.cut(s).Volume]}))
