# Probabilistic Model Using VED

Volumetric Energy Density (VED) is the amount of energy (capacity, kWh) that can be stored in a given volume or how much laser energy is applied per unit volume of material.

**VED = P/vth**

where
- power, P, [W] = [J/s]
- scan velocity, v, [mm/s]
- layer thickness, t, [mm]
- hatch spacing, h, [mm]

This model predicts a **distribution** of fatigue lives instead of one value.

Here, VED is a **process input** that controls defect statistics.

---

# Imports

---

# 1. Input Parameters
collects all fixed inputs (material, geometry, loading, AM process)

---

## 1.1. Material Parameters
Paris law constants, fracture toughness, threshold SIF

Paris–Erdogan law:  **da/dN = C · ΔK^m**
- valid for  K_th < ΔK < K_c  (Stage II crack growth)

---

**CITE SOURCES FOR VARIABLE VALUES**

---

## 1.2. Geometry Parameters
specimen dimensions, defect location (→ Y factor)

---

## 1.3. Loading Parameters
stress amplitude, mean stress, frequency

---

**CITE SOURCES FOR VARIABLE VALUES**

---

## 1.4. Process Params & VED
laser power, scan speed, hatch spacing, layer thickness

---

Volumetric Energy Density (VED) is the amount of energy (capacity, kWh) that can be stored in a given volume or how much laser energy is applied per unit volume of material.

**VED = P / (vht)**

where
- power, P, [W] = [J/s]
- scan velocity, v, [mm/s]
- layer thickness, t, [mm]
- hatch spacing, h, [mm]

and
- low VED → lack-of-fusion porosity
- high VED → keyhole porosity
- both increase defect density

Here, VED is a **process input** that controls defect statistics.

---

**CITE SOURCES FOR VARIABLE VALUES**

---

# 2. Volume, Defect Density, and PDF
- Volumetric Energy Density (VED) from AM process parameters
- Defect number density rho_def from XCT data
- Expected defect count in the gauge volume
- Parametric PDF fit to measured defect sizes

---

## 2.1. Defect Density
The defect density [no. of defects/mm^3] is given by

**rho_def = N_def / V_scan**

Expected defects in gauge volume:  **⟨N⟩ = rho_def · V**

---

## 2.2. VED–Defect Density Correlation
A U-shaped empirical curve relates VED to defect density:
both under- and over-melting increase porosity.

---

**NOTE: **rho_op** and **rho_defects** are the same!!

---

## 2.3. Synthetic Defect Population
Generate a synthetic defect population (many specimens, each with many defects) from the VED.

---

### 2.3.a. Defect Size Distribution Parameters
Connect LPBF process parameters (VED) to defect-size population with **empirical statistical models**.

Assume defect size follows a **lognormal distribution**.

**values are placeholder values!!**

---

### 2.3.b. Generate Synthetic Population

---

## 2.4. Fit Parametric PDF
Three candidate distributions are fitted by MLE.

The best distribution is selected by the lowest Kolmogorov–Smirnov statistic.

---

### 2.4.a. Defect Size Histogram & PDF

---

## 2.5. Max.-Defect Distribution
Each specimen contains many defects.

Fatigue failure is controlled by the **largest** defect (Murakami).

Instead of taking all the defects from every specimen, only the critical (max.) defect will be chosen for further analysis.

The distribution of per-specimen maxima follows a Generalized Extreme Value (GEV) distribution.

---

### 2.5.a. Generalized Extreme Value Distribution (GEV)
- each specimen contains many defects
- fatigue failure is governed by the largest critical defect
- so the distribution of maxima tends toward a GEV distribution

---

## 2.6. Paris-Law Fatigue Life Formulae
Integrating Paris law from a_0 to a_f with the Shiozawa approximation
(a_f >> a_i, so the a_f term → 0 for m > 2):

        N_f ≈ 2 / [(m-2) · C · (Y·delta_sigma)^m · pi^(m/2)] · a_i^(1 - m/2)

Re-written in terms of the initial SIF range deltaK_i = Y·delta_sigma·√(pi·a_i):

        N_f ≈ 2 / [(m-2) · C · pi · (Y·delta_sigma)^2] · deltaK_i^(2-m)

---

The **stress intensity factor, delta(K)**, the measure of the severity of a crack situation, is determined by

**delta(K) = Y * stress_amp * sqrt(pi * A)**

Assume the defect_size is the crack length: defect_size, A = crack_length, a

---

## 2.7 Fatigue Life Dist. at Fixed Stress
Paris law + Shiozawa gives N_f for each specimen.

The resulting distribution captures the scatter from defect variability alone.

---

### 2.7.a Shiozawa Plot: deltaK_i vs N_f / √A
Expected slope from Paris law:

deltaK_i ∝ (N/√A)^(1/(2-m)) → **slope = 1/(2-m)**

---

### 2.7.b Reliability Curves: Empirical & Weibull Model

The fraction of specimens surviving beyond N cycles:

**R(N) = P(N_f > N)**

The Weibull model **R(N) = exp[-(N/η)^β]** is fitted for comparison

where:

- R(N) = reliability
- η = characteristic life
- β = Weibull shape parameter

---

# Monte Carlo Loop

---

## Fixed Stress

---

### Fatigue Life

---

### GEV, P vs sqrt(A)
- each specimen contains many defects
- fatigue failure is governed by the largest critical defect
- so the distribution of maxima tends toward a GEV distribution

---

### Shiozawa Curves

---

Shiozawa: stress intensity factor, delta(K), at the critical defect vs. sqrt(A)

---

Under constant stress, as the size of the defect increases, the stress intensity factor increases exponentially since both x and y, delta(K) and sqrt(A), respectively, are log-transformed.

---

#### Confidence Intervals

---

The narrow confidence intervals imply a good certainty in the estimate.

---

### Reliability Curves
the probability a specimen survives beyond a given 

fraction of specimens that survive past N cycles:

**R(N) = P(N_f > N)**

---

At low cycle counts, near one, almost nothing has failed yet. Then the curve drops: at around 50%, reliability has decreased and about half have failed. Finally, reliability approaches zero, so around 1100 cycles, almost all specimens have failed.

---

#### Weibull Reliability Model
This is more of a **statistical reliability model** rather than a crack-growth physics model.

Instead of simulating defects directly, failure probability is modeled with a Weibull distribution.

Typically, **R(N) = exp[-(N/η)^β]**

where:

- R(N) = reliability
- η = characteristic life
- β = Weibull shape parameter

This model describes how failure probability evolves with cycles.

---

Since the Weibull reliability curve and the Monte Carlo reliability curve are mostly close, the probabilistic model is internally consistent and the Weibull approximation is describing the failure behavior pretty well.

---

### Normalized Life
plot **delta(K_i) vs N/sqrt(A)**
where N/sqrt(A) = defect-normalized life

---

## Varying Sress

---

### Shiozawa Curve
with normalized life plot **delta(K_i) vs N/sqrt(A)** where N/sqrt(A) = defect-normalized life

---

A higher stress amplitude results in a higher stress intensity factor.
The stress intensity factor and Murakami factor are related exponentially since both axes are log-transformed.

---

### Reliability Curves
the probability a specimen survives beyond a given life

fraction of specimens that survive past N cycles:

**R(N) = P(N_f > N)**

---

At low cycle counts, near 100% reliability, almost nothing has failed yet. At around 60%, reliability has decreased and almost half the specimens have failed. Finally, reliability approaches zero, so around 130 cycles, almost all specimens have failed.

---

#### Weibull Reliability Model
R(N) = exp[-(N/eta)^beta]

---

Since the Weibull reliability curve and the Monte Carlo reliability curve are mostly close, the probabilistic model is internally consistent and the Weibull approximation is describing the failure behavior pretty well.