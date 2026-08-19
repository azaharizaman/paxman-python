from paxman.api.bootstrap import register_all_shipped
from paxman.api.canonicalize import canonicalize
from paxman.core.discovery import register_capability
from paxman.core.errors import CapabilityError
from paxman.core.extensions import register_grammar, register_rule

__all__ = [
    "CapabilityError",
    "canonicalize",
    "register_capability",
    "register_all_shipped",
    "register_grammar",
    "register_rule",
]
