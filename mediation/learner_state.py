"""Per-student learner state for multi-signal synthesis (H3)."""

from __future__ import annotations

from dataclasses import dataclass

from mediation.synthesize import StudentChannels, SynthesisResult, classify_student


@dataclass
class LearnerState:
    student_id: str
    raw_risk: float
    help_risk: float
    reflect_risk: float
    raw_baseline: bool = False
    help_baseline: bool = False
    reflect_baseline: bool = False

    def synthesize(self, *, threshold: float = 0.50) -> SynthesisResult:
        return classify_student(
            StudentChannels(
                student_id=self.student_id,
                raw_risk=self.raw_risk,
                help_risk=self.help_risk,
                reflect_risk=self.reflect_risk,
                raw_baseline=self.raw_baseline,
                help_baseline=self.help_baseline,
                reflect_baseline=self.reflect_baseline,
            ),
            threshold=threshold,
        )
