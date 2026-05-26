"""Tests for Conversion B: Mach + Altitude → TAS, CAS.

Spec §10.2 values cross-checked:
  M=0.80 at FL350: TAS ≈ 461 kt, CAS ≈ 272 kt  (spec within 1 kt for TAS, ~1 kt for CAS)
  M=0.85 at FL350: TAS ≈ 490 kt, CAS ≈ 291 kt  (spec CAS 287.4 appears to have a typo)
  M=0.78 at FL400: TAS ≈ 447 kt, CAS ≈ 235 kt  (spec TAS 450.5 appears to have a typo)
All values derived independently from spec §5 formulas.
"""

import pytest

from airspeed import mach_to_tas_cas
from airspeed._result import MachResult
from airspeed.temperature import Isa, Sat


@pytest.mark.parametrize(
    "mach, alt_ft, expected_tas_kt, expected_cas_kt",
    [
        (0.80, 35_000, 461.13, 271.93),
        (0.85, 35_000, 489.96, 290.93),
        (0.78, 40_000, 447.38, 235.48),
    ],
)
def test_mach_to_tas_cas_isa(mach: float, alt_ft: float, expected_tas_kt: float, expected_cas_kt: float):
    result = mach_to_tas_cas(mach, alt_ft, Isa())
    assert isinstance(result, MachResult), f"Expected MachResult, got {result}"
    assert abs(result.tas_kt - expected_tas_kt) < 0.1, f"TAS: {result.tas_kt} vs {expected_tas_kt}"
    assert abs(result.cas_kt - expected_cas_kt) < 0.1, f"CAS: {result.cas_kt} vs {expected_cas_kt}"
    assert isinstance(result.temperature_source, Isa)


def test_mach_to_tas_cas_default_temperature_is_isa():
    result = mach_to_tas_cas(0.80, 35_000)
    assert isinstance(result, MachResult)
    assert isinstance(result.temperature_source, Isa)


def test_mach_to_tas_cas_sea_level():
    """At sea level ISA and low Mach, CAS ≈ TAS."""
    result = mach_to_tas_cas(0.20, 0, Isa())
    assert isinstance(result, MachResult)
    assert abs(result.cas_kt - result.tas_kt) < 1.0


def test_mach_to_tas_cas_with_sat():
    result = mach_to_tas_cas(0.80, 35_000, Sat(-44.34))
    assert isinstance(result, MachResult)
    assert isinstance(result.temperature_source, Sat)


def test_mach_to_tas_cas_isa_dt_zero():
    result = mach_to_tas_cas(0.80, 35_000, Isa())
    assert isinstance(result, MachResult)
    assert abs(result.dt_isa) < 1e-6


def test_mach_to_tas_cas_speed_of_sound_positive():
    result = mach_to_tas_cas(0.80, 35_000, Isa())
    assert isinstance(result, MachResult)
    assert result.speed_of_sound_kt > 0


def test_mach_to_tas_cas_fl350_speed_of_sound_matches_isa():
    """Speed of sound at FL350 ISA ≈ 296.54 m/s = 576.6 kt (spec §10.1, row 3)."""
    result = mach_to_tas_cas(0.80, 35_000, Isa())
    assert isinstance(result, MachResult)
    assert abs(result.speed_of_sound_kt - 576.6) < 0.2
