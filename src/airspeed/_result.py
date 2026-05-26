from __future__ import annotations

from dataclasses import dataclass

from airspeed.temperature import TemperatureSource


@dataclass(frozen=True)
class AirConditions:
    sat_c: float
    speed_of_sound_kt: float
    pressure_mbar: float
    t_isa_c: float
    dt_isa: float  # SAT − T_ISA, positive = ISA+
    temperature_source: TemperatureSource


@dataclass(frozen=True)
class CasResult(AirConditions):
    mach: float
    tas_kt: float


@dataclass(frozen=True)
class MachResult(AirConditions):
    cas_kt: float
    tas_kt: float


@dataclass(frozen=True)
class TasResult(AirConditions):
    mach: float
    cas_kt: float


type AirspeedResult = CasResult | MachResult | TasResult
