"""Harbor 0.23 keyword-compatible entry; keep the versioned entry compatible."""
from geotree.enhanced_agent import EnhancedAgent as FrozenEnhancedAgent

class EnhancedAgent(FrozenEnhancedAgent):
    @staticmethod
    def name():
        return 'geotree-enhanced-k-v2'

    def version(self):
        return '0.1.1'

    async def setup(self, environment):
        return await super().setup(environment=environment)

    async def run(self, instruction, environment, context):
        return await super().run(instruction=instruction, environment=environment, context=context)
