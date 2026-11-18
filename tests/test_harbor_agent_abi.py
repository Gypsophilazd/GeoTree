"""Required no-model preflight for all concrete GeoTree Harbor agents."""
import importlib
import inspect
import json
import os
from pathlib import Path
import pkgutil
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import geotree
from geotree import enhanced_agent as entry
from harbor.agents.base import BaseAgent
from harbor.agents.factory import AgentFactory
from harbor.models.agent.context import AgentContext
from harbor.models.trajectories import Trajectory

def load(path, logs):
    return AgentFactory.create_agent_from_import_path(path, logs, model_name=None)

class ABI(unittest.TestCase):
    def test_all_concrete_entries(self):
        paths=[]
        for info in pkgutil.iter_modules(geotree.__path__, 'geotree.'):
            module=importlib.import_module(info.name)
            for name, cls in vars(module).items():
                if inspect.isclass(cls) and cls.__module__==info.name and issubclass(cls,BaseAgent) and not inspect.isabstract(cls):
                    paths.append(f'{info.name}:{name}')
        self.assertIn('geotree.enhanced_agent:EnhancedAgent',paths)
        self.assertIn('geotree.paired_agent:PairedAgent',paths)
        with tempfile.TemporaryDirectory() as tmp:
            for path in sorted(paths):
                with self.subTest(path=path):
                    a=load(path,Path(tmp))
                    for name,keys in (('setup',dict(environment=object())),('run',dict(instruction='',environment=object(),context=AgentContext()))):
                        method=getattr(a,name)
                        self.assertTrue(inspect.iscoroutinefunction(method))
                        sig=inspect.signature(method)
                        self.assertIn('environment',sig.parameters)
                        sig.bind(**keys)
                    print('ABI PASS',path,inspect.signature(a.setup),inspect.signature(a.run))

class MockEnvironment:
    def __init__(self, *, fail=False):
        self.fail=fail
        self.commands=[]
        self.uploads=[]
    async def exec(self, command, **opts):
        self.commands.append((command,opts))
        return SimpleNamespace(return_code=int(self.fail),stdout='',stderr='')
    async def upload_file(self,source,dest):
        self.uploads.append((Path(source).read_bytes(),dest))

class OfflineMailbox:
    async def propose(self,obs):
        return dict(request_id=obs['request_id'],action='done',reason='offline ABI fixture',code=''),dict(input_tokens=3,output_tokens=2)
    def __init__(self,root,budget):pass

class EnhancedLifecycle(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup)
        p=Path(temp.name)
        self.root=p/'k';self.trial='k-0123456789abcdef-k1'
        (self.root/self.trial).mkdir(parents=True)
        self.instruction='Fixture: one parametric body.'
        text=p/'e02-j/public/text_create/instruction.md';text.parent.mkdir(parents=True)
        text.write_text(self.instruction)
        for ctx in (patch.object(entry,'ROOT',self.root),patch.object(entry,'Mailbox',OfflineMailbox),
                    patch.dict(os.environ,dict(GEOTREE_PUBLIC_INSTRUCTION=str(text),GEOTREE_INSTRUCTION_SHA256=entry.digest_bytes(text.read_bytes()),GEOTREE_K_TRIAL=self.trial,GEOTREE_K_DEADLINE=str(time.time()+30)))):
            ctx.start();self.addCleanup(ctx.stop)
        self.a=load('geotree.enhanced_agent:EnhancedAgent',p/'logs')
    async def test_keyword_lifecycle(self):
        e=MockEnvironment();c=AgentContext()
        self.assertIsNone(await self.a.setup(environment=e))
        self.assertIsNone(await self.a.run(instruction=self.instruction,environment=e,context=c))
        self.assertTrue(e.uploads)
        self.assertTrue(self.a.capabilities.atif)
        t=Trajectory.model_validate_json((self.a.logs_dir/'trajectory.json').read_text())
        self.assertEqual(len(t.steps),1)
        self.assertEqual(json.loads((self.a.root/'terminal.json').read_text()),{'status':'done'})
        self.assertEqual(c.metadata['geotree_terminal'],'done')
    async def test_setup_error_propagates(self):
        with self.assertRaisesRegex(RuntimeError,'setup_failed'):
            await self.a.setup(environment=MockEnvironment(fail=True))
    async def test_run_error_propagates_and_reports_terminal(self):
        e=MockEnvironment();c=AgentContext()
        await self.a.setup(environment=e)
        with self.assertRaisesRegex(ValueError,'task_instruction_mismatch'):
            await self.a.run(instruction='wrong public input',environment=e,context=c)
        self.assertEqual(json.loads((self.a.root/'terminal.json').read_text()),{'status':'error'})
        self.assertEqual(c.metadata['geotree_terminal'],'error')
if __name__=='__main__':unittest.main()
