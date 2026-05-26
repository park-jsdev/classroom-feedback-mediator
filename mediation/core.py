"""Linear topic mediation: P_t = w_r R_t + w_d D_t + w_f F."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TopicSignals:
    topic_id: str
    gap_prevalence: float  # R_t
    survey_difficulty: float | None = None  # s_t


@dataclass
class DecisionRecord:
    topic_id: str
    gap_prevalence: float
    survey_difficulty: float | None
    survey_disagreement: float
    teacher_friction: float
    priority_score: float
    rank: int


def compute_disagreement(r_t: float, s_t: float | None) -> float:
    if s_t is None:
        return 0.0
    return abs(r_t - s_t)


def mediate_topics(
    topics: list[TopicSignals],
    teacher_friction: float,
    *,
    w_r: float = 0.70,
    w_d: float = 0.20,
    w_f: float = 0.10,
) -> list[DecisionRecord]:
    """Rank topics by linear priority (descending); ties broken by R_t."""
    rows: list[tuple[str, float, float | None, float, float]] = []
    for topic in topics:
        d_t = compute_disagreement(topic.gap_prevalence, topic.survey_difficulty)
        p_t = w_r * topic.gap_prevalence + w_d * d_t + w_f * teacher_friction
        rows.append(
            (topic.topic_id, topic.gap_prevalence, topic.survey_difficulty, d_t, p_t)
        )

    rows.sort(key=lambda row: (-row[4], -row[1], row[0]))

    records: list[DecisionRecord] = []
    for rank, (topic_id, r_t, s_t, d_t, p_t) in enumerate(rows, start=1):
        records.append(
            DecisionRecord(
                topic_id=topic_id,
                gap_prevalence=r_t,
                survey_difficulty=s_t,
                survey_disagreement=d_t,
                teacher_friction=teacher_friction,
                priority_score=p_t,
                rank=rank,
            )
        )
    return records
