"""
1. Input Parameters
========================
Defines and validates all fixed inputs required by the probabilistic fatigue-life
prediction framework (material, geometric, loading, and AM process parameters).
"""

from dataclasses import dataclass, field
from typing import Literal
import math


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class MaterialParams:
    """Paris law and fracture mechanics constants."""
    C: float          # Paris law pre-factor  [m/cycle / (MPa√m)^m]
    m: float          # Paris law exponent    [–]
    Kc: float         # Fracture toughness    [MPa√m]
    Kth: float        # Threshold SIF range   [MPa√m]
    E: float          # Young's modulus       [GPa]

    def __post_init__(self):
        assert self.C > 0,   f"Paris constant C must be > 0, got {self.C}"
        assert self.m > 0,   f"Paris exponent m must be > 0, got {self.m}"
        assert self.Kc > 0,  f"Fracture toughness Kc must be > 0"
        assert self.Kth >= 0, f"Threshold Kth must be >= 0"
        assert self.E > 0,   f"Young's modulus E must be > 0"


@dataclass
class GeometricParams:
    """Sample geometry and geometry correction factor."""
    cross_section_width: float   # [m]
    cross_section_height: float  # [m]
    gauge_length: float          # [m]
    defect_location: Literal["internal", "surface"] = "internal"

    @property
    def gauge_volume(self) -> float:
        """V = w × h × L  [m^3]"""
        return self.cross_section_width * self.cross_section_height * self.gauge_length

    @property
    def Y(self) -> float:
        """Geometry correction factor per Murakami framework."""
        return 0.5 if self.defect_location == "internal" else 0.6

    def __post_init__(self):
        for attr in ("cross_section_width", "cross_section_height", "gauge_length"):
            assert getattr(self, attr) > 0, f"{attr} must be > 0"
        assert self.defect_location in ("internal", "surface"), (
            "defect_location must be 'internal' or 'surface'"
        )


@dataclass
class LoadingParams:
    """Cyclic loading conditions."""
    sigma_a: float        # Stress amplitude  [MPa]
    sigma_m: float = 0.0  # Mean stress       [MPa]
    frequency: float = 1.0  # Cyclic frequency [Hz]

    @property
    def sigma_max(self) -> float:
        return self.sigma_m + self.sigma_a

    @property
    def sigma_min(self) -> float:
        return self.sigma_m - self.sigma_a

    @property
    def R(self) -> float:
        """Stress ratio sigma_min / sigma_max. Returns -inf if sigma_max == 0."""
        if self.sigma_max == 0:
            return float("-inf")
        return self.sigma_min / self.sigma_max

    @property
    def delta_sigma(self) -> float:
        """Stress range delta_sigma = 2 sigma_a (fully reversed) or sigma_max − max(sigma_min, 0)."""
        return self.sigma_max - max(self.sigma_min, 0.0)

    def __post_init__(self):
        assert self.sigma_a > 0,    "Stress amplitude must be > 0"
        assert self.frequency > 0,  "Frequency must be > 0"


@dataclass
class AMProcessParams:
    """Additive manufacturing (laser powder-bed fusion) process parameters."""
    laser_power: float    # P  [W]
    scan_speed: float     # v  [mm/s]
    hatch_spacing: float  # h  [mm]
    layer_thickness: float  # t  [mm]

    @property
    def VED(self) -> float:
        """
        Volumetric Energy Density  EVED = P / (v * h * t)  [J/mm^3]
        """
        denom = self.scan_speed * self.hatch_spacing * self.layer_thickness
        if denom == 0:
            raise ValueError("scan_speed, hatch_spacing, and layer_thickness must all be non-zero.")
        return self.laser_power / denom

    def __post_init__(self):
        for attr in ("laser_power", "scan_speed", "hatch_spacing", "layer_thickness"):
            assert getattr(self, attr) > 0, f"AM process parameter '{attr}' must be > 0"


@dataclass
class FrameworkInputs:
    """
    Top-level container that bundles all sigma parameter groups.
    Pass this object to every subsequent step.
    """
    material: MaterialParams
    geometry: GeometricParams
    loading: LoadingParams
    am_process: AMProcessParams

    def summary(self) -> str:
        lines = [
            "=" * 55,
            "  Framework Inputs Summary",
            "=" * 55,
            "",
            "[Material]",
            f"  C   = {self.material.C:.3e}  [m/cycle / (MPa√m)^m]",
            f"  m   = {self.material.m}",
            f"  Kc  = {self.material.Kc} MPa√m",
            f"  Kth = {self.material.Kth} MPa√m",
            f"  E   = {self.material.E} GPa",
            "",
            "[Geometry]",
            f"  Cross-section  = {self.geometry.cross_section_width*1e3:.1f} × "
            f"{self.geometry.cross_section_height*1e3:.1f} mm",
            f"  Gauge length   = {self.geometry.gauge_length*1e3:.1f} mm",
            f"  Gauge volume V = {self.geometry.gauge_volume*1e9:.4f} mm^3",
            f"  Defect location: {self.geometry.defect_location}  →  Y = {self.geometry.Y}",
            "",
            "[Loading]",
            f"  sigma_a = {self.loading.sigma_a} MPa",
            f"  sigma_m = {self.loading.sigma_m} MPa",
            f"  sigma_max = {self.loading.sigma_max:.2f} MPa,  sigma_min = {self.loading.sigma_min:.2f} MPa",
            f"  R = {self.loading.R:.3f},  delta_sigma = {self.loading.delta_sigma:.2f} MPa",
            f"  f = {self.loading.frequency} Hz",
            "",
            "[AM Process]",
            f"  P = {self.am_process.laser_power} W",
            f"  v = {self.am_process.scan_speed} mm/s",
            f"  h = {self.am_process.hatch_spacing} mm",
            f"  t = {self.am_process.layer_thickness} mm",
            f"  EVED = {self.am_process.VED:.4f} J/mm^3",
            "=" * 55,
        ]
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Example / default parameters (Ti-6Al-4V LPBF, literature values)
# ---------------------------------------------------------------------------

def example_inputs() -> FrameworkInputs:
    """
    Returns a FrameworkInputs object populated with representative values for
    Ti-6Al-4V produced by laser powder-bed fusion.  Replace with   own data.
    """
    return FrameworkInputs(
        material=MaterialParams(
            C=1.0e-11,   # typical Ti-6Al-4V Paris pre-factor (SI units)
            m=3.2,
            Kc=60.0,     # MPa√m
            Kth=3.0,     # MPa√m
            E=114.0,     # GPa
        ),
        geometry=GeometricParams(
            cross_section_width=5e-3,    # 5 mm
            cross_section_height=5e-3,   # 5 mm
            gauge_length=20e-3,          # 20 mm
            defect_location="internal",
        ),
        loading=LoadingParams(
            sigma_a=200.0,   # MPa
            sigma_m=0.0,     # fully reversed, R = -1
            frequency=20.0,  # Hz
        ),
        am_process=AMProcessParams(
            laser_power=200.0,      # W
            scan_speed=1200.0,      # mm/s
            hatch_spacing=0.11,     # mm
            layer_thickness=0.03,   # mm
        ),
    )


# ---------------------------------------------------------------------------
# Quick self-test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    inputs = example_inputs()
    print(inputs.summary())