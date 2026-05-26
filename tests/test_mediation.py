from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mediation.core import TopicSignals, mediate_topics
from mediation.explain import explain_topic, recommend_roles
from mediation.run import resolve_gap_prevalence
from mediation.synthesize import StudentChannels, classify_student
from teacher_pipeline.teacher import TeacherFeedback, friction_from_feedback


def test_mediation_ranks_by_priority():
    topics = [
        TopicSignals("high", 0.8, 0.2),
        TopicSignals("low", 0.1, 0.1),
    ]
    records = mediate_topics(topics, teacher_friction=0.2)
    assert records[0].topic_id == "high"
    assert records[0].rank == 1
    assert abs(records[0].survey_disagreement - 0.6) < 1e-9


def test_gap_count_resolves_prevalence():
    r = resolve_gap_prevalence(gap_count=16, total_students=159)
    assert abs(r - 16 / 159) < 1e-9


def test_friction_from_human_feedback():
    items = [
        TeacherFeedback("trust_uncertainty"),
        TeacherFeedback("actionable_insight"),
        TeacherFeedback("usability_friction"),
    ]
    f = friction_from_feedback(items)
    assert 0 < f < 1


def test_explanation_and_recommendation():
    topics = [TopicSignals("planning", 0.15, 0.19)]
    record = mediate_topics(topics, teacher_friction=0.22)[0]
    explanation = explain_topic(record, cohort_friction=0.22)
    roles = recommend_roles(record, cohort_friction=0.22)
    assert explanation
    assert roles["teacher"]
    assert roles["student"]
    assert roles["researcher"]


def test_isolated_learner_surfaced():
    channels = StudentChannels(
        student_id="case_a",
        raw_risk=0.31,
        help_risk=0.70,
        reflect_risk=0.52,
        raw_baseline=False,
        help_baseline=False,
        reflect_baseline=False,
    )
    result = classify_student(channels, threshold=0.50)
    assert result.synthesis_score >= 0.50
    assert result.isolated is True


def test_mediation_policy_rank():
    from api.schemas import StudentSignals, TeacherSignals, TopicInput, Weights
    from mediation.policy import MediationPolicy

    policy = MediationPolicy(weights=Weights(w_r=0.7, w_d=0.2, w_f=0.1))
    teacher = TeacherSignals(
        feedback=[
            {"type": "trust_uncertainty", "severity": "medium"},
            {"type": "usability_friction", "severity": "low"},
        ]
    )
    student = StudentSignals(
        topics=[
            TopicInput(topic_id="high", gap_prevalence=0.8, survey_difficulty=0.2),
            TopicInput(topic_id="low", gap_prevalence=0.1, survey_difficulty=0.1),
        ]
    )
    friction, ranked = policy.rank(teacher, student)
    assert 0 < friction <= 1
    assert ranked[0].topic_id == "high"
    assert ranked[0].decision_record.R_t == 0.8
    assert ranked[0].recommendations.researcher


def test_learner_state_synthesize():
    from mediation.learner_state import LearnerState

    state = LearnerState(
        student_id="case_a",
        raw_risk=0.31,
        help_risk=0.70,
        reflect_risk=0.52,
    )
    result = state.synthesize(threshold=0.50)
    assert result.isolated is True


def test_synthesize_sample_case_a():
    from api.openapi_examples import SAMPLE_SYNTHESIZE_REQUEST
    from api.schemas import SynthesizeRequest
    from mediation.synthesize import StudentChannels, classify_student

    req = SynthesizeRequest.model_validate(SAMPLE_SYNTHESIZE_REQUEST)
    by_id = {s.student_id: s for s in req.students}
    case_a = classify_student(
        StudentChannels(
            student_id=by_id["case_a"].student_id,
            raw_risk=by_id["case_a"].raw_risk,
            help_risk=by_id["case_a"].help_risk,
            reflect_risk=by_id["case_a"].reflect_risk,
            raw_baseline=by_id["case_a"].raw_baseline,
            help_baseline=by_id["case_a"].help_baseline,
            reflect_baseline=by_id["case_a"].reflect_baseline,
        ),
        threshold=req.threshold,
    )
    assert case_a.isolated is True
    flagged = classify_student(
        StudentChannels(
            student_id=by_id["baseline_flagged"].student_id,
            raw_risk=by_id["baseline_flagged"].raw_risk,
            help_risk=by_id["baseline_flagged"].help_risk,
            reflect_risk=by_id["baseline_flagged"].reflect_risk,
            raw_baseline=by_id["baseline_flagged"].raw_baseline,
            help_baseline=by_id["baseline_flagged"].help_baseline,
            reflect_baseline=by_id["baseline_flagged"].reflect_baseline,
        ),
        threshold=req.threshold,
    )
    assert flagged.isolated is False


def test_weight_sensitivity_sample_topics():
    from api.openapi_examples import SAMPLE_MEDIATION_REQUEST
    from api.schemas import WeightSensitivityRequest
    from api.service import weight_sensitivity

    req = WeightSensitivityRequest.model_validate(SAMPLE_MEDIATION_REQUEST)
    top5, results = weight_sensitivity(req.teacher_signals, req.student_signals.topics, req.profiles)
    assert "string" not in top5
    assert top5[0] == "analogical_reasoning"
    assert results[0][0].name == "default"
    assert results[1][0].name == "stable_disagreement_up"


def test_sample_mediation_matches_paper_appendix():
    """Bundled course_sample reproduces Appendix decision-record Panel A values."""
    from api.openapi_examples import SAMPLE_MEDIATION_REQUEST
    from api.schemas import MediateRequest
    from api.service import run_mediation

    req = MediateRequest.model_validate(SAMPLE_MEDIATION_REQUEST)
    friction, topics = run_mediation(req.teacher_signals, req.student_signals.topics, req.weights)
    by_id = {t.topic_id: t for t in topics}

    assert abs(friction - 0.220) < 1e-9
    analogical = by_id["analogical_reasoning"]
    planning = by_id["planning"]
    assert analogical.rank == 1
    assert planning.rank == 3
    assert abs(analogical.decision_record.R_t - 0.157) < 0.001
    assert abs(analogical.decision_record.D_t - 0.036) < 0.001
    assert abs(analogical.decision_record.F - 0.220) < 0.001
    assert abs(analogical.priority - 0.139) < 0.001
    assert abs(planning.decision_record.R_t - 0.101) < 0.001
    assert abs(planning.decision_record.D_t - 0.036) < 0.001
    assert abs(planning.priority - 0.100) < 0.001


def test_api_root_redirects_to_docs():
    from fastapi.testclient import TestClient

    from api.app import app

    client = TestClient(app)
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/docs"


def test_api_mediate_course_sample():
    from fastapi.testclient import TestClient

    from api.app import app

    client = TestClient(app)
    from api.openapi_examples import SAMPLE_MEDIATION_REQUEST

    response = client.post("/mediate", json=SAMPLE_MEDIATION_REQUEST)
    assert response.status_code == 200
    body = response.json()
    assert abs(body["teacher_friction"] - 0.220) < 0.001
    assert body["topics"][0]["topic_id"] == "analogical_reasoning"
    assert body["topics"][0]["rank"] == 1


def test_api_explain_unknown_topic_returns_404():
    from fastapi.testclient import TestClient

    from api.app import app
    from api.openapi_examples import SAMPLE_MEDIATION_REQUEST

    client = TestClient(app)
    response = client.post("/explain/not_a_topic", json=SAMPLE_MEDIATION_REQUEST)
    assert response.status_code == 404
    assert "available_topic_ids" in response.json()["detail"]
