"""OpenAPI / Swagger examples loaded from the sample request file."""

from __future__ import annotations

import json
from pathlib import Path

_EXAMPLES_DIR = Path(__file__).resolve().parents[1] / "examples"


def _load(name: str) -> dict:
    with (_EXAMPLES_DIR / name).open(encoding="utf-8") as handle:
        return json.load(handle)


SAMPLE_MEDIATION_REQUEST = _load("sample_mediation_request.json")
SAMPLE_SYNTHESIZE_REQUEST = _load("sample_synthesize_request.json")

MEDIATE_BODY_EXAMPLES = {
    "course_sample": {
        "summary": "Three-topic course snapshot (paper appendix)",
        "description": (
            "Study-offering snapshot: teacher friction F=0.220 (cohort aggregate from coded "
            "interviews); student topics match Appendix decision-record Panel A. Use for "
            "/mediate, /explain/{topic_id}, and /decision_record/{topic_id}. "
            "The path topic_id must appear in student_signals.topics."
        ),
        "value": SAMPLE_MEDIATION_REQUEST,
    }
}

RECOMMEND_BODY_EXAMPLES = {
    "course_sample_top5": {
        "summary": "Top-5 topics from paper appendix snapshot",
        "description": "Same classroom snapshot as course_sample; returns top_k ranked topics.",
        "value": {**SAMPLE_MEDIATION_REQUEST, "top_k": 5},
    }
}

WEIGHT_SENSITIVITY_BODY_EXAMPLES = {
    "course_sample_default_profiles": {
        "summary": "Course snapshot (server default weight profiles)",
        "description": (
            "Omit profiles or set profiles to null to use built-in default and "
            "stable_disagreement_up profiles. Do not send Swagger's placeholder profile object."
        ),
        "value": SAMPLE_MEDIATION_REQUEST,
    }
}

SYNTHESIZE_BODY_EXAMPLES = {
    "case_a_isolated": {
        "summary": "Case A isolated learner + one baseline-flagged peer",
        "description": "case_a is isolated at threshold 0.5; baseline_flagged is not.",
        "value": SAMPLE_SYNTHESIZE_REQUEST,
    }
}

TOPIC_ID_EXAMPLES = {
    "analogical_reasoning": {
        "summary": "Top-ranked topic in sample",
        "value": "analogical_reasoning",
    },
    "planning": {
        "summary": "Sample topic",
        "value": "planning",
    },
}
