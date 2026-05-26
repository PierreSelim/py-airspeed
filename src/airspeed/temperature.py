from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Isa:
    """Derive temperature from the ISA model at altitude. No sensor required."""


@dataclass(frozen=True)
class Sat:
    """Direct static air temperature measurement in °C."""

    temperature_c: float


@dataclass(frozen=True)
class Tat:
    """Total air temperature in °C + probe recovery factor η (default: 1.0 adiabatic)."""

    temperature_c: float
    eta: float = 1.0


type TemperatureSource = Isa | Sat | Tat
