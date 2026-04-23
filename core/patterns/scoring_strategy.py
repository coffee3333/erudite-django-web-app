"""
Strategy design pattern for challenge scoring.

Different scoring strategies are interchangeable: the submission view
calls the appropriate strategy based on challenge type without knowing
the concrete implementation details.
"""
from abc import ABC, abstractmethod


class ScoringStrategy(ABC):
    """Abstract scoring strategy — all strategies must implement compute_score."""

    @abstractmethod
    def compute_score(self, challenge, is_correct: bool, hint_used: bool) -> int:
        """Return the integer score earned for this submission."""
        ...


class ExactMatchScoringStrategy(ScoringStrategy):
    """Full score for correct answer, zero for incorrect."""

    def compute_score(self, challenge, is_correct: bool, hint_used: bool) -> int:
        if not is_correct:
            return 0
        base = challenge.points
        return round(base * 0.5) if hint_used else base


class PartialCreditScoringStrategy(ScoringStrategy):
    """Weighted partial credit based on test-case pass rate (for code challenges)."""

    def __init__(self, earned_weight: float, total_weight: float):
        self._earned = earned_weight
        self._total = total_weight

    def compute_score(self, challenge, is_correct: bool, hint_used: bool) -> int:
        if self._total == 0:
            return 0
        base = round((self._earned / self._total) * challenge.points)
        return round(base * 0.5) if (hint_used and is_correct) else base


class ScoringContext:
    """Context: receives a strategy and delegates scoring computation."""

    def __init__(self, strategy: ScoringStrategy):
        self._strategy = strategy

    def set_strategy(self, strategy: ScoringStrategy):
        self._strategy = strategy

    def compute(self, challenge, is_correct: bool, hint_used: bool) -> int:
        return self._strategy.compute_score(challenge, is_correct, hint_used)
