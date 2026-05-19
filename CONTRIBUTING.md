# Contributing to LPI Platform

## Onboarding (REQUIRED before writing code)
1. Read `lpi-developer-kit/README.md` (22KB — comprehensive)
2. Complete Level 5-6 challenges from the dev kit
3. Study the existing LPI MCP server tools

## Protocol
1. Read failing test
2. Make test pass
3. `make test` + `make lint`
4. Commit, push, PR to staging
5. CI green + review required

## Daily Report
Update `reports/YYYY-MM-DD.md` daily.

## Setup
```bash
git clone https://github.com/Life-Atlas/lpi-platform.git
cd lpi-platform
pip install -e ".[dev]"
make test
```
