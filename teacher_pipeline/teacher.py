"""Teacher friction F from coded feedback or signal rows."""

from __future__ import annotations

from dataclasses import dataclass

FRICTION_GROUPS = frozenset({"usability_friction_signal", "trust_uncertainty_signal"})

FEEDBACK_TYPE_TO_GROUP: dict[str, str] = {
    "trust_uncertainty": "trust_uncertainty_signal",
    "usability_friction": "usability_friction_signal",
    "usability_ease": "positive_instructional_signal",
    "actionable_insight": "positive_instructional_signal",
    "actionable_insights": "positive_instructional_signal",
    "missing_topic_context": "positive_instructional_signal",
    "positive_instructional": "positive_instructional_signal",
}


@dataclass
class SignalRow:
    signal_group: str


@dataclass
class TeacherFeedback:
    type: str
    severity: str = "medium"


def compute_teacher_friction(rows: list[SignalRow]) -> float:
    if not rows:
        raise ValueError("At least one teacher signal row is required.")
    friction_count = sum(1 for row in rows if row.signal_group in FRICTION_GROUPS)
    return friction_count / len(rows)


def friction_from_feedback(items: list[TeacherFeedback]) -> float:
    rows: list[SignalRow] = []
    for item in items:
        key = item.type.strip().lower()
        group = FEEDBACK_TYPE_TO_GROUP.get(
            key, key if key.endswith("_signal") else "positive_instructional_signal"
        )
        rows.append(SignalRow(signal_group=group))
    return compute_teacher_friction(rows)
