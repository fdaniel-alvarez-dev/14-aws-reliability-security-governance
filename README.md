# 14-aws-reliability-security-governance

A practical Linux governance blueprint that turns “tribal knowledge” into repeatable controls: baseline hardening checks, evidence artifacts, and CI-friendly validation.

Focus: governance


## The top pains this repo addresses
1) Preventing configuration drift and insecure defaults—codify baseline expectations and generate auditable evidence.
2) Reducing downtime caused by manual changes—make checks repeatable, deterministic, and runnable before/after maintenance windows.
3) Improving incident readiness—make “what do we do now?” actionable with runbooks, SLOs, and safe-by-default tooling.

## Quick demo (local)
```bash
make demo
make test
```

What you get:
- a baseline audit “pipeline” that produces a JSON report artifact
- demo-mode tests that run fully offline against built-in fixtures
- production-mode checks (guarded) that read real local system state when explicitly enabled

## Tests (two modes)
This repository supports exactly two test modes via `TEST_MODE`:

- `demo`: fast, offline tests against fixtures only.
- `production`: guarded checks against real system state (no network) when properly configured.

Demo:
```bash
TEST_MODE=demo python3 tests/run_tests.py
```

Production (guarded):
```bash
TEST_MODE=production PRODUCTION_TESTS_CONFIRM=1 python3 tests/run_tests.py
```

## Sponsorship and authorship
Sponsored by:
CloudForgeLabs  
https://cloudforgelabs.ainextstudios.com/  
support@ainextstudios.com

Built by:
Freddy D. Alvarez  
https://www.linkedin.com/in/freddy-daniel-alvarez/

For job opportunities, contact:
it.freddy.alvarez@gmail.com

## License
Personal/non-commercial use is free. Commercial use requires permission (paid license).
See `LICENSE` and `COMMERCIAL_LICENSE.md` for details. For commercial licensing, contact: `it.freddy.alvarez@gmail.com`.
Note: this is a non-commercial license and is not OSI-approved; GitHub may not classify it as a standard open-source license.
