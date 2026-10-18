from __future__ import annotations

import csv
from pathlib import Path

from .engine import ProcessTargets, SystemRequirement


def markdown(targets: list[ProcessTargets], systems: list[SystemRequirement]) -> str:
    gaps = [s for s in systems if s.rto_gap or s.rpo_gap]
    out = ["# Business impact analysis", ""]
    out += ["## Gaps (required recovery stricter than current capability)", ""]
    if gaps:
        out += ["| System | Needs RTO | Can do | Needs RPO | Can do | Needed by |", "|---|---|---|---|---|---|"]
        for s in sorted(gaps, key=lambda s: (not s.rto_gap, s.name)):
            out.append(f"| **{s.name}** | {s.required_rto} | {s.capability_rto}{' ❌' if s.rto_gap else ''} | "
                       f"{s.required_rpo} | {s.capability_rpo}{' ❌' if s.rpo_gap else ''} | {', '.join(s.needed_by)} |")
    else:
        out.append("None: every system meets the targets of the processes that depend on it.")
    out += ["", "## Process targets", "", "| Process | MTPD | Driven by | RTO | RPO |", "|---|---|---|---|---|"]
    out += [f"| {t.name} | {t.mtpd or '> 1w'} | {t.driver or '-'} | {t.rto} | {t.rpo} |" for t in targets]
    out += ["", "## System requirements", "", "| System | Required RTO | Required RPO | Needed by |", "|---|---|---|---|"]
    out += [f"| {s.name} | {s.required_rto or 'none'} | {s.required_rpo or 'none'} | {', '.join(s.needed_by) or '-'} |"
            for s in systems]
    return "\n".join(out) + "\n"


def write_csv(path: Path, systems: list[SystemRequirement]) -> None:
    with path.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["system", "required_rto", "required_rpo", "capability_rto", "capability_rpo", "rto_gap", "rpo_gap", "needed_by"])
        for s in systems:
            w.writerow([s.name, s.required_rto, s.required_rpo, s.capability_rto, s.capability_rpo,
                        s.rto_gap, s.rpo_gap, ";".join(s.needed_by)])
