import unittest
from geotree.geometry_observer import check_constraints,GeometryObservation,inspect_file
class Contract(unittest.TestCase):
 def c(self,**kw):return dict(id='fixture',metric='solid_count',expected=1,source={'kind':'fixture','reviewed':True,'locator':'unit fixture'},mapping_reviewed=True)|kw
 def test_valid_not_correct(self):
  o=GeometryObservation(shape_valid=True,solid_count=2).to_dict();self.assertEqual(check_constraints(o,[self.c()])[0]['status'],'FAIL');self.assertIn('target_geometry_correctness',o['unknown_fields'])
 def test_unknown_target(self):self.assertEqual(check_constraints({'volume':20},[self.c(metric='volume',expected=None)])[0]['status'],'UNKNOWN')
 def test_no_source(self):self.assertEqual(check_constraints({'solid_count':1},[self.c(source={})])[0]['status'],'UNKNOWN')
 def test_no_mapping(self):self.assertEqual(check_constraints({'solid_count':1},[self.c(mapping_reviewed=False)])[0]['status'],'UNKNOWN')
 def test_equal_and_wrong_size(self):
  c=self.c(metric='bounding_box.XLength',expected=10,tolerance=.001);self.assertEqual(check_constraints({'bounding_box':{'XLength':10}},[c])[0]['status'],'PASS');self.assertEqual(check_constraints({'bounding_box':{'XLength':11}},[c])[0]['status'],'FAIL')
 def test_nonfinite(self):self.assertEqual(check_constraints({'solid_count':1},[self.c(expected=float('nan'))])[0]['status'],'UNKNOWN')
 def test_path(self):
  with self.assertRaises(ValueError):inspect_file('/etc/passwd','/app')
if __name__=='__main__':unittest.main()
