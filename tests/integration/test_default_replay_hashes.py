"""Baseline replay-hash snapshot.

The replay_hash is the engine's behavioral contract: any pipeline change
that alters the candidate set, provenance set, or serialized contract
shifts a hash and fails here. Literals captured 2026-08-04 on the
refactor/streamline-recognition branch. ISBN baseline added 2026-08-05.
Money baseline added 2026-08-06.
URL baseline added 2026-08-07.

The recognition-homogeneity migration MUST land with zero hash changes:
the candidate set it produces is identical to today's. Update these
literals only as an intentional, reviewed consequence of a pipeline change.
"""

import pytest

import paxman
from paxman.capabilities.Country.capability import CountryCapability
from paxman.capabilities.Date.capability import DateCapability
from paxman.capabilities.Email.capability import EmailCapability
from paxman.capabilities.IP.capability import IPCapability
from paxman.capabilities.ISBN.capability import ISBNCapability
from paxman.capabilities.Money.capability import MoneyCapability
from paxman.capabilities.Phone.capability import PhoneCapability
from paxman.capabilities.URL.capability import URLCapability
from paxman.core.discovery import register_capability, reset_registry
from paxman.core.domain import Resolution

# NOTE: each case registers its capability explicitly. The
# paxman/capabilities/__init__.py exports (Country, Date, Email, IP, ISBN,
# Money, Phone) are a packaging surface, not a registry side effect.

BASELINE_HASHES = {
    "date": "30d8cda36f6c484ae97142642eeb76f815759eb051e51432fa264b9b4bb9b5f2",
    "country": "1f56d993e973871a45f35d57e13efe1448f18e5d663aa763f2899364f041ac85",
    "email": "dccb1dec8fbd851c360ecb5feb0ed321a00a2ee6931ed2ba6505c0f92f9ffa31",
    "ip": "f1ae902a100305b511413c34b95ae444386fc864da31c1a02e00fbe1faefa8e4",
    "phone": "01cd035c735461929e5c2974e3b65fbbd615c389c15c3a650113e5050057df7a",
    "isbn": "ad3f0912118b4c47f7cfb56271e8eb143d1fb0bc20ca49b358617a8a8b30f91e",
    "money": "7caeed999ed75780d8300c0cb18631dd0a5e763defbd8f162906d29add4eb1da",
    "url": "4dd3c9ba701daafc8f8a4450b0d52519195e74db4ceda299a7b8f5e721f3484d",
}

CASES = [
    ("date", DateCapability, "2026-07-26"),
    ("country", CountryCapability, "United States"),
    ("email", EmailCapability, "user@example.com"),
    ("ip", IPCapability, "192.168.1.1"),
    ("phone", PhoneCapability, "+1 555 123 4567"),
    ("isbn", ISBNCapability, "9780306406157"),
    ("money", MoneyCapability, "USD500"),
]


@pytest.fixture(autouse=True)
def _fresh_registry():
    """Reset the registry before and after each test."""
    reset_registry()
    yield
    reset_registry()


@pytest.mark.integration
@pytest.mark.parametrize(
    ("key", "capability_cls", "input_text"),
    CASES,
    ids=[key for key, _, _ in CASES],
)
def test_default_replay_hash_matches_baseline(key, capability_cls, input_text):
    register_capability(capability_cls())
    contract = capability_cls.create_contract()
    result = paxman.canonicalize(input_text, contract)
    assert result.status == Resolution.SUCCESS
    assert result.version_stamp.replay_hash == BASELINE_HASHES[key]


@pytest.mark.integration
def test_url_capability_replay_hash():
    register_capability(URLCapability())
    contract = URLCapability.create_contract(year=2026)
    result = paxman.canonicalize("HTTPS://Example.COM:443/path/../other", contract)
    assert result.status == Resolution.SUCCESS
    assert result.version_stamp.replay_hash == BASELINE_HASHES["url"]
