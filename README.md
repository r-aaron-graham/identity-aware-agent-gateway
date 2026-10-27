# Identity-Aware Agent Gateway

[![CI](https://github.com/r-aaron-graham/identity-aware-agent-gateway/actions/workflows/ci.yml/badge.svg)](https://github.com/r-aaron-graham/identity-aware-agent-gateway/actions/workflows/ci.yml)
![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)
![Docker](https://img.shields.io/badge/docker-ready-2496ED.svg?logo=docker&logoColor=white)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**A FastAPI gateway that decides what an AI agent may do *for this specific user*: signed role tokens, classification-aware retrieval, permission-scoped tools, a policy engine with five release outcomes, a full audit trail, and a human review queue.**

## Quickstart (about 2 minutes, no API keys)

```bash
git clone https://github.com/r-aaron-graham/identity-aware-agent-gateway.git
cd identity-aware-agent-gateway
docker compose up --build
```

Open http://127.0.0.1:8000 for the UI or http://127.0.0.1:8000/docs for the API. Then try it from the command line:

```bash
TOKEN=$(curl -s http://127.0.0.1:8000/api/v1/auth/demo-tokens | python -c "import sys,json; print(json.load(sys.stdin)['analyst']['token'])")

curl -s -X POST http://127.0.0.1:8000/api/v1/agent/query \
  -H "Authorization: Bearer $TOKEN" -H "content-type: application/json" \
  -d '{"prompt":"Summarize the oncall incident runbook","requested_tool":"search_docs","sensitivity":"medium"}'
# -> "outcome": "approved", with cited internal sources

curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8000/api/v1/reviews -H "Authorization: Bearer $TOKEN"
# -> 403: analysts cannot see the review queue
```

## Configuration

| Variable | Default | Description |
| --- | --- | --- |
| `IAAG_SECRET_KEY` | `change-me` | HMAC key for signing tokens. The app logs a warning at startup if you leave the default. |
| `IAAG_DB_PATH` | `./data/iaag.db` | SQLite database location |
| `IAAG_AUTO_INIT_DB` | `true` | Create tables on startup |
| `IAAG_TOKEN_TTL_SECONDS` | `43200` | Token lifetime (12 hours) |
| `IAAG_ENABLE_DEMO_TOKENS` | `true` | Serves `/api/v1/auth/demo-tokens`, which hands out tokens for every role including admin. **Set to `false` anywhere that isn't a local demo.** |

A production-style starter service that demonstrates the core argument behind the article:

> **Why Identity Is the Missing Primitive in AI Agents**

Most AI agent examples ask one question:

**What can the model do?**

This repository is built around a harder one:

**What is this system authorized to do for this user, under these conditions?**

Instead of treating identity as only a login feature, this service treats identity as a **runtime control primitive** that shapes:

- what the caller can see
- which tools the caller can invoke
- what sensitivity level is acceptable for that role
- when the request should be approved, clarified, downgraded, reviewed, or refused
- what gets written into the audit trail

The project is intentionally designed to showcase:

- AI systems architecture
- enterprise access and policy thinking
- role-based request handling
- permission-scoped tool usage
- identity-shaped retrieval
- auditability and operational trust
- governed release behavior
- identity-provider / service-provider style integration patterns

## What this repository does

Identity-Aware Agent Gateway sits between an upstream AI request and the final response.

For every request it performs:

1. **Identity verification**
2. **Role and permission resolution**
3. **Risk and policy evaluation**
4. **Classification-aware retrieval**
5. **Permission-scoped tool execution**
6. **Release decision**
7. **Audit logging**
8. **Human review routing when required**

The service chooses one of five outcomes:

- `approved`
- `clarify`
- `fallback`
- `review_required`
- `refused`

## Production value

This is not a notebook and not a throwaway demo page.

It is useful as a real internal control service for teams that want to:

- gate agent requests by role and sensitivity
- ensure retrieval is shaped by access scope
- prevent unauthorized tool calls
- persist request decisions and review state
- expose a stable API to upstream agent workflows
- create a visible audit trail for AI operations

It is still a **starter implementation**, not a finished enterprise platform. The next upgrades would be SSO, PostgreSQL, external policy management, distributed telemetry, and richer tool adapters.

## Main features

- FastAPI service with OpenAPI docs
- Signed bearer tokens with role claims
- Sample users for viewer, analyst, architect, reviewer, and admin
- Classification-aware retrieval (`public`, `internal`, `restricted`, `confidential`)
- Policy engine with role, sensitivity, ambiguity, and destructive-action rules
- Permission-scoped tool adapters
- SQLite persistence for requests, sources, reviews, and audit events
- Review queue with resolve workflow
- Metrics endpoint
- Browser UI with built-in demo tokens for easy testing
- Docker support
- Automated tests

## Repository layout

```text
identity-aware-agent-gateway/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── db.py
│   ├── models.py
│   ├── auth.py
│   ├── routes.py
│   ├── services/
│   │   ├── identity.py
│   │   ├── policy.py
│   │   ├── retrieval.py
│   │   ├── tools.py
│   │   └── workflow.py
│   ├── templates/
│   │   └── index.html
│   ├── static/
│   │   └── app.js
│   └── sql/
│       └── schema.sql
├── docs/
│   └── architecture.md
├── scripts/
│   ├── seed.py
│   └── mint_demo_tokens.py
├── tests/
│   ├── test_auth.py
│   ├── test_policy.py
│   └── test_api.py
├── Dockerfile
├── docker-compose.yml
├── Makefile
├── requirements.txt
└── README.md
```

## Install and run

### Local Python install

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python scripts/seed.py
uvicorn app.main:app --reload
```

Open:

- UI: http://127.0.0.1:8000/
- API docs: http://127.0.0.1:8000/docs

### Docker

```bash
docker compose up --build
```

## Step-by-step beginner test

### 1. Open the browser UI
Go to `http://127.0.0.1:8000/`

### 2. Click **Load Demo Tokens**
The UI will load signed tokens for sample identities:

- viewer
- analyst
- architect
- reviewer
- admin

### 3. Pick a role and submit these tests

#### Approved
Role: `analyst`  
Prompt: `Summarize the oncall incident runbook`  
Expected outcome: `approved`

#### Clarify
Role: `viewer`  
Prompt: `Can you handle this for me?`  
Expected outcome: `clarify`

#### Refused
Role: `analyst`  
Prompt: `Delete the customer records and wipe the logs`  
Expected outcome: `refused`

#### Review required
Role: `analyst`  
Prompt: `Export the quarterly finance data`  
Tool: `finance_export`  
Expected outcome: `review_required`

#### Fallback
Role: `architect`  
Prompt: `Summarize the lotus cluster migration status`  
Expected outcome: `fallback`

### 4. Review queue
Use the `reviewer` or `admin` token in the Review Queue section to load open review items and resolve them.

## API usage

### Get demo tokens

```bash
curl http://127.0.0.1:8000/api/v1/auth/demo-tokens
```

### Submit a request

```bash
curl -X POST http://127.0.0.1:8000/api/v1/agent/query \
  -H "Authorization: Bearer <PASTE_ANALYST_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Summarize the oncall incident runbook",
    "requested_tool": "search_docs",
    "sensitivity": "medium"
  }'
```

### Read a trace

```bash
curl http://127.0.0.1:8000/api/v1/traces/<trace_id> \
  -H "Authorization: Bearer <PASTE_ANALYST_TOKEN>"
```

### Review queue

```bash
curl http://127.0.0.1:8000/api/v1/reviews \
  -H "Authorization: Bearer <PASTE_REVIEWER_TOKEN>"
```

## Core request lifecycle

```text
User / Upstream Agent
        |
        v
  Bearer Token
        |
        v
  Identity Resolution
        |
        v
  Role + Permission Context
        |
        v
  Policy Evaluation
        |
        +--> clarify
        +--> refused
        +--> review_required
        |
        v
  Classification-Aware Retrieval
        |
        v
  Permission-Scoped Tool Execution
        |
        v
  Approved / Fallback / Review
        |
        v
  Audit Trail + Metrics + Review Queue
```

## What this proves in the article

This repository makes the article’s argument concrete:

- identity shapes retrieval **before** answer generation
- tool access is permission-aware
- risk tolerance changes by role
- sensitive actions can escalate instead of executing
- audit records carry identity context
- AI behavior is a governed workflow, not only a model output

## Running tests

```bash
pip install -r requirements-dev.txt
make lint   # ruff
make test   # pytest with coverage
```

The suite covers the policy engine, the full request and review lifecycle, and the identity boundary: missing, malformed, tampered and expired tokens, role escalation via a forged claim, cross-user trace access, reviewer-only endpoints, double-resolving a review, and disabling demo tokens. CI also builds the Docker image, waits for its healthcheck, runs an end-to-end query, and verifies the container is not running as root.

## License

MIT. See [LICENSE](LICENSE).
