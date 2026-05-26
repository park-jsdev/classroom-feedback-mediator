"""Cohort-level mediation policy: ranks topics from classroom signals."""

from __future__ import annotations

from dataclasses import dataclass, field

from api.schemas import StudentSignals, TeacherSignals, TopicPriorityOut, Weights
from mediation.run import run_mediation


@dataclass
class MediationPolicy:
    """Transparent ranking policy over teacher and student subsystem signals."""

    weights: Weights = field(default_factory=Weights)

    def rank(
        self,
        teacher: TeacherSignals,
        student: StudentSignals,
    ) -> tuple[float, list[TopicPriorityOut]]:
        """Return cohort friction F and ranked topics with decision records."""
        return run_mediation(teacher, student.topics, self.weights)
