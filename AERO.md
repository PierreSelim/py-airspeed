# Aeronautical physics — equations and references

This document describes the physical models and equations implemented in the Rust core (`src-rust/`).

---

## ISA Standard Atmosphere

### Constants

| Symbol | Value | Description |
|--------|-------|-------------|
| T₀ | 288.15 K (15 °C) | Sea-level temperature |
| P₀ | 101 325 Pa | Sea-level static pressure |
| a₀ | 340.294 m/s | Sea-level speed of sound |
| L | 0.0065 °C/m | Tropospheric temperature lapse rate |
| g₀ | 9.80665 m/s² | Standard gravity |
| R | 287.05287 J/(kg·K) | Specific gas constant for dry air |
| γ | 1.4 | Ratio of specific heats |
| h_trop | 11 000 m (36 089 ft) | Tropopause altitude |
| T_strat | 216.65 K (−56.5 °C) | Stratospheric temperature (isothermal) |
| P_trop | 22 632.1 Pa | Static pressure at the tropopause |

Source: ICAO Doc 7488 [1].

### Altitude model

Altitude input is in feet; converted internally to metres as `h_m = h_ft × 0.3048`.

**Troposphere** (0 ≤ h ≤ 11 000 m):

```
T(h) = T₀ − L·h

P(h) = P₀ · (T(h) / T₀)^(g₀ / (R·L))       exponent = 5.2559
```

**Stratosphere** (11 000 m < h ≤ 20 000 m = 65 617 ft):

```
T = 216.65 K   (constant)

P(h) = P_trop · exp(−g₀ · (h − 11 000) / (R · T_strat))
```

---

## Speed of sound

```
a = 20.0468 · √T     [m/s,  T in K]
```

Derived from `a = √(γ·R·T)` with γ = 1.4 and R = 287.05287 J/(kg·K).

---

## Impact pressure

The impact (differential) pressure q_c is defined by the **isentropic subsonic Pitot formula** (valid for M < 1):

```
q_c = P · ((1 + 0.2·M²)^3.5 − 1)
```

The exponent 3.5 = γ/(γ−1).

---

## Calibrated Airspeed (CAS)

CAS is defined as the equivalent airspeed that produces the same impact pressure q_c in ISA sea-level conditions:

```
q_c = P₀ · ((1 + 0.2·(V_CAS / a₀)²)^3.5 − 1)
```

Inverted to obtain CAS from q_c:

```
V_CAS = a₀ · √(5 · ((q_c / P₀ + 1)^(2/7) − 1))     [m/s, convert to kt]
```

---

## The three conversions

### Conversion A — CAS + altitude → Mach, TAS

1. Compute P and T_ISA at altitude from the ISA model.
2. Resolve T_SAT from the temperature source (see [Temperature sources](#temperature-sources)).
3. Compute q_c from CAS:   `q_c = P₀ · ((1 + 0.2·(V_CAS/a₀)²)^3.5 − 1)`
4. Compute Mach:            `M = √(5 · ((q_c/P + 1)^(2/7) − 1))`
5. Compute speed of sound:  `a = 20.0468 · √T_SAT`
6. Compute TAS:             `V_TAS = M · a`

Mach is pressure-only and independent of temperature; temperature is used only for TAS.

### Conversion B — Mach + altitude → TAS, CAS

1. Compute P and T_ISA at altitude from the ISA model.
2. Resolve T_SAT from the temperature source.
3. Compute q_c from Mach:   `q_c = P · ((1 + 0.2·M²)^3.5 − 1)`
4. Compute CAS:             `V_CAS = a₀ · √(5 · ((q_c/P₀ + 1)^(2/7) − 1))`
5. Compute speed of sound:  `a = 20.0468 · √T_SAT`
6. Compute TAS:             `V_TAS = M · a`

### Conversion C — TAS + altitude → Mach, CAS

1. Compute P and T_ISA at altitude from the ISA model.
2. Resolve T_SAT (see [Newton-Raphson solver](#newton-raphson-solver-tas--tat-case) when TAT is the source).
3. Compute speed of sound:  `a = 20.0468 · √T_SAT`
4. Compute Mach:            `M = V_TAS / a`
5. Compute q_c and CAS as in Conversion B steps 3–4.

---

## Temperature sources

### ISA

`T_SAT = T_ISA(h)` — standard atmosphere temperature at altitude.

### Direct SAT

`T_SAT` is provided directly by the operator.

### TAT probe

A TAT (Total Air Temperature) probe measures the adiabatic stagnation temperature. The relationship between TAT and SAT is:

```
T_TAT = T_SAT · (1 + η · 0.2 · M²)
```

where η ∈ (0, 1] is the **recovery factor** (1.0 for an ideal adiabatic probe, < 1 for partial recovery).

Inverted:

```
T_SAT = T_TAT / (1 + η · 0.2 · M²)
```

This inversion is direct when M is already known (Conversions A and B). For Conversion C, both M and T_SAT are unknown — see below.

---

## Newton-Raphson solver (TAS + TAT case)

When both TAS and TAT are given, M and T_SAT are coupled. The solver finds T_SAT satisfying:

```
f(T_SAT) = T_SAT · (1 + η · 0.2 · M(T_SAT)²) − T_TAT = 0

where  M(T_SAT) = V_TAS / (20.0468 · √T_SAT)
```

**Initial guess** (assumes M ≈ 0.5):

```
T_SAT⁰ = T_TAT / (1 + η · 0.2 · 0.25)
```

**Each iteration:**

```
aₙ         = 20.0468 · √T_SATₙ
Mₙ         = V_TAS / aₙ
fₙ         = T_SATₙ · (1 + η · 0.2 · Mₙ²) − T_TAT
f′ₙ        = 1 + η · 0.1 · Mₙ²
T_SATₙ₊₁  = T_SATₙ − fₙ / f′ₙ
```

**Convergence criterion:** `|T_SATₙ₊₁ − T_SATₙ| < 10⁻⁶ K`, up to 50 iterations.  
If M ≥ 1 is encountered during iteration, a `SupersonicError` is returned immediately.  
If convergence is not reached within 50 iterations, a `SolverNoConvergenceError` is returned.

---

## References

[1] International Civil Aviation Organization. *Manual of the ICAO Standard Atmosphere*, 3rd ed. ICAO Doc 7488, 1993.

[2] Gracey, W. *Measurement of Aircraft Speed and Altitude*. NASA Reference Publication 1046, 1980.

[3] ESDU. *Equations for calculation of International Standard Atmosphere*. ESDU Data Item 77022, amended 1986.
