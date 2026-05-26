"""Shared mediation helpers for API routes."""

from __future__ import annotations

from scipy import stats

from api.schemas import TeacherSignals, TopicInput, WeightProfile, Weights
from mediation.core import mediate_topics
from mediation.run import resolve_friction, run_mediation, topic_signals_from_input

__all__ = ["run_mediation", "weight_sensitivity"]

DEFAULT_PROFILES = [
    WeightProfile(name="default", w_r=0.70, w_d=0.20, w_f=0.10),
    WeightProfile(name="stable_disagreement_up", w_r=0.60, w_d=0.40, w_f=0.00),
]


def weight_sensitivity(
    teacher_signals: TeacherSignals,
    topics: list[TopicInput],
    profiles: list[WeightProfile] | None = None,
) -> tuple[list[str], list[tuple[WeightProfile, list[str], float | None]]]:
    if not profiles:
        profiles = DEFAULT_PROFILES
    friction = resolve_friction(teacher_signals)
    base_signals = topic_signals_from_input(topics)

    default = profiles[0]
    default_records = mediate_topics(base_signals, friction, w_r=default.w_r, w_d=default.w_d, w_f=default.w_f)
    default_top5 = [r.topic_id for r in default_records[:5]]
    default_ranks = {r.topic_id: r.rank for r in default_records}

    results: list[tuple[WeightProfile, list[str], float | None]] = []
    for profile in profiles:
        records = mediate_topics(base_signals, friction, w_r=profile.w_r, w_d=profile.w_d, w_f=profile.w_f)
        top5 = [r.topic_id for r in records[:5]]
        rho: float | None = None
        if profile.name != default.name:
            xs = [default_ranks[r.topic_id] for r in records]
            ys = [r.rank for r in records]
            rho = float(stats.spearmanr(xs, ys).statistic)
        results.append((profile, top5, rho))
    return default_top5, results
