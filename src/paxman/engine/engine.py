"""The engine: a pure, stateless referee that runs the canonicalization pipeline.

Concentrates the three invariants — Boundary, Determinism, Replay — in one
sealed component (PRD §5.1). Holds no domain opinion; only the rules of
engagement.
"""
