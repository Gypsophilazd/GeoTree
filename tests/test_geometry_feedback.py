import asyncio,json,tempfile,unittest
from pathlib import Path
from geotree.geometry_observer import GeometryObservation
from geotree.geometry_feedback import GeometryFeedbackExecutor
from geotree.nosearch import MockProvider,NoSearchRuntime,FeedbackRecorder,ActionProposal
class Base:
    def __init__(self,code=0):self.code=code;self.calls=0
    async def execute(self,p):self.calls+=1;return {'status':'executed','exit_status':self.code,'stdout':'','stderr':''}
class Integration(unittest.IsolatedAsyncioTestCase):
    async def test_loop_and_atif(self):
        p=MockProvider(['run_freecad','done']);base=Base()
        async def reader():return GeometryObservation(shape_valid=True,solid_count=1)
        with tempfile.TemporaryDirectory() as tmp:
            r=NoSearchRuntime(p,GeometryFeedbackExecutor(base,reader),FeedbackRecorder(tmp),max_steps=2)
            self.assertEqual(await r.run('synthetic task'),'done');self.assertEqual(base.calls,1)
            feedback=p.observations[1]['history'][0]['geometry_observer']
            self.assertTrue(feedback['observation']['shape_valid']);self.assertIn('target_geometry_correctness',feedback['observation']['unknown_fields'])
            self.assertNotIn('reward',json.dumps(p.observations))
            from harbor.models.trajectories import Trajectory
            tr=Trajectory.model_validate_json((Path(tmp)/'trajectory.json').read_text());self.assertEqual(len(tr.steps),2)
            self.assertEqual(len([json.loads(x) for x in (Path(tmp)/'trace.jsonl').read_text().splitlines()]),6)
    async def test_failed_execution_no_stale_observation(self):
        async def reader():raise AssertionError('must not inspect stale artifact')
        result=await GeometryFeedbackExecutor(Base(1),reader).execute(ActionProposal('1','run_freecad','',''))
        self.assertEqual(result['geometry_observer']['status'],'NOT_RUN');self.assertEqual(result['exit_status'],1)
    async def test_observer_failure_preserves_execution(self):
        async def reader():raise ValueError('invalid file')
        result=await GeometryFeedbackExecutor(Base(),reader).execute(ActionProposal('1','run_freecad','',''))
        self.assertEqual(result['geometry_observer']['status'],'ERROR');self.assertEqual(result['exit_status'],0)
    async def test_observer_timeout(self):
        async def reader():await asyncio.sleep(1)
        result=await GeometryFeedbackExecutor(Base(),reader,timeout_sec=.001).execute(ActionProposal('1','run_freecad','',''))
        self.assertEqual(result['geometry_observer']['status'],'ERROR');self.assertEqual(result['exit_status'],0)
    async def test_non_geometry_action(self):
        async def reader():raise AssertionError('must not run')
        result=await GeometryFeedbackExecutor(Base(),reader).execute(ActionProposal('1','check_workspace','',''))
        self.assertNotIn('geometry_observer',result)
    async def test_untyped_payload_rejected(self):
        async def reader():return {'reward':1}
        result=await GeometryFeedbackExecutor(Base(),reader).execute(ActionProposal('1','run_freecad','',''))
        self.assertEqual(result['geometry_observer']['status'],'ERROR');self.assertNotIn('reward',str(result))
if __name__=='__main__':unittest.main()
