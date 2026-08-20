"""Capability scaffolder — generate a gate-passing capability skeleton.

Stdlib-only generator that emits a complete, import-time-enforcement-satisfying
capability skeleton: package files, one placeholder grammar + rule with full
enforced metadata, test stubs, and the ``paxman/capabilities/__init__.py``
wiring. A contributor's job changes from "hand-assemble the unanimous surface
from prose" to "verify and fill in the domain".

Usage::

    uv run python tools/new_capability.py <PackageName> --name <snake> \\
        --authority <str> --spec-name <str> --spec-url <str> \\
        --publication-year <int> \\
        [--spec-version <str>] [--default-format <str>]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import NoReturn

# --------------------------------------------------------------------------- #
# Templates (embedded string constants; tokens replaced via str.replace).
# Tokens: __PKG__ __NAME__ __AUTH__ __SPEC_NAME__ __SPEC_URL__ __YEAR__
#         __SPEC_VER__ __DEF_FMT__ __AUTH_SNAKE__ __RULE_FILE__
# --------------------------------------------------------------------------- #

_PACKAGE_INIT = '''"""__PKG__ capability package."""

from __future__ import annotations

from paxman.capabilities.__PKG__.capability import __PKG__Capability
from paxman.capabilities.__PKG__.contract import __PKG__Contract
from paxman.capabilities.__PKG__.notation import __PKG__Notation

__all__ = ["__PKG__Capability", "__PKG__Contract", "__PKG__Notation"]
'''

_NOTATION = '''"""__PKG__ notation — scaffolded placeholder.

TODO(scaffold): shape the notation per your domain.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class __PKG__Notation:
    """Scaffolded notation for __PKG__.

    TODO(scaffold): replace the single ``value`` field with domain-shaped
    fields (one ``str``/typed component per recognition capture group).
    """

    value: str  # TODO(scaffold): replace with domain fields
'''

_CONTRACT = '''"""__PKG__ contract — user-facing configuration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar

from paxman.core.capability_contract import CapabilityContract


@dataclass(frozen=True)
class __PKG__Contract(CapabilityContract):
    """User-facing configuration for the __PKG__ capability.

    Attributes:
        capability_name: Fixed to "__NAME__" (not user-settable).
        output_format: Canonical output format — "__DEF_FMT__" is the only
            format. Optional — None/"default"/"__DEF_FMT__" all resolve to
            "__DEF_FMT__".
        excluded_rules: Tuple of rule names to exclude.
        pinned_rules: Pin to specific rules (takes precedence over
            excluded_rules).
        year: Year for temporal filtering.
        extra_grammars: Community grammar names (opt-in) to run alongside
            the shipped grammars, in order (SEAM — inherited from base).
    """

    DEFAULT_OUTPUT_FORMAT: ClassVar[str] = "__DEF_FMT__"
    # TODO(scaffold): offer alternative output formats here.
    OFFERED_OUTPUT_FORMATS: ClassVar[frozenset[str]] = frozenset()

    capability_name: str = field(default="__NAME__", init=False)

    def __post_init__(self) -> None:
        super().__post_init__()
'''

_CAPABILITY = '''"""__PKG__ capability — wires grammars and rules together."""

from __future__ import annotations

from collections.abc import Sequence

from paxman.capabilities.__PKG__.contract import __PKG__Contract
from paxman.capabilities.__PKG__.grammar.__NAME___recognition import (
    __PKG__Recognition,
)
from paxman.capabilities.__PKG__.notation import __PKG__Notation
from paxman.capabilities.__PKG__.rules.__RULE_FILE__ import __PKG__Rule
from paxman.core.capability import Capability
from paxman.core.domain import Grammar, Rule


class __PKG__Capability(Capability[__PKG__Notation]):
    """__PKG__ canonicalization capability (scaffold).

    TODO(scaffold): describe what this capability recognizes and the
    authoritative specification(s) it validates against.
    """

    name = "__NAME__"

    def get_grammars(self) -> list[Grammar[__PKG__Notation]]:
        """Return the default grammar instances."""
        return [__PKG__Recognition()]

    def get_rules(self) -> list[Rule[__PKG__Notation]]:
        """Return the default validation rule instances."""
        return [__PKG__Rule()]

    @staticmethod
    def create_contract(
        *,
        excluded_rules: Sequence[str] | None = None,
        pinned_rules: Sequence[str] | None = None,
        year: int | None = None,
        output_format: str | None = None,
        extra_grammars: Sequence[str] | None = None,
    ) -> __PKG__Contract:
        """Factory method for creating contracts with proper defaults.

        Args:
            excluded_rules: Rule names to exclude.
            pinned_rules: Pin to specific rules (takes precedence over
                excluded_rules).
            year: Year for temporal filtering.
            output_format: Output format for canonical values. Optional;
                None/"default"/"__DEF_FMT__" resolve to "__DEF_FMT__".
            extra_grammars: Community grammar names (opt-in) to run
                alongside the shipped grammars, in order (SEAM — the
                surface guard's common block ends with this parameter).

        Returns:
            Configured __PKG__Contract instance.
        """
        return __PKG__Contract(
            excluded_rules=tuple(excluded_rules) if excluded_rules else (),
            pinned_rules=tuple(pinned_rules) if pinned_rules is not None else None,
            year=year,
            output_format=output_format,
            extra_grammars=tuple(extra_grammars) if extra_grammars else (),
        )

    # format_value: NOT overridden — the canonical value IS the default
    # format, and there are no offered alternatives. The Capability base
    # provides the identity formatter. TODO(scaffold): override if you offer
    # alternative output formats.
'''

_GRAMMAR = '''"""__PKG__ recognition grammar — scaffolded placeholder.

TODO(scaffold): replace the placeholder pattern with a real recognizer that
emits span-bearing RecognitionMatch objects.
"""

from __future__ import annotations

import re

from paxman.capabilities.__PKG__.notation import __PKG__Notation
from paxman.core.domain import Grammar, RecognitionMatch

# Placeholder pattern: never matches NON-EMPTY text (it matches only the empty
# string). TODO(scaffold): replace with the real recognition pattern.
_PATTERN = re.compile(r"$^")


class __PKG__Recognition(Grammar[__PKG__Notation]):
    """Scaffolded grammar: __NAME___recognition."""

    name = "__NAME___recognition"
    semantics = "__NAME___recognition"  # TODO(scaffold): coalesce if sharing a meaning
    single_value = False  # TODO(scaffold): opt in when one mention per call

    def recognize(self, text: str) -> list[RecognitionMatch[__PKG__Notation]]:
        """TODO(scaffold): return span-bearing matches for __PKG__ input."""
        return []
'''

_RULE = '''"""__PKG__ rule — scaffolded placeholder (publication: __AUTH__).

TODO(scaffold): implement matches()/normalize() against your authority.
"""

from __future__ import annotations

from paxman.capabilities.__PKG__.notation import __PKG__Notation
from paxman.core.contract import Contract
from paxman.core.domain import Provenance, Rule, RuleStrategy

PUBLICATION = Provenance(
    authority="__AUTH__",
    specification_name="__SPEC_NAME__",
    kind="specification",
    reference_url="__SPEC_URL__",
    version=__SPEC_VER__,  # TODO(scaffold): set when --spec-version is provided
    lifecycle="active",
    publication_year=__YEAR__,
)


class __PKG__Rule(Rule[__PKG__Notation]):
    """Placeholder validation rule for __PKG__.

    TODO(scaffold): rename to the real Section {X.Y.Z}-{description}; implement
    matches()/normalize() against your authority.
    """

    name = "Section 1-overview"  # TODO(scaffold): Section {X.Y.Z}-{description}
    strategy = RuleStrategy.REGEX  # TODO(scaffold): match strategy to representation
    provenance = PUBLICATION
    citation = "Section TODO"  # TODO(scaffold): real citation
    target_semantics = frozenset({"__NAME___recognition"})
    requires_features = frozenset()

    def matches(self, notation: __PKG__Notation, contract: Contract) -> bool:
        """TODO(scaffold): return True when notation is valid per authority."""
        return True

    def normalize(self, notation: __PKG__Notation, contract: Contract) -> str:
        """TODO(scaffold): return the canonical form of notation.value."""
        return notation.value
'''

_GRAMMAR_INIT = '''"""__PKG__ recognition grammars."""
'''

_RULES_INIT = '''"""__PKG__ validation rules."""
'''

_TESTS_INIT = '''"""__NAME__ capability tests (scaffold)."""
'''

_TEST_NOTATION = '''"""Tests for __PKG__Notation (scaffold)."""

import dataclasses

import pytest

from paxman.capabilities.__PKG__.notation import __PKG__Notation


@pytest.mark.capability
class Test__PKG__Notation:
    """Tests for __PKG__Notation."""

    def test_value_attribute(self) -> None:
        n = __PKG__Notation(value="example")
        assert n.value == "example"

    def test_frozen(self) -> None:
        n = __PKG__Notation(value="example")
        with pytest.raises(dataclasses.FrozenInstanceError):
            n.value = "other"  # type: ignore[misc]
'''

_TEST_GRAMMAR = '''"""Tests for __PKG__ recognition grammar (scaffold)."""

import pytest

from paxman.capabilities.__PKG__.grammar.__NAME___recognition import (
    __PKG__Recognition,
)
from paxman.core.domain import Grammar


@pytest.mark.capability
class Test__PKG__Recognition:
    """Grammar: __NAME___recognition."""

    def setup_method(self) -> None:
        self.grammar: Grammar = __PKG__Recognition()

    def test_semantics(self) -> None:
        assert self.grammar.semantics == "__NAME___recognition"

    def test_single_value_false(self) -> None:
        assert self.grammar.single_value is False

    def test_recognize_returns_empty(self) -> None:
        assert self.grammar.recognize("anything") == []
'''

_TEST_RULES = '''"""Tests for __PKG__ rule (scaffold)."""

import pytest

from paxman.capabilities.__PKG__.rules.__RULE_FILE__ import __PKG__Rule
from paxman.core.domain import RuleStrategy


@pytest.mark.capability
class Test__PKG__Rule:
    """Rule: Section 1-overview (scaffold)."""

    def setup_method(self) -> None:
        self.rule = __PKG__Rule()

    def test_rule_metadata(self) -> None:
        assert self.rule.name == "Section 1-overview"
        assert self.rule.strategy is RuleStrategy.REGEX
        assert self.rule.target_semantics == frozenset({"__NAME___recognition"})
        assert self.rule.requires_features == frozenset()
        assert self.rule.provenance.publication_year == __YEAR__

    def test_matches(self) -> None:
        from paxman.capabilities.__PKG__.contract import __PKG__Contract
        from paxman.capabilities.__PKG__.notation import __PKG__Notation

        contract = __PKG__Contract()
        assert self.rule.matches(__PKG__Notation(value="example"), contract) is True

    def test_normalize_returns_canonical_string(self) -> None:
        from paxman.capabilities.__PKG__.contract import __PKG__Contract
        from paxman.capabilities.__PKG__.notation import __PKG__Notation

        contract = __PKG__Contract()
        result = self.rule.normalize(__PKG__Notation(value="example"), contract)
        assert isinstance(result, str)
        assert result == "example"
'''

_TEST_CAPABILITY = '''"""Tests for the __PKG__ capability wiring (scaffold)."""

import pytest

from paxman.api import canonicalize
from paxman.capabilities.__PKG__.capability import __PKG__Capability
from paxman.capabilities.__PKG__.contract import __PKG__Contract
from paxman.core.discovery import register_capability, reset_registry
from paxman.core.domain import Resolution


@pytest.mark.capability
class Test__PKG__Capability:
    """Capability wiring — grammars, rules, factory."""

    def setup_method(self) -> None:
        self.capability = __PKG__Capability()

    def test_metadata(self) -> None:
        assert self.capability.name == "__NAME__"

    def test_get_grammars(self) -> None:
        names = {g.name for g in self.capability.get_grammars()}
        assert names == {"__NAME___recognition"}

    def test_get_rules(self) -> None:
        names = {r.name for r in self.capability.get_rules()}
        assert names == {"Section 1-overview"}

    def test_create_contract_defaults(self) -> None:
        contract = self.capability.create_contract()
        assert isinstance(contract, __PKG__Contract)
        assert contract.output_format == "__DEF_FMT__"


@pytest.mark.capability
class Test__PKG__CapabilityPipeline:
    """End-to-end: scaffold probe resolves to MISSING."""

    @pytest.fixture(autouse=True)
    def _clean_registry(self) -> None:
        reset_registry()
        yield
        reset_registry()

    def test_scaffold_probe_missing(self) -> None:
        register_capability(__PKG__Capability())
        contract = __PKG__Capability.create_contract()
        result = canonicalize("scaffold probe", contract)
        assert result.status == Resolution.MISSING
        assert result.canonicalized_value is None
'''


def _render(template: str, subs: dict[str, str]) -> str:
    """Replace every ``__TOKEN__`` in *template* using *subs*."""
    text = template
    for token, value in subs.items():
        text = text.replace(token, value)
    return text


def _escape_for_double_quoted(value: str) -> str:
    """Escape *value* for safe interpolation inside a double-quoted Python string.

    Handles the injection surface where CLI-provided strings are spliced into
    ``\"...\"`` literals in generated source (authority, spec_name, spec_url,
    spec_version, default_format). Escapes backslash, double-quote, and
    control characters so the rendered file remains a single string literal.
    """

    return (
        value.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\r", "\\r")
    )


_PACKAGE_NAME_RE = re.compile(r"^[A-Z][A-Za-z0-9]+$")
_REGISTRY_NAME_RE = re.compile(r"^[a-z][a-z0-9_]*$")
_IMPORT_RE = re.compile(
    r"^\s*from paxman\.capabilities\.(\w+)\.capability import (\w+)Capability as (\w+)$"
)


def _authority_snake(authority: str) -> str:
    """Lowercase, non-alphanumeric-collapsed snake form of *authority*."""
    return re.sub(r"[^a-z0-9]+", "_", authority.lower()).strip("_")


def _parse_args(argv: list[str]) -> argparse.Namespace:
    """Parse the CLI; argparse raises SystemExit(2) on error."""
    parser = argparse.ArgumentParser(
        prog="new_capability",
        description="Generate a scaffolded Paxman capability skeleton.",
    )
    parser.add_argument("package_name", help="CapWords package name (e.g. Timezone)")
    parser.add_argument("--name", required=True, help="lowercase snake registry name")
    parser.add_argument("--authority", required=True, help="authority name")
    parser.add_argument("--spec-name", required=True, dest="spec_name")
    parser.add_argument("--spec-url", required=True, dest="spec_url")
    parser.add_argument(
        "--publication-year", required=True, type=int, dest="publication_year"
    )
    parser.add_argument("--spec-version", default=None, dest="spec_version")
    parser.add_argument("--default-format", default="canonical", dest="default_format")
    return parser.parse_args(argv)


def _fail(message: str) -> NoReturn:
    """Print an error to stderr and exit 2 (no files written)."""
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(2)


def _wire_capabilities_init(init_path: Path, package: str) -> None:
    """Insert the import line + __all__ entry in alphabetical position.

    Surgical edit: preserves the existing docstring, blank lines, and
    comments by locating the last ``from paxman.capabilities.`` import line
    and the ``__all__`` assignment via regex, then inserting only the new
    entries. The previous implementation rebuilt the whole file from a
    hard-coded template, which would drop future header comments.

    Supports both eager (PEP 562 pre-Item 8) and lazy (PEP 562 __getattr__)
    layouts. In lazy mode also wires ``_LAZY`` and the ``TYPE_CHECKING`` block.
    """

    text = init_path.read_text(encoding="utf-8")

    is_lazy = "_LAZY" in text and "if TYPE_CHECKING:" in text

    if is_lazy:
        # --- Lazy layout: wire _LAZY dict ---
        lazy_match = re.search(r"_LAZY:\s*dict\[.*?\] = \{(.*?)\}", text, re.DOTALL)
        if lazy_match is None:
            _fail("could not locate _LAZY in paxman/capabilities/__init__.py")
        lazy_body = lazy_match.group(1)
        # collect existing keys: "Name": ("module", "Attr"),
        existing_lazy: dict[str, str] = {}
        for lm in re.finditer(r'"(\w+)":\s*\("([^"]+)",\s*"([^"]+)"\)', lazy_body):
            existing_lazy[lm.group(1)] = (
                f'    "{lm.group(1)}": ("{lm.group(2)}", "{lm.group(3)}"),'
            )
        # add new entry
        new_lazy_line = (
            f'    "{package}": ("paxman.capabilities.{package}.capability", '
            f'"{package}Capability"),'
        )
        existing_lazy[package] = new_lazy_line
        sorted_lazy_lines = [existing_lazy[k] for k in sorted(existing_lazy)]
        text = (
            text[: lazy_match.start(1)]
            + "\n"
            + "\n".join(sorted_lazy_lines)
            + "\n"
            + text[lazy_match.end(1) :]
        )

        # --- Wire TYPE_CHECKING block ---
        tc_match = re.search(
            r"if TYPE_CHECKING:\n((?:[ \t]+from paxman\.capabilities\.\w+\.capability "  # noqa: E501
            r"import \w+Capability as \w+\n?)+)",
            text,
        )
        if tc_match is None:
            _fail(
                "could not locate TYPE_CHECKING imports in "  # noqa: E501
                "paxman/capabilities/__init__.py"
            )
        tc_body = tc_match.group(1)
        tc_imports: dict[str, str] = {}
        for line in tc_body.splitlines():
            m = _IMPORT_RE.match(line)
            if m:
                alias = m.group(3)
                tc_imports[alias] = line
        new_tc_line = (  # noqa: E501
            f"    from paxman.capabilities.{package}.capability import "
            f"{package}Capability as {package}"
        )
        tc_imports[package] = new_tc_line
        sorted_tc = [tc_imports[k] for k in sorted(tc_imports)]
        new_tc_block = "\n".join(sorted_tc) + "\n"
        text = text[: tc_match.start(1)] + new_tc_block + text[tc_match.end(1) :]
    else:
        # --- Eager layout (legacy) ---
        import_lines = text.splitlines()
        last_cap_import_idx = -1
        for idx, line in enumerate(import_lines):
            if _IMPORT_RE.match(line):
                last_cap_import_idx = idx
        if last_cap_import_idx == -1:
            _fail(  # noqa: E501
                "could not locate capability imports in paxman/capabilities/__init__.py"
            )

        # Build sorted import block (existing + new), then replace only the
        # contiguous import block.
        imports: list[tuple[str, str]] = []
        for line in text.splitlines():
            match = _IMPORT_RE.match(line)
            if match:
                imports.append((match.group(3), line))
        imports.append(
            (
                package,
                f"from paxman.capabilities.{package}.capability "
                f"import {package}Capability as {package}",
            )
        )
        imports.sort(key=lambda item: item[0])
        import_block = "\n".join(line for _, line in imports)

        # Locate the contiguous block of capability imports to replace.
        first_cap_idx = next(
            idx for idx, line in enumerate(import_lines) if _IMPORT_RE.match(line)
        )
        # Find the end of the contiguous block (first non-import after first).
        block_end = last_cap_import_idx + 1
        # Preserve everything before the block and after it.
        new_lines = (
            import_lines[:first_cap_idx]
            + import_block.splitlines()
            + import_lines[block_end:]
        )
        text = "\n".join(new_lines) + "\n"

    # --- Insert __all__ entry in sorted position (shared) ---
    all_match = re.search(r"__all__\s*=\s*\[(.*?)\]", text, re.DOTALL)
    if all_match is None:
        _fail("could not locate __all__ in paxman/capabilities/__init__.py")
    existing = re.findall(r'"([^"]+)"', all_match.group(1))
    entries = sorted(existing + [package])
    all_block = "[\n" + "".join(f'    "{entry}",\n' for entry in entries) + "]"
    text = (
        text[: all_match.start()] + f"__all__ = {all_block}" + text[all_match.end() :]
    )
    init_path.write_text(text, encoding="utf-8")


def _wire_surface_guard(
    surface_path: Path, package: str, name: str, default_format: str
) -> None:
    """Mirror the __all__ wiring into the homogeneity surface guard.

    test_surface_covers_every_exported_capability asserts every name in
    paxman.capabilities.__all__ appears in _CAPABILITY_SURFACES, so the
    scaffold must add the new capability there too.
    """
    text = surface_path.read_text(encoding="utf-8")

    import_lines: list[tuple[str, str]] = []
    for line in text.splitlines():
        match = re.match(
            r"^from paxman\.capabilities\.(\w+)\.(capability|contract|notation) "
            r"import (\w+)$",
            line,
        )
        if match:
            import_lines.append((match.group(1), line))
    cap_import = (
        f"from paxman.capabilities.{package}.capability import {package}Capability"
    )
    contract_import = (
        f"from paxman.capabilities.{package}.contract import {package}Contract"
    )
    import_lines.append((package, cap_import))
    import_lines.append((package, contract_import))
    import_lines.sort(key=lambda item: item[0])
    import_block = "\n".join(line for _, line in import_lines)

    lines = text.splitlines()
    start = next(
        i for i, ln in enumerate(lines) if ln.startswith("from paxman.capabilities.")
    )
    end = next(i for i, ln in enumerate(lines) if ln.startswith("from paxman.core."))
    text = "\n".join(lines[:start] + import_block.splitlines() + lines[end:]) + "\n"

    match = re.search(r"(_CAPABILITY_SURFACES\s*=\s*\[)(.*?)(\n\])", text, re.DOTALL)
    if match is None:
        _fail(
            "could not locate _CAPABILITY_SURFACES in "
            "tests/unit/test_capability_surface.py"
        )
    header, body, tail = match.group(1), match.group(2), match.group(3)
    existing_ids = re.findall(r'id="([^"]+)"', body)
    new_entry = (
        f"    pytest.param(\n"
        f"        {package}Capability,\n"
        f"        {package}Contract,\n"
        f'        "{_escape_for_double_quoted(default_format)}",\n'
        f'        id="{_escape_for_double_quoted(name)}",\n'
        f"    ),"
    )
    entry_ends = [m.start() for m in re.finditer(r"\),", body)]
    insert_idx = 0
    while insert_idx < len(existing_ids) and existing_ids[insert_idx] < name:
        insert_idx += 1
    if insert_idx >= len(entry_ends):
        new_body = body.rstrip() + "\n" + new_entry
    else:
        cut = entry_ends[insert_idx] + 2
        new_body = body[:cut] + "\n" + new_entry + body[cut:]
    text = text[: match.start()] + header + new_body + tail + text[match.end() :]
    surface_path.write_text(text, encoding="utf-8")


def main(argv: list[str]) -> int:
    """Scaffold a new capability. Returns 0 on success; exits 2 on refusal."""
    args = _parse_args(argv)

    package = args.package_name
    name = args.name

    # --- Guards: validate everything before ANY write (D7) ---
    if not _PACKAGE_NAME_RE.match(package):
        _fail(f"package name {package!r} must be CapWords (^[A-Z][A-Za-z0-9]+$)")
    if not _REGISTRY_NAME_RE.match(name):
        _fail(f"registry name {name!r} must be lowercase snake_case")

    repo_root = Path(__file__).resolve().parents[1]
    pkg_dir = repo_root / "paxman" / "capabilities" / package
    init_path = repo_root / "paxman" / "capabilities" / "__init__.py"

    if pkg_dir.exists():
        _fail(f"capability package already exists: {pkg_dir}")
    if init_path.exists():
        init_text = init_path.read_text(encoding="utf-8")
        if f"as {package}" in init_text or f'"{package}"' in init_text:
            _fail(f"capability already wired in {init_path}")

    authority_snake = _authority_snake(args.authority)
    rule_file = f"{authority_snake}_ed{args.publication_year}"
    # Escape user strings for safe interpolation inside double-quoted literals.
    # Defense-in-depth: even though Provenance fields are data, the templates
    # splice them into ``"..."`` contexts, so quotes/newlines must be escaped.
    esc_authority = _escape_for_double_quoted(args.authority)
    esc_spec_name = _escape_for_double_quoted(args.spec_name)
    esc_spec_url = _escape_for_double_quoted(args.spec_url)
    esc_default_format = _escape_for_double_quoted(args.default_format)
    if args.spec_version is None:
        spec_version = "None"
    else:
        spec_version = f'"{_escape_for_double_quoted(args.spec_version)}"'

    subs = {
        "__PKG__": package,
        "__NAME__": name,
        "__AUTH__": esc_authority,
        "__SPEC_NAME__": esc_spec_name,
        "__SPEC_URL__": esc_spec_url,
        "__YEAR__": str(args.publication_year),
        "__SPEC_VER__": spec_version,
        "__DEF_FMT__": esc_default_format,
        "__AUTH_SNAKE__": authority_snake,
        "__RULE_FILE__": rule_file,
    }

    # --- Generate the 13-file inventory (D3) ---
    files: list[tuple[Path, str]] = [
        (pkg_dir / "__init__.py", _render(_PACKAGE_INIT, subs)),
        (pkg_dir / "notation.py", _render(_NOTATION, subs)),
        (pkg_dir / "contract.py", _render(_CONTRACT, subs)),
        (pkg_dir / "capability.py", _render(_CAPABILITY, subs)),
        (pkg_dir / "grammar" / "__init__.py", _render(_GRAMMAR_INIT, subs)),
        (
            pkg_dir / "grammar" / f"{name}_recognition.py",
            _render(_GRAMMAR, subs),
        ),
        (pkg_dir / "rules" / "__init__.py", _render(_RULES_INIT, subs)),
        (pkg_dir / "rules" / f"{rule_file}.py", _render(_RULE, subs)),
        (
            repo_root / "tests" / "capabilities" / name / "__init__.py",
            _render(_TESTS_INIT, subs),
        ),
        (
            repo_root / "tests" / "capabilities" / name / "test_notation.py",
            _render(_TEST_NOTATION, subs),
        ),
        (
            repo_root / "tests" / "capabilities" / name / "test_grammar.py",
            _render(_TEST_GRAMMAR, subs),
        ),
        (
            repo_root / "tests" / "capabilities" / name / "test_rules.py",
            _render(_TEST_RULES, subs),
        ),
        (
            repo_root / "tests" / "capabilities" / name / "test_capability.py",
            _render(_TEST_CAPABILITY, subs),
        ),
    ]

    for path, content in files:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    # --- Wire paxman/capabilities/__init__.py (D4) ---
    _wire_capabilities_init(init_path, package)

    surface_path = repo_root / "tests" / "unit" / "test_capability_surface.py"
    if surface_path.exists():
        _wire_surface_guard(surface_path, package, name, args.default_format)

    # --- Post-generation output (D6) ---
    print("Generated capability skeleton:")
    for path, _ in files:
        print(f"  {path.relative_to(repo_root)}")
    print(f"  {init_path.relative_to(repo_root)} (wired)")
    print("\nNext steps (the scaffolder could not do these for you):")
    print("  1. Replace the placeholder grammar pattern with a real recognizer.")
    print("  2. Rename Section 1-overview and implement matches()/normalize().")
    print("  3. Shape the notation beyond the placeholder `value` field.")
    print("  4. Add grammar/data/ and rules/data/ when authority tables arrive.")
    print("  5. Register in your entry point; sweep README/CONTEXT/AGENTS docs.")
    print("  6. Delete or extend the placeholder grammar/rule as needed.")
    print("  Note: the scaffold wires the capability into paxman.capabilities.__all__;")
    print(
        "        update tests/unit/test_capability_exports.py's ten-name set only when"
    )
    print("        promoting the capability to a shipped (registry-frozen) capability.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
