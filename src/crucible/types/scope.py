"""Entity scope + response detail (port of ``types/scope.ts``).

Internal helper types for the API scope resolver (not part of the public
``types`` index in the TS source).
"""

from __future__ import annotations

from typing import Literal

from typing_extensions import TypedDict


class ScopeAll(TypedDict):
    type: Literal["all"]


class ScopeSpecification(TypedDict):
    type: Literal["specification"]


class ScopeEpic(TypedDict, total=False):
    type: Literal["epic"]
    id: str
    includeTickets: bool


class ScopeTicket(TypedDict):
    type: Literal["ticket"]
    id: str


class ScopeTickets(TypedDict):
    type: Literal["tickets"]
    ids: list[str]


EntityScope = ScopeAll | ScopeSpecification | ScopeEpic | ScopeTicket | ScopeTickets

ResponseDetail = Literal["minimal", "standard", "full"]
