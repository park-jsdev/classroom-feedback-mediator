"""FastAPI service for classroom feedback mediation."""

from __future__ import annotations

from fastapi import Body, FastAPI, HTTPException, Path
from fastapi.responses import RedirectResponse

from api.openapi_examples import (
    MEDIATE_BODY_EXAMPLES,
    RECOMMEND_BODY_EXAMPLES,
    SYNTHESIZE_BODY_EXAMPLES,
    TOPIC_ID_EXAMPLES,
    WEIGHT_SENSITIVITY_BODY_EXAMPLES,
)
from api.schemas import (
    DecisionRecordOut,
    ExplainResponse,
    MediateRequest,
    MediateResponse,
    RecommendRequest,
    RecommendResponse,
    SynthesizeRequest,
    SynthesizeResponse,
    SynthesizeResultOut,
    TopicPriorityOut,
    WeightSensitivityRequest,
    WeightSensitivityResponse,
    WeightSensitivityResult,
)
from api.service import run_mediation, weight_sensitivity
from mediation.learner_state import LearnerState

app = FastAPI(
    title="Classroom Feedback Mediator",
    description=(
        "Interpretable coordination layer for human-AI co-agency under incomplete feedback. "
        "Accepts classroom-level teacher feedback and student topic observations; "
        "computes ranked priorities with explanations and recommendations.\n\n"
        "**Swagger tip:** Select the named request examples (e.g. **course_sample**, **case_a_isolated**) "
        "instead of the auto-generated schema defaults (`\"string\"`, zeros). "
        "For `/explain/{topic_id}`, the path ID must appear in `student_signals.topics`."
    ),
    version="0.2.0",
)


def _http_value_error(exc: ValueError) -> HTTPException:
    return HTTPException(status_code=422, detail=str(exc))


def _find_topic(topics: list[TopicPriorityOut], topic_id: str) -> TopicPriorityOut:
    match = next((t for t in topics if t.topic_id == topic_id), None)
    if match is not None:
        return match
    available = [t.topic_id for t in topics]
    raise HTTPException(
        status_code=404,
        detail={
            "message": f"topic_id not found: {topic_id}",
            "available_topic_ids": available,
            "hint": (
                "The path topic_id must match a topic_id in student_signals.topics "
                "in the request body. In Swagger, replace the default body with the "
                "course_sample example before calling /explain."
            ),
        },
    )


@app.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    """Browser entry point — interactive API docs live at /docs."""
    return RedirectResponse(url="/docs")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/mediate", response_model=MediateResponse)
def mediate(
    request: MediateRequest = Body(..., openapi_examples=MEDIATE_BODY_EXAMPLES),
) -> MediateResponse:
    try:
        friction, topics = run_mediation(request.teacher_signals, request.student_signals.topics, request.weights)
    except ValueError as exc:
        raise _http_value_error(exc) from exc
    return MediateResponse(teacher_friction=friction, weights=request.weights, topics=topics)


@app.post("/recommend", response_model=RecommendResponse)
def recommend(
    request: RecommendRequest = Body(..., openapi_examples=RECOMMEND_BODY_EXAMPLES),
) -> RecommendResponse:
    try:
        _, topics = run_mediation(request.teacher_signals, request.student_signals.topics, request.weights)
    except ValueError as exc:
        raise _http_value_error(exc) from exc
    return RecommendResponse(top_k=request.top_k, topics=topics[: request.top_k])


@app.post("/explain/{topic_id}", response_model=ExplainResponse)
def explain_topic_route(
    topic_id: str = Path(..., description="Must match a topic_id in the request body.", openapi_examples=TOPIC_ID_EXAMPLES),
    request: MediateRequest = Body(..., openapi_examples=MEDIATE_BODY_EXAMPLES),
) -> ExplainResponse:
    try:
        _, topics = run_mediation(request.teacher_signals, request.student_signals.topics, request.weights)
    except ValueError as exc:
        raise _http_value_error(exc) from exc
    match = _find_topic(topics, topic_id)
    return ExplainResponse(
        topic_id=match.topic_id,
        priority=match.priority,
        rank=match.rank,
        explanation=match.explanation,
        decision_record=match.decision_record,
        recommendations=match.recommendations,
    )


@app.post("/decision_record/{topic_id}", response_model=DecisionRecordOut)
def decision_record(
    topic_id: str = Path(..., description="Must match a topic_id in the request body.", openapi_examples=TOPIC_ID_EXAMPLES),
    request: MediateRequest = Body(..., openapi_examples=MEDIATE_BODY_EXAMPLES),
) -> DecisionRecordOut:
    try:
        _, topics = run_mediation(request.teacher_signals, request.student_signals.topics, request.weights)
    except ValueError as exc:
        raise _http_value_error(exc) from exc
    match = _find_topic(topics, topic_id)
    return DecisionRecordOut(
        topic_id=match.topic_id,
        gap_prevalence=match.gap_prevalence,
        survey_difficulty=match.survey_difficulty,
        survey_disagreement=match.survey_disagreement,
        teacher_friction=match.teacher_friction,
        priority_score=match.priority,
        rank=match.rank,
        explanation=match.explanation,
        decision_record=match.decision_record,
        recommendations=match.recommendations,
    )


@app.post("/weight_sensitivity", response_model=WeightSensitivityResponse)
def weight_sensitivity_route(
    request: WeightSensitivityRequest = Body(..., openapi_examples=WEIGHT_SENSITIVITY_BODY_EXAMPLES),
) -> WeightSensitivityResponse:
    try:
        default_top5, rows = weight_sensitivity(
            request.teacher_signals,
            request.student_signals.topics,
            request.profiles,
        )
    except ValueError as exc:
        raise _http_value_error(exc) from exc
    return WeightSensitivityResponse(
        default_top5=default_top5,
        results=[
            WeightSensitivityResult(profile=profile, top5_topics=top5, spearman_vs_default=rho)
            for profile, top5, rho in rows
        ],
    )


@app.post("/synthesize", response_model=SynthesizeResponse)
def synthesize(
    request: SynthesizeRequest = Body(..., openapi_examples=SYNTHESIZE_BODY_EXAMPLES),
) -> SynthesizeResponse:
    results = []
    for student in request.students:
        result = LearnerState(
            student_id=student.student_id,
            raw_risk=student.raw_risk,
            help_risk=student.help_risk,
            reflect_risk=student.reflect_risk,
            raw_baseline=student.raw_baseline,
            help_baseline=student.help_baseline,
            reflect_baseline=student.reflect_baseline,
        ).synthesize(threshold=request.threshold)
        results.append(
            SynthesizeResultOut(
                student_id=result.student_id,
                synthesis_score=result.synthesis_score,
                isolated=result.isolated,
                raw_risk=result.raw_risk,
                help_risk=result.help_risk,
                reflect_risk=result.reflect_risk,
            )
        )
    return SynthesizeResponse(threshold=request.threshold, results=results)
