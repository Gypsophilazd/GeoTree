import unittest,io,json
from studio.backend.deepseek import call
class TestResponses(unittest.TestCase):
 def test_sse(self):
  a={'request_id':'fixture','action':'run_freecad','code':'import FreeCAD','reason':'fixture'}
  ev=[{'type':'response.output_text.delta','delta':json.dumps(a)},
      {'type':'response.completed','response':{'model':'deepseek-flash','usage':{'input_tokens':9,'output_tokens':5}}}]
  def fake(req,timeout):
   self.assertEqual(req.full_url,'https://api.deepseek.com/responses')
   self.assertEqual(json.loads(req.data)['model'],'deepseek-flash')
   self.assertTrue(json.loads(req.data)['stream'])
   return io.BytesIO(b''.join(b'data: '+json.dumps(e).encode()+b'\n\n' for e in ev))
  x,u,m=call('fixture',lambda *x:None,fake,key='fake')
  self.assertEqual((x,u,m),(a,{'input_tokens':9,'output_tokens':5},'deepseek-flash'))
 def test_failed(self):
  with self.assertRaisesRegex(RuntimeError,'response.failed'):
   call('fixture',lambda *x:None,lambda *a,**k:io.BytesIO(b'data: {"type":"response.failed"}\n'),key='fake')
 def test_bad_json(self):
  with self.assertRaises(json.JSONDecodeError):
   call('fixture',lambda*x:None,lambda *a,**k:io.BytesIO(b'data: {"type":"response.completed","response":{"output":[{"content":[{"type":"output_text","text":"not JSON"}]}]}}\n'),key='fake')
if __name__=='__main__':unittest.main(verbosity=2)
