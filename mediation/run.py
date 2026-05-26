"""Cohort mediation pipeline (shared by REST API and MediationPolicy)."""

from __future__ import annotations

from api.schemas import (
    DecisionRecordPayload,
    RecommendationAction,
    RoleRecommendations,
    TeacherSignals,
    TopicInput,
    TopicPriorityOut,
    Weights,
)
from mediation.core import DecisionRecord, TopicSignals, mediate_topics
from mediation.explain import explain_topic, recommend_roles
from teacher_pipeline.teacher import (
    SignalRow,
    TeacherFeedback,
    compute_teacher_friction,
    friction_from_feedback,
)


def resolve_gap_prevalence(
    *,
    gap_prevalence: float | None = None,
    gap_count: int | None = None,
    total_students: int | None = None,
) -> float:
    if gap_prevalence is not None:
        return gap_prevalence
    if gap_count is not None and total_students is not None:
        if total_students <= 0:
            raise ValueError("total_students must be positive when using gap_count")
        return gap_count / total_students
    raise ValueError("Provide gap_prevalence or (gap_count, total_students)")


def resolve_friction(teacher_signals: TeacherSignals) -> float:
    if teacher_signals.feedback:
        items = [TeacherFeedback(type=f.type, severity=f.severity) for f in teacher_signals.feedback]
        return friction_from_feedback(items)
    if teacher_signals.friction is not None:
        return teacher_signals.friction
    if teacher_signals.signal_rows:
        rows = [SignalRow(signal_group=str(r.get("signal_group", ""))) for r in teacher_signals.signal_rows]
        return compute_teacher_friction(rows)
    raise ValueError("Provide teacher_signals.feedback, friction, or signal_rows")


def topic_signals_from_input(topics: list[TopicInput]) -> list[TopicSignals]:
    if not topics:
        raise ValueError("student_signals.topics must be non-empty")
    out: list[TopicSignals] = []
    for t in topics:
        r_t = resolve_gap_prevalence(
            gap_prevalence=t.gap_prevalence,
            gap_count=t.gap_count,
            total_students=t.total_students,
        )
        out.append(TopicSignals(topic_id=t.topic_id, gap_prevalence=r_t, survey_difficulty=t.survey_difficulty))
    return out


def _role_recommendations(roles: dict[str, list]) -> RoleRecommendations:
    return RoleRecommendations(
        teacher=[RecommendationAction(type=a.type, action=a.action) for a in roles["teacher"]],
        student=[RecommendationAction(type=a.type, action=a.action) for a in roles["student"]],
        researcher=[RecommendationAction(type=a.type, action=a.action) for a in roles["researcher"]],
    )


def enrich_record(record: DecisionRecord, weights: Weights) -> TopicPriorityOut:
    explanation = explain_topic(record, cohort_friction=record.teacher_friction)
    roles = recommend_roles(record, cohort_friction=record.teacher_friction)
    decision_record = DecisionRecordPayload(
        R_t=record.gap_prevalence,
        D_t=record.survey_disagreement,
        F=record.teacher_friction,
        weights=weights,
    )
    return TopicPriorityOut(
        topic_id=record.topic_id,
        priority=record.priority_score,
        rank=record.rank,
        gap_prevalence=record.gap_prevalence,
        survey_difficulty=record.survey_difficulty,
        survey_disagreement=record.survey_disagreement,
        teacher_friction=record.teacher_friction,
        explanation=explanation,
        decision_record=decision_record,
        recommendations=_role_recommendations(roles),
    )


def run_mediation(
    teacher_signals: TeacherSignals,
    topics: list[TopicInput],
    weights: Weights,
) -> tuple[float, list[TopicPriorityOut]]:
    friction = resolve_friction(teacher_signals)
    records = mediate_topics(
        topic_signals_from_input(topics),
        friction,
        w_r=weights.w_r,
        w_d=weights.w_d,
        w_f=weights.w_f,
    )
    return friction, [enrich_record(r, weights) for r in records]
