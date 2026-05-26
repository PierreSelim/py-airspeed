use crate::errors::DomainError;
use crate::isa::{isa_at_altitude, A0, P0};
use crate::solver::solve_sat_from_tas_tat;
use crate::temperature::TemperatureSource;
use crate::types::{Feet, Kelvin, Knots, Mach, MetersPerSec, Pascals};

const KT_TO_MS: f64 = 0.514444;
const MS_TO_KT: f64 = 1.943844;
const SPEED_OF_SOUND_COEFF: f64 = 20.0468; // a = COEFF × √SAT  [m/s, K]

pub struct AirspeedResult {
    pub mach: Option<Mach>,
    pub cas: Option<Knots>,
    pub tas: Option<Knots>,
    pub sat: Kelvin,
    pub speed_of_sound: MetersPerSec,
    pub pressure: Pascals,
    pub t_isa: Kelvin,
    pub dt_isa: f64,
    pub temperature_provenance: u8,
}

fn qc_from_cas(cas_kt: f64) -> f64 {
    let cas_ms = cas_kt * KT_TO_MS;
    let mu0 = cas_ms / A0;
    P0 * ((1.0 + 0.2 * mu0 * mu0).powf(3.5) - 1.0)
}

fn qc_from_mach(mach: f64, pressure_pa: f64) -> f64 {
    pressure_pa * ((1.0 + 0.2 * mach * mach).powf(3.5) - 1.0)
}

fn mach_from_qc_p(qc: f64, p: f64) -> f64 {
    (5.0 * ((qc / p + 1.0).powf(2.0 / 7.0) - 1.0)).sqrt()
}

fn cas_kt_from_qc(qc: f64) -> f64 {
    A0 * (5.0 * ((qc / P0 + 1.0).powf(2.0 / 7.0) - 1.0)).sqrt() * MS_TO_KT
}

/// Conversion A: CAS + Altitude → Mach, TAS
/// Temperature is optional (default: ISA); used only for TAS computation.
pub fn cas_to_mach_tas(
    cas: Knots,
    altitude: Feet,
    temperature: TemperatureSource,
) -> Result<AirspeedResult, DomainError> {
    let isa = isa_at_altitude(altitude);
    let qc = qc_from_cas(cas.value());
    let mach = mach_from_qc_p(qc, isa.pressure.value());

    if mach >= 1.0 {
        return Err(DomainError::Supersonic { mach });
    }

    let mach_typed = Mach::new(mach)?;
    let prov = temperature.provenance_code();
    let sat = temperature.resolve_sat(isa.temperature, mach);
    let a = SPEED_OF_SOUND_COEFF * sat.value().sqrt();
    let tas_kt = mach * a * MS_TO_KT;
    let tas_typed = Knots::new(tas_kt)?;

    Ok(AirspeedResult {
        mach: Some(mach_typed),
        cas: None,
        tas: Some(tas_typed),
        sat,
        speed_of_sound: MetersPerSec::new(a)?,
        pressure: isa.pressure,
        t_isa: isa.temperature,
        dt_isa: sat.value() - isa.temperature.value(),
        temperature_provenance: prov,
    })
}

/// Conversion B: Mach + Altitude → TAS, CAS
/// Temperature is optional (default: ISA); used only for TAS computation.
pub fn mach_to_tas_cas(
    mach: Mach,
    altitude: Feet,
    temperature: TemperatureSource,
) -> Result<AirspeedResult, DomainError> {
    let isa = isa_at_altitude(altitude);
    let qc = qc_from_mach(mach.value(), isa.pressure.value());
    let cas_kt = cas_kt_from_qc(qc);
    let cas_typed = Knots::new(cas_kt)?;

    let prov = temperature.provenance_code();
    let sat = temperature.resolve_sat(isa.temperature, mach.value());
    let a = SPEED_OF_SOUND_COEFF * sat.value().sqrt();
    let tas_kt = mach.value() * a * MS_TO_KT;
    let tas_typed = Knots::new(tas_kt)?;

    Ok(AirspeedResult {
        mach: None,
        cas: Some(cas_typed),
        tas: Some(tas_typed),
        sat,
        speed_of_sound: MetersPerSec::new(a)?,
        pressure: isa.pressure,
        t_isa: isa.temperature,
        dt_isa: sat.value() - isa.temperature.value(),
        temperature_provenance: prov,
    })
}

/// Conversion C: TAS + Altitude → Mach, CAS
/// Temperature is always required.
pub fn tas_to_mach_cas(
    tas: Knots,
    altitude: Feet,
    temperature: TemperatureSource,
) -> Result<AirspeedResult, DomainError> {
    let isa = isa_at_altitude(altitude);
    let prov = temperature.provenance_code();
    let tas_ms = tas.value() * KT_TO_MS;

    let sat = match temperature {
        TemperatureSource::Isa => isa.temperature,
        TemperatureSource::Sat(t) => t,
        TemperatureSource::Tat { tat, eta } => {
            let sat_val = solve_sat_from_tas_tat(tas_ms, tat.value(), eta.value())?;
            Kelvin::new(sat_val)?
        }
    };

    let a = SPEED_OF_SOUND_COEFF * sat.value().sqrt();
    let mach = tas_ms / a;

    if mach >= 1.0 {
        return Err(DomainError::Supersonic { mach });
    }

    let mach_typed = Mach::new(mach)?;
    let qc = qc_from_mach(mach, isa.pressure.value());
    let cas_kt = cas_kt_from_qc(qc);
    let cas_typed = Knots::new(cas_kt)?;

    Ok(AirspeedResult {
        mach: Some(mach_typed),
        cas: Some(cas_typed),
        tas: None,
        sat,
        speed_of_sound: MetersPerSec::new(a)?,
        pressure: isa.pressure,
        t_isa: isa.temperature,
        dt_isa: sat.value() - isa.temperature.value(),
        temperature_provenance: prov,
    })
}
