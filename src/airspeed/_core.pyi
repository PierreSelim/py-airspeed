"""Type stubs for the Rust extension module airspeed._core.

All three raw functions raise AirspeedException (or a subclass) on error.
They never return error values — the Python wrapper in __init__.py converts
exceptions to the AirspeedError value hierarchy.

Temperature source encoding:
    temp_kind=0  →  ISA (temp_k and eta ignored)
    temp_kind=1  →  SAT  (temp_k = SAT in K, eta ignored)
    temp_kind=2  →  TAT  (temp_k = TAT in K, eta = recovery factor)
"""

from __future__ import annotations

class AirspeedException(Exception): ...
class OutOfRangeException(AirspeedException): ...
class SupersonicException(AirspeedException): ...
class TatBelowSatException(AirspeedException): ...
class SolverNoConvergenceException(AirspeedException): ...

class RawAirspeedResult:
    mach: float | None
    cas_kt: float | None
    tas_kt: float | None
    sat_k: float
    speed_of_sound_ms: float
    pressure_pa: float
    t_isa_k: float
    dt_isa: float
    temperature_provenance: int  # 0=ISA  1=MeasuredSat  2=DerivedFromTat

def cas_to_mach_tas_raw(
    cas_kt: float, alt_ft: float, temp_kind: int, temp_k: float, eta: float
) -> RawAirspeedResult: ...
def mach_to_tas_cas_raw(
    mach: float, alt_ft: float, temp_kind: int, temp_k: float, eta: float
) -> RawAirspeedResult: ...
def tas_to_mach_cas_raw(
    tas_kt: float, alt_ft: float, temp_kind: int, temp_k: float, eta: float
) -> RawAirspeedResult: ...
