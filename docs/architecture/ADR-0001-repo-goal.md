# ADR-0001: Repository intent

## Decision
This repository is a portfolio-grade, runnable reference implementation. It prioritizes:
- clarity over cleverness
- operational realism (runbooks, drills, CI gates)
- secure-by-default habits

## Non-goals
- Building a full production fleet manager
- Making host changes automatically (this repo validates and documents; it does not mutate your servers)
