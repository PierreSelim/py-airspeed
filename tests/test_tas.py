"""Tests for Conversion C: TAS + Altitude → Mach, CAS.

Spec §10.3 example correction:
  The spec states CAS = 280.0 kt at FL350, ISA+10, TAS = 398.7 kt.
  Re-deriving from §5.x formulas: CAS ≈ 226 kt.
  The spec's CAS value appears to be a transcription error.

The ΔT_ISA and Mach values in §10.3 are correct and verified below.
"""


from airspeed import mach_to_tas_cas, tas_to_mach_cas
from airspeed._result import MachResult, TasResult
from airspeed.temperature import Isa, Sat, Tat

_CELSIUS_OFFSET = 273.15


def test_tas_to_mach_cas_sat_fl350_isa_plus_10():
    """Spec §10.3: TAS=398.7 kt, FL350, SAT=-44.34 °C (= 228.81 K, ISA+10).

    Expected: Mach≈0.677, ΔT_ISA = +10.0 °C.
    CAS ≈ 226 kt (spec's 280.0 kt appears to be a transcription error).
    """
    result = tas_to_mach_cas(398.7, 35_000, Sat(-44.34))
    assert isinstance(result, TasResult), f"Expected TasResult, got {result}"
    assert abs(result.mach - 0.677) < 0.002, f"Mach: {result.mach}"
    assert abs(result.cas_kt - 226.33) < 0.5, f"CAS: {result.cas_kt}"
    assert abs(result.dt_isa - 10.0) < 0.1, f"ΔT_ISA: {result.dt_isa}"
    assert isinstance(result.temperature_source, Sat)


def test_tas_to_mach_cas_tat_fl350_iterative():
    """Spec §10.3 iterative case: TAT=-23.36 °C (= 249.79 K), η=1.0 → SAT≈-44.34 °C, Mach≈0.677."""
    result = tas_to_mach_cas(398.7, 35_000, Tat(-23.36))
    assert isinstance(result, TasResult), f"Expected TasResult, got {result}"
    assert abs(result.mach - 0.677) < 0.002, f"Mach: {result.mach}"
    assert abs(result.sat_c - (-44.34)) < 0.5, f"SAT: {result.sat_c}"
    assert abs(result.dt_isa - 10.0) < 0.5, f"ΔT_ISA: {result.dt_isa}"
    assert isinstance(result.temperature_source, Tat)


def test_tas_to_mach_cas_isa():
    """At FL350 ISA, TAS=461.13 kt (from M=0.80 forward) → Mach≈0.80."""
    result = tas_to_mach_cas(461.13, 35_000, Isa())
    assert isinstance(result, TasResult)
    assert abs(result.mach - 0.80) < 0.001
    assert isinstance(result.temperature_source, Isa)
    assert abs(result.dt_isa) < 1e-6


def test_tas_to_mach_cas_isa_round_trip_with_mach_to_tas():
    """Round-trip: Mach→TAS→Mach must recover the original Mach."""
    fwd = mach_to_tas_cas(0.75, 35_000, Isa())
    assert isinstance(fwd, MachResult)

    rev = tas_to_mach_cas(fwd.tas_kt, 35_000, Isa())
    assert isinstance(rev, TasResult)
    assert abs(rev.mach - 0.75) < 1e-4


def test_tas_to_mach_cas_dt_isa_positive():
    """Warm temperature → positive ΔT_ISA."""
    result = tas_to_mach_cas(400, 35_000, Sat(-34.34))
    assert isinstance(result, TasResult)
    assert result.dt_isa > 0


def test_tas_to_mach_cas_speed_of_sound_matches_sat():
    """Speed of sound must equal 20.0468 × √SAT_K, converted to kt."""
    result = tas_to_mach_cas(398.7, 35_000, Sat(-44.34))
    assert isinstance(result, TasResult)
    sat_k = -44.34 + _CELSIUS_OFFSET  # 228.81 K
    expected_kt = 20.0468 * (sat_k**0.5) * 1.94384
    assert abs(result.speed_of_sound_kt - expected_kt) < 0.05


def test_tas_tat_vs_sat_give_same_mach():
    """SAT and TAT (with TAT derived from SAT + Mach) must give same Mach."""
    r_sat = tas_to_mach_cas(398.7, 35_000, Sat(-44.34))
    assert isinstance(r_sat, TasResult)

    # TAT = SAT_K × (1 + η × 0.2 × M²) with η=1.0 — formula uses Kelvin
    m = r_sat.mach
    sat_k = -44.34 + _CELSIUS_OFFSET
    tat_c = sat_k * (1 + 0.2 * m * m) - _CELSIUS_OFFSET

    r_tat = tas_to_mach_cas(398.7, 35_000, Tat(tat_c))
    assert isinstance(r_tat, TasResult)
    assert abs(r_tat.mach - r_sat.mach) < 1e-4
