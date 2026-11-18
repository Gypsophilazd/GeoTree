"""Deterministic Harbor adapter for infrastructure checks, with no model."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from harbor.agents.base import BaseAgent
from harbor.agents.capabilities import AgentCapabilities
from harbor.environments.base import BaseEnvironment
from harbor.models.agent.context import AgentContext
from harbor.models.trajectories import Agent, Step, Trajectory

_COMMAND = "test -d /app && printf 'geotree-workspace-ok\\n'"
_TOOL = "check_task_workspace"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class GeoTreeNoModelAgent(BaseAgent):
    capabilities = AgentCapabilities(atif=True)

    @staticmethod
    def name() -> str:
        return "geotree-nomodel"

    def version(self) -> str:
        return "0.1.0"

    def _event(self, phase: str, **fields: object) -> None:
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        with (self.logs_dir / "geotree-events.jsonl").open("a", encoding="utf-8") as out:
            out.write(json.dumps({"time": _now(), "phase": phase, **fields}) + "\n")

    async def setup(self, environment: BaseEnvironment) -> None:
        if self.model_name is not None:
            raise ValueError("GeoTreeNoModelAgent requires no model")
        self._event("setup")

    async def run(
        self, instruction: str, environment: BaseEnvironment, context: AgentContext
    ) -> None:
        if self.model_name is not None:
            raise ValueError("GeoTreeNoModelAgent requires no model")
        self._event("run_start")
        # Neither the instruction nor tool data may influence the command.
        result = await environment.exec(_COMMAND, cwd="/app", timeout_sec=10)
        status = result.return_code
        outcome = "workspace_ok" if status == 0 else "workspace_check_failed"
        self._event("run_end", exit_status=status, outcome=outcome)
        trajectory = Trajectory(
            schema_version="ATIF-v1.8",
            session_id=str(uuid4()),
            agent=Agent(name=self.name(), version=self.version()),
            steps=[
                Step.model_validate({
                    "step_id": 1, "timestamp": _now(), "source": "agent",
                    "message": "Check the task workspace without a model.",
                    "llm_call_count": 0,
                    "tool_calls": [{"tool_call_id": "workspace-1",
                                    "function_name": _TOOL, "arguments": {}}],
                    "observation": {"results": [{"source_call_id": "workspace-1",
                                                 "content": outcome,
                                                 "extra": {"exit_status": status}}]},
                }),
            ],
        )
        destination: Path = self.logs_dir / "trajectory.json"
        scratch = destination.with_suffix(".tmp")
        scratch.write_text(trajectory.model_dump_json(exclude_none=True, indent=2) + "\n",
                           encoding="utf-8")
        scratch.replace(destination)
        if status != 0:
            raise RuntimeError(f"Workspace check exited {status}")
