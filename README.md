# Fraud Detection & Financial Wellness Copilot

Credit-card fraud detection with classical machine learning and an autoencoder, plus a customer-facing AI copilot (Claude) that explains flagged transactions and gives *grounded* financial guidance using tools, retrieval (RAG), memory and guardrails.

Everything runs in one notebook, [`Fraud Detection and Financial Wellness Copilot.ipynb`](Fraud%20Detection%20and%20Financial%20Wellness%20Copilot.ipynb), with the data stored in PostgreSQL (Docker). A 12-minute slide deck is in [`presentation/`](presentation/).

> This is a learning project built on a public, anonymised data set. The customers, merchant categories and calendar dates in the agent demo are **mock or assumed**, and nothing here is production-ready or financial advice.

## What it does

| Part | What |
|---|---|
| Data | [Kaggle Credit Card Fraud Detection](https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud) (284,807 transactions, 492 frauds) plus four monthly FRED macro series; cleaning, time features, storage in PostgreSQL |
| Statistics | class imbalance, class-conditional distributions, Mann-Whitney and Kolmogorov-Smirnov tests with effect sizes |
| Classical ML | Logistic Regression, Random Forest, Gradient Boosting; PR-AUC as the main measure; an **exact cost-based decision threshold** chosen on a validation split |
| Deep learning | a PyTorch autoencoder trained only on legitimate transactions; reconstruction error as the anomaly score |
| AI agent | Claude with five tools (recent transactions, transaction risk, spending breakdown, guidance search, escalation to a human), retrieval over a small knowledge base, conversation memory and code-level guardrails; every run is logged |
| Dashboard | `dashboard.png` (300 DPI) summarising the results |

## Results (test split, 95 frauds)

Each model uses the decision threshold chosen on the validation split by minimising cost (a missed fraud costs its amount, a false alarm costs 5; both are assumptions).

| Model | PR-AUC | Recall | Precision | Total cost |
|---|---|---|---|---|
| Random Forest | 0.847 | 0.737 | 0.959 | 5,172 |
| Gradient Boosting | 0.760 | 0.768 | 0.859 | 3,306 |
| Logistic Regression | 0.729 | 0.747 | 0.888 | 3,303 |
| Autoencoder (no fraud labels) | 0.318 | 0.726 | 0.232 | 3,879 |
| *Flag nothing* | - | 0 | - | 12,973 |

- The model with the best PR-AUC (Random Forest) is not the cheapest: it missed larger frauds. With only 95 test frauds a few large ones decide the cost, so treat the cost ranking as indicative.
- The agent was run with `claude-haiku-5-5` on 7 scenarios (9 turns): all pass the automatic checks and no final answer contained a number or ID that a tool had not returned. Manual review found a cited passage paraphrased with a changed meaning, which a numeric check cannot catch. Details are in the notebook (section 6) and in `agent_transcripts.md`.

## Repository layout

| Path | What |
|---|---|
| `Fraud Detection and Financial Wellness Copilot.ipynb` | the whole project, with outputs from a full run |
| `docker-compose.yml` | PostgreSQL 16 (port **5433**, database `fraud_copilot`, user `proj`, no password: local use only) |
| `requirements.txt` | Python dependencies |
| `.env.example` | environment variables the notebook reads |
| `knowledge_base/` | documents the agent retrieves from (short sample notes; add real guides here) |
| `data/` | place `creditcard.csv` here (see `data/README.md`) |
| `tools/make_synthetic_data.py` | writes a synthetic look-alike file for smoke tests only |
| `dashboard.png`, `agent_transcripts.md`, `agent_transcripts.jsonl` | outputs of the run |
| `presentation/` | slide deck (PowerPoint and PDF) |

## Quick start

1. **Python 3.11+** and the dependencies:
   ```
   pip install -r requirements.txt
   ```
2. **Database** (Docker Desktop must be running):
   ```
   docker compose up -d
   ```
   The same with plain Docker:
   ```
   docker run --name fraud-postgres -e POSTGRES_USER=proj -e POSTGRES_HOST_AUTH_METHOD=trust -e POSTGRES_DB=fraud_copilot -p 5433:5432 -d postgres:16
   ```
   Stop or restart later with `docker stop fraud-postgres` / `docker start fraud-postgres`; remove everything with `docker compose down -v`.
3. **Data:** download `creditcard.csv` from Kaggle into `data/` (see `data/README.md`). The file should have 284,807 rows and 492 frauds.
4. **Keys** (set as environment variables *before* starting Jupyter; never commit them):
   - `ANTHROPIC_API_KEY` for the real agent. Without it a *scripted stand-in* (simple rules, **not** a language model) runs instead and every log line says so.
   - `FRED_API_KEY` is optional; without it the public FRED CSV download is used.

   PowerShell: `$env:ANTHROPIC_API_KEY = "..."`   bash: `export ANTHROPIC_API_KEY="..."`
5. **Run:** start `jupyter lab` from the repository folder, open the notebook and choose *Restart Kernel and Run All Cells*. Expect about 10-20 minutes (Random Forest and the autoencoder dominate); the agent part makes about 20 small API calls.
6. Check the first output cells: the data note names the Kaggle data set, the raw data has 284,807 rows and 492 frauds, the database says `PostgreSQL`, and the agent backend names the Claude model.

## Configuration

| Variable | Default | Meaning |
|---|---|---|
| `DATABASE_URL` | `postgresql://proj@localhost:5433/fraud_copilot` | database connection |
| `CREDITCARD_CSV` | `data/creditcard.csv` | path to the data file |
| `ANTHROPIC_API_KEY` | (unset) | enables the real Claude agent |
| `AGENT_MODEL` | `claude-opus-5-5` | Claude model used by the agent (the reported run used `claude-haiku-5-5`) |
| `FRED_API_KEY` | (unset) | optional FRED API key |
| `FP_COST` | `5` | assumed cost of one false alarm, used by the cost-based threshold |
| `RAG_BACKEND` | `tfidf` | `embeddings` switches to sentence-transformers + FAISS (not tested) |
| `ALLOW_SQLITE_FALLBACK` | (unset) | `1` uses a local SQLite file when Docker is unavailable (testing only; the notebook says so) |

## How the agent stays grounded

- Every account fact must come from a tool result; there is deliberately **no** balance tool, so a balance question is refused.
- A **code-level grounding check** compares every number and ID in an answer with the tool results and user messages of the conversation; with Claude, an unsupported answer triggers one correction request.
- The session decides which customer's data can be read: a request for another customer is refused in code, not only in the prompt.
- Text coming from tools, documents or users is treated as data, not as instructions; disputed or risky transactions are escalated to a human (a mock case here).
- The system prompt stays identical for a whole conversation, because the API binds earlier reasoning blocks to it.
- The check is numeric: it cannot see a wrong *claim* that contains no number, so the logged conversations also need a manual review.

## Limitations

- The data are anonymised (`V1`-`V28` are PCA components), cover two days and one card population, and contain no card or account identifier; the macro series are constant (one month) and carry no information.
- The split is random and stratified; there is no later period to test on. Only 95 frauds are in the test split.
- No model was tuned; the cost-based results depend on the assumed false-alarm cost.
- The agent was run once with one small model on seven scenarios; other models or runs may behave differently. The knowledge base consists of short author-written sample notes, not official guidance.

## Data and citations

- Credit Card Fraud Detection, Machine Learning Group - ULB, Kaggle: https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud (check the data set page for its license). Original publication: Dal Pozzolo, Caelen, Johnson, Bontempi, *Calibrating Probability with Undersampling for Unbalanced Classification*, IEEE CIDM 2015.
- FRED, Federal Reserve Bank of St. Louis (FEDFUNDS, CPIAUCSL, UNRATE, UMCSENT): https://fred.stlouisfed.org/
- Libraries: scikit-learn, PyTorch, SQLAlchemy, pandas, matplotlib, seaborn, Anthropic API.
