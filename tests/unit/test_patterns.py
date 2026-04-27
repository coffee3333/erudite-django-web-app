"""Tests for Strategy scoring pattern and Observer enrollment pattern."""
import pytest
from unittest.mock import MagicMock
from core.patterns.scoring_strategy import (
    ExactMatchScoringStrategy, PartialCreditScoringStrategy, ScoringContext
)
from core.patterns.enrollment_observer import (
    EnrollmentEventBus, EnrollmentEvent, EnrollmentObserver
)


class TestExactMatchScoringStrategy:
    def _challenge(self, points=10):
        c = MagicMock()
        c.points = points
        return c

    def test_correct_answer_returns_full_points(self):
        strategy = ExactMatchScoringStrategy()
        challenge = self._challenge(points=10)
        assert strategy.compute_score(challenge, is_correct=True, hint_used=False) == 10

    def test_incorrect_answer_returns_zero(self):
        strategy = ExactMatchScoringStrategy()
        challenge = self._challenge(points=10)
        assert strategy.compute_score(challenge, is_correct=False, hint_used=False) == 0

    def test_correct_with_hint_returns_half_points(self):
        strategy = ExactMatchScoringStrategy()
        challenge = self._challenge(points=10)
        assert strategy.compute_score(challenge, is_correct=True, hint_used=True) == 5


class TestPartialCreditScoringStrategy:
    def _challenge(self, points=10):
        c = MagicMock()
        c.points = points
        return c

    def test_full_weight_gives_full_score(self):
        strategy = PartialCreditScoringStrategy(earned_weight=3, total_weight=3)
        assert strategy.compute_score(self._challenge(10), True, False) == 10

    def test_partial_weight_gives_partial_score(self):
        strategy = PartialCreditScoringStrategy(earned_weight=1, total_weight=2)
        assert strategy.compute_score(self._challenge(10), True, False) == 5

    def test_zero_total_weight_returns_zero(self):
        strategy = PartialCreditScoringStrategy(earned_weight=0, total_weight=0)
        assert strategy.compute_score(self._challenge(10), True, False) == 0


class TestScoringContext:
    def test_context_delegates_to_strategy(self):
        mock_strategy = MagicMock()
        mock_strategy.compute_score.return_value = 7
        ctx = ScoringContext(mock_strategy)
        challenge = MagicMock()
        result = ctx.compute(challenge, True, False)
        assert result == 7
        mock_strategy.compute_score.assert_called_once_with(challenge, True, False)


class TestEnrollmentObserverPattern:
    def test_observer_notified_on_event(self):
        bus = EnrollmentEventBus()
        received = []

        class TestObserver(EnrollmentObserver):
            def on_enrollment(self, event):
                received.append(event)

        obs = TestObserver()
        bus.subscribe(obs)

        course = MagicMock()
        student = MagicMock()
        event = EnrollmentEvent(EnrollmentEvent.ENROLLED, course, student)
        bus.notify(event)

        assert len(received) == 1
        assert received[0].event_type == "enrolled"

    def test_unsubscribed_observer_not_notified(self):
        bus = EnrollmentEventBus()
        received = []

        class TestObserver(EnrollmentObserver):
            def on_enrollment(self, event):
                received.append(event)

        obs = TestObserver()
        bus.subscribe(obs)
        bus.unsubscribe(obs)
        bus.notify(EnrollmentEvent(EnrollmentEvent.ENROLLED, MagicMock(), MagicMock()))
        assert len(received) == 0

    def test_failing_observer_does_not_propagate_exception(self):
        bus = EnrollmentEventBus()

        class BadObserver(EnrollmentObserver):
            def on_enrollment(self, event):
                raise RuntimeError("Observer failed")

        bus.subscribe(BadObserver())
        # Should not raise
        bus.notify(EnrollmentEvent(EnrollmentEvent.ENROLLED, MagicMock(), MagicMock()))
