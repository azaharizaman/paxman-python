from hypothesis import HealthCheck, settings

settings.register_profile(
    "ci",
    max_examples=100,
    suppress_health_check=[HealthCheck.too_slow],
    deadline=None,
)
settings.load_profile("ci")
