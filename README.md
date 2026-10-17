# Insurance Claims Assessment Agent

Car-insurance claims assistant. Prepares a structured assessment for a human adjuster.
It never approves or rejects a claim.

## Setup
```
git clone <repo-url>
cd insurance-claims-agent
uv sync
copy .env.example .env   # then add your own API keys
uv run python smoke_test.py
```