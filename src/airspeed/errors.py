from __future__ import annotations

from dataclasses import dataclass


class AirspeedError:
    """Sealed base class for all airspeed computation errors.
    Never instantiated directly — use the concrete subclasses.
    """


@dataclass(frozen=True)
class OutOfRangeError(AirspeedError):
    field: str
    unit: str
    value: float

    def __str__(self) -> str:
        return f"{self.field} = {self.value:.3g} {self.unit} is out of valid range"


@dataclass(frozen=True)
class SupersonicError(AirspeedError):
    mach: float

    def __str__(self) -> str:
        return f"Supersonic Mach {self.mach:.4f} — subsonic formulas invalid"


@dataclass(frozen=True)
class TatBelowSatError(AirspeedError):
    tat_c: float
    sat_c: float

    def __str__(self) -> str:
        return f"TAT {self.tat_c:.2f} °C < SAT {self.sat_c:.2f} °C — sensor inconsistency"


@dataclass(frozen=True)
class SolverNoConvergenceError(AirspeedError):
    iterations: int

    def __str__(self) -> str:
        return f"Newton-Raphson did not converge after {self.iterations} iterations"


type AnyAirspeedError = OutOfRangeError | SupersonicError | TatBelowSatError | SolverNoConvergenceError
