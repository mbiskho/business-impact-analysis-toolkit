# Business Impact Analysis Toolkit

Turns BIA interviews into recovery targets you can defend. Each business process records how bad an outage gets over time. The toolkit derives the maximum tolerable period of disruption (MTPD), the RTO and RPO, and pushes those targets down to every system the process depends on. A system ends up with the strictest RTO of anything that needs it.

```
processes.yaml (interview output)            systems.yaml (what runs where)
  impact by category over time ─┐               ┌─ current capability: RTO/RPO we can actually achieve
                                ▼               ▼
                     MTPD → RTO, RPO per process ──► required RTO/RPO per system (strictest dependant)
                                                     ──► gaps: required stricter than capability
                                                     ──► report.md + targets.csv
```

## How targets are derived

- Impacts are scored 1-5 per category (financial, customer, regulatory, reputational) at fixed points in time: 1h, 4h, 1d, 3d, 1w.
- **MTPD** is the first time point where any category reaches the organisation's tolerance (default 4, "major").
- **RTO** is MTPD × `rto_ratio` (default 0.5), rounded down to a standard tier (1h, 4h, 1d, 3d, 1w). Recovery has to finish well before the disruption becomes intolerable, not at the moment it does.
- **RPO** comes straight from the interview (`max_data_loss`).
- **Systems inherit** the minimum RTO and RPO of every process that depends on them, directly or through other systems.
- **Gaps** are systems whose required RTO/RPO is stricter than what they can do today. That list is the DR investment case.

## Usage

```bash
pip install -e ".[dev]"
bia analyse examples/processes.yaml examples/systems.yaml --out out/
# out/report.md   per-process targets, per-system requirements, gaps first
# out/targets.csv for the risk register / GRC tool
```

## Layout

```
bia/model.py    loading + validation (unknown dependencies, missing time points)
bia/engine.py   MTPD, RTO tiering, dependency propagation, gaps (pure functions)
bia/report.py   Markdown and CSV output
bia/cli.py      `bia analyse`
examples/       a small bank: payments, onboarding, reporting, and what they run on
tests/
```
