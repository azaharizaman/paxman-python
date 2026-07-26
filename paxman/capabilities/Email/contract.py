"""Email contract for Email capability."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class EmailContract:
    """User-facing contract for Email capability."""

    capability_name: str = field(default="email", init=False)
    include_obfuscated: bool = False
    include_localhost: bool = True
    excluded_rules: tuple[str, ...] = field(default_factory=tuple)
    year: int | None = None
    output_format: str | None = None
    two_digit_base_year: int | None = None

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
            "year": self.year,
            "output_format": self.output_format,
            "two_digit_base_year": self.two_digit_base_year,
        }
