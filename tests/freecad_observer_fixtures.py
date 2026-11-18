import json,sys
import FreeCAD as App,Part
from geotree.geometry_observer import observe_document,inspect_file
out={}
cs=json.load(open('/app/constraints.json'))
out['existing']=inspect_file('/app/input/answer.FCStd','/app/input',cs).to_dict()
assert out['existing']['shape_valid'] is True and out['existing']['solid_count']==1
assert all(c['status']=='PASS' for c in out['existing']['constraint_checks'][:5])
assert out['existing']['constraint_checks'][-1]['status']=='UNKNOWN'
d=App.newDocument('FixtureValid');b=d.addObject('PartDesign::Body','Body');s=b.newObject('Sketcher::SketchObject','Rectangle')
for a,c in [((0,0),(10,0)),((10,0),(10,5)),((10,5),(0,5)),((0,5),(0,0))]:s.addGeometry(Part.LineSegment(App.Vector(*a,0),App.Vector(*c,0)),False)
p=b.newObject('PartDesign::Pad','Pad');p.Profile=s;p.Length=2;d.recompute()
c=dict(id='width',metric='bounding_box.XLength',expected=12,tolerance=0,mapping_reviewed=True,source=dict(kind='fixture',reviewed=True,locator='intentional wrong-size fixture'))
out['valid_but_wrong_dimension']=observe_document(d,[c]).to_dict();assert out['valid_but_wrong_dimension']['shape_valid'];assert out['valid_but_wrong_dimension']['constraint_checks'][0]['status']=='FAIL';App.closeDocument(d.Name)
d=App.newDocument('FixtureDisconnected');f=d.addObject('Part::Feature','Compound');f.Shape=Part.makeCompound([Part.makeBox(1,1,1),Part.makeBox(1,1,1,App.Vector(4,0,0))]);d.recompute();out['two_solids']=observe_document(d).to_dict();assert out['two_solids']['solid_count']==2;assert 'not_single_solid' in out['two_solids']['geometry_errors'];App.closeDocument(d.Name)
d=App.newDocument('FixtureBroken');b=d.addObject('PartDesign::Body','Body');p=b.newObject('PartDesign::Pad','NoProfile');d.recompute();out['missing_profile']=observe_document(d).to_dict();assert any('missing Profile' in x for x in out['missing_profile']['dependency_warnings']);App.closeDocument(d.Name)
d=App.newDocument('FixtureEmpty');out['empty']=observe_document(d).to_dict();assert out['empty']['shape_valid'] is None;App.closeDocument(d.Name)
# Report an actual upstream execution error independently of geometric facts.
d=App.newDocument('FixtureError');out['execution_error']=observe_document(d,execution_errors=['fixture tool exited 7']).to_dict();assert out['execution_error']['execution_errors'];App.closeDocument(d.Name)
print('GEOTREE_JSON_BEGIN')
print(json.dumps(out,indent=2,allow_nan=False))
print('GEOTREE_JSON_END')
print('PASS 6 FreeCAD observer cases (existing + 5 synthetic); no benchmark or model run')
