"""FreeCAD geometry fixtures and untrusted packet controls for E03, no scorer."""
import unittest
import sys
from dataclasses import asdict
from pathlib import Path
try:
    import FreeCAD as App, Part
except ImportError as exc:
    raise unittest.SkipTest("Run this suite with the FreeCAD container") from exc
sys.path.insert(0,"/opt/geotree")
from active_geometry import public_specs,validate_query,result,FRAME_EVIDENCE,MAPPING_EVIDENCE,MOUNT_EVIDENCE,TRAP_EVIDENCE

class ActiveGeometry(unittest.TestCase):
    def setUp(self):
        values=dict(plate_thickness=8,center_bore_diameter=7,center_bore_axis_y=264.5,
                    mounting_hole_diameter=4,central_trapezoidal_opening_lower_flat_width=24,
                    central_trapezoidal_opening_corner_radius=2,truss_layout_symmetry_axis_x=0,
                    middle_outer_rectangle_center_y=0,middle_outer_rectangle_height=240,
                    small_outer_rectangle_center_y=260,small_outer_rectangle_height=30,
                    side_mounting_hole_axis_x=40,side_mounting_hole_row_1_y=20,
                    central_trapezoidal_opening_center_y=0)
        self.source="\n".join([FRAME_EVIDENCE,MAPPING_EVIDENCE,MOUNT_EVIDENCE,*TRAP_EVIDENCE,
                    "- base_sketch_plane_rotation_angle = 90 degrees",
                    *(f"- {k} = {v} mm" for k,v in values.items())])
        self.values,self.cat=public_specs(self.source)
        self.doc=App.newDocument('Control')
    def tearDown(self):
        App.closeDocument(self.doc.Name)
    def build(self,thickness=8.,diameter=7.,positions=(264.5,)):
        shape=Part.makeBox(280,thickness,550,App.Vector(-140,0,-275))
        for py in positions:
            cyl=Part.makeCylinder(diameter/2,thickness+2,App.Vector(0,-1,-py),App.Vector(0,1,0))
            shape=shape.cut(cyl)
        b=self.doc.addObject('PartDesign::Body','Body')
        f=b.newObject('PartDesign::Feature','SyntheticShape');f.Shape=shape
        self.doc.recompute()
        self.assertTrue(b.Shape.isValid())
    def inspect(self,key):return result(self.doc,self.cat[key],self.values,'0'*64)
    def test_pass(self):
        self.build()
        for k in ('plate_thickness','plate_datum_y','center_bore_diameter','center_bore_axis_y'):
            self.assertEqual(self.inspect(k)['status'],'PASS')
    def test_wrong_values_same_mapping(self):
        self.build(thickness=9.,diameter=5.,positions=(258.,))
        for k,expected in [('plate_thickness',9.),('center_bore_diameter',5.),('center_bore_axis_y',258.)]:
            row=self.inspect(k);self.assertTrue(row['unique_mapping'])
            self.assertEqual(row['status'],'FAIL');self.assertAlmostEqual(row['measured'],expected)
    def test_duplicate_is_unknown_not_closest_to_expected(self):
        self.build(diameter=4.,positions=(248.,264.5))
        self.assertEqual(self.inspect('center_bore_axis_y')['status'],'UNKNOWN')
    def test_forged_query_and_unproven_source(self):
        a=asdict(self.cat['center_bore_diameter'])
        self.assertEqual(validate_query(a,self.cat),self.cat['center_bore_diameter'])
        for bad in (a|{'verified':True},a|{'evidence_source':'fake'},a|{'constraint_id':'/app/private'}):
            with self.assertRaises(ValueError):validate_query(bad,self.cat)
        self.assertEqual(public_specs(self.source.replace("global -Z","global +Z")),({},{}))
if __name__=='__main__':unittest.main(verbosity=2)
