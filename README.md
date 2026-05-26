# Classroom Feedback Mediator

Interpretable **coordination layer** for human–AI co-agency under incomplete feedback. Companion to the HAI-Agency @ AIED 2026 workshop paper.

> **Not** an autonomous teaching system — a transparent decision mechanism that ranks topic priorities from teacher and student signals without graded outcomes.

## API design

The API accepts **classroom-level objects**, not precomputed paper variables. For the bundled `examples/sample_mediation_request.json`, cohort teacher friction `F=0.220` is supplied directly (study aggregate from coded interviews); topic gap counts and survey difficulties match the paper appendix decision-record table.

```json
{
  "teacher_signals": {
    "friction": 0.220
  },
  "student_signals": {
    "topics": [
      {
        "topic_id": "planning",
        "gap_count": 16,
        "total_students": 159,
        "survey_difficulty": 0.064
      }
    ]
  }
}
```

You may instead pass coded `feedback` items or legacy `signal_rows`; the service derives `F` from those when `friction` is omitted:

```json
{
  "teacher_signals": {
    "feedback": [
      {"type": "trust_uncertainty", "severity": "medium"},
      {"type": "actionable_insight", "severity": "high"}
    ]
  },
  "student_signals": {
    "topics": [
      {
        "topic_id": "planning",
        "gap_count": 16,
        "total_students": 159,
        "survey_difficulty": 0.064
      }
    ]
  }
}
```

Each ranked topic returns an auditable **decision record** and **role-specific recommendations** for teacher, student, and researcher subsystems:

```json
{
  "topic_id": "planning",
  "priority": 0.100,
  "rank": 3,
  "explanation": ["elevated gap prevalence"],
  "decision_record": {
    "R_t": 0.101,
    "D_t": 0.037,
    "F": 0.220,
    "weights": {"w_r": 0.7, "w_d": 0.2, "w_f": 0.1}
  },
  "recommendations": {
    "teacher": [
      {"type": "teacher_intervention", "action": "Review prerequisite concepts for this topic."}
    ],
    "student": [
      {"type": "student_reflection", "action": "Prompt learners to compare self-rated understanding with recent help-seeking behavior."}
    ],
    "researcher": [
      {"type": "researcher_audit", "action": "Inspect whether the topic priority is robust under alternate weights."}
    ]
  }
}
```

The **researcher lane** supports governance of the mediation process: audit contradictions, weight sensitivity, and trace review before authorizing intervention.

## Python abstractions

Two library-level types mirror the paper architecture without new behavior:

```python
from api.schemas import StudentSignals, TeacherSignals
from mediation import LearnerState, MediationPolicy

policy = MediationPolicy()
friction, ranked = policy.rank(teacher_signals, student_signals)

state = LearnerState(
    student_id="case_a",
    raw_risk=0.31,
    help_risk=0.70,
    reflect_risk=0.52,
)
result = state.synthesize(threshold=0.50)
```

- **`MediationPolicy`** — cohort ranking (`/mediate`)
- **`LearnerState`** — per-student σ synthesis (`/synthesize`)

## Endpoints

All ranking endpoints accept the same body: `teacher_signals` + `student_signals.topics` (+ optional `weights`). In Swagger, select a **named example** before Execute (not the `"string"` placeholders).

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/` | Redirects to `/docs` |
| GET | `/health` | Liveness |
| POST | `/mediate` | Full ranked topic table + decision records (H1) |
| POST | `/recommend` | Top-k topics only |
| POST | `/explain/{topic_id}` | Single-topic explanation + recommendations |
| POST | `/decision_record/{topic_id}` | Auditable numeric trace for one topic |
| POST | `/weight_sensitivity` | Rank stability under alternate weights |
| POST | `/synthesize` | Isolated-learner surfacing (H3) |

**Swagger examples:** `course_sample` (mediation), `course_sample_top5` (`/recommend`), `case_a_isolated` (`/synthesize`). For `/explain/{topic_id}`, the path ID must appear in the request body. On `/weight_sensitivity`, omit `profiles` to use built-in defaults.

**`spearman_vs_default`:** `1.0` = identical rank order vs default weights; `null` on the default profile itself.

## Quick start

```bash
cd mediator
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn api.app:app --reload --port 8080
```

```bash
curl -X POST http://127.0.0.1:8080/mediate \
  -H "Content-Type: application/json" \
  -d @examples/sample_mediation_request.json
```

Open `http://127.0.0.1:8080/` (redirects to Swagger docs).

## Layout

```
teacher_pipeline/   coded feedback → F
mediation/          P_t ranking, explanations, MediationPolicy, LearnerState
api/                REST service
examples/           paper-aligned sample requests
tests/
```

## Tests

```bash
pytest
```

Includes regression checks that `examples/sample_mediation_request.json` and `examples/sample_synthesize_request.json` reproduce the paper appendix decision-record tables.

## License

MIT
