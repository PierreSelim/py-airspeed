use crate::errors::DomainError;

macro_rules! newtype {
    ($name:ident, $unit:expr, $check:expr) => {
        #[derive(Debug, Clone, Copy, PartialEq, PartialOrd)]
        pub struct $name(f64);

        impl $name {
            pub fn new(value: f64) -> Result<Self, DomainError> {
                if $check(value) {
                    Ok(Self(value))
                } else {
                    Err(DomainError::OutOfRange {
                        field: stringify!($name),
                        unit: $unit,
                        value,
                    })
                }
            }

            pub fn value(self) -> f64 {
                self.0
            }
        }
    };
}

newtype!(Knots, "kt", |v: f64| v > 0.0 && v < 661.0);
newtype!(MetersPerSec, "m/s", |v: f64| v > 0.0);
newtype!(Mach, "—", |v: f64| (0.0..1.0).contains(&v));
newtype!(Feet, "ft", |v: f64| (0.0..=65_617.0).contains(&v));
newtype!(Kelvin, "K", |v: f64| v > 0.0 && v < 400.0);
newtype!(Pascals, "Pa", |v: f64| v > 0.0);
newtype!(RecoveryFactor, "—", |v: f64| v > 0.0 && v <= 1.0);
