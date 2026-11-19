"""Carga y validación de la configuración de un escenario.

Responsable: A.

Una configuración se construye siempre como ``configs/base.json`` + un diff
(``overrides``) que se fusiona en profundidad. El resultado se convierte en
dataclasses inmutables (:class:`Config`) y se valida:

* claves desconocidas o ausentes -> :class:`ConfigError`;
* tipos incorrectos -> :class:`ConfigError`;
* reglas semánticas (repartos que suman 1, perfiles que suman 1, rangos de las
  distribuciones, etc.) -> :class:`ConfigError`.

Unidades: los nombres de campo llevan sufijo de unidad (``_min``, ``_s``,
``_m``, ``_mps``). Los tiempos ``t_*_min`` son minutos respecto al inicio del
partido (``t = 0``).
"""

from __future__ import annotations

import copy
import dataclasses
import json
import math
import types
import typing
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIGS_DIR = REPO_ROOT / "configs"
BASE_CONFIG_PATH = CONFIGS_DIR / "base.json"
EXPERIMENTS_DIR = CONFIGS_DIR / "experiments"

QUEUE_DISCIPLINES = ("fifo", "priority")
EXIT_POLICIES = ("simultaneous", "staggered")
_SUM_TOL = 1e-6


class ConfigError(ValueError):
    """Configuración inválida (clave desconocida, tipo erróneo o regla rota)."""


# --------------------------------------------------------------------------
# Distribuciones
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Triangular:
    """Triangular(low, mode, high)."""

    low: float
    mode: float
    high: float

    @property
    def mean(self) -> float:
        return (self.low + self.mode + self.high) / 3


@dataclass(frozen=True)
class Uniform:
    """Uniforme(low, high)."""

    low: float
    high: float

    @property
    def mean(self) -> float:
        return (self.low + self.high) / 2


@dataclass(frozen=True)
class TruncNormal:
    """Normal(mean, sd) truncada en [min, max]."""

    mean: float
    sd: float
    min: float
    max: float


@dataclass(frozen=True)
class ArrivalBin:
    """Franja del perfil de llegadas: [start_min, end_min) con probabilidad prob."""

    start_min: float
    end_min: float
    prob: float


@dataclass(frozen=True)
class GroupParams:
    """Colectivo de espectadores: proporción y factor sobre la velocidad."""

    share: float
    speed_factor: float


# --------------------------------------------------------------------------
# Incidencias y emergencia
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class SeatConflictParams:
    """I1 · Conflicto por asiento."""

    enabled: bool
    prob: float
    resolution_min: Triangular


@dataclass(frozen=True)
class ReadFailureParams:
    """I2 · Fallo de lectura en el torno."""

    enabled: bool
    prob: float
    extra_s: Uniform


@dataclass(frozen=True)
class TurnstileFailureParams:
    """I3 · Avería de torno (tiempo entre fallos exponencial)."""

    enabled: bool
    mtbf_min: float
    repair_min: Uniform


@dataclass(frozen=True)
class GateClosureParams:
    """I4 · Cierre de la puerta ``gate`` (1-indexada) de la macrozona ``zone``."""

    enabled: bool
    zone: str
    gate: int
    start_min: float
    duration_min: float


@dataclass(frozen=True)
class IncidentsConfig:
    seat_conflict: SeatConflictParams
    read_failure: ReadFailureParams
    turnstile_failure: TurnstileFailureParams
    gate_closure: GateClosureParams


@dataclass(frozen=True)
class EmergencyConfig:
    """Fase D · Evacuación de emergencia (E7, E8)."""

    enabled: bool
    alarm_min: float
    exit_width_factor: float
    speed_factor: float
    reaction_s: Triangular
    blocked_exit: bool
    blocked_exit_zone: str
    reference_min: float


# --------------------------------------------------------------------------
# Config principal
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Config:
    """Todos los parámetros de un escenario (espejo de ``configs/base.json``)."""

    name: str
    n_spectators: int
    zones: tuple[str, ...]
    zone_share: tuple[float, ...]
    gates_per_zone: int
    turnstiles_per_gate: int
    blocks_per_zone: int
    lower_tier_blocks: tuple[int, ...]
    vomitory_capacity: int
    exits_per_zone: int
    exit_width_m: float
    exit_rate_per_m_min: float
    stewards_per_zone: int
    t_open_min: float
    t_start_min: float
    t_end_min: float
    max_sim_hours: float
    queue_discipline: str
    priority_groups: tuple[str, ...]
    exit_policy: str
    exit_stagger_min: float
    redirect_on_gate_closure: bool
    arrival_profile: str
    arrival_profiles: dict[str, tuple[ArrivalBin, ...]]
    groups: dict[str, GroupParams]
    service_time_s: Triangular
    speed_mps: TruncNormal
    distance_m: Uniform
    vomitory_pass_s: Triangular
    incidents: IncidentsConfig
    emergency: EmergencyConfig
    raw: dict[str, Any] = field(default_factory=dict, compare=False, repr=False)
    """Diccionario fusionado del que sale esta Config (para trazabilidad)."""

    # -- derivados útiles ---------------------------------------------------

    @property
    def active_profile(self) -> tuple[ArrivalBin, ...]:
        return self.arrival_profiles[self.arrival_profile]

    @property
    def exit_rate_per_exit_min(self) -> float:
        """Personas/min que atraviesan una salida en régimen ordinario."""
        return self.exit_width_m * self.exit_rate_per_m_min

    @property
    def n_gates(self) -> int:
        return len(self.zones) * self.gates_per_zone

    @property
    def n_turnstiles(self) -> int:
        return self.n_gates * self.turnstiles_per_gate

    def tier_of_block(self, block: int) -> str:
        """``"lower"`` si el bloque está en la grada inferior, si no ``"upper"``."""
        return "lower" if block in self.lower_tier_blocks else "upper"


# --------------------------------------------------------------------------
# Fusión y construcción
# --------------------------------------------------------------------------


def deep_merge(base: Mapping[str, Any], overrides: Mapping[str, Any] | None) -> dict[str, Any]:
    """Devuelve una copia de ``base`` con ``overrides`` fusionado recursivamente.

    Los diccionarios se fusionan clave a clave; cualquier otro valor (listas
    incluidas) se reemplaza entero. No modifica los argumentos.
    """
    result = copy.deepcopy(dict(base))
    for key, value in (overrides or {}).items():
        if isinstance(value, Mapping) and isinstance(result.get(key), Mapping):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def _type_name(tp: Any) -> str:
    return getattr(tp, "__name__", str(tp))


def _build(tp: Any, value: Any, path: str) -> Any:
    """Convierte ``value`` (JSON) al tipo anotado ``tp`` validando la forma."""
    origin = typing.get_origin(tp)
    args = typing.get_args(tp)

    if dataclasses.is_dataclass(tp):
        return _build_dataclass(tp, value, path)
    if origin is tuple:
        if not isinstance(value, list):
            raise ConfigError(f"{path}: se esperaba una lista, no {type(value).__name__}")
        if len(args) == 2 and args[1] is Ellipsis:
            return tuple(_build(args[0], v, f"{path}[{i}]") for i, v in enumerate(value))
        raise ConfigError(f"{path}: tipo tuple no soportado {tp}")  # pragma: no cover
    if origin is dict:
        if not isinstance(value, Mapping):
            raise ConfigError(f"{path}: se esperaba un objeto, no {type(value).__name__}")
        return {str(k): _build(args[1], v, f"{path}.{k}") for k, v in value.items()}
    if origin in (typing.Union, types.UnionType):  # pragma: no cover - no se usa aún
        raise ConfigError(f"{path}: Union no soportado")
    if tp is bool:
        if not isinstance(value, bool):
            raise ConfigError(f"{path}: se esperaba bool, no {value!r}")
        return value
    if tp is int:
        if isinstance(value, bool) or not isinstance(value, int):
            raise ConfigError(f"{path}: se esperaba int, no {value!r}")
        return value
    if tp is float:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ConfigError(f"{path}: se esperaba número, no {value!r}")
        if not math.isfinite(value):
            raise ConfigError(f"{path}: número no finito {value!r}")
        return float(value)
    if tp is str:
        if not isinstance(value, str):
            raise ConfigError(f"{path}: se esperaba str, no {value!r}")
        return value
    raise ConfigError(f"{path}: tipo no soportado {_type_name(tp)}")  # pragma: no cover


def _build_dataclass(cls: type, value: Any, path: str) -> Any:
    # ArrivalBin se escribe en JSON como [start, end, prob].
    if cls is ArrivalBin and isinstance(value, list):
        if len(value) != 3:
            raise ConfigError(f"{path}: una franja es [inicio_min, fin_min, prob]")
        value = dict(zip(("start_min", "end_min", "prob"), value, strict=True))
    if not isinstance(value, Mapping):
        raise ConfigError(f"{path}: se esperaba un objeto, no {type(value).__name__}")

    hints = typing.get_type_hints(cls)
    fields = [f for f in dataclasses.fields(cls) if f.name != "raw"]
    names = {f.name for f in fields}
    unknown = sorted(set(value) - names)
    if unknown:
        raise ConfigError(f"{path or 'config'}: claves desconocidas {unknown}")
    missing = sorted(n for n in names if n not in value)
    if missing:
        raise ConfigError(f"{path or 'config'}: faltan claves {missing}")
    kwargs = {
        f.name: _build(hints[f.name], value[f.name], f"{path}.{f.name}" if path else f.name)
        for f in fields
    }
    return cls(**kwargs)


# --------------------------------------------------------------------------
# Validación semántica
# --------------------------------------------------------------------------


def _check(cond: bool, msg: str) -> None:
    if not cond:
        raise ConfigError(msg)


def _check_tri(t: Triangular, path: str, *, positive: bool = True) -> None:
    _check(t.low <= t.mode <= t.high, f"{path}: debe cumplirse low <= mode <= high")
    if positive:
        _check(t.low >= 0, f"{path}: low debe ser >= 0")


def _check_uni(u: Uniform, path: str) -> None:
    _check(0 <= u.low <= u.high, f"{path}: debe cumplirse 0 <= low <= high")


def _check_prob(p: float, path: str) -> None:
    _check(0.0 <= p <= 1.0, f"{path}: probabilidad fuera de [0, 1]")


def validate(cfg: Config) -> None:
    """Comprueba las reglas semánticas; lanza :class:`ConfigError` si alguna falla."""
    _check(cfg.n_spectators > 0, "n_spectators debe ser > 0")
    _check(len(cfg.zones) > 0, "zones no puede estar vacío")
    _check(len(set(cfg.zones)) == len(cfg.zones), "zones tiene repetidos")
    _check(len(cfg.zone_share) == len(cfg.zones), "zone_share debe tener un valor por zona")
    _check(all(s >= 0 for s in cfg.zone_share), "zone_share no admite negativos")
    _check(abs(sum(cfg.zone_share) - 1) < _SUM_TOL, "zone_share debe sumar 1")
    for name in (
        "gates_per_zone",
        "turnstiles_per_gate",
        "blocks_per_zone",
        "vomitory_capacity",
        "exits_per_zone",
        "stewards_per_zone",
    ):
        _check(getattr(cfg, name) >= 1, f"{name} debe ser >= 1")
    _check(cfg.exit_width_m > 0 and cfg.exit_rate_per_m_min > 0, "capacidad de salida > 0")
    _check(
        all(1 <= b <= cfg.blocks_per_zone for b in cfg.lower_tier_blocks),
        "lower_tier_blocks fuera de 1..blocks_per_zone",
    )
    _check(cfg.t_open_min < cfg.t_start_min < cfg.t_end_min, "t_open < t_start < t_end")
    _check(cfg.max_sim_hours > 0, "max_sim_hours debe ser > 0")
    _check(cfg.queue_discipline in QUEUE_DISCIPLINES, f"queue_discipline en {QUEUE_DISCIPLINES}")
    _check(cfg.exit_policy in EXIT_POLICIES, f"exit_policy en {EXIT_POLICIES}")
    _check(cfg.exit_stagger_min >= 0, "exit_stagger_min debe ser >= 0")
    unknown_groups = set(cfg.priority_groups) - set(cfg.groups)
    _check(not unknown_groups, f"priority_groups con grupos desconocidos {sorted(unknown_groups)}")

    # Perfiles de llegada
    _check(cfg.arrival_profile in cfg.arrival_profiles, "arrival_profile no está definido")
    for pname, bins in cfg.arrival_profiles.items():
        _check(len(bins) > 0, f"arrival_profiles.{pname} vacío")
        for i, b in enumerate(bins):
            _check(b.start_min < b.end_min, f"arrival_profiles.{pname}[{i}]: inicio >= fin")
            _check_prob(b.prob, f"arrival_profiles.{pname}[{i}]")
            if i:
                _check(
                    bins[i - 1].end_min <= b.start_min,
                    f"arrival_profiles.{pname}: franjas desordenadas o solapadas",
                )
        _check(
            bins[0].start_min >= cfg.t_open_min,
            f"arrival_profiles.{pname}: llegadas antes de abrir puertas",
        )
        total = sum(b.prob for b in bins)
        _check(abs(total - 1) < _SUM_TOL, f"arrival_profiles.{pname} suma {total}, no 1")

    # Grupos
    _check(len(cfg.groups) > 0, "groups no puede estar vacío")
    for gname, g in cfg.groups.items():
        _check_prob(g.share, f"groups.{gname}.share")
        _check(g.speed_factor > 0, f"groups.{gname}.speed_factor debe ser > 0")
    total = sum(g.share for g in cfg.groups.values())
    _check(abs(total - 1) < _SUM_TOL, f"groups.*.share suma {total}, no 1")

    # Distribuciones
    _check_tri(cfg.service_time_s, "service_time_s")
    _check_tri(cfg.vomitory_pass_s, "vomitory_pass_s")
    _check_uni(cfg.distance_m, "distance_m")
    sp = cfg.speed_mps
    _check(sp.sd >= 0 and 0 < sp.min <= sp.mean <= sp.max, "speed_mps: 0 < min <= mean <= max")

    # Incidencias
    inc = cfg.incidents
    _check_prob(inc.seat_conflict.prob, "incidents.seat_conflict.prob")
    _check_tri(inc.seat_conflict.resolution_min, "incidents.seat_conflict.resolution_min")
    _check_prob(inc.read_failure.prob, "incidents.read_failure.prob")
    _check_uni(inc.read_failure.extra_s, "incidents.read_failure.extra_s")
    _check(inc.turnstile_failure.mtbf_min > 0, "incidents.turnstile_failure.mtbf_min > 0")
    _check_uni(inc.turnstile_failure.repair_min, "incidents.turnstile_failure.repair_min")
    gc = inc.gate_closure
    _check(gc.zone in cfg.zones, "incidents.gate_closure.zone no está en zones")
    _check(1 <= gc.gate <= cfg.gates_per_zone, "incidents.gate_closure.gate fuera de rango")
    _check(gc.duration_min >= 0, "incidents.gate_closure.duration_min >= 0")

    # Emergencia
    em = cfg.emergency
    _check(em.exit_width_factor > 0 and em.speed_factor > 0, "emergency: factores > 0")
    _check_tri(em.reaction_s, "emergency.reaction_s")
    _check(em.reference_min > 0, "emergency.reference_min > 0")
    if em.blocked_exit:
        _check(em.blocked_exit_zone in cfg.zones, "emergency.blocked_exit_zone no está en zones")
        _check(cfg.exits_per_zone >= 2, "bloquear una salida exige exits_per_zone >= 2")


# --------------------------------------------------------------------------
# API pública
# --------------------------------------------------------------------------


def _read_json(path: str | Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise ConfigError(f"{path}: el JSON raíz debe ser un objeto")
    return data


def config_from_dict(data: Mapping[str, Any]) -> Config:
    """Construye y valida una :class:`Config` a partir de un diccionario completo."""
    cfg = _build_dataclass(Config, data, "")
    cfg = dataclasses.replace(cfg, raw=copy.deepcopy(dict(data)))
    validate(cfg)
    return cfg


def load_config(
    path: str | Path = BASE_CONFIG_PATH, overrides: Mapping[str, Any] | None = None
) -> Config:
    """Carga ``path`` (normalmente ``configs/base.json``), fusiona ``overrides`` y valida.

    Raises:
        ConfigError: si hay claves desconocidas o ausentes, tipos erróneos o
            alguna regla semántica no se cumple.
    """
    return config_from_dict(deep_merge(_read_json(path), overrides))


@dataclass(frozen=True)
class Experiment:
    """Un fichero de ``configs/experiments``: una o varias configuraciones."""

    experiment: str
    """Código del experimento (X0..X7, S1)."""
    label: str
    question: str
    configs: tuple[Config, ...]
    """Una Config por escenario. Los ficheros con ``overrides`` dan una sola."""
    path: Path


_EXPERIMENT_KEYS = {"experiment", "label", "question", "overrides", "variants"}


def load_experiment(path: str | Path, base_path: str | Path = BASE_CONFIG_PATH) -> Experiment:
    """Carga un fichero de experimento (diff sobre ``base_path``).

    El fichero tiene ``experiment``, ``label``, ``question`` y exactamente uno de:

    * ``overrides``: dict que se fusiona sobre la base -> una Config;
    * ``variants``: lista de ``{"name", "overrides"}`` -> una Config por variante
      (``name`` de la variante pasa a ``Config.name``).

    Si un escenario no fija ``name``, se usa el nombre del fichero (sin ``.json``).
    """
    path = Path(path)
    data = _read_json(path)
    unknown = sorted(set(data) - _EXPERIMENT_KEYS)
    if unknown:
        raise ConfigError(f"{path.name}: claves desconocidas {unknown}")
    for key in ("experiment", "label", "question"):
        if not isinstance(data.get(key), str):
            raise ConfigError(f"{path.name}: falta '{key}' (str)")
    has_ov, has_var = "overrides" in data, "variants" in data
    if has_ov == has_var:
        raise ConfigError(f"{path.name}: debe tener 'overrides' o 'variants' (solo uno)")

    base = _read_json(base_path)
    scenarios: list[dict[str, Any]] = []
    if has_ov:
        ov = dict(data["overrides"])
        ov.setdefault("name", path.stem)
        scenarios.append(ov)
    else:
        if not isinstance(data["variants"], list) or not data["variants"]:
            raise ConfigError(f"{path.name}: 'variants' debe ser una lista no vacía")
        for i, var in enumerate(data["variants"]):
            if not isinstance(var, Mapping) or set(var) != {"name", "overrides"}:
                raise ConfigError(f"{path.name}: variants[{i}] debe ser {{name, overrides}}")
            scenarios.append({**var["overrides"], "name": var["name"]})

    configs = []
    for ov in scenarios:
        try:
            configs.append(config_from_dict(deep_merge(base, ov)))
        except ConfigError as exc:
            raise ConfigError(f"{path.name} [{ov.get('name')}]: {exc}") from exc
    return Experiment(
        experiment=data["experiment"],
        label=data["label"],
        question=data["question"],
        configs=tuple(configs),
        path=path,
    )
