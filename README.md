# airspeed

Bidirectional CAS / Mach / TAS conversions with ISA atmosphere and temperature sensors.

- **Rust core** (PyO3 / maturin) — validated inputs, no silent numeric failures
- **Errors as values** — nothing is raised; success and failure are distinct types
- **Three temperature sources** — ISA model, direct SAT, or TAT probe with Newton-Raphson solver

See [AERO.md](AERO.md) for the implemented equations and references.

---

## Prerequisites

- Python ≥ 3.12
- Rust toolchain — install via [rustup](https://rustup.rs)
- [uv](https://docs.astral.sh/uv/) for Python dependency management

---

## Build

```bash
# Create virtual environment and install dev dependencies
uv sync --group dev

# Compile the Rust extension and install in editable mode
uv run maturin develop --release

# Run tests with coverage
uv run pytest tests/ --cov=src --cov-report=term-missing

# Lint and type-check
uv run ruff check src/ tests/
uv run pyright src/
```

---

## Examples

### CAS + altitude → Mach, TAS

```python
from airspeed import cas_to_mach_tas, Isa
from airspeed import CasResult, AirspeedError

match cas_to_mach_tas(250.0, 35_000.0, Isa()):
    case CasResult() as r:
        print(f"Mach {r.mach:.3f}  TAS {r.tas_kt:.1f} kt  ΔT {r.dt_isa:+.1f} °C")
    case AirspeedError() as e:
        print(f"Error: {e}")
```

### Mach + altitude → TAS, CAS

```python
from airspeed import mach_to_tas_cas, Sat
from airspeed import MachResult, AirspeedError

match mach_to_tas_cas(0.80, 35_000.0, Sat(-44.34)):
    case MachResult() as r:
        print(f"TAS {r.tas_kt:.1f} kt  CAS {r.cas_kt:.1f} kt  SAT {r.sat_c:.2f} °C")
    case AirspeedError() as e:
        print(f"Error: {e}")
```

### TAS + altitude → Mach, CAS  (TAT probe, iterative)

```python
from airspeed import tas_to_mach_cas, Tat
from airspeed import TasResult, AirspeedError

match tas_to_mach_cas(398.7, 35_000.0, Tat(-23.36, eta=1.0)):
    case TasResult() as r:
        print(f"Mach {r.mach:.3f}  CAS {r.cas_kt:.1f} kt  SAT {r.sat_c:.2f} °C")
    case AirspeedError() as e:
        print(f"Error: {e}")
```

---

## API

### Temperature source

```python
Isa()                                      # ISA standard atmosphere at altitude (default)
Sat(temperature_c: float)                  # direct static air temperature in °C
Tat(temperature_c: float, eta: float=1.0)  # TAT probe reading in °C + recovery factor η
```

`tas_to_mach_cas` has no default temperature — TAS→Mach always requires a temperature source.

### Result types

All fields are plain `float`. The three types share `AirConditions` as a base:

| Field | Description |
|-------|-------------|
| `sat_c` | static air temperature, °C |
| `speed_of_sound_kt` | kt |
| `pressure_mbar` | mbar (= hPa) |
| `t_isa_c` | ISA temperature at altitude, °C |
| `dt_isa` | SAT − T_ISA, positive = ISA+ |
| `temperature_source` | the `Isa`, `Sat`, or `Tat` passed in |

| Type | Computed fields |
|------|----------------|
| `CasResult` | `mach`, `tas_kt` |
| `MachResult` | `cas_kt`, `tas_kt` |
| `TasResult` | `mach`, `cas_kt` |

`type AirspeedResult = CasResult | MachResult | TasResult` is exported as a convenience alias.

### Errors

| Class | Fields |
|-------|--------|
| `OutOfRangeError` | `field: str, unit: str, value: float` |
| `SupersonicError` | `mach: float` |
| `TatBelowSatError` | `tat_c: float, sat_c: float` |
| `SolverNoConvergenceError` | `iterations: int` |

All inherit from `AirspeedError`.

### Valid input ranges

| Input | Range |
|-------|-------|
| CAS, TAS | (0, 661) kt |
| Mach | [0, 1) |
| Altitude | [0, 65 617] ft |
| Recovery factor η | (0, 1] |

---

## License

MIT — see [LICENSE](LICENSE).
