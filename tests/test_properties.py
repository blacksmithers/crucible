"""C9 — scoring invariants via property-based testing (hypothesis)."""

from __future__ import annotations

from typing import Any

from hypothesis import given
from hypothesis import strategies as st

from crucible.config import load_defaults
from crucible.scoring import compute_global_score, compute_topology_penalties

_CONFIG = load_defaults()
_COMPLEXITY = st.sampled_from(["small", "medium", "large", "xlarge"])
_TYPE = st.sampled_from(["implementation", "verification"])


@st.composite
def specs(draw: st.DrawFn) -> dict[str, Any]:
    n_epics = draw(st.integers(min_value=0, max_value=3))
    epics = []
    ticket_counter = 0
    all_ids: list[str] = []
    for ei in range(n_epics):
        n_tickets = draw(st.integers(min_value=0, max_value=4))
        tickets = []
        for _ in range(n_tickets):
            tid = f"t{ticket_counter}"
            ticket_counter += 1
            # Depend on an arbitrary subset of already-created tickets (acyclic).
            deps = draw(st.lists(st.sampled_from(all_ids or ["__none__"]), max_size=2))
            dependencies = [
                {"ticketId": d, "type": "requires"} for d in deps if d != "__none__"
            ]
            tickets.append(
                {
                    "id": tid,
                    "ticketType": draw(_TYPE),
                    "complexity": draw(_COMPLEXITY),
                    "dependencies": dependencies,
                }
            )
            all_ids.append(tid)
        epics.append({"id": f"e{ei}", "tickets": tickets})
    return {"id": "spec", "epics": epics, "blueprints": []}


@given(specs())
def test_global_score_within_bounds(spec: dict[str, Any]) -> None:
    gb = compute_global_score(spec, _CONFIG["scoring"]["weights"], _CONFIG)
    assert 0.0 <= gb.global_score <= 100.0
    assert gb.spec_score is not None and 0.0 <= gb.spec_score <= 100.0
    if gb.epic_avg is not None:
        assert 0.0 <= gb.epic_avg <= 100.0
    if gb.ticket_avg is not None:
        assert 0.0 <= gb.ticket_avg <= 100.0


@given(specs())
def test_topology_penalty_non_positive(spec: dict[str, Any]) -> None:
    topo = compute_topology_penalties(spec, _CONFIG)
    assert topo.total_penalty <= 0.0
    assert topo.island_count <= topo.root_count
    assert topo.island_count <= topo.leaf_count
