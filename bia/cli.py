from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .engine import process_targets, propagate
from .model import load
from .report import markdown, write_csv


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="bia")
    sub = ap.add_subparsers(dest="cmd", required=True)
    a_ = sub.add_parser("analyse")
    a_.add_argument("processes")
    a_.add_argument("systems")
    a_.add_argument("--out", type=Path, default=Path("out"))
    a_.add_argument("--tolerance", type=int, default=4, help="impact score that is no longer tolerable (1-5)")
    a_.add_argument("--rto-ratio", type=float, default=0.5, help="RTO as a fraction of MTPD")
    a = ap.parse_args(argv)

    procs, systems = load(a.processes, a.systems)
    targets = [process_targets(p, a.tolerance, a.rto_ratio) for p in procs]
    reqs = propagate(targets, procs, systems)
    a.out.mkdir(parents=True, exist_ok=True)
    (a.out / "report.md").write_text(markdown(targets, reqs))
    write_csv(a.out / "targets.csv", reqs)
    gaps = sum(r.rto_gap or r.rpo_gap for r in reqs)
    print(f"{len(procs)} processes, {len(reqs)} systems, {gaps} with gaps → {a.out}/report.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
