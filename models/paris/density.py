"""
2. Specimen Volume, Defect Density, and Defect PDF
=======================================================
Computes the defect number density from XCT/fractography data,
derives the expected number of defects in the gauge volume,
and fits a parametric PDF to the measured defect-size population.

Supported distributions
-----------------------
  • lognormal  — ln(a) ~ N(mu_ln, sigma_ln^2)  — default for LPBF porosity
  • weibull    — two-parameter Weibull
  • gumbel     — Gumbel (extreme-value type I, max)

This is intentionally data-agnostic;
call ``fit_defect_pdf()`` with array of measured defect sizes once data are available.
"""

from __future__ import annotations

import math
import numpy as np
from dataclasses import dataclass
from typing import Literal, Optional
from scipy import stats
from scipy.stats import kstest

from inputs import FrameworkInputs


# ---------------------------------------------------------------------------
# Data containers
# ---------------------------------------------------------------------------

@dataclass
class XCTData:
    """
    Raw output from an XCT or fractographic characterization campaign.

    Parameters
    ----------
    defect_sizes : array-like
        Measured equivalent defect diameters (or √area values) in metres.
    scanned_volume : float
        Total volume inspected by XCT  [m^3].
    """
    defect_sizes: np.ndarray      # [m]
    scanned_volume: float         # [m^3]

    def __post_init__(self):
        self.defect_sizes = np.asarray(self.defect_sizes, dtype=float)
        assert self.defect_sizes.size > 0,      "defect_sizes must not be empty"
        assert np.all(self.defect_sizes > 0),   "all defect sizes must be positive"
        assert self.scanned_volume > 0,         "scanned_volume must be > 0"

    @property
    def N_defects(self) -> int:
        return len(self.defect_sizes)


@dataclass
class DefectDensityResult:
    """Output of Step 2 defect-density calculation."""
    rho_def: float           # defect number density  rho_def = N_def / V_scan  [m⁻^3]
    expected_N_gauge: float  # expected defects in gauge volume  ⟨N⟩ = rho_def · V  [–]
    gauge_volume: float      # V  [m^3]
    scanned_volume: float    # V_scan  [m^3]
    N_detected: int          # number of defects detected in V_scan

    def summary(self) -> str:
        lines = [
            "",
            "[Defect Density]",
            f"  Scanned volume   V_scan = {self.scanned_volume*1e9:.4f} mm^3",
            f"  Detected defects N_def  = {self.N_detected}",
            f"  Defect density   rho_def  = {self.rho_def:.4e} m⁻^3",
            f"  Gauge volume     V      = {self.gauge_volume*1e9:.4f} mm^3",
            f"  Expected defects ⟨N⟩   = {self.expected_N_gauge:.2f}",
        ]
        return "\n".join(lines)


@dataclass
class DefectPDFResult:
    """Fitted parametric PDF for defect sizes."""
    distribution: Literal["lognormal", "weibull", "gumbel"]
    params: dict                  # distribution parameters (named)
    scipy_dist: object            # frozen scipy.stats distribution for sampling / pdf
    ks_statistic: float           # Kolmogorov–Smirnov test statistic
    ks_pvalue: float              # KS p-value (higher → better fit)
    fit_notes: str = ""

    def summary(self) -> str:
        param_str = ", ".join(f"{k}={v:.4g}" for k, v in self.params.items())
        lines = [
            "",
            "[Defect PDF]",
            f"  Distribution : {self.distribution}",
            f"  Parameters   : {param_str}",
            f"  KS statistic : {self.ks_statistic:.4f}",
            f"  KS p-value   : {self.ks_pvalue:.4f}",
        ]
        if self.fit_notes:
            lines.append(f"  Notes        : {self.fit_notes}")
        return "\n".join(lines)

    def sample(self, n: int, rng: Optional[np.random.Generator] = None) -> np.ndarray:
        """Draw n Monte Carlo samples of defect size [m]."""
        if rng is not None:
            return self.scipy_dist.rvs(size=n, random_state=rng)
        return self.scipy_dist.rvs(size=n)

    def pdf(self, a: np.ndarray) -> np.ndarray:
        """Evaluate the fitted PDF at crack sizes a [m]."""
        return self.scipy_dist.pdf(a)


# ---------------------------------------------------------------------------
# Step 2 functions
# ---------------------------------------------------------------------------

def compute_defect_density(xct: XCTData, inputs: FrameworkInputs) -> DefectDensityResult:
    """
    Eq. (2): rho_def = N_def / V_scan
    Expected defects in gauge volume: ⟨N⟩ = rho_def · V
    """
    rho = xct.N_defects / xct.scanned_volume
    V_gauge = inputs.geometry.gauge_volume
    return DefectDensityResult(
        rho_def=rho,
        expected_N_gauge=rho * V_gauge,
        gauge_volume=V_gauge,
        scanned_volume=xct.scanned_volume,
        N_detected=xct.N_defects,
    )


def fit_defect_pdf(
    xct: XCTData,
    distribution: Literal["lognormal", "weibull", "gumbel", "best"] = "best",
) -> DefectPDFResult:
    """
    Fit a parametric PDF to the measured defect sizes using MLE.

    Parameters
    ----------
    xct : XCTData
        Raw XCT measurements.
    distribution : str
        Which distribution family to fit.  Use ``"best"`` to automatically
        select by lowest KS statistic.

    Returns
    -------
    DefectPDFResult
        Fitted distribution with KS goodness-of-fit statistics.
    """
    sizes = xct.defect_sizes

    candidates = (
        ["lognormal", "weibull", "gumbel"]
        if distribution == "best"
        else [distribution]
    )

    results = []
    for dist_name in candidates:
        result = _fit_single(sizes, dist_name)
        results.append(result)

    # Select best by KS statistic (lowest = best fit to data)
    best = min(results, key=lambda r: r.ks_statistic)

    if distribution == "best":
        best.fit_notes = (
            f"Auto-selected from {candidates} by KS statistic. "
            f"KS values: "
            + ", ".join(
                f"{r.distribution}={r.ks_statistic:.4f}" for r in results
            )
        )

    return best


def _fit_single(
    sizes: np.ndarray,
    dist_name: Literal["lognormal", "weibull", "gumbel"],
) -> DefectPDFResult:
    """Internal: fit one distribution family and return a DefectPDFResult."""

    if dist_name == "lognormal":
        # scipy lognormal: parameterized as s=sigma_ln, scale=exp(mu_ln)
        s, loc, scale = stats.lognorm.fit(sizes, floc=0)
        mu_ln = math.log(scale)
        sigma_ln = s
        frozen = stats.lognorm(s=sigma_ln, loc=0, scale=math.exp(mu_ln))
        params = {"mu_ln": mu_ln, "sigma_ln": sigma_ln}

    elif dist_name == "weibull":
        # scipy uses weibull_min; shape=k, scale=λ
        k, loc, scale = stats.weibull_min.fit(sizes, floc=0)
        frozen = stats.weibull_min(c=k, loc=0, scale=scale)
        params = {"k": k, "lambda": scale}

    elif dist_name == "gumbel":
        loc, scale = stats.gumbel_r.fit(sizes)
        frozen = stats.gumbel_r(loc=loc, scale=scale)
        params = {"loc": loc, "scale": scale}

    else:
        raise ValueError(f"Unknown distribution: {dist_name!r}")

    ks_stat, ks_p = kstest(sizes, frozen.cdf)
    return DefectPDFResult(
        distribution=dist_name,
        params=params,
        scipy_dist=frozen,
        ks_statistic=ks_stat,
        ks_pvalue=ks_p,
    )


# ---------------------------------------------------------------------------
# VED → defect PDF correlation (empirical, Step 2.3)
# ---------------------------------------------------------------------------

@dataclass
class VEDCorrelation:
    """
    Empirical correlations between EVED and defect-PDF parameters.
    Populated from a process-window characterization campaign.

    Each attribute is a callable  f(EVED) → parameter value.

    Example
    -------
    You may fit polynomial or power-law models to   campaign data::

        import numpy as np
        corr = VEDCorrelation(
            mu_ln_of_VED   = lambda ved: -2.3 + 0.01 * ved,
            sigma_ln_of_VED= lambda ved: 0.4,
        )
    """
    mu_ln_of_VED: object      # callable: EVED [J/mm^3] → mu_ln  [ln(m)]
    sigma_ln_of_VED: object   # callable: EVED [J/mm^3] → sigma_ln  [–]

    def predict_pdf(self, VED: float) -> DefectPDFResult:
        """
        Predict the lognormal defect PDF directly from VED without new XCT data.
        Useful for evaluating new AM builds within the characterized process window.
        """
        mu_ln = self.mu_ln_of_VED(VED)
        sigma_ln = self.sigma_ln_of_VED(VED)
        frozen = stats.lognorm(s=sigma_ln, loc=0, scale=math.exp(mu_ln))
        return DefectPDFResult(
            distribution="lognormal",
            params={"mu_ln": mu_ln, "sigma_ln": sigma_ln},
            scipy_dist=frozen,
            ks_statistic=float("nan"),
            ks_pvalue=float("nan"),
            fit_notes=f"Predicted from VED={VED:.4f} J/mm^3 via empirical correlation.",
        )


# ---------------------------------------------------------------------------
# Convenience: run both sub-steps together
# ---------------------------------------------------------------------------

def run_2(
    inputs: FrameworkInputs,
    xct: XCTData,
    distribution: Literal["lognormal", "weibull", "gumbel", "best"] = "best",
    verbose: bool = True,
) -> tuple[DefectDensityResult, DefectPDFResult]:
    """
    Execute Step 2 in full:
      1. Compute defect number density and expected count in gauge volume.
      2. Fit a parametric PDF to measured defect sizes.

    Parameters
    ----------
    inputs      : FrameworkInputs from Step 1.
    xct         : XCTData with measured defect sizes and scanned volume.
    distribution: PDF family to fit, or 'best' for automatic selection.
    verbose     : Print summary to stdout.

    Returns
    -------
    (DefectDensityResult, DefectPDFResult)
    """
    density = compute_defect_density(xct, inputs)
    pdf_fit = fit_defect_pdf(xct, distribution=distribution)

    if verbose:
        print(density.summary())
        print(pdf_fit.summary())

    return density, pdf_fit


# ---------------------------------------------------------------------------
# Quick self-test with placeholder synthetic data
# (replace defect_sizes with   real XCT array)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.dirname(__file__))

    from inputs import example_inputs

    inputs = example_inputs()
    print(inputs.summary())

    # ------------------------------------------------------------------ #
    # PLACEHOLDER: replace this array with real XCT defect sizes [m]     #
    # ------------------------------------------------------------------ #
    rng = np.random.default_rng(42)
    placeholder_sizes = stats.lognorm.rvs(
        s=0.5, scale=np.exp(np.log(50e-6)), size=80, random_state=rng
    )

    xct = XCTData(
        defect_sizes=placeholder_sizes,
        scanned_volume=inputs.geometry.gauge_volume * 3.0,   # e.g. 3 specimens scanned
    )

    density_result, pdf_result = run_2(inputs, xct, distribution="best")

    # Sample 5 initial crack sizes for a quick check
    a0_samples = pdf_result.sample(5, rng=rng)
    print("\n[Sample a₀ values (m)]:", np.array2string(a0_samples, precision=3, formatter={"float_kind": lambda x: f"{x:.3e}"}))