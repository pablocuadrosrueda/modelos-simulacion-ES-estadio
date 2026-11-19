"""Flujos de números aleatorios independientes por fuente de azar.

Responsable: A.

Cada fuente de azar del modelo tiene su propio ``numpy.random.Generator``,
derivado de la semilla de la réplica con ``SeedSequence``. El índice de cada
fuente es fijo (posición en :data:`STREAM_NAMES`), de modo que:

* la misma semilla reproduce exactamente la réplica;
* consumir más o menos números de una fuente no altera las demás. Esto es lo
  que permite usar números aleatorios comunes entre escenarios (memoria §5.3).

Regla: **solo se añaden nombres al final** de :data:`STREAM_NAMES`. Reordenar
o borrar cambia todos los resultados (anótalo en ``docs/DECISIONES.md``).

Ejemplo::

    rngs = RngStreams(seed=1234)
    s = rngs["service"].triangular(2, 4, 6)
"""

from __future__ import annotations

from collections.abc import Iterator

import numpy as np

STREAM_NAMES: tuple[str, ...] = (
    "arrivals",  # franja e instante de llegada
    "assignment",  # macrozona, puerta y bloque
    "group",  # estándar / mayores / PMR
    "speed",  # velocidad de marcha
    "distance",  # distancia puerta -> asiento
    "service",  # servicio en torno
    "read_failure",  # I2: ocurrencia y tiempo extra
    "vomitory",  # paso por el vomitorio
    "seat_conflict",  # I1: ocurrencia y resolución
    "turnstile_failure",  # I3: tiempo entre fallos y reparación
    "exit_choice",  # desempates al elegir salida
    "reaction",  # tiempo de reacción a la alarma
    "gate_choice",  # desempates al redirigir (I4)
)
"""Fuentes de azar. El índice de cada nombre es su posición: no reordenar."""

STREAM_INDEX: dict[str, int] = {name: i for i, name in enumerate(STREAM_NAMES)}


class RngStreams:
    """Colección de generadores independientes, uno por fuente de azar.

    Args:
        seed: semilla (entero >= 0) de la réplica.

    Los generadores se crean bajo demanda y se cachean: ``rngs["x"]`` devuelve
    siempre el mismo objeto dentro de una réplica.
    """

    def __init__(self, seed: int) -> None:
        if isinstance(seed, bool) or not isinstance(seed, (int, np.integer)) or seed < 0:
            raise ValueError(f"seed debe ser un entero >= 0, no {seed!r}")
        self.seed = int(seed)
        self._cache: dict[str, np.random.Generator] = {}

    @staticmethod
    def seed_sequence(seed: int, name: str) -> np.random.SeedSequence:
        """``SeedSequence`` del flujo ``name`` para la semilla ``seed``.

        Equivale al hijo ``STREAM_INDEX[name]`` de ``SeedSequence(seed).spawn``,
        pero sin depender del orden en que se piden los flujos.
        """
        try:
            idx = STREAM_INDEX[name]
        except KeyError:
            raise KeyError(f"Flujo aleatorio desconocido: {name!r}. Ver STREAM_NAMES.") from None
        return np.random.SeedSequence(entropy=seed, spawn_key=(idx,))

    def __getitem__(self, name: str) -> np.random.Generator:
        gen = self._cache.get(name)
        if gen is None:
            gen = np.random.default_rng(self.seed_sequence(self.seed, name))
            self._cache[name] = gen
        return gen

    def get(self, name: str) -> np.random.Generator:
        """Alias de ``rngs[name]``."""
        return self[name]

    def __iter__(self) -> Iterator[str]:
        return iter(STREAM_NAMES)

    def __repr__(self) -> str:
        return f"RngStreams(seed={self.seed})"
