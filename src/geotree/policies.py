"""Frozen structural search contract; no Lite implementation."""
from dataclasses import dataclass
from typing import Protocol, Sequence
from geotree.nosearch import ActionProposal

@dataclass(frozen=True)
class CandidateBatch:
    candidates: tuple[ActionProposal, ...]
    def __post_init__(self):
        if not 1 <= len(self.candidates) <= 3:
            raise ValueError('candidate count must be 1..3')

class SearchPolicy(Protocol):
    k: int
    def select(self, proposals: Sequence[ActionProposal]) -> ActionProposal: ...
