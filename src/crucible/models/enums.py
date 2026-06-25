"""OpenSpec v1.1 enums (port of ``@specforge/spec-types`` enums).

Values are verbatim string literals so they round-trip identically to the
TypeScript schema and the JSON seeds.
"""

from __future__ import annotations

from enum import StrEnum

__all__ = [
    "ApiContractType",
    "BlueprintCategory",
    "BlueprintCoverageType",
    "BlueprintFormat",
    "Complexity",
    "DependencyType",
    "EpicCategory",
    "GoalType",
    "GuardrailCategory",
    "GuardrailScope",
    "NfrCategory",
    "RequirementType",
    "TechLayer",
    "TestType",
    "TicketType",
]


class GoalType(StrEnum):
    BUSINESS = "business"
    TECHNICAL = "technical"
    USER = "user"
    OPERATIONAL = "operational"


class RequirementType(StrEnum):
    FUNCTIONAL = "functional"
    BUSINESS_RULE = "business-rule"
    INTEGRATION = "integration"


class NfrCategory(StrEnum):
    PERFORMANCE = "performance"
    SECURITY = "security"
    SCALABILITY = "scalability"
    RELIABILITY = "reliability"
    AVAILABILITY = "availability"
    USABILITY = "usability"
    MAINTAINABILITY = "maintainability"
    OBSERVABILITY = "observability"
    COMPLIANCE = "compliance"
    ACCESSIBILITY = "accessibility"


class GuardrailCategory(StrEnum):
    TECHNICAL = "technical"
    BUSINESS = "business"
    REGULATORY = "regulatory"
    ETHICAL = "ethical"
    OPERATIONAL = "operational"


class GuardrailScope(StrEnum):
    SPEC = "spec"
    EPIC = "epic"
    TICKET = "ticket"


class TechLayer(StrEnum):
    DATABASE = "database"
    BACKEND = "backend"
    FRONTEND = "frontend"
    INFRASTRUCTURE = "infrastructure"
    DEVOPS = "devops"
    OBSERVABILITY = "observability"
    AUTH = "auth"
    INTEGRATION = "integration"
    TESTING = "testing"


class ApiContractType(StrEnum):
    REST = "rest"
    GRAPHQL = "graphql"
    RPC = "rpc"
    EVENT = "event"
    CLI = "cli"


class EpicCategory(StrEnum):
    FOUNDATION = "foundation"
    FUNCTIONAL = "functional"
    NON_FUNCTIONAL = "non_functional"
    VERIFICATION = "verification"


class TestType(StrEnum):
    UNIT = "unit"
    INTEGRATION = "integration"
    E2E = "e2e"
    TYPECHECK = "typecheck"
    LINT = "lint"
    BUILD = "build"
    CONTRACT = "contract"
    STRUCTURAL = "structural"
    LAYOUT = "layout"
    A11Y = "a11y"
    PERFORMANCE = "performance"


class TicketType(StrEnum):
    IMPLEMENTATION = "implementation"
    VERIFICATION = "verification"


class Complexity(StrEnum):
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    XLARGE = "xlarge"


class DependencyType(StrEnum):
    REQUIRES = "requires"
    BLOCKS = "blocks"


class BlueprintCategory(StrEnum):
    FLOWCHART = "flowchart"
    ARCHITECTURE = "architecture"
    STATE = "state"
    SEQUENCE = "sequence"
    ERD = "erd"
    MOCKUP = "mockup"
    ADR = "adr"
    COMPONENT = "component"
    DEPLOYMENT = "deployment"
    API = "api"
    ALGORITHM = "algorithm"
    PROTOCOL = "protocol"
    GLOSSARY = "glossary"
    DESIGN_SYSTEM = "design_system"


class BlueprintFormat(StrEnum):
    MARKDOWN = "markdown"
    MERMAID = "mermaid"
    ASCII = "ascii"
    MIXED = "mixed"
    HTML = "html"
    SVG = "svg"
    IMAGE = "image"


class BlueprintCoverageType(StrEnum):
    TICKET = "ticket"
    ALL = "all"
