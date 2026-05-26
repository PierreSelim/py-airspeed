use crate::errors::DomainError;

const MAX_ITER: usize = 50;
const EPSILON: f64 = 1e-6; // K, convergence criterion
const SPEED_OF_SOUND_COEFF: f64 = 20.0468; // a = COEFF × √SAT  [m/s, K]

/// Newton-Raphson solver for the implicit SAT equation when TAS and TAT are known.
///
/// Solves: f(SAT) = SAT × (1 + η × 0.2 × M²) − TAT = 0
/// where   M = TAS_ms / (20.0468 × √SAT)
///
/// Derivative: f'(SAT) = 1 + η × 0.1 × M²
pub fn solve_sat_from_tas_tat(tas_ms: f64, tat_k: f64, eta: f64) -> Result<f64, DomainError> {
    // Initial guess: assume M ≈ 0.5  →  M² = 0.25
    let mut sat = tat_k / (1.0 + eta * 0.2 * 0.25);

    for _ in 0..MAX_ITER {
        let a = SPEED_OF_SOUND_COEFF * sat.sqrt();
        let m = tas_ms / a;

        if m >= 1.0 {
            return Err(DomainError::Supersonic { mach: m });
        }

        let m_sq = m * m;
        let f = sat * (1.0 + eta * 0.2 * m_sq) - tat_k;
        let f_prime = 1.0 + eta * 0.1 * m_sq;

        let sat_new = sat - f / f_prime;

        if (sat_new - sat).abs() < EPSILON {
            return Ok(sat_new);
        }

        sat = sat_new;
    }

    Err(DomainError::SolverNoConvergence {
        iterations: MAX_ITER,
    })
}
