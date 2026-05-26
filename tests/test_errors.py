"""Tests for error values, error __str__, and Rust error propagation.

Error paths in __init__.py are only reached when the Rust extension raises
an exception.  The tests below trigger those paths using:
  - Out-of-range float values that Rust rejects
  - Physical extremes that yield M ≥ 1 (SupersonicError from Rust)
"""

from airspeed import cas_to_mach_tas, mach_to_tas_cas, tas_to_mach_cas
from airspeed.errors import (
    AirspeedError,
    OutOfRangeError,
    SolverNoConvergenceError,
    SupersonicError,
    TatBelowSatError,
)
from airspeed.temperature import Isa, Sat


class TestErrorStrings:
    def test_out_of_range_str(self):
        e = OutOfRangeError("Knots", "kt", 700.0)
        assert "700" in str(e)
        assert "kt" in str(e)

    def test_supersonic_str(self):
        e = SupersonicError(mach=1.23456)
        s = str(e)
        assert "1.2346" in s
        assert "supersonic" in s.lower() or "Supersonic" in s

    def test_tat_below_sat_str(self):
        e = TatBelowSatError(tat_c=-73.15, sat_c=-53.15)
        s = str(e)
        assert "-73.15" in s
        assert "-53.15" in s
        assert "°C" in s

    def test_solver_no_convergence_str(self):
        e = SolverNoConvergenceError(iterations=50)
        assert "50" in str(e)


class TestRustErrorPropagation:
    """Exercise the except branches in __init__.py by passing out-of-range values.

    These bypass any Python-level guard and let Rust raise the exception directly.
    """

    def test_cas_out_of_range_propagates(self):
        result = cas_to_mach_tas(700.0, 35_000, Isa())
        assert isinstance(result, AirspeedError)
        assert isinstance(result, OutOfRangeError)
        assert result.field == "Knots"

    def test_mach_out_of_range_propagates(self):
        result = mach_to_tas_cas(1.5, 35_000, Isa())
        assert isinstance(result, AirspeedError)
        assert isinstance(result, OutOfRangeError)

    def test_tas_out_of_range_propagates(self):
        result = tas_to_mach_cas(700.0, 35_000, Sat(-44.34))
        assert isinstance(result, AirspeedError)
        assert isinstance(result, OutOfRangeError)


class TestSupersonicError:
    """Physical inputs that result in Mach ≥ 1 trigger SupersonicError."""

    def test_cas_supersonic_at_extreme_altitude(self):
        """CAS near limit (660 kt) at max altitude (65 617 ft) → M >> 1."""
        result = cas_to_mach_tas(660.0, 65_617.0, Isa())
        assert isinstance(result, SupersonicError)
        assert result.mach > 1.0

    def test_tas_supersonic_at_cold_stratosphere(self):
        """TAS near limit (659 kt) at 40 000 ft (stratosphere, T=216.65 K).
        Speed of sound at 40 000 ft ≈ 295 m/s ≈ 573 kt → M ≈ 1.15 > 1.
        """
        result = tas_to_mach_cas(659.0, 40_000.0, Isa())
        assert isinstance(result, SupersonicError)
        assert result.mach > 1.0


class TestAirspeedErrorBaseClass:
    def test_isinstance_hierarchy(self):
        e = OutOfRangeError("x", "u", 1.0)
        assert isinstance(e, AirspeedError)
        assert isinstance(e, OutOfRangeError)

    def test_supersonic_is_airspeed_error(self):
        e = SupersonicError(mach=1.1)
        assert isinstance(e, AirspeedError)
