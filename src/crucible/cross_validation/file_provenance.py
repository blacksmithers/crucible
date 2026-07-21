"""Unified file-provenance cross-validation checks (emissions).

The four static invariants
(#1 consume-exists, #2 consume-ordered, #3 create-fresh, #5 no-delete-of-
spec-touched) under the ``file-provenance`` category, plus the folded
single-creator check (#4), which keeps its own ``file-conflict`` category and
config key. Supersedes ``files.py`` (``file-consistency`` +
``files-to-be-referenced``).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .. import i18n
from ..types.config import ValidatorConfig
from ..types.result import CrossValidationFinding
from .emission import CVEmission


def _all_tickets(spec: dict[str, Any]) -> list[dict[str, Any]]:
    return [t for e in (spec.get("epics") or []) for t in (e.get("tickets") or [])]


@dataclass(frozen=True)
class FileProvenanceContext:
    """Optional context threaded from the phase context: the real-repo file set
    (grep evidence) supplied by the MCP-local double-call.

    ``existing_files`` semantics (TRI-STATE):

    - ABSENT (``None`` — no ctx at all, or ctx with ``existing_files=None``) →
      strict spec-internal model, ``E = created_paths`` only. A consumed path
      with no in-spec creator is (correctly) still an error for a greenfield /
      repo-less caller.
    - PRESENT-but-empty (``frozenset()``) → grep ran and confirmed nothing → a
      consumed path that isn't created in-spec genuinely does not exist → a
      real finding.
    """

    existing_files: frozenset[str] | None = None


def build_transitive_deps(
    ticket_id: str, adj: dict[str, list[str]], cache: dict[str, set[str]]
) -> set[str]:
    """Transitive dependency closure of a ticket: the set of every ticket
    reachable FROM ``ticket_id`` by following its ``dependencies`` edges (i.e.
    everything it transitively requires). Memoised via ``cache``.

    Public so the concurrent-modification reachability check (invariante #6)
    reuses the SAME primitive as invariante #2 (consume-ordered)
    rather than re-deriving it.
    """
    if ticket_id in cache:
        return cache[ticket_id]
    result: set[str] = set()
    stack = list(adj.get(ticket_id) or [])
    visiting: set[str] = set()

    while stack:
        current = stack.pop()
        if current in visiting or current == ticket_id:
            continue
        visiting.add(current)
        result.add(current)
        stack.extend(adj.get(current) or [])

    cache[ticket_id] = result
    return result


# The three roles that CONSUME a file. `ordered` marks the roles that also
# require a transitive dependency on the file's in-spec creator (invariante #2).
# `filesToBeDeleted` only needs the file to exist (invariante #1); its extra
# static rule (#5 — no-delete-of-spec-touched) is applied separately
# below (deleted ∈ createdPaths ∪ modifiedPaths).
CONSUMER_ROLES: tuple[tuple[str, str, bool], ...] = (
    ("filesToBeReferenced", "references", True),
    ("filesToBeModified", "modifies", True),
    ("filesToBeDeleted", "deletes", False),
)


@dataclass(frozen=True)
class FileProvenanceMaps:
    """The single-valued file→provider maps the file-provenance model is built
    on, factored out of :func:`check_file_provenance` so the cycle-resolution
    analyzer and the creator election reuse the EXACT
    provenance rule instead of re-deriving it (no drift):

    - ``file_to_creator`` (invariante #2 — single-valued): a path's provider is
      its in-spec CREATOR (``filesToBeCreated``, unconditional — creation always
      wins), or — for a path no ticket creates — the FIRST ticket that MODIFIES
      it (the brownfield standin). Iteration order is epics flattened over their tickets,
      the same order the checks use, so "first modifier" is stable.
    - ``created_paths`` / ``modified_paths`` — the create/modify path sets
      (#3/#5).
    """

    file_to_creator: dict[str, str] = field(default_factory=dict)
    created_paths: set[str] = field(default_factory=set)
    modified_paths: set[str] = field(default_factory=set)


def build_file_provenance_maps(spec: dict[str, Any]) -> FileProvenanceMaps:
    all_tickets = _all_tickets(spec)
    file_to_creator: dict[str, str] = {}
    created_paths: set[str] = set()
    modified_paths: set[str] = set()

    for ticket in all_tickets:
        tid = ticket["id"]
        # Primary provenance: a real in-spec creation (unconditional — a later
        # creator overrides an earlier modifier standin, keeping creation
        # precedence).
        for path in ticket.get("filesToBeCreated") or []:
            created_paths.add(path)
            file_to_creator[path] = tid
        # Secondary provenance: a modifier stands in as the provider for a
        # pre-existing file it edits, only when no ticket creates that path.
        for path in ticket.get("filesToBeModified") or []:
            modified_paths.add(path)
            if path not in file_to_creator:
                file_to_creator[path] = tid

    return FileProvenanceMaps(
        file_to_creator=file_to_creator,
        created_paths=created_paths,
        modified_paths=modified_paths,
    )


def check_file_provenance(
    spec: dict[str, Any],
    config: ValidatorConfig,
    ctx: FileProvenanceContext | None = None,
    language: str = "en",
) -> list[CVEmission]:
    """Unified file-provenance check — existence + ordering across the
    three consumer roles (``filesToBeReferenced``, ``filesToBeModified``,
    ``filesToBeDeleted``), superseding the referenced-only
    ``check_files_to_be_referenced``.

    Existence set ``E = existing_files ∪ created_paths`` (static; no wave
    timeline):

    - **consume-exists** (invariante #1): a consumed path ∉ ``E`` → error.
    - **consume-ordered** (invariante #2): when a consumed path's provenance is
      an in-spec ticket-creation (∈ ``created_paths``, not grep), the consumer
      must have a transitive dependency on the creator → else error. Applies to
      the two ``ordered`` roles only.
    """
    del config  # reserved for signature parity with the check registry
    all_tickets = _all_tickets(spec)
    adj: dict[str, list[str]] = {}
    # Single-valued provenance maps (invariante #2/#3/#5), factored to a shared
    # helper so the cycle-resolution analyzer reuses the SAME rule.
    # created_paths/modified_paths = every path the spec itself creates or edits.
    maps = build_file_provenance_maps(spec)
    file_to_creator = maps.file_to_creator
    created_paths = maps.created_paths
    modified_paths = maps.modified_paths
    dep_cache: dict[str, set[str]] = {}

    for ticket in all_tickets:
        adj[ticket["id"]] = [d["ticketId"] for d in (ticket.get("dependencies") or [])]

    existing_files = ctx.existing_files if ctx is not None else None

    # E = existing_files ∪ created_paths. When existing_files is ABSENT, the
    # model is strict spec-internal (E = created_paths only).
    def exists_in_repo(path: str) -> bool:
        return (existing_files is not None and path in existing_files) or path in created_paths

    emissions: list[CVEmission] = []

    for ticket in all_tickets:
        tid = ticket["id"]
        transitive_deps: set[str] | None = None

        for role, verb, ordered in CONSUMER_ROLES:
            for path in ticket.get(role) or []:
                # invariante #1 — consume-exists. Existence is the prerequisite;
                # when it fails we do not also emit an ordering finding for the
                # same path.
                if not exists_in_repo(path):
                    emissions.append(
                        CVEmission(
                            finding=CrossValidationFinding(
                                category="file-provenance",
                                severity="error",
                                field=f"tickets[id={tid}].{role}:{path}",
                                message=(
                                    f'Ticket "{tid}" {verb} "{path}" but no ticket creates it '
                                    f"and it does not exist in the repository"
                                ),
                                entity_ids=[tid],
                                primary_entity_id=tid,
                                operations=["create_ticket", "update_ticket"],
                            ),
                            guidance=i18n.render(
                                i18n.text(language, "cv.fileProvenance.noProvenance"),
                                {
                                    "ticketId": tid,
                                    "verb": i18n.text(language, f"cv.verb.{verb}"),
                                    "path": path,
                                    "role": role,
                                },
                            ),
                        )
                    )
                    continue

                # invariante #2 — consume-ordered (referenced + modified only).
                if not ordered:
                    continue
                # grep-provenance (pre-existing in the repo) needs no ordering edge.
                if existing_files is not None and path in existing_files:
                    continue

                creator = file_to_creator.get(path)
                if creator and creator != tid:
                    if transitive_deps is None:
                        transitive_deps = build_transitive_deps(tid, adj, dep_cache)
                    if creator not in transitive_deps:
                        emissions.append(
                            CVEmission(
                                finding=CrossValidationFinding(
                                    category="file-provenance",
                                    severity="error",
                                    field=f"tickets[id={tid}].{role}:{path}",
                                    message=(
                                        f'Ticket "{tid}" {verb} "{path}" (created by '
                                        f'"{creator}") but does not declare a transitive '
                                        f"dependency on the creator"
                                    ),
                                    entity_ids=[tid],
                                    primary_entity_id=tid,
                                    operations=["create_dependencies"],
                                ),
                                guidance=i18n.render(
                                    i18n.text(
                                        language, "cv.fileProvenance.missingOrderingEdge"
                                    ),
                                    {
                                        "ticketId": tid,
                                        "verb": i18n.text(language, f"cv.verb.{verb}"),
                                        "path": path,
                                        "creator": creator,
                                    },
                                ),
                            )
                        )

        # invariante #3 — create-fresh. A `filesToBeCreated` path that
        # ALREADY exists in the real repo is a modify mislabelled as create. Only
        # decidable with grep evidence: no-op when `existing_files` is ABSENT, a
        # real finding when grep confirms the path is present.
        for path in ticket.get("filesToBeCreated") or []:
            if existing_files is not None and path in existing_files:
                emissions.append(
                    CVEmission(
                        finding=CrossValidationFinding(
                            category="file-provenance",
                            severity="error",
                            field=f"tickets[id={tid}].filesToBeCreated:{path}",
                            message=(
                                f'Ticket "{tid}" declares creating "{path}" but that file '
                                f"already exists in the repository"
                            ),
                            entity_ids=[tid],
                            primary_entity_id=tid,
                            operations=["update_ticket"],
                        ),
                        guidance=i18n.render(
                            i18n.text(language, "cv.fileProvenance.createExisting"),
                            {"ticketId": tid, "path": path},
                        ),
                    )
                )

        # invariante #5 — no-delete-of-spec-touched. A `filesToBeDeleted`
        # path that the spec itself creates or modifies (∈ created_paths ∪
        # modified_paths) is contradictory: deleting a file the plan produces or
        # edits is wasted work. Fully STATIC — no wave timeline (this supersedes
        # the two deleted `wave-deletion-*` checks).
        for path in ticket.get("filesToBeDeleted") or []:
            if path in created_paths or path in modified_paths:
                producer = file_to_creator.get(path)
                entity_ids = [producer, tid] if producer and producer != tid else [tid]
                emissions.append(
                    CVEmission(
                        finding=CrossValidationFinding(
                            category="file-provenance",
                            severity="error",
                            field=f"tickets[id={tid}].filesToBeDeleted:{path}",
                            message=(
                                f'Ticket "{tid}" deletes "{path}", which the specification '
                                f"itself creates or modifies"
                            ),
                            entity_ids=entity_ids,
                            primary_entity_id=tid,
                            operations=["update_ticket", "delete_ticket"],
                        ),
                        guidance=i18n.render(
                            i18n.text(language, "cv.fileProvenance.deleteSpecTouched"),
                            {"ticketId": tid, "path": path},
                        ),
                    )
                )

    return emissions


def compute_grep_candidates(spec: dict[str, Any]) -> list[str]:
    """The grep candidate paths the CPS pass-1 asks the MCP-local to
    probe. The union of BOTH candidate sets the file-provenance model needs
    real-repo evidence for:

    (a) **consume-exists candidates** — every path CONSUMED (referenced /
        modified / deleted) by some ticket that NO ticket creates.
    (b) **create-fresh candidates** — EVERY ``filesToBeCreated`` path across the
        spec: does this "created" file ALREADY exist in the repo?

    ⚠ (b) is seeded independently of any finding: create-fresh's paths ARE
    created-by-a-ticket, so a "not-created" sourcing would structurally exclude
    them and invariante #3 would silently no-op in the deployed double-call.

    Returns a de-duplicated, sorted list (stable for tests/snapshots).
    """
    all_tickets = _all_tickets(spec)
    created_paths: set[str] = set()
    for ticket in all_tickets:
        for path in ticket.get("filesToBeCreated") or []:
            created_paths.add(path)

    candidates: set[str] = set()
    # (a) consumed-but-uncreated — the three consumer roles, minus in-spec creations.
    for ticket in all_tickets:
        for role in ("filesToBeReferenced", "filesToBeModified", "filesToBeDeleted"):
            for path in ticket.get(role) or []:
                if path not in created_paths:
                    candidates.add(path)
    # (b) all created paths — the create-fresh channel (load-bearing, see above).
    candidates |= created_paths

    return sorted(candidates)


def check_file_consistency(spec: dict[str, Any], language: str = "en") -> list[CVEmission]:
    """Single-creator check (invariante #4), folded under the file-provenance
    umbrella. Each created path
    must have exactly one creator ticket; two or more tickets declaring the same
    path in ``filesToBeCreated`` is a merge conflict. Static — grep-independent.

    ⚠ The finding ``category`` stays ``file-conflict`` and it keeps its own
    ``file-conflict`` config key + registry entry.
    """
    all_tickets = _all_tickets(spec)
    file_to_tickets: dict[str, list[str]] = {}

    for ticket in all_tickets:
        for path in ticket.get("filesToBeCreated") or []:
            file_to_tickets.setdefault(path, []).append(ticket["id"])

    emissions: list[CVEmission] = []
    for path, ticket_ids in file_to_tickets.items():
        if len(ticket_ids) > 1:
            sorted_ids = sorted(ticket_ids)
            primary = sorted_ids[0]
            list_str = ", ".join(sorted_ids)
            emissions.append(
                CVEmission(
                    finding=CrossValidationFinding(
                        category="file-conflict",
                        severity="error",
                        field=f"filesToBeCreated:{path}",
                        message=(
                            f'File "{path}" is in filesToBeCreated of multiple tickets: {list_str}'
                        ),
                        entity_ids=sorted_ids,
                        primary_entity_id=primary,
                        operations=["update_ticket"],
                    ),
                    guidance=i18n.render(
                        i18n.text(language, "cv.fileConflict.multipleCreators"),
                        {"path": path, "ticketList": list_str},
                    ),
                )
            )

    return emissions
