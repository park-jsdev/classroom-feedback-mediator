"""Human-readable explanations and role-specific recommendations."""

from __future__ import annotations

from dataclasses import dataclass

from mediation.core import DecisionRecord


@dataclass
class RecommendationAction:
    type: str
    action: str


def explain_topic(record: DecisionRecord, *, cohort_friction: float) -> list[str]:
    reasons: list[str] = []
    if record.gap_prevalence >= 0.10:
        reasons.append("high gap prevalence across the cohort")
    elif record.gap_prevalence >= 0.05:
        reasons.append("elevated gap prevalence")

    if record.survey_disagreement >= 0.04:
        reasons.append("student difficulty disagrees with gap evidence")
    elif record.survey_disagreement > 0:
        reasons.append("moderate survey-to-gap disagreement")

    if cohort_friction >= 0.15:
        reasons.append("unresolved teacher trust or usability concerns")

    if not reasons:
        reasons.append("combined signal weighting across student and teacher channels")
    return reasons


def recommend_roles(record: DecisionRecord, *, cohort_friction: float) -> dict[str, list[RecommendationAction]]:
    teacher: list[RecommendationAction] = []
    student: list[RecommendationAction] = []
    researcher: list[RecommendationAction] = []

    if record.gap_prevalence >= 0.08:
        teacher.append(
            RecommendationAction(
                type="teacher_intervention",
                action="Review prerequisite concepts for this topic.",
            )
        )

    if record.survey_disagreement >= 0.04:
        student.append(
            RecommendationAction(
                type="student_reflection",
                action="Prompt learners to compare self-rated understanding with recent help-seeking behavior.",
            )
        )
        researcher.append(
            RecommendationAction(
                type="researcher_audit",
                action="Audit disagreement between gap prevalence and survey difficulty.",
            )
        )

    if record.gap_prevalence >= 0.05:
        teacher.append(
            RecommendationAction(
                type="teacher_intervention",
                action="Inspect unresolved discussion threads on this topic.",
            )
        )

    if cohort_friction >= 0.15:
        teacher.append(
            RecommendationAction(
                type="teacher_intervention",
                action="Review instructor dashboard observations and interview themes.",
            )
        )

    researcher.extend(
        [
            RecommendationAction(
                type="researcher_audit",
                action="Inspect whether the topic priority is robust under alternate weights.",
            ),
            RecommendationAction(
                type="researcher_audit",
                action="Review representative student traces before authorizing intervention.",
            ),
        ]
    )

    if not student:
        student.append(
            RecommendationAction(
                type="student_reflection",
                action="Monitor self-reported difficulty on this topic during the next survey window.",
            )
        )

    if not teacher:
        teacher.append(
            RecommendationAction(
                type="teacher_intervention",
                action="Monitor learner activity and revisit during the next topic snapshot.",
            )
        )

    return {"teacher": teacher, "student": student, "researcher": researcher}
