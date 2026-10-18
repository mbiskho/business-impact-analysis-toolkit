import pytest

from bia.engine import mtpd, process_targets, propagate, tier_at_or_below
from bia.model import BIAError, Process, System


def proc(name, scores, deps=(), rpo="1h"):
    imp = {c: dict(zip(["1h", "4h", "1d", "3d", "1w"], scores)) for c in ("financial", "customer", "regulatory", "reputational")}
    return Process(name, "owner", imp, rpo, list(deps))


def test_mtpd_is_first_tolerable_breach():
    assert mtpd(proc("p", [1, 2, 4, 5, 5])) == ("1d", "financial")
    assert mtpd(proc("p", [1, 1, 2, 3, 3])) == (None, None)


def test_rto_is_half_mtpd_rounded_down_to_a_tier():
    assert tier_at_or_below(12) == "4h"      # MTPD 1d -> 12h -> 4h tier
    assert process_targets(proc("p", [1, 2, 4, 5, 5])).rto == "4h"
    assert process_targets(proc("p", [4, 5, 5, 5, 5])).rto == "1h"   # MTPD 1h -> 0.5h -> smallest tier


def test_system_inherits_strictest_target_through_dependencies():
    procs = [proc("fast", [4, 5, 5, 5, 5], ["api"], rpo="15m"), proc("slow", [1, 1, 1, 4, 5], ["dw"], rpo="1d")]
    systems = {"api": System("api", "1h", "15m", ["db"]), "dw": System("dw", "1d", "1d", ["db"]),
               "db": System("db", "4h", "15m")}
    reqs = {r.name: r for r in propagate([process_targets(p) for p in procs], procs, systems)}
    assert reqs["db"].required_rto == "1h" and reqs["db"].needed_by == ["fast", "slow"]
    assert reqs["db"].rto_gap and not reqs["db"].rpo_gap
    assert not reqs["dw"].rto_gap


def test_cycles_are_rejected():
    procs = [proc("p", [4, 5, 5, 5, 5], ["a"])]
    systems = {"a": System("a", "1h", "1h", ["b"]), "b": System("b", "1h", "1h", ["a"])}
    with pytest.raises(BIAError):
        propagate([process_targets(procs[0])], procs, systems)
