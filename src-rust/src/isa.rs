use crate::types::{Feet, Kelvin, Pascals};

/// ISA constants — ICAO Doc 7488
pub const T0: f64 = 288.15; // K, sea-level temperature
pub const P0: f64 = 101_325.0; // Pa, sea-level static pressure
pub const A0: f64 = 340.294; // m/s, sea-level speed of sound

const L: f64 = 0.0065; // K/m, tropospheric lapse rate
const G0: f64 = 9.806_65; // m/s²
const R: f64 = 287.052_87; // J/(kg·K)
const H_TROP: f64 = 11_000.0; // m, tropopause altitude
const T_STRAT: f64 = 216.65; // K
const P_TROP: f64 = 22_632.1; // Pa, pressure at tropopause

/// g₀ / (R × L)  ≈ 5.25588
const ISA_EXPONENT: f64 = G0 / (R * L);
/// g₀ / (R × T_strat)  ≈ 0.00015769
const STRAT_SCALE: f64 = G0 / (R * T_STRAT);

pub struct IsaState {
    pub pressure: Pascals,
    pub temperature: Kelvin,
}

pub fn isa_at_altitude(altitude: Feet) -> IsaState {
    let h_m = altitude.value() * 0.3048;

    if h_m <= H_TROP {
        let t = T0 - L * h_m;
        let p = P0 * (1.0 - L * h_m / T0).powf(ISA_EXPONENT);
        IsaState {
            // Both are within domain bounds for any valid altitude
            pressure: Pascals::new(p).expect("ISA pressure always positive"),
            temperature: Kelvin::new(t).expect("ISA temperature always in range"),
        }
    } else {
        let p = P_TROP * (-(STRAT_SCALE * (h_m - H_TROP))).exp();
        IsaState {
            pressure: Pascals::new(p).expect("ISA pressure always positive"),
            temperature: Kelvin::new(T_STRAT).expect("stratosphere temperature in range"),
        }
    }
}
