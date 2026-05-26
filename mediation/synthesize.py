"""Per-student multi-signal synthesis for isolated-learner surfacing."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class StudentChannels:
    student_id: str
    raw_risk: float
    help_risk: float
    reflect_risk: float
    raw_baseline: bool
    help_baseline: bool
    reflect_baseline: bool


@dataclass
class SynthesisResult:
    student_id: str
    synthesis_score: float
    isolated: bool
    raw_risk: float
    help_risk: float
    reflect_risk: float


DEFAULT_WEIGHTS = (0.35, 0.35, 0.30)
DEFAULT_THRESHOLD = 0.50


def synthesis_score(
    raw_risk: float,
    help_risk: float,
    reflect_risk: float,
    *,
    w_raw: float = DEFAULT_WEIGHTS[0],
    w_help: float = DEFAULT_WEIGHTS[1],
    w_refl: float = DEFAULT_WEIGHTS[2],
) -> float:
    return w_raw * raw_risk + w_help * help_risk + w_refl * reflect_risk


def classify_student(
    channels: StudentChannels,
    *,
    threshold: float = DEFAULT_THRESHOLD,
) -> SynthesisResult:
    sigma = synthesis_score(channels.raw_risk, channels.help_risk, channels.reflect_risk)
    baselines_silent = not (
        channels.raw_baseline or channels.help_baseline or channels.reflect_baseline
    )
    isolated = baselines_silent and sigma >= threshold
    return SynthesisResult(
        student_id=channels.student_id,
        synthesis_score=sigma,
        isolated=isolated,
        raw_risk=channels.raw_risk,
        help_risk=channels.help_risk,
        reflect_risk=channels.reflect_risk,
    )
