from __future__ import annotations

from dataclasses import dataclass

from .model import CATEGORIES, HOURS, TIMEPOINTS, BIAError, Process, System, hours

TIERS = ["1h", "4h", "1d", "3d", "1w"]


@dataclass
class ProcessTargets:
    name: str
    mtpd: str | None      # None: never reaches tolerance within a week
    driver: str | None    # category that hits tolerance first
    rto: str
    rpo: str


@dataclass
class SystemRequirement:
    name: str
    required_rto: str | None
    required_rpo: str | None
    needed_by: list[str]
    capability_rto: str
    capability_rpo: str

    @property
    def rto_gap(self) -> bool:
        return self.required_rto is not None and hours(self.capability_rto) > hours(self.required_rto)

    @property
    def rpo_gap(self) -> bool:
        return self.required_rpo is not None and hours(self.capability_rpo) > hours(self.required_rpo)


def mtpd(p: Process, tolerance: int = 4) -> tuple[str | None, str | None]:
    for t in TIMEPOINTS:
        for cat in CATEGORIES:
            if p.impacts[cat][t] >= tolerance:
                return t, cat
    return None, None


def tier_at_or_below(h: float) -> str:
    """Largest standard tier that is <= h hours (at least the smallest tier)."""
    fitting = [t for t in TIERS if HOURS[t] <= h]
    return fitting[-1] if fitting else TIERS[0]


def process_targets(p: Process, tolerance: int = 4, rto_ratio: float = 0.5) -> ProcessTargets:
    m, driver = mtpd(p, tolerance)
    rto = tier_at_or_below(HOURS[m] * rto_ratio) if m else "1w"
    return ProcessTargets(p.name, m, driver, rto, p.max_data_loss)


def propagate(targets: list[ProcessTargets], procs: list[Process], systems: dict[str, System]) -> list[SystemRequirement]:
    """Each system needs the strictest RTO/RPO of every process reaching it through the dependency graph."""
    by_name = {t.name: t for t in targets}
    req: dict[str, dict] = {s: {"rto": None, "rpo": None, "by": set()} for s in systems}

    def visit(system: str, t: ProcessTargets, path: tuple[str, ...]) -> None:
        if system in path:
            raise BIAError(f"dependency cycle: {' -> '.join(path + (system,))}")
        r = req[system]
        if r["rto"] is None or hours(t.rto) < hours(r["rto"]):
            r["rto"] = t.rto
        if r["rpo"] is None or hours(t.rpo) < hours(r["rpo"]):
            r["rpo"] = t.rpo
        r["by"].add(t.name)
        for d in systems[system].depends_on:
            visit(d, t, path + (system,))

    for p in procs:
        for s in p.depends_on:
            visit(s, by_name[p.name], ())
    return [SystemRequirement(name, r["rto"], r["rpo"], sorted(r["by"]),
                              systems[name].capability_rto, systems[name].capability_rpo)
            for name, r in req.items()]
