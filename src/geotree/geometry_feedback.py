"""Opt-in G1 executor decorator. Existing agent entry points remain unchanged.
The injected reader must use the same task environment and read only agent artifacts.
No benchmark reward is accepted as geometry feedback. Not a security boundary.
"""
import asyncio
from geotree.geometry_observer import GeometryObservation

class GeometryFeedbackExecutor:
    def __init__(self, executor, read_geometry, timeout_sec=10):
        self.executor = executor
        self.read_geometry = read_geometry
        self.timeout_sec = timeout_sec

    async def execute(self, proposal):
        result = dict(await self.executor.execute(proposal))
        if proposal.action != 'run_freecad':
            return result
        if result.get('exit_status') != 0:
            result['geometry_observer'] = {'status': 'NOT_RUN', 'reason': 'execution_failed; prior artifact may be stale'}
            return result
        try:
            observation = await asyncio.wait_for(self.read_geometry(), self.timeout_sec)
            if not isinstance(observation, GeometryObservation):
                raise TypeError('reader must return GeometryObservation')
            result['geometry_observer'] = {'status': 'PASS', 'observation': observation.to_dict()}
        except Exception as e:
            result['geometry_observer'] = {'status': 'ERROR', 'error': f'{type(e).__name__}: {e}'}
        return result
