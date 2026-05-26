from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator

from api.openapi_examples import SAMPLE_MEDIATION_REQUEST, SAMPLE_SYNTHESIZE_REQUEST


class TeacherFeedbackItem(BaseModel):
    type: str = Field(..., examples=["trust_uncertainty", "actionable_insight", "usability_friction"])
    severity: str = Field("medium", examples=["low", "medium", "high"])


class TeacherSignals(BaseModel):
    feedback: list[TeacherFeedbackItem] = Field(default_factory=list)
    # Legacy / advanced: precomputed friction or raw coded rows
    friction: float | None = Field(None, ge=0.0, le=1.0)
    signal_rows: list[dict[str, str]] | None = None


class TopicInput(BaseModel):
    topic_id: str = Field(..., examples=["analogical_reasoning", "planning", "frames"])
    gap_prevalence: float | None = Field(None, ge=0.0, le=1.0)
    gap_count: int | None = Field(None, ge=0)
    total_students: int | None = Field(None, ge=1)
    survey_difficulty: float | None = Field(None, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def check_gap_source(self) -> TopicInput:
        has_prev = self.gap_prevalence is not None
        has_counts = self.gap_count is not None and self.total_students is not None
        if not has_prev and not has_counts:
            raise ValueError("Each topic requires gap_prevalence or (gap_count, total_students)")
        return self


class StudentSignals(BaseModel):
    topics: list[TopicInput]


class Weights(BaseModel):
    w_r: float = 0.70
    w_d: float = 0.20
    w_f: float = 0.10


class MediateRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"examples": [SAMPLE_MEDIATION_REQUEST]},
    )

    teacher_signals: TeacherSignals
    student_signals: StudentSignals
    weights: Weights = Field(default_factory=Weights)


class RecommendationAction(BaseModel):
    type: str = Field(..., examples=["teacher_intervention", "student_reflection", "researcher_audit"])
    action: str = Field(..., examples=["Review prerequisite concepts for this topic."])


class RoleRecommendations(BaseModel):
    teacher: list[RecommendationAction] = Field(default_factory=list)
    student: list[RecommendationAction] = Field(default_factory=list)
    researcher: list[RecommendationAction] = Field(default_factory=list)


class DecisionRecordPayload(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    R_t: float = Field(..., serialization_alias="R_t")
    D_t: float = Field(..., serialization_alias="D_t")
    F: float = Field(..., serialization_alias="F")
    weights: Weights


class TopicPriorityOut(BaseModel):
    topic_id: str
    priority: float
    rank: int
    gap_prevalence: float
    survey_difficulty: float | None
    survey_disagreement: float
    teacher_friction: float
    explanation: list[str]
    decision_record: DecisionRecordPayload
    recommendations: RoleRecommendations


class MediateResponse(BaseModel):
    teacher_friction: float
    weights: Weights
    topics: list[TopicPriorityOut]


class DecisionRecordOut(BaseModel):
    topic_id: str
    gap_prevalence: float
    survey_difficulty: float | None
    survey_disagreement: float
    teacher_friction: float
    priority_score: float
    rank: int
    explanation: list[str]
    decision_record: DecisionRecordPayload
    recommendations: RoleRecommendations


class RecommendRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"examples": [{**SAMPLE_MEDIATION_REQUEST, "top_k": 5}]},
    )

    teacher_signals: TeacherSignals
    student_signals: StudentSignals
    weights: Weights = Field(default_factory=Weights)
    top_k: int = Field(5, ge=1, le=50)


class RecommendResponse(BaseModel):
    top_k: int
    topics: list[TopicPriorityOut]


class ExplainResponse(BaseModel):
    topic_id: str
    priority: float
    rank: int
    explanation: list[str]
    decision_record: DecisionRecordPayload
    recommendations: RoleRecommendations


class WeightProfile(BaseModel):
    name: str = Field(..., examples=["default", "stable_disagreement_up"])
    w_r: float = Field(..., ge=0.0, le=1.0, examples=[0.7])
    w_d: float = Field(..., ge=0.0, le=1.0, examples=[0.2])
    w_f: float = Field(..., ge=0.0, le=1.0, examples=[0.1])


class WeightSensitivityRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"examples": [SAMPLE_MEDIATION_REQUEST]},
    )

    teacher_signals: TeacherSignals
    student_signals: StudentSignals
    profiles: list[WeightProfile] | None = Field(
        None,
        description="Optional weight profiles. Omit or null to use server defaults.",
    )

    @model_validator(mode="after")
    def normalize_profiles(self) -> WeightSensitivityRequest:
        if self.profiles is not None and len(self.profiles) == 0:
            self.profiles = None
        return self


class WeightSensitivityResult(BaseModel):
    profile: WeightProfile
    top5_topics: list[str]
    spearman_vs_default: float | None = None


class WeightSensitivityResponse(BaseModel):
    default_top5: list[str]
    results: list[WeightSensitivityResult]


class StudentChannelInput(BaseModel):
    student_id: str = Field(..., examples=["case_a"])
    raw_risk: float = Field(..., ge=0.0, le=1.0, examples=[0.31])
    help_risk: float = Field(..., ge=0.0, le=1.0, examples=[0.70])
    reflect_risk: float = Field(..., ge=0.0, le=1.0, examples=[0.52])
    raw_baseline: bool = False
    help_baseline: bool = False
    reflect_baseline: bool = False


class SynthesizeRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"examples": [SAMPLE_SYNTHESIZE_REQUEST]},
    )

    students: list[StudentChannelInput]
    threshold: float = Field(0.50, ge=0.01, le=1.0, description="σ threshold for isolated-learner flag")


class SynthesizeResultOut(BaseModel):
    student_id: str
    synthesis_score: float
    isolated: bool
    raw_risk: float
    help_risk: float
    reflect_risk: float


class SynthesizeResponse(BaseModel):
    threshold: float
    results: list[SynthesizeResultOut]
