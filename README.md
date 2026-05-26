# Classroom Feedback Mediator

Reference implementation for the interpretable decision layer described in *Surfacing Isolated Learners with Outcome-Independent Mediation of Feedback between Teachers and Students Using AI* (HAI-Agency @ AIED 2026).

The service ranks **course topics** from teacher and student signals: gap prevalence `R_t`, survey–gap disagreement `D_t`, and cohort teacher friction `F`, without using grades or other outcome labels:

```
P_t = w_r * R_t + w_d * D_t + w_f * F
```

Default weights `(w_r, w_d, w_f) = (0.70, 0.20, 0.10)`. Per-topic outputs include a **decision record** (inputs, score, rank) and optional role-specific recommendations. A separate synthesis endpoint flags **isolated learners** surfaced by multi-signal integration but missed by single-channel baselines (paper H3).

This repository is a **demonstration artifact for replication**, not a deployed teaching system.

## Use case

During a course offering, instructors and learning systems accumulate **asynchronous** and **heterogeneous signals**: dashboard observations, help-seeking traces, mid-course surveys, that are difficult to reconcile into a single support plan, especially before grades are available. The mediator addresses that gap by producing a **shared, inspectable topic ranking** that each role can act on.

- **Teachers** can use ranked priorities to decide where to revisit material, prepare office-hour focus, or review unresolved Q&A threads. They can interpret student needs at a topic level granularity. Each topic includes a decision record showing *why* it ranked highly (e.g., high gap prevalence, disagreement between traces and self-report, elevated instructor concern), along with a score.

- **Students** receive reflection-oriented targets tied to topics where cohort evidence and self-report diverge, supporting metacognition without automated grading or intervention. Their feedback directly shapes the instruction they receive. Isolated students who may not have been identified before might receive teacher support.

- **Researchers and system designers** can audit weights, run `/weight_sensitivity`, and inspect traces before implementing features or a policy change. `/synthesize` supports a complementary check: learners surfaced only when understanding, help-seeking, and reflection signals are considered together.

- **ITS / LA integrators** can treat the service as a coordination layer between existing analytics (trace pipelines, survey ingest, instructor analytic dashboards) and downstream adaptation logic. Your system supplies classroom observations, the mediator returns ranked topics and structured recommendations, you retain control over what gets automated.

**Typical flow:**

```
  Teacher dashboard / coded interviews          Student traces + survey
              │                                          │
              └──────────────►  POST /mediate  ◄─────────┘
                                    │
                    ranked topics + decision records
                                    │
              ┌─────────────────────┼─────────────────────┐
              ▼                     ▼                     ▼
        instructor targets    reflection prompts    audit / weight check
              │                                           │
              └──── optional: POST /synthesize ───────────┘
                         (isolated-learner review)
```

**Example:** an instructor sees *analogical reasoning* ranked first, based on student feedback and questions. `/decision_record/analogical_reasoning` returns `R_t`, `D_t`, `F`, and `P_t` so they can verify the priority from student feedback, AI interactions, and other teachers, against their own plan before adjusting the next week's discussion. A separate `/synthesize` call on per-student risk channels may alert the teacher about a student who may need support, who did not self report difficulty, but help-seeking evidence suggests unresolved questions. These students are candidates for human follow-up, not automatic action, and teachers can review evidence in analytic dashboards.

## Requirements

- Python 3.11+
- Dependencies in `requirements.txt` (`fastapi`, `uvicorn`, `pydantic`, `scipy`; `pytest` for tests)

Use any environment manager (Conda, `pip`, or a virtualenv). A dedicated venv is optional.

## Installation and run

```bash
cd mediator
pip install -r requirements.txt
uvicorn api.app:app --reload --port 8080
```

With Conda, activate your environment first, then run the same `pip install` and `uvicorn` commands from the repository root.

Interactive API documentation: [http://127.0.0.1:8080/docs](http://127.0.0.1:8080/docs) (or open `/`, which redirects there).

## Reproducing appendix examples

Bundled requests match the paper appendix decision-record tables:

| File | Endpoint | Content |
|------|----------|---------|
| `examples/sample_mediation_request.json` | `POST /mediate` | Three-topic snapshot; F=0.220; Panel A topic priorities |
| `examples/sample_synthesize_request.json` | `POST /synthesize` | Case A vs. baseline-flagged peer; Panel B |

```bash
curl -X POST http://127.0.0.1:8080/mediate \
  -H "Content-Type: application/json" \
  -d @examples/sample_mediation_request.json
```

In Swagger, select the named examples (`course_sample`, `case_a_isolated`, etc.) rather than the auto-generated schema defaults.

## Request format

Inputs are **classroom-level observations**, not precomputed paper tables. Teacher friction may be supplied directly or derived from coded feedback:

```json
{
  "teacher_signals": { "friction": 0.220 },
  "student_signals": {
    "topics": [
      {
        "topic_id": "analogical_reasoning",
        "gap_count": 25,
        "total_students": 159,
        "survey_difficulty": 0.193
      }
    ]
  },
  "weights": { "w_r": 0.7, "w_d": 0.2, "w_f": 0.1 }
}
```

Alternatively, pass `teacher_signals.feedback` (list of coded items) or `teacher_signals.signal_rows`; omit `friction` when using those fields.

## Python API

```python
from api.schemas import StudentSignals, TeacherSignals, Weights
from mediation import LearnerState, MediationPolicy

policy = MediationPolicy(weights=Weights())
teacher = TeacherSignals(friction=0.220)
student = StudentSignals(topics=[...])  # TopicInput list

friction, ranked = policy.rank(teacher, student)

state = LearnerState(
    student_id="case_a",
    raw_risk=0.31,
    help_risk=0.70,
    reflect_risk=0.52,
)
result = state.synthesize(threshold=0.50)
```

- **`MediationPolicy`** — cohort topic ranking (`POST /mediate`)
- **`LearnerState`** — per-student synthesis score σ (`POST /synthesize`)

## REST endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/` | Redirect to `/docs` |
| GET | `/health` | Liveness |
| POST | `/mediate` | Full ranked topic table and decision records |
| POST | `/recommend` | Top-k topics (default k=5) |
| POST | `/explain/{topic_id}` | Explanation and recommendations for one topic |
| POST | `/decision_record/{topic_id}` | Numeric audit trace for one topic |
| POST | `/weight_sensitivity` | Rank stability under alternate weight profiles |
| POST | `/synthesize` | Isolated-learner flags from per-student risk channels |

For `/explain/{topic_id}` and `/decision_record/{topic_id}`, `topic_id` must appear in `student_signals.topics`. On `/weight_sensitivity`, omit `profiles` to use built-in default and `stable_disagreement_up` profiles.

## Repository layout

```
api/                REST service and request schemas
mediation/          Priority scoring, explanations, MediationPolicy, LearnerState
teacher_pipeline/   Teacher friction from coded feedback
examples/           Appendix-aligned sample requests
tests/              Unit and API regression tests
```

## Tests

```bash
pytest
```

Regression tests assert that the bundled example files reproduce the appendix decision-record values.

## License

MIT
