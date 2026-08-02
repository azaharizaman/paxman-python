"""Email contract for Email capability."""

from __future__ import annotations

from dataclasses import dataclass, field

from paxman.core.contract import resolve_output_format


@dataclass(frozen=True)
class EmailContract:
    """User-facing contract for Email capability."""

    capability_name: str = field(default="email", init=False)
    include_obfuscated: bool = False
    include_localhost: bool = True
    excluded_rules: tuple[str, ...] = field(default_factory=tuple)
    pinned_rules: tuple[str, ...] | None = None
    year: int | None = None
    output_format: str | None = None

    def __post_init__(self) -> None:
        """Validate output_format against Email's single canonical form.

        Email has exactly one canonical output form. Accepted values are
        ``None`` (unset), ``"default"``, and ``"email"`` (the single
        canonical form); any other value raises :class:`ContractError`.

        Raises:
            ContractError: If ``output_format`` is not ``None``, ``"default"``,
                or ``"email"``.
        """
        object.__setattr__(
            self,
            "output_format",
            resolve_output_format(
                self.output_format,
                capability_name="email",
                offered_formats=frozenset(),
                default_format="email",
            ),
        )

    @property
    def active_grammars(self) -> list[str]:
        grammar_rules: dict[str, bool] = {
            "standard_recognition": True,
            "obfuscated_recognition": self.include_obfuscated,
            "localhost_recognition": self.include_localhost,
        }
        return [name for name, active in grammar_rules.items() if active]

    def as_dict(self) -> dict[str, object]:
        return {
            "capability_name": self.capability_name,
            "include_obfuscated": self.include_obfuscated,
            "include_localhost": self.include_localhost,
            "excluded_rules": self.excluded_rules,
            "pinned_rules": self.pinned_rules,
            "year": self.year,
            "output_format": self.output_format,
        }
