// pyo3 0.22 emits spurious `unexpected_cfgs` warnings from create_exception! macro
// internals — suppress them until the crate is updated.
#![allow(unexpected_cfgs)]
// pyo3's #[pyfunction] expansion adds an internal .into() on the error type,
// which clippy flags as useless when the error is already PyErr.
#![allow(clippy::useless_conversion)]

use pyo3::prelude::*;
use pyo3::PyTypeInfo;

mod airspeed;
mod errors;
mod isa;
mod solver;
mod temperature;
mod types;

use errors::DomainError;
use temperature::TemperatureSource;
use types::{Feet, Kelvin, Knots, Mach, RecoveryFactor};

pyo3::create_exception!(_core, AirspeedException, pyo3::exceptions::PyException);
pyo3::create_exception!(_core, OutOfRangeException, AirspeedException);
pyo3::create_exception!(_core, SupersonicException, AirspeedException);
pyo3::create_exception!(_core, TatBelowSatException, AirspeedException);
pyo3::create_exception!(_core, SolverNoConvergenceException, AirspeedException);

#[pyclass(frozen, get_all)]
struct RawAirspeedResult {
    mach: Option<f64>,
    cas_kt: Option<f64>,
    tas_kt: Option<f64>,
    sat_k: f64,
    speed_of_sound_ms: f64,
    pressure_pa: f64,
    t_isa_k: f64,
    dt_isa: f64,
    temperature_provenance: u8,
}

impl From<DomainError> for PyErr {
    fn from(e: DomainError) -> Self {
        match e {
            DomainError::OutOfRange { field, unit, value } => {
                PyErr::new::<OutOfRangeException, _>((field, unit, value))
            }
            DomainError::Supersonic { mach } => PyErr::new::<SupersonicException, _>((mach,)),
            DomainError::TatBelowSat { tat, sat } => {
                PyErr::new::<TatBelowSatException, _>((tat, sat))
            }
            DomainError::SolverNoConvergence { iterations } => {
                PyErr::new::<SolverNoConvergenceException, _>((iterations as u64,))
            }
        }
    }
}

fn parse_temperature(kind: u8, temp_k: f64, eta: f64) -> Result<TemperatureSource, DomainError> {
    match kind {
        0 => Ok(TemperatureSource::Isa),
        1 => Ok(TemperatureSource::Sat(Kelvin::new(temp_k)?)),
        2 => Ok(TemperatureSource::Tat {
            tat: Kelvin::new(temp_k)?,
            eta: RecoveryFactor::new(eta)?,
        }),
        _ => Err(DomainError::OutOfRange {
            field: "temp_kind",
            unit: "—",
            value: kind as f64,
        }),
    }
}

fn to_raw(r: airspeed::AirspeedResult) -> RawAirspeedResult {
    RawAirspeedResult {
        mach: r.mach.map(|m| m.value()),
        cas_kt: r.cas.map(|c| c.value()),
        tas_kt: r.tas.map(|t| t.value()),
        sat_k: r.sat.value(),
        speed_of_sound_ms: r.speed_of_sound.value(),
        pressure_pa: r.pressure.value(),
        t_isa_k: r.t_isa.value(),
        dt_isa: r.dt_isa,
        temperature_provenance: r.temperature_provenance,
    }
}

#[pyfunction]
fn cas_to_mach_tas_raw(
    cas_kt: f64,
    alt_ft: f64,
    temp_kind: u8,
    temp_k: f64,
    eta: f64,
) -> PyResult<RawAirspeedResult> {
    let cas = Knots::new(cas_kt)?;
    let alt = Feet::new(alt_ft)?;
    let temp = parse_temperature(temp_kind, temp_k, eta)?;
    Ok(to_raw(airspeed::cas_to_mach_tas(cas, alt, temp)?))
}

#[pyfunction]
fn mach_to_tas_cas_raw(
    mach: f64,
    alt_ft: f64,
    temp_kind: u8,
    temp_k: f64,
    eta: f64,
) -> PyResult<RawAirspeedResult> {
    let m = Mach::new(mach)?;
    let alt = Feet::new(alt_ft)?;
    let temp = parse_temperature(temp_kind, temp_k, eta)?;
    Ok(to_raw(airspeed::mach_to_tas_cas(m, alt, temp)?))
}

#[pyfunction]
fn tas_to_mach_cas_raw(
    tas_kt: f64,
    alt_ft: f64,
    temp_kind: u8,
    temp_k: f64,
    eta: f64,
) -> PyResult<RawAirspeedResult> {
    let tas = Knots::new(tas_kt)?;
    let alt = Feet::new(alt_ft)?;
    let temp = parse_temperature(temp_kind, temp_k, eta)?;
    Ok(to_raw(airspeed::tas_to_mach_cas(tas, alt, temp)?))
}

#[pymodule]
fn _core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<RawAirspeedResult>()?;
    m.add(
        "AirspeedException",
        AirspeedException::type_object_bound(m.py()),
    )?;
    m.add(
        "OutOfRangeException",
        OutOfRangeException::type_object_bound(m.py()),
    )?;
    m.add(
        "SupersonicException",
        SupersonicException::type_object_bound(m.py()),
    )?;
    m.add(
        "TatBelowSatException",
        TatBelowSatException::type_object_bound(m.py()),
    )?;
    m.add(
        "SolverNoConvergenceException",
        SolverNoConvergenceException::type_object_bound(m.py()),
    )?;
    m.add_function(wrap_pyfunction!(cas_to_mach_tas_raw, m)?)?;
    m.add_function(wrap_pyfunction!(mach_to_tas_cas_raw, m)?)?;
    m.add_function(wrap_pyfunction!(tas_to_mach_cas_raw, m)?)?;
    Ok(())
}
