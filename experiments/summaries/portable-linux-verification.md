# Portable snapshot verification

Linux Python 3.12 / Harbor 0.23.0 locked install: PASS (91 resolved dependencies plus editable GeoTree).

Existing local FreeCAD 1.1.0 image, no new image pull:

sha256:2e1e1306135a9c0d69febd0c5257c4585abe3be67f9ed8b5396de20e52ee4e76

Ran 24 tests in 0.063s
OK
ABI PASS geotree.decision_bridge:DecisionBridgeAgent (environment) (instruction, environment, context)
ABI PASS geotree.enhanced_agent:EnhancedAgent (environment) -> None (instruction, environment, context) -> None
ABI PASS geotree.enhanced_agent_l:EnhancedAgent (environment) -> None (instruction, environment, context) -> None
ABI PASS geotree.enhanced_agent_v2:EnhancedAgent (environment) (instruction, environment, context)
ABI PASS geotree.harbor_agent:GeoTreeNoModelAgent (environment: 'BaseEnvironment') -> 'None' (instruction: 'str', environment: 'BaseEnvironment', context: 'AgentContext') -> 'None'
ABI PASS geotree.nosearch_agent:GeoTreeNoSearchAgent (environment) (instruction, environment, context)
ABI PASS geotree.paired_agent:PairedAgent (environment) (instruction, environment, context)
PASS nullable stdout/stderr, feedback -> next decision, ATIF
PASS rejected action feedback and no rejected execution
PASS tool timeout feedback
PASS illegal model payload and maximum budget
PASS no action beyond budget
PASS replaceable JSON transport without Codex
PASS relay timeout/error signals
PASS adapter exceptional termination signal
PASS adapter normal termination signal
PASS basic code rejection; NOT a Python sandbox proof
PASS decision 4, CAD 2, stale ID, soft overshoot, ATIF, single and total deadlines
PASS FreeCAD 1.1.0 GeometryObserver; hard FAIL -> verified PASS; original unchanged; wrong SHA rejected
PASS synthetic Harbor mailbox, post-CAD evidence feedback; real model calls=0
ACCEPT: terminal=done

No model traffic or Benchmark scoring. The Harbor test used a separate synthetic fixture with verification disabled.
