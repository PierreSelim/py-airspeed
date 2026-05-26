"""Tests for Conversion A: CAS + Altitude → Mach, TAS.

Note: Spec §10.1 validation table has incorrect Mach values.
The TAS values are roughly correct; Mach values were independently re-derived
from the spec's §5.x formulas.  Expected values below were obtained by running
the implementation and cross-checking the round-trip Mach→CAS identity.
"""

import pytest

from airspeed import cas_to_mach_tas, mach_to_tas_cas
from airspeed._result import CasResult, MachResult
from airspeed.temperature import Isa, Sat, Tat


@pytest.mark.parametrize(
    "cas_kt, alt_ft, expected_mach, expected_tas_kt",
    [
        (100, 0, 0.1512, 100.0),
        (250, 10_000, 0.4523, 288.7),
        (250, 35_000, 0.7412, 427.2),
        (300, 35_000, 0.8736, 503.5),
    ],
)
def test_cas_to_mach_tas_isa(cas_kt: float, alt_ft: float, expected_mach: float, expected_tas_kt: float):
    result = cas_to_mach_tas(cas_kt, alt_ft, Isa())
    assert isinstance(result, CasResult), f"Expected CasResult, got {result}"
    assert abs(result.mach - expected_mach) < 0.001, f"Mach: {result.mach} vs {expected_mach}"
    assert abs(result.tas_kt - expected_tas_kt) < 1.0, f"TAS: {result.tas_kt} vs {expected_tas_kt}"
    assert isinstance(result.temperature_source, Isa)


def test_cas_to_mach_tas_default_temperature_is_isa():
    result = cas_to_mach_tas(250, 35_000)
    assert isinstance(result, CasResult)
    assert isinstance(result.temperature_source, Isa)


def test_cas_to_mach_tas_with_sat():
    result = cas_to_mach_tas(250, 35_000, Sat(-44.34))
    assert isinstance(result, CasResult)
    assert isinstance(result.temperature_source, Sat)
    assert abs(result.sat_c - (-44.34)) < 0.01


def test_cas_to_mach_tas_with_tat():
    result = cas_to_mach_tas(280, 35_000, Tat(-23.36))
    assert isinstance(result, CasResult)
    assert isinstance(result.temperature_source, Tat)


def test_cas_to_mach_tas_sea_level_isa():
    """At sea level ISA, CAS = TAS."""
    result = cas_to_mach_tas(100, 0, Isa())
    assert isinstance(result, CasResult)
    assert abs(result.tas_kt - 100.0) < 0.5
    assert abs(result.dt_isa) < 0.01


def test_cas_to_mach_tas_pressure_at_sea_level():
    result = cas_to_mach_tas(100, 0, Isa())
    assert isinstance(result, CasResult)
    assert abs(result.pressure_mbar - 1013.25) < 0.01


def test_cas_to_mach_tas_isa_t_deviation():
    """For ISA atmosphere, ΔT_ISA must be zero."""
    result = cas_to_mach_tas(250, 35_000, Isa())
    assert isinstance(result, CasResult)
    assert abs(result.dt_isa) < 1e-6


def test_cas_to_mach_tas_round_trip():
    """CAS→Mach then Mach→CAS must recover the original CAS."""
    r1 = cas_to_mach_tas(280, 35_000, Isa())
    assert isinstance(r1, CasResult)
    r2 = mach_to_tas_cas(r1.mach, 35_000, Isa())
    assert isinstance(r2, MachResult)
    assert abs(r2.cas_kt - 280.0) < 0.01
