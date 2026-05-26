#![allow(dead_code)] // TatBelowSat kept for spec completeness — unreachable with valid inputs
use thiserror::Error;

#[derive(Debug, Clone, PartialEq, Error)]
pub enum DomainError {
    #[error("{field} = {value:.3} {unit} is out of valid range")]
    OutOfRange {
        field: &'static str,
        unit: &'static str,
        value: f64,
    },

    #[error("Supersonic Mach {mach:.4} computed — subsonic formulas invalid")]
    Supersonic { mach: f64 },

    #[error("TAT {tat:.2} K < SAT {sat:.2} K — sensor inconsistency")]
    TatBelowSat { tat: f64, sat: f64 },

    #[error("Newton-Raphson solver did not converge after {iterations} iterations")]
    SolverNoConvergence { iterations: usize },
}
