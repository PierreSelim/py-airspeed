from __future__ import annotations

from airspeed import _core
from airspeed._result import AirConditions, AirspeedResult, CasResult, MachResult, TasResult
from airspeed.errors import (
    AirspeedError,
    OutOfRangeError,
    SolverNoConvergenceError,
    SupersonicError,
    TatBelowSatError,
)
from airspeed.temperature import Isa, Sat, Tat, TemperatureSource

_MS_TO_KT = 1.94384
_PA_TO_MBAR = 1.0 / 100.0
_CELSIUS_OFFSET = 273.15

__all__ = [
    "cas_to_mach_tas",
    "mach_to_tas_cas",
    "tas_to_mach_cas",
    "AirConditions",
    "AirspeedResult",
    "CasResult",
    "MachResult",
    "TasResult",
    "AirspeedError",
    "OutOfRangeError",
    "SupersonicError",
    "TatBelowSatError",
    "SolverNoConvergenceError",
    "Isa",
    "Sat",
    "Tat",
    "TemperatureSource",
]


def _unpack_temperature(temp: TemperatureSource) -> tuple[int, float, float]:
    match temp:
        case Isa():
            return (0, 0.0, 1.0)
        case Sat(temperature_c=t):
            return (1, t + _CELSIUS_OFFSET, 1.0)
        case Tat(temperature_c=t, eta=e):
            return (2, t + _CELSIUS_OFFSET, e)


def _convert_exception(exc: Exception) -> AirspeedError:
    if isinstance(exc, _core.OutOfRangeException):
        field, unit, value = exc.args
        return OutOfRangeError(field=str(field), unit=str(unit), value=float(value))
    if isinstance(exc, _core.SupersonicException):
        (mach,) = exc.args
        return SupersonicError(mach=float(mach))
    if isinstance(exc, _core.TatBelowSatException):
        tat_k, sat_k = exc.args
        return TatBelowSatError(tat_c=float(tat_k) - _CELSIUS_OFFSET, sat_c=float(sat_k) - _CELSIUS_OFFSET)
    if isinstance(exc, _core.SolverNoConvergenceException):
        (iterations,) = exc.args
        return SolverNoConvergenceError(iterations=int(iterations))
    return OutOfRangeError(field="unknown", unit="", value=0.0)


def _conditions_kwargs(raw: _core.RawAirspeedResult, temperature: TemperatureSource) -> dict:
    return {
        "sat_c": raw.sat_k - _CELSIUS_OFFSET,
        "speed_of_sound_kt": raw.speed_of_sound_ms * _MS_TO_KT,
        "pressure_mbar": raw.pressure_pa * _PA_TO_MBAR,
        "t_isa_c": raw.t_isa_k - _CELSIUS_OFFSET,
        "dt_isa": raw.dt_isa,
        "temperature_source": temperature,
    }


def cas_to_mach_tas(
    cas_kt: float,
    altitude_ft: float,
    temperature: TemperatureSource = Isa(),
) -> CasResult | AirspeedError:
    kind, temp_k, eta = _unpack_temperature(temperature)
    try:
        raw = _core.cas_to_mach_tas_raw(cas_kt, altitude_ft, kind, temp_k, eta)
        return CasResult(**_conditions_kwargs(raw, temperature), mach=raw.mach, tas_kt=raw.tas_kt)
    except _core.AirspeedException as exc:
        return _convert_exception(exc)


def mach_to_tas_cas(
    mach: float,
    altitude_ft: float,
    temperature: TemperatureSource = Isa(),
) -> MachResult | AirspeedError:
    kind, temp_k, eta = _unpack_temperature(temperature)
    try:
        raw = _core.mach_to_tas_cas_raw(mach, altitude_ft, kind, temp_k, eta)
        return MachResult(**_conditions_kwargs(raw, temperature), cas_kt=raw.cas_kt, tas_kt=raw.tas_kt)
    except _core.AirspeedException as exc:
        return _convert_exception(exc)


def tas_to_mach_cas(
    tas_kt: float,
    altitude_ft: float,
    temperature: TemperatureSource,
) -> TasResult | AirspeedError:
    kind, temp_k, eta = _unpack_temperature(temperature)
    try:
        raw = _core.tas_to_mach_cas_raw(tas_kt, altitude_ft, kind, temp_k, eta)
        return TasResult(**_conditions_kwargs(raw, temperature), mach=raw.mach, cas_kt=raw.cas_kt)
    except _core.AirspeedException as exc:
        return _convert_exception(exc)
