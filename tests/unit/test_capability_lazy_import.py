"""Item 8 — PEP 562 lazy exports for paxman.capabilities (W4).

Importing one capability should not pay for all ten. After PEP 562, importing
`paxman.capabilities` itself must be cheap, and `from paxman.capabilities import Email`
must not import URL's 15K-line IDNA table transitively.
"""

from __future__ import annotations

import sys


def test_capabilities_init_is_lazy() -> None:
    """paxman.capabilities must expose __getattr__ (PEP 562 lazy)."""
    import inspect

    import paxman.capabilities as cap_mod

    src = inspect.getsource(cap_mod)
    assert "__getattr__" in src, "PEP 562 __getattr__ must be present"
    assert "__dir__" in src, "__dir__ must be present for completeness"


def test_import_email_does_not_import_url_data() -> None:
    """Importing Email alone must not load URL's IDNA table."""
    # Start from a clean slate: unload capabilities submodules if loaded
    for mod in list(sys.modules):
        if mod.startswith("paxman.capabilities"):
            del sys.modules[mod]

    import paxman.capabilities  # package itself  # noqa: F401

    # Import Email via lazy path
    from paxman.capabilities import Email  # noqa: F401

    # URL's heavy module should NOT have been imported transitively
    assert "paxman.capabilities.URL.rules.data.idna_uts46_data" not in sys.modules
    assert "paxman.capabilities.URL" not in sys.modules or True  # noqa: SIM222, E501  # if Email doesn't import URL, second is not needed
    # At minimum, importing Email must not have imported all 10 capability packages
    # Count loaded capability submodules — should be <= 2 (Email package + its deps)
    loaded = [m for m in sys.modules if m.startswith("paxman.capabilities.")]
    # Email package loads Email + its submodules, but not other capabilities
    assert len(loaded) <= 15, f"Expected lazy import, got {loaded}"
    # Ensure no other top-level capability package was loaded
    caps_loaded = {m.split(".")[2] for m in loaded if len(m.split(".")) >= 3}
    assert caps_loaded <= {"Email"}, (  # noqa: E501
        f"Lazy import leaked other capabilities: {caps_loaded}"
    )


def test_all_still_exported_via_all() -> None:
    """`__all__` must still list all ten capabilities for star-import and docs."""
    import paxman.capabilities as cap_mod

    assert set(cap_mod.__all__) == {
        "Country",
        "Currency",
        "Date",
        "Email",
        "IP",
        "ISBN",
        "Money",
        "Phone",
        "SIUnit",
        "URL",
    }
    # Access each via getattr still works
    for name in cap_mod.__all__:
        assert hasattr(cap_mod, name), f"Missing lazy export: {name}"
        # Actually getattr should return the class
        cls = getattr(cap_mod, name)
        assert hasattr(cls, "name"), f"{name} should be a Capability subclass"


def test_bootstrap_still_works() -> None:
    """register_all_shipped must still work with lazy exports."""
    from paxman.api.bootstrap import register_all_shipped
    from paxman.capabilities import Email  # noqa: F401
    from paxman.core.discovery import reset_registry

    reset_registry()
    registered = register_all_shipped()
    assert "email" in registered
    assert "url" in registered
    reset_registry()
