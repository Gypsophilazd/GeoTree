import FreeCAD as App
import Part
import Sketcher
X0 = 24
Y0 = 24
BASE = 26
HEIGHT = 20
APEX_X = 37
THICKNESS = 5
REMOTE_HOLE_X = 91
d=App.newDocument('RepairPlate')
b=d.addObject('PartDesign::Body','Plate')
frame=App.Placement(App.Vector(0,0,0),App.Rotation(App.Vector(1,0,0),-90))
s=b.newObject('Sketcher::SketchObject','Stock')
s.Placement=frame
p=[App.Vector(0,0,0),App.Vector(110,0,0),App.Vector(110,100,0),App.Vector(0,100,0)]
for i in range(4):
 s.addGeometry(Part.LineSegment(p[i],p[(i+1)%4]),False)
pad=b.newObject('PartDesign::Pad','StockPad')
pad.Profile=s
pad.Length=THICKNESS
d.recompute()
t=b.newObject('Sketcher::SketchObject','TargetProfile')
t.Placement=frame
q=[App.Vector(X0,Y0,0),App.Vector(X0+BASE,Y0,0),App.Vector(APEX_X,Y0+HEIGHT,0)]
for i in range(3):
 t.addGeometry(Part.LineSegment(q[i],q[(i+1)%3]),False)
d.recompute()
c=b.newObject('PartDesign::Pocket','TargetCut')
c.Profile=t
c.Reversed=True
c.Length=THICKNESS
d.recompute()
z=b.newObject('Sketcher::SketchObject','WitnessProfile')
z.Placement=frame
z.addGeometry(Part.Circle(App.Vector(REMOTE_HOLE_X,76,0),App.Vector(0,0,1),3),False)
d.recompute()
w=b.newObject('PartDesign::Pocket','WitnessCut')
w.Profile=z
w.Reversed=True
w.Length=THICKNESS
d.recompute()
d.saveAs('/app/answer.FCStd')
