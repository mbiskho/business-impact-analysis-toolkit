from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

TIMEPOINTS = ["1h", "4h", "1d", "3d", "1w"]
HOURS = {"15m": 0.25, "1h": 1, "4h": 4, "1d": 24, "3d": 72, "1w": 168, "2w": 336}
CATEGORIES = ["financial", "customer", "regulatory", "reputational"]


@dataclass
class Process:
    name: str
    owner: str
    impacts: dict[str, dict[str, int]]   # category -> timepoint -> 1..5
    max_data_loss: str                   # e.g. "15m", "1d"
    depends_on: list[str] = field(default_factory=list)


@dataclass
class System:
    name: str
    capability_rto: str
    capability_rpo: str
    depends_on: list[str] = field(default_factory=list)


class BIAError(ValueError):
    pass


def hours(label: str) -> float:
    if label not in HOURS:
        raise BIAError(f"unknown duration {label!r}; use one of {list(HOURS)}")
    return HOURS[label]


def load(processes_path: str | Path, systems_path: str | Path) -> tuple[list[Process], dict[str, System]]:
    procs = [Process(**p) for p in yaml.safe_load(Path(processes_path).read_text())["processes"]]
    systems = {s["name"]: System(**s) for s in yaml.safe_load(Path(systems_path).read_text())["systems"]}
    for p in procs:
        for cat in CATEGORIES:
            row = p.impacts.get(cat, {})
            if missing := [t for t in TIMEPOINTS if t not in row]:
                raise BIAError(f"{p.name}: {cat} impact missing time points {missing}")
            if any(not 1 <= v <= 5 for v in row.values()):
                raise BIAError(f"{p.name}: {cat} scores must be 1-5")
            if any(row[a] > row[b] for a, b in zip(TIMEPOINTS, TIMEPOINTS[1:])):
                raise BIAError(f"{p.name}: {cat} impact decreases over time; interviews usually mean the opposite")
        hours(p.max_data_loss)
        for d in p.depends_on:
            if d not in systems:
                raise BIAError(f"{p.name} depends on unknown system {d!r}")
    for s in systems.values():
        hours(s.capability_rto), hours(s.capability_rpo)
        for d in s.depends_on:
            if d not in systems:
                raise BIAError(f"system {s.name} depends on unknown system {d!r}")
    return procs, systems
