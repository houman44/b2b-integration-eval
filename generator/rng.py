"""Deterministic randomness that is stable across Python versions.

The Python docs guarantee only that Random.random() returns the same
sequence for the same int seed across versions; randrange, choice and
shuffle may change. Everything here is built on random() alone.
"""
import random


class SeededRNG:
    def __init__(self, seed: int):
        if not isinstance(seed, int):
            raise TypeError("seed must be an int")
        self._r = random.Random(seed)

    def below(self, n: int) -> int:
        return int(self._r.random() * n)

    def between(self, lo: int, hi: int) -> int:
        """Inclusive range."""
        return lo + self.below(hi - lo + 1)

    def choice(self, seq):
        return seq[self.below(len(seq))]

    def digits(self, k: int) -> str:
        return "".join(str(self.below(10)) for _ in range(k))
