use crate::types::{Kelvin, RecoveryFactor};

#[derive(Debug, Clone, Copy)]
pub enum TemperatureSource {
    Isa,
    Sat(Kelvin),
    Tat { tat: Kelvin, eta: RecoveryFactor },
}

impl TemperatureSource {
    #[allow(dead_code)] // convenience constructor — public API, used in tests and examples
    pub fn tat_adiabatic(tat: Kelvin) -> Self {
        Self::Tat {
            tat,
            eta: RecoveryFactor::new(1.0).expect("1.0 is always a valid recovery factor"),
        }
    }

    /// Resolve to SAT given a known Mach number (not used in the iterative case).
    pub fn resolve_sat(self, t_isa: Kelvin, mach: f64) -> Kelvin {
        match self {
            TemperatureSource::Isa => t_isa,
            TemperatureSource::Sat(t) => t,
            TemperatureSource::Tat { tat, eta } => {
                // SAT = TAT / (1 + η × 0.2 × M²)  — denominator ≥ 1, so SAT ≤ TAT always
                let sat = tat.value() / (1.0 + eta.value() * 0.2 * mach * mach);
                Kelvin::new(sat).expect("SAT derived from valid TAT is always in range")
            }
        }
    }

    /// Provenance code: 0 = ISA, 1 = measured SAT, 2 = derived from TAT
    pub fn provenance_code(self) -> u8 {
        match self {
            TemperatureSource::Isa => 0,
            TemperatureSource::Sat(_) => 1,
            TemperatureSource::Tat { .. } => 2,
        }
    }
}
