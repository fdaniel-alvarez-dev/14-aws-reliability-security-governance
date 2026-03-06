# SLOs and error budgets (practical template)

This document turns reliability goals into measurable targets.

## Service context
- What are we protecting? Linux hosts and the services they run.
- Top pains this repo targets:
  1) Preventing configuration drift and insecure defaults—codify baseline expectations and generate auditable evidence.
  2) Reducing downtime caused by manual changes—make checks repeatable, deterministic, and runnable before/after maintenance windows.
  3) Improving incident readiness—make “what do we do now?” actionable with runbooks, SLOs, and safe-by-default tooling.

## Suggested SLIs (examples)
- Availability: host/service uptime
- Patch compliance: % hosts within patch window
- Security baseline compliance: % hosts passing critical checks (SSH, access controls)
- Recovery: restore drill time for critical services (where applicable)

## Suggested SLOs (start conservative, iterate)
- Availability: 99.9% monthly for critical services
- Patch compliance: 95% of hosts patched within 14 days (example)
- Baseline compliance: 100% pass for critical security checks (example)

## Error budget policy
- If error budget burn is high, freeze risky changes, focus on stability.
- If stable, ship improvements with stronger automation.
