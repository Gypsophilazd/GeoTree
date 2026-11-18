import json
from pathlib import Path
from geotree.paths import runtime_dir
from harbor.agents.base import BaseAgent
from harbor.agents.capabilities import AgentCapabilities
from geotree.nosearch import CodexMailboxProvider,Executor,FeedbackRecorder,NoSearchRuntime
ROOT=(runtime_dir()/'legacy-nosearch/mailbox')
class GeoTreeNoSearchAgent(BaseAgent):
    capabilities=AgentCapabilities(atif=True)
    @staticmethod
    def name():return 'geotree-nosearch-dev'
    def version(self):return '0.1.0'
    async def setup(self,environment):
        if self.model_name:raise ValueError('credentials remain in trusted Windows provider')
        ROOT.mkdir(parents=True,exist_ok=True);self.logs_dir.mkdir(parents=True,exist_ok=True)
        result=await environment.exec('mkdir -p /tmp/geotree-home && chown 65534:65534 /tmp/geotree-home /app && chmod 700 /logs',timeout_sec=10)
        if result.return_code:raise RuntimeError('development isolation setup failed')
    async def run(self,instruction,environment,context):
        status='error'
        try:
            await environment.download_file('/app/6b54209a13.png',ROOT/'drawing.png')
            runtime=NoSearchRuntime(CodexMailboxProvider(ROOT),Executor(environment,self.logs_dir),FeedbackRecorder(self.logs_dir),max_steps=4)
            status=await runtime.run(instruction)
        finally:
            p=ROOT/'terminal.tmp';p.write_text(json.dumps({'status':status}));p.replace(ROOT/'terminal.json')
