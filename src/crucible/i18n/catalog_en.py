"""Canonical English guidance strings, keyed for translation overlay.

Every string that reaches the ``guidance`` output layer resolves through this
catalog (via :func:`crucible.i18n.text`), so a translation catalog can override
any of them by key. The English here is the byte-exact prose the engine has
always emitted — moving a string into this catalog must never change EN output.

Rubric ``curriculumPrompt`` / ``naWithoutReasonPrompt`` texts are NOT here: their
English source of truth stays in ``guidance/rubric/data/rubric.json``;
translations override them per rubric-entry id (see ``rubricPrompts`` /
``naPrompts`` in a translation catalog).
"""

from __future__ import annotations

TEXT_EN: dict[str, str] = {
    # -- individual-finding prose scaffolding ---------------------------------
    "guidance.entity.specification": "Specification",
    "guidance.entity.epic": "Epic",
    "guidance.entity.ticket": "Ticket",
    "guidance.status.missing": "missing",
    "guidance.status.partial": "incomplete",
    "guidance.individual.frame": '{entityType} "{entityLabel}" — {statusLabel} "{fieldName}". {prompt}',
    "guidance.individual.naFrame": (
        '{entityType} "{entityLabel}" — field "{fieldName}" is marked N/A but no '
        "naReason provided. {naPrompt}"
    ),
    "guidance.individual.naFallback": (
        "Either populate the field, or add naReason explaining why this field doesn't "
        "apply to this {entityType}."
    ),
    "guidance.individual.defaultPrompt": '{verb} the "{fieldName}" field.',
    # -- composite-pattern prose ----------------------------------------------
    "guidance.foundationGap.specification": (
        'Specification "{title}" — planning_spec phase incomplete.\n\n'
        "The following structural curriculum steps are not yet fulfilled:\n"
        "{missingFields}\n\n"
        "DECLARE these foundational fields together. They are interdependent: goals scope "
        "what architecture must achieve, architecture constrains what scope can promise, "
        "scope determines which requirements are in or out.\n\n"
        "Operation available: action_planning_session({\n"
        "  operation: { type: 'set_metadata', goals, architecture, requirements, scope, ... }\n"
        "})"
    ),
    "guidance.foundationGap.epic": (
        'Epic "{title}" — epic_expansion phase has critical gaps:\n'
        "{missingFields}\n\n"
        "DECLARE these together via a single update.\n\n"
        "Operation available: action_planning_session({\n"
        '  operation: { type: \'update_epic\', epicId: "{entityId}", '
        "architecture, scope, objective, ... }\n"
        "})"
    ),
    "guidance.foundationGap.ticket": (
        'Ticket "{title}" — ticket_expansion has critical gaps:\n'
        "{missingFields}\n\n"
        "DECLARE all together. Files determine scope, AC determines verifiability, steps "
        "determine execution sequence, ticketType determines whether testSpecification is "
        "required.\n\n"
        "Operation available: action_planning_session({\n"
        '  operation: { type: \'update_ticket\', ticketId: "{entityId}", ... }\n'
        "})"
    ),
    "guidance.foundationGap.fallback": (
        "DECLARE: {entityId} has {count} missing critical fields."
    ),
    "guidance.tacticalGap.ticket": (
        'Ticket "{title}" has the following recommended fields incomplete:\n'
        "{missingFields}\n\n"
        "EVALUATE the behavior the declared files must produce, then DECLARE the missing "
        "fields.\n\n"
        "Operation available: action_planning_session({\n"
        '  operation: { type: \'update_ticket\', ticketId: "{entityId}", ... }\n'
        "})"
    ),
    "guidance.tacticalGap.epic": (
        'Epic "{title}" has the following recommended fields incomplete:\n'
        "{missingFields}\n\n"
        "EVALUATE what is needed, then DECLARE these fields in a single update.\n\n"
        "Operation available: action_planning_session({\n"
        '  operation: { type: \'update_epic\', epicId: "{entityId}", ... }\n'
        "})"
    ),
    "guidance.tacticalGap.specLabel": 'Specification "{title}"',
    "guidance.tacticalGap.fallback": (
        "{entityLabel} has recommended fields incomplete:\n"
        "{missingFields}\n\n"
        "EVALUATE and DECLARE the missing fields."
    ),
    "guidance.conditionalGap.frame": (
        "Verification ticket \"{title}\" has ticketType='verification' but "
        "testSpecification is incomplete:\n"
        "{missing}\n\n"
        "DECLARE the complete test specification covering what this verification must assert "
        "and how.\n\n"
        "Operation available: action_planning_session({\n"
        '  operation: { type: \'update_ticket\', ticketId: "{entityId}", '
        "testSpecification: { testTypes, qualityGates, testCommands, coverageTarget } }\n"
        "})"
    ),
    "guidance.conditionalGap.testTypes": "  - testTypes empty (minimum 1)",
    "guidance.conditionalGap.qualityGates": "  - qualityGates empty (minimum 1)",
    "guidance.conditionalGap.testCommands": "  - testCommands empty",
    "guidance.conditionalGap.coverageTarget": "  - coverageTarget not set",
    "guidance.conditionalGap.absent": "  - testSpecification absent",
    # -- fixed decomposition-phase prompts ------------------------------------
    "guidance.fixed.epicDecomposition": (
        "Decomposition phase. Review the current set of epics and decide whether "
        "the decomposition is sufficient. Available operations: create_epic, "
        "update_epic, delete_epic. To advance to the next phase, invoke "
        "complete_planning_session explicitly."
    ),
    "guidance.fixed.ticketDecomposition": (
        "Decomposition phase. Review the current set of tickets in this epic and "
        "decide whether the decomposition is sufficient. Available operations: "
        "create_ticket, update_ticket, delete_ticket. To advance to the next phase, "
        "invoke complete_planning_session explicitly."
    ),
    # -- operation descriptions ------------------------------------------------
    "operations.set_metadata": (
        "Update spec-level fields (goals, architecture, requirements, scope, ...)"
    ),
    "operations.create_epic": "Create a new epic (minimal: title + description + objective)",
    "operations.update_epic": "Update epic fields (architecture, scope, objective, ...)",
    "operations.delete_epic": "Delete an epic and all its tickets",
    "operations.create_ticket": "Create a new ticket (minimal: epicId + title)",
    "operations.update_ticket": (
        "Update ticket fields (acceptanceCriteria, implementationSteps, ...)"
    ),
    "operations.delete_ticket": "Delete a ticket",
    "operations.create_dependencies": "Declare ticket dependencies in batch (up to 5000 pairs)",
    "operations.delete_dependencies": "Remove dependency links",
    "operations.create_blueprint": (
        "Create a new blueprint (title, content, category, coverageType)"
    ),
    "operations.update_blueprint": "Update blueprint fields (coverageType, content, ...)",
    "operations.delete_blueprint": "Delete a blueprint",
    "operations.link_blueprint_to_tickets": "Link a blueprint to one or more tickets",
    "operations.unlink_blueprint_to_tickets": (
        "Remove a blueprint link from one or more tickets"
    ),
    "operations.get_ticket": "Read a ticket for exploration mid-session",
    "operations.get_status": "Get a snapshot of spec/epic/ticket status",
    "operations.gps": "Full X-ray of the specification",
    # -- cross-validation guidance prose --------------------------------------
    "cv.verb.references": "references",
    "cv.verb.modifies": "modifies",
    "cv.verb.deletes": "deletes",
    "cv.circularDependency": (
        "Dependency cycle detected: {arrow}. Cycles break topological "
        "ordering and stall execution at runtime — no ticket in the cycle "
        "can start because each one waits on the other. Remove one of the "
        "dependencies in the cycle (typically the least critical) or "
        "restructure the work split to eliminate the circularity. If two "
        "tickets have a natural circular dependency, they may need to be "
        "consolidated into a single ticket."
    ),
    "cv.brokenReference": (
        'Ticket "{ticketId}" references "{depId}" in dependencies, but '
        '"{depId}" does not exist in any epic of the spec. Broken '
        "references cause immediate failure at runtime when the lifecycle "
        "tries to resolve dependencies to compute execution order. Resolve by "
        "creating the missing ticket (if it's part of the real work) OR by "
        "removing the reference (if it was a typo or a renamed ticket)."
    ),
    "cv.orphanReference": (
        'Ticket "{ticketId}" declares no dependencies (no prior work listed), but other '
        "tickets depend on it. Unjustified roots indicate that preparatory work was "
        "implicitly assumed — there's likely setup, infrastructure, or modeling that "
        "precedes this ticket but wasn't articulated in the spec. Either add the "
        "tickets that precede this work as dependencies, or justify it as a "
        "foundational root if the ticket is genuinely the starting point."
    ),
    "cv.islandTicket": (
        'Ticket "{ticketId}" has neither dependencies nor dependents — it is fully '
        "isolated from the execution graph. Isolated tickets break wave computation "
        "because there is no natural execution order, and may indicate work "
        "disconnected from the rest of the spec (likely a planning smell). Add a "
        "dependency pointing to a ticket that precedes this work, make another "
        "ticket depend on this one, or justify the isolation when the ticket is a "
        "genuinely standalone, intentionally isolated setup task."
    ),
    "cv.topologyRootsExceed": (
        "Spec has {rootCount} tickets without dependencies (roots), but the maximum "
        "allowed is {maximum} (computed: {formula}, ratio {ratioPct}% capped at "
        "{rootCap}). Too many roots indicates that sequencing was under-declared — "
        "several tickets can start in parallel, but this rarely reflects the reality of "
        "implementation. Establish dependencies between related tickets to reflect the "
        "real execution order, or justify the legitimately foundational roots. Real "
        "foundational tickets (3–5 roots) are acceptable when justified; the excess is "
        "almost always a lack of articulation."
    ),
    "cv.topologyLeavesExceed": (
        "Spec has {leafCount} tickets with no dependents (leaves), but the maximum "
        "allowed is {maximum} (computed: {formula}, ratio {ratioPct}% capped at "
        "{leafCap}). Too many leaves indicates that the set of terminal tickets does "
        "not converge — some of them likely should feed into other tickets (e.g., "
        "implementation tickets that should be consumed by verification or integration "
        "tickets). Consider adding integration/verification tickets that depend on the "
        "existing leaves, or consolidate tickets that produce similar outputs."
    ),
    "cv.waveSizeExceed": (
        "Wave {waveNumber} has {ticketCount} tickets — exceeds the configured "
        "maximum ({maximum} per wave). Too much parallelism in the same wave "
        "indicates that dependencies between related tickets were not declared — some "
        "of these tickets likely depend on each other but it was not made explicit. "
        "Simple split suggestion (arbitrary algorithm, humans should review): keep "
        '[{baseJoin}] in the current wave, and add "{suggestedAnchor}" '
        "to the dependencies of tickets [{interJoin}] to create an intermediate "
        "wave. Result: wave {waveNumber} with {baseCount} "
        "tickets, intermediate wave with "
        "{intermediateCount} tickets. Algorithm splits by "
        "alphabetic order with an arbitrary anchor — adjust to reflect real semantic "
        "relationships between tickets when known. Alternatively, if {maximum}+ "
        "tickets really are independent (unlikely in practice), raise "
        "maxTicketsPerWave in the config."
    ),
    "cv.concurrentModification": (
        'Tickets {quoted} all modify "{path}", but no dependency path orders them '
        "relative to each other in the dependency DAG — their edits to the same "
        "file are unordered and mutually independent."
    ),
    "cv.concurrentModification.connector": " and ",
    "cv.fileProvenance.noProvenance": (
        'Ticket "{ticketId}" {verb} "{path}" (in {role}), but no ticket '
        'declares "{path}" in filesToBeCreated and it is not present '
        "in the repository — the file has no provenance."
    ),
    "cv.fileProvenance.missingOrderingEdge": (
        'Ticket "{ticketId}" {verb} "{path}", which ticket '
        '"{creator}" creates, but "{ticketId}" has no transitive '
        'dependency on "{creator}" — the file exists, only the '
        "ordering edge between them is missing."
    ),
    "cv.fileProvenance.createExisting": (
        'Ticket "{ticketId}" declares creating "{path}" (in filesToBeCreated), '
        'but "{path}" already exists in the repository — this is a '
        "modification of an existing file, not a fresh creation."
    ),
    "cv.fileProvenance.deleteSpecTouched": (
        'Ticket "{ticketId}" deletes "{path}" (in filesToBeDeleted), but '
        '"{path}" is created or modified by another ticket in this '
        "specification — the spec both produces/edits and deletes the "
        "same file."
    ),
    "cv.fileConflict.multipleCreators": (
        'File "{path}" is declared in filesToBeCreated of multiple tickets '
        "[{ticketList}], but a file can have only one creator."
    ),
    "cv.blueprintCoverage": (
        'Blueprint "{title}" is linked to {linkedCount} ticket{plural}; '
        "configured minimum: {minTickets}. Underused blueprints indicate that "
        "the architectural pattern was not propagated to implementation — either "
        "the blueprint is unnecessary, or tickets that should consume it are "
        "missing. Review the tickets and link the blueprint to more tickets that "
        "should follow it, consolidate tickets that should use the blueprint but "
        "do not declare it, or remove the blueprint if it has no practical use in "
        "the current spec. Blueprints exist to propagate architectural "
        "decisions — without propagation they are dead weight."
    ),
}
