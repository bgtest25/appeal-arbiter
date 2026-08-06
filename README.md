# appeal-arbiter

A multi-agent system that adjudicates contested content-moderation appeals: given an original
enforcement action (warning, content removal, suspension, ban), the objective evidence, and the
appellant's own statement, it reaches a final decision — **uphold**, **overturn**, or
**escalate** — with full reasoning.

**Live demo:** https://appeal-arbiter-production.up.railway.app/docs

## Architecture

A supervisor + three independent specialist agents, built on LangGraph:

```
                 ┌─────────────┐
        ┌───────▶│  evidence   │───────┐
        │        └─────────────┘       │
        │        ┌─────────────┐       ▼
 START ─┼───────▶│   policy    │──▶ supervisor ──▶ END
        │        └─────────────┘       ▲
        │        ┌─────────────┐       │
        └───────▶│  precedent  │───────┘
                 └─────────────┘
```

Each specialist reasons over exactly one kind of evidence, so their assessments are genuinely
independent signals rather than three copies of the same judgment:

- **Evidence** — does the objective content summary actually support the original action, compared
  against the appellant's own statement?
- **Policy** — do excerpts retrieved from the platform's actual community guidelines (via a local
  Chroma vector store) support classifying this as a violation?
- **Precedent** — how were the most similar past-resolved cases actually decided, and is this case
  meaningfully different?

The **supervisor** reconciles the three assessments into one final decision. When they agree, it
confirms the consensus. When they disagree, it explains which specialist's reasoning is more
decisive for that specific case — not a majority vote — or escalates if the disagreement reflects
genuine ambiguity rather than one side clearly being right.

## Eval results

18 hand-labeled synthetic fixtures (not scraped from real user data — same honest-eval methodology
as disclosed in `fixtures/appeal_cases.py`), replayed through the live graph with real LLM calls,
no mocking (`scripts/eval_appeals.py`):

- **94.4% agreement** with ground truth (17/18)
- Per-outcome F1: uphold 0.94, overturn 1.00, escalate 0.67 (n=2, the hardest class)
- Individual specialist accuracy: evidence 94.4%, policy 88.9%, precedent 94.4%

Full breakdown, confusion matrix, and per-case supervisor reasoning: `scripts/eval_results.json`.

## Running it

```bash
uv sync  # or: pip install -e ".[dev]"
cp .env.example .env  # add your ANTHROPIC_API_KEY
uvicorn appeal_arbiter.main:app --reload
```

- `GET /fixtures` — list the 18 synthetic fixtures
- `POST /fixtures/{id}/adjudicate` — run one through the graph
- `POST /appeals/adjudicate` — submit a new case
- `GET /health`

Run the eval yourself: `python scripts/eval_appeals.py`

## Deployment

Deployed on Railway from the included `Dockerfile`. A parallel AWS deployment path also exists
(`terraform/` — ECR + App Runner + Organizations member account) but isn't the active target; see
commit history for context.
