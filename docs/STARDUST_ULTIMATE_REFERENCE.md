# 🛰️ Project STARDUST — Ultimate Technical Reference

## ML-Accelerated Conjunction Screening Triage Engine

**Hackathon:** Smart India Hackathon (SIH) 2026
**Team:** DEFCON
**Problem Statement ID:** SIH26209 (Student Innovation — Space Technology, Software)
**Date:** August 2026

---

## Table of Contents

1. [Problem Context & ISRO Data](#1-problem-context--isro-data)
2. [System Architecture](#2-system-architecture)
3. [Project Directory Structure](#3-project-directory-structure)
4. [Technology Stack — Exact Versions & Libraries](#4-technology-stack--exact-versions--libraries)
5. [Module 1: TLE Ingestion from CelesTrak](#5-module-1-tle-ingestion-from-celestrak)
6. [Module 2: SGP4 Orbital Propagation](#6-module-2-sgp4-orbital-propagation)
7. [Module 3: MOID Coarse Geometric Filter](#7-module-3-moid-coarse-geometric-filter)
8. [Module 4: Chan Formula — Probability of Collision](#8-module-4-chan-formula--probability-of-collision)
9. [Module 5: Feature Engineering for ML](#9-module-5-feature-engineering-for-ml)
10. [Module 6: Synthetic Data Generation](#10-module-6-synthetic-data-generation)
11. [Module 7: ML Pre-Filter (XGBoost/LightGBM)](#11-module-7-ml-pre-filter-xgboostlightgbm)
12. [Module 8: Streamlit Triage Dashboard](#12-module-8-streamlit-triage-dashboard)
13. [Evaluation Metrics for Safety-Critical ML](#13-evaluation-metrics-for-safety-critical-ml)
14. [36-Hour Hackathon Execution Timeline](#14-36-hour-hackathon-execution-timeline)
15. [Risk Register & Mitigations](#15-risk-register--mitigations)
16. [Presentation & Judging Strategy](#16-presentation--judging-strategy)
17. [Key Constants & Thresholds Reference](#17-key-constants--thresholds-reference)
18. [References & Papers](#18-references--papers)

---

## 1. Problem Context & ISRO Data

### 1.1 The Core Problem

India's space assets face an escalating collision risk from orbital debris. The **Combined Space Operations Center (CSpOC)** of the U.S. Space Command issued **over 150,000 close-approach alerts** for ISRO's Earth-orbiting satellites in 2025 alone. Despite this enormous alert volume, ISRO executed only:

| Year | Collision Avoidance Manoeuvres (CAMs) |
|------|------------------------------------:|
| 2025 | 20 |
| 2026 (Jan–Aug) | 9 |
| **Total (18 months)** | **29** |

**Source:** August 2026 Lok Sabha reply by the Indian government (PIB, IndiaExpress, The Hindu).

This means **< 0.02%** of all alerts result in an actual manoeuvre — a staggering signal-to-noise ratio that wastes enormous computational and analyst time.

### 1.2 ISRO's SSA Infrastructure

- **NETRA (Network for Space Object Tracking and Analysis):** ISRO's dedicated SSA centre
- **MOTR (Multi-Object Tracking Radar):** Located at Sriharikota for debris tracking
- **Hanle Optical Telescope:** New telescope in Ladakh nearing completion for GEO altitude tracking
- **20 active LEO satellites** in the most congested orbital regime
- **DFSM (Debris-Free Space Mission):** India's target of zero debris from all missions by 2030

### 1.3 Why STARDUST Matters

STARDUST is NOT an autonomous collision avoidance system. It is a **decision-support triage layer** that:

1. **Reduces computational load** by filtering 99%+ of safe pairs before expensive physics runs
2. **Reduces analyst fatigue** by surfacing only high-priority threats
3. **Preserves safety** by biasing toward false positives (flag everything uncertain)
4. **Complements validated math** — the Chan formula still runs on all flagged pairs

---

## 2. System Architecture

### 2.1 Pipeline Funnel Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    STARDUST SCREENING PIPELINE                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Step 1: TLE INGESTION (CelesTrak API)                         │
│  ──────────────────────────────────────                         │
│  Input:  ~30,000 active + debris objects                       │
│  Output: Parsed orbital elements in memory                     │
│  Pairs:  ~450,000,000 (N*(N-1)/2)                              │
│                    │                                            │
│                    ▼                                            │
│  Step 2: COARSE SCREEN (MOID Filter)                           │
│  ──────────────────────────────────────                         │
│  Filter: MOID > 10 km → DISCARD                               │
│  Output: ~50,000–150,000 surviving pairs                       │
│                    │                                            │
│                    ▼                                            │
│  Step 3: SGP4 PROPAGATION (7-day window)                       │
│  ──────────────────────────────────────                         │
│  Action: Propagate surviving pairs at 60s intervals            │
│  Output: TCA, miss distance, relative velocity for each pair   │
│                    │                                            │
│                    ▼                                            │
│  Step 4: ML PRE-FILTER (XGBoost/LightGBM)                     │
│  ──────────────────────────────────────                         │
│  Input:  Engineered features (see Section 9)                   │
│  Output: Binary: "Flag for Review" (1) / "Likely Safe" (0)    │
│  Target: Recall ≥ 99.9% — ZERO missed threats                 │
│  Result: ~100–500 flagged pairs                                │
│                    │                                            │
│                    ▼                                            │
│  Step 5: FINE SCREEN (Chan Formula)                            │
│  ──────────────────────────────────────                         │
│  Action: Full probability of collision (PoC) calculation       │
│  Output: Pc value for each flagged pair                        │
│  Filter: Pc > 1e-4 → CRITICAL ALERT                           │
│                    │                                            │
│                    ▼                                            │
│  Step 6: TRIAGE DASHBOARD (Streamlit)                          │
│  ──────────────────────────────────────                         │
│  Display: Funnel chart, 3D encounter geometry, threat table    │
│  Action:  Analyst review → approve/reject CAM recommendation   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Component Interaction Diagram

```
┌──────────────┐     HTTP GET      ┌─────────────┐
│  CelesTrak   │ ◄──────────────── │ TLE Fetcher  │
│  API Server  │ ────────────────► │  (Python)    │
└──────────────┘   JSON/TLE data   └──────┬───────┘
                                          │
                                          ▼
                                  ┌──────────────┐
                                  │ Orbit Parser │
                                  │ (sgp4 lib)   │
                                  └──────┬───────┘
                                         │
                              ┌──────────┴──────────┐
                              ▼                     ▼
                     ┌──────────────┐      ┌──────────────┐
                     │ MOID Filter  │      │ SGP4 Propagator │
                     │ (numpy/scipy)│      │ (sgp4/skyfield) │
                     └──────┬───────┘      └──────┬──────────┘
                            │                     │
                            └──────────┬──────────┘
                                       ▼
                              ┌──────────────┐
                              │ Feature      │
                              │ Engineer     │
                              └──────┬───────┘
                                     │
                                     ▼
                              ┌──────────────┐     ┌──────────────┐
                              │ ML Classifier │────►│ Chan Formula │
                              │ (LightGBM)   │     │ (scipy)      │
                              └──────┬───────┘     └──────┬───────┘
                                     │                    │
                                     └──────────┬─────────┘
                                                ▼
                                       ┌──────────────┐
                                       │  Streamlit   │
                                       │  Dashboard   │
                                       └──────────────┘
```

---

## 3. Project Directory Structure

```
stardust/
├── README.md
├── requirements.txt
├── config.py                    # All thresholds, constants, API URLs
├── main.py                      # Pipeline orchestrator
│
├── data/
│   ├── raw/                     # Downloaded TLE files (cached)
│   ├── processed/               # Parsed orbital elements (parquet/csv)
│   └── training/                # Synthetic training dataset
│       ├── features.parquet
│       └── labels.parquet
│
├── src/
│   ├── __init__.py
│   ├── tle_fetcher.py           # CelesTrak API client
│   ├── orbit_parser.py          # TLE → Satrec object parsing
│   ├── sgp4_propagator.py       # SGP4 propagation + TCA finder
│   ├── moid_calculator.py       # Minimum Orbit Intersection Distance
│   ├── chan_formula.py           # 2D collision probability (Chan/Foster)
│   ├── feature_engineer.py      # Orbital mechanics → ML features
│   ├── data_generator.py        # Synthetic training data pipeline
│   ├── ml_model.py              # XGBoost/LightGBM training + inference
│   └── utils.py                 # Coordinate transforms, constants
│
├── models/
│   ├── stardust_model.json      # Trained LightGBM/XGBoost model
│   ├── threshold.json           # Optimal decision threshold
│   └── feature_names.json       # Feature order for inference
│
├── dashboard/
│   ├── app.py                   # Streamlit dashboard entry point
│   ├── components/
│   │   ├── funnel_chart.py      # Triage funnel visualization
│   │   ├── encounter_3d.py      # 3D encounter + covariance ellipsoid
│   │   ├── threat_table.py      # Interactive CDM table
│   │   └── metrics_bar.py       # Top KPI metrics row
│   └── assets/
│       └── style.css            # Custom dashboard styling
│
├── notebooks/
│   ├── 01_data_exploration.ipynb
│   ├── 02_feature_analysis.ipynb
│   └── 03_model_evaluation.ipynb
│
└── tests/
    ├── test_moid.py
    ├── test_chan_formula.py
    ├── test_propagator.py
    └── test_ml_model.py
```

---

## 4. Technology Stack — Exact Versions & Libraries

### 4.1 Python Dependencies (`requirements.txt`)

```
# Core Scientific Computing
numpy>=1.26.0
scipy>=1.12.0
pandas>=2.2.0

# Orbital Mechanics
sgp4>=2.23                     # SGP4/SDP4 propagator (C-accelerated)
skyfield>=1.48                 # High-level astronomy library (wraps sgp4)
astropy>=6.0                   # Coordinate frames, time handling

# Machine Learning
xgboost>=2.0.0                 # Gradient boosted trees
lightgbm>=4.3.0                # Fast GBDT (preferred for inference speed)
scikit-learn>=1.4.0            # Metrics, preprocessing, train/test split
imbalanced-learn>=0.12.0       # SMOTE, ADASYN (if needed for comparison)
joblib>=1.3.0                  # Model serialization

# Dashboard
streamlit>=1.35.0              # Web dashboard framework
plotly>=5.22.0                 # Interactive 3D charts, funnel charts
altair>=5.3.0                  # Declarative statistical viz (optional)

# Data & HTTP
requests>=2.31.0               # HTTP client for CelesTrak API
pyarrow>=15.0.0                # Parquet file I/O
tqdm>=4.66.0                   # Progress bars

# Development
pytest>=8.0.0                  # Testing framework
black>=24.0.0                  # Code formatting
```

### 4.2 Key Library Justifications

| Library | Why This One | Alternative Considered |
|---------|-------------|----------------------|
| `sgp4` | C-accelerated, exact NORAD algorithm, supports batch propagation via `SatrecArray` | `poliastro` (heavier, more features than needed) |
| `lightgbm` | 2-3x faster inference than XGBoost, native GOSS handles imbalanced data, leaf-wise growth captures complex patterns | `xgboost` (slightly slower, used as comparison baseline) |
| `streamlit` | Rapid prototyping for hackathon, built-in `st.metric`, `st.data_editor`, `@st.fragment` for live updates | `dash` (more complex setup), `gradio` (ML-focused, less dashboard-like) |
| `plotly` | 3D scatter/surface for encounter geometry, built-in `go.Funnel`, interactive hover | `matplotlib` (static only), `bokeh` (steeper learning curve) |

---

## 5. Module 1: TLE Ingestion from CelesTrak

### 5.1 What is a TLE?

A **Two-Line Element Set (TLE)** is a standardized format encoding the orbital elements of an Earth-orbiting object. It was designed by NORAD/USSPACECOM and is used worldwide.

#### TLE Format Breakdown

```
Line 0: SATELLITE NAME                              (optional name line)
Line 1: 1 NNNNNC NNNNNAAA NNNNN.NNNNNNNN +.NNNNNNNN +NNNNN-N +NNNNN-N N NNNNN
Line 2: 2 NNNNN NNN.NNNN NNN.NNNN NNNNNNN NNN.NNNN NNN.NNNN NN.NNNNNNNNNNNNNN
```

**Example (ISS):**
```
ISS (ZARYA)
1 25544U 98067A   24001.50000000  .00016717  00000-0  10270-3 0  9006
2 25544  51.6400 208.9163 0006703  35.7025 324.4332 15.49560532431103
```

**Field-by-Field Breakdown:**

| Field | Line | Cols | Description | Example |
|-------|------|------|-------------|---------|
| Catalog Number | 1 | 3-7 | NORAD catalog ID | 25544 |
| Classification | 1 | 8 | U=Unclassified, C=Classified, S=Secret | U |
| Int'l Designator | 1 | 10-17 | Launch year, number, piece | 98067A |
| Epoch Year | 1 | 19-20 | 2-digit year | 24 (=2024) |
| Epoch Day | 1 | 21-32 | Day of year + fractional day | 001.50000000 |
| Mean Motion Derivative | 1 | 34-43 | ṅ/2 (rev/day²) | .00016717 |
| BSTAR Drag | 1 | 54-61 | Atmospheric drag coefficient | 10270-3 |
| Inclination | 2 | 9-16 | Orbital inclination (degrees) | 51.6400 |
| RAAN | 2 | 18-25 | Right Ascension of Ascending Node (°) | 208.9163 |
| Eccentricity | 2 | 27-33 | (decimal point assumed) | 0006703 → 0.0006703 |
| Arg of Perigee | 2 | 35-42 | Argument of perigee (°) | 35.7025 |
| Mean Anomaly | 2 | 44-51 | Mean anomaly (°) | 324.4332 |
| Mean Motion | 2 | 53-63 | Revolutions per day | 15.49560532 |
| Revolution Number | 2 | 64-68 | Orbit count at epoch | 43110 |

### 5.2 CelesTrak API Endpoints

**Base URL:** `https://celestrak.org/NORAD/elements/gp.php`

| Query Type | Parameter | Example URL |
|-----------|-----------|-------------|
| Active satellites | `GROUP=active` | `gp.php?GROUP=active&FORMAT=json` |
| Space debris | `GROUP=debris` | `gp.php?GROUP=debris&FORMAT=json` |
| Starlink constellation | `GROUP=starlink` | `gp.php?GROUP=starlink&FORMAT=json` |
| GPS constellation | `GROUP=gps-ops` | `gp.php?GROUP=gps-ops&FORMAT=json` |
| Single satellite by ID | `CATNR=25544` | `gp.php?CATNR=25544&FORMAT=json` |
| By launch designator | `INTDES=2024-001` | `gp.php?INTDES=2024-001&FORMAT=json` |

**Available formats:** `json`, `json-pretty`, `tle`, `3le`, `xml`, `kvn`, `csv`

**Rate Limiting:** CelesTrak updates GP data every **2 hours**. Do NOT poll more frequently.

### 5.3 Implementation: `tle_fetcher.py`

```python
"""
tle_fetcher.py — CelesTrak TLE Data Ingestion Module

Fetches Two-Line Element sets from CelesTrak's public API
and parses them into structured data for the STARDUST pipeline.
"""

import requests
import json
import time
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import pandas as pd

# Constants
CELESTRAK_BASE_URL = "https://celestrak.org/NORAD/elements/gp.php"
CACHE_DIR = Path("data/raw")
CACHE_EXPIRY_HOURS = 2  # CelesTrak update cycle

# Satellite groups relevant for conjunction screening
GROUPS = {
    "active": "Active satellites (ISRO + global)",
    "debris": "Cataloged space debris",
    "starlink": "SpaceX Starlink constellation",
    "stations": "Space stations (ISS, Tiangong)",
}


def fetch_tle_group(group: str, format: str = "json",
                    use_cache: bool = True) -> List[Dict]:
    """
    Fetch TLE data for a satellite group from CelesTrak.

    Args:
        group: One of 'active', 'debris', 'starlink', etc.
        format: Response format ('json', 'tle', 'csv', etc.)
        use_cache: If True, use cached data if < 2 hours old

    Returns:
        List of satellite data dictionaries (JSON format) or raw TLE lines
    """
    cache_file = CACHE_DIR / f"{group}_{format}.json"

    # Check cache freshness
    if use_cache and cache_file.exists():
        mod_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
        if datetime.now() - mod_time < timedelta(hours=CACHE_EXPIRY_HOURS):
            with open(cache_file, 'r') as f:
                return json.load(f)

    # Fetch from CelesTrak
    url = f"{CELESTRAK_BASE_URL}?GROUP={group}&FORMAT={format}"

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()

        # Cache the result
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        with open(cache_file, 'w') as f:
            json.dump(data, f)

        print(f"[TLE Fetcher] Downloaded {len(data)} objects "
              f"from group '{group}'")
        return data

    except requests.RequestException as e:
        print(f"[TLE Fetcher] Error fetching {group}: {e}")
        # Fall back to cache if available
        if cache_file.exists():
            with open(cache_file, 'r') as f:
                return json.load(f)
        raise


def fetch_all_groups() -> pd.DataFrame:
    """
    Fetch active satellites and debris, combine into a single DataFrame.

    Returns:
        DataFrame with columns: NORAD_CAT_ID, OBJECT_NAME, TLE_LINE1,
        TLE_LINE2, EPOCH, INCLINATION, ECCENTRICITY, RA_OF_ASC_NODE,
        ARG_OF_PERICENTER, MEAN_ANOMALY, MEAN_MOTION, BSTAR, etc.
    """
    all_data = []

    for group in ["active", "debris"]:
        group_data = fetch_tle_group(group, format="json")
        for obj in group_data:
            obj["SOURCE_GROUP"] = group
        all_data.extend(group_data)

    df = pd.DataFrame(all_data)
    print(f"[TLE Fetcher] Total catalog: {len(df)} objects "
          f"({df['SOURCE_GROUP'].value_counts().to_dict()})")
    return df


def parse_json_to_orbital_elements(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert CelesTrak JSON fields to standardized orbital elements.

    CelesTrak JSON keys (examples):
        OBJECT_NAME, NORAD_CAT_ID, EPOCH, MEAN_MOTION,
        ECCENTRICITY, INCLINATION, RA_OF_ASC_NODE,
        ARG_OF_PERICENTER, MEAN_ANOMALY, BSTAR,
        MEAN_MOTION_DOT, MEAN_MOTION_DDOT, TLE_LINE1, TLE_LINE2
    """
    # Standard gravitational parameter (Earth) in km³/s²
    MU_EARTH = 398600.4418

    # Convert mean motion (rev/day) → semi-major axis (km)
    # n = sqrt(mu / a³)  →  a = (mu / (2πn/86400)²)^(1/3)
    n_rad_s = df["MEAN_MOTION"] * 2 * 3.141592653589793 / 86400.0
    df["SEMI_MAJOR_AXIS_KM"] = (MU_EARTH / (n_rad_s ** 2)) ** (1.0 / 3.0)

    # Compute perigee and apogee altitudes
    R_EARTH = 6378.137  # km
    df["PERIGEE_ALT_KM"] = (
        df["SEMI_MAJOR_AXIS_KM"] * (1 - df["ECCENTRICITY"]) - R_EARTH
    )
    df["APOGEE_ALT_KM"] = (
        df["SEMI_MAJOR_AXIS_KM"] * (1 + df["ECCENTRICITY"]) - R_EARTH
    )

    return df
```

### 5.4 CelesTrak JSON Response Schema

Each object in the JSON array has these fields:

```json
{
  "OBJECT_NAME": "ISS (ZARYA)",
  "OBJECT_ID": "1998-067A",
  "EPOCH": "2024-01-01T12:00:00.000000",
  "MEAN_MOTION": 15.495605,
  "ECCENTRICITY": 0.0006703,
  "INCLINATION": 51.64,
  "RA_OF_ASC_NODE": 208.9163,
  "ARG_OF_PERICENTER": 35.7025,
  "MEAN_ANOMALY": 324.4332,
  "EPHEMERIS_TYPE": 0,
  "CLASSIFICATION_TYPE": "U",
  "NORAD_CAT_ID": 25544,
  "ELEMENT_SET_NO": 900,
  "REV_AT_EPOCH": 43110,
  "BSTAR": 0.0001027,
  "MEAN_MOTION_DOT": 0.00016717,
  "MEAN_MOTION_DDOT": 0,
  "TLE_LINE0": "0 ISS (ZARYA)",
  "TLE_LINE1": "1 25544U 98067A ...",
  "TLE_LINE2": "2 25544 ..."
}
```

---

## 6. Module 2: SGP4 Orbital Propagation

### 6.1 What is SGP4?

**SGP4 (Simplified General Perturbations 4)** is the standard algorithm used by NORAD/USSPACECOM to propagate TLE-based orbits. It models:

- Earth's oblate gravitational field (J2, J3, J4 zonal harmonics)
- Atmospheric drag (via the BSTAR coefficient)
- Sun/Moon gravitational perturbations (for deep-space objects → SDP4)

**Output:** Position (x, y, z) and velocity (vx, vy, vz) in the **TEME (True Equator, Mean Equinox)** reference frame, in **km** and **km/s**.

**Accuracy:** ~1 km position error per day of propagation. TLEs degrade rapidly; best used within 7 days of epoch.

### 6.2 The `sgp4` Python Library

The `sgp4` PyPI package is the community-standard C-accelerated implementation.

#### Basic Usage

```python
from sgp4.api import Satrec, SatrecArray
from sgp4.api import jday
import numpy as np

# Parse a single TLE
line1 = '1 25544U 98067A   24001.50000000  .00016717  00000-0  10270-3 0  9006'
line2 = '2 25544  51.6400 208.9163 0006703  35.7025 324.4332 15.49560532431103'

satellite = Satrec.twoline2rv(line1, line2)

# Propagate to a specific time (UTC)
# jday(year, month, day, hour, minute, second)
jd, fr = jday(2024, 1, 2, 12, 0, 0)

error_code, position_teme, velocity_teme = satellite.sgp4(jd, fr)
# position_teme = (x, y, z) in km (TEME frame)
# velocity_teme = (vx, vy, vz) in km/s (TEME frame)
# error_code = 0 means success

if error_code == 0:
    print(f"Position (TEME): {position_teme} km")
    print(f"Velocity (TEME): {velocity_teme} km/s")
```

#### Batch Propagation with `SatrecArray` (FAST)

```python
from sgp4.api import Satrec, SatrecArray
import numpy as np

# Load many satellites
satellites = []
for tle_line1, tle_line2 in tle_pairs:
    satellites.append(Satrec.twoline2rv(tle_line1, tle_line2))

# Create array for vectorized propagation
sat_array = SatrecArray(satellites)

# Define time array (7 days, 60-second intervals)
# = 10,080 time steps
jd_base, fr_base = jday(2024, 1, 1, 0, 0, 0)
time_steps = np.arange(0, 7 * 86400, 60) / 86400.0  # days
jd_array = np.full(len(time_steps), jd_base)
fr_array = fr_base + time_steps

# Propagate ALL satellites at ALL times simultaneously
# errors shape: (num_sats, num_times)
# positions shape: (num_sats, num_times, 3)
# velocities shape: (num_sats, num_times, 3)
errors, positions, velocities = sat_array.sgp4(jd_array, fr_array)
```

### 6.3 Finding Time of Closest Approach (TCA)

```python
"""
sgp4_propagator.py — Orbit Propagation & TCA Finder
"""

import numpy as np
from sgp4.api import Satrec, jday
from scipy.optimize import minimize_scalar
from typing import Tuple, Dict


def propagate_pair(
    sat1: Satrec, sat2: Satrec,
    start_jd: float, start_fr: float,
    window_days: float = 7.0,
    step_seconds: float = 60.0
) -> Dict:
    """
    Propagate two satellites and find their closest approach.

    Returns:
        Dict with keys: tca_jd, tca_fr, miss_distance_km,
        rel_velocity_km_s, pos1_tca, pos2_tca, vel1_tca, vel2_tca
    """
    # Coarse scan: propagate at step_seconds intervals
    n_steps = int(window_days * 86400 / step_seconds)
    min_dist = float('inf')
    min_idx = 0

    for i in range(n_steps):
        fr = start_fr + (i * step_seconds / 86400.0)
        jd = start_jd

        # Handle day rollover
        while fr >= 1.0:
            fr -= 1.0
            jd += 1.0

        e1, r1, v1 = sat1.sgp4(jd, fr)
        e2, r2, v2 = sat2.sgp4(jd, fr)

        if e1 != 0 or e2 != 0:
            continue

        r1, r2 = np.array(r1), np.array(r2)
        dist = np.linalg.norm(r1 - r2)

        if dist < min_dist:
            min_dist = dist
            min_idx = i

    # Fine refinement: bisection around the minimum
    t_min = max(0, min_idx - 1) * step_seconds / 86400.0
    t_max = min(n_steps - 1, min_idx + 1) * step_seconds / 86400.0

    def distance_at_t(t_days):
        fr = start_fr + t_days
        jd = start_jd
        while fr >= 1.0:
            fr -= 1.0
            jd += 1.0
        e1, r1, v1 = sat1.sgp4(jd, fr)
        e2, r2, v2 = sat2.sgp4(jd, fr)
        if e1 != 0 or e2 != 0:
            return 1e12
        return np.linalg.norm(np.array(r1) - np.array(r2))

    result = minimize_scalar(distance_at_t, bounds=(t_min, t_max),
                             method='bounded')
    tca_t = result.x

    # Get full state at TCA
    fr_tca = start_fr + tca_t
    jd_tca = start_jd
    while fr_tca >= 1.0:
        fr_tca -= 1.0
        jd_tca += 1.0

    _, r1, v1 = sat1.sgp4(jd_tca, fr_tca)
    _, r2, v2 = sat2.sgp4(jd_tca, fr_tca)
    r1, r2 = np.array(r1), np.array(r2)
    v1, v2 = np.array(v1), np.array(v2)

    return {
        "tca_jd": jd_tca,
        "tca_fr": fr_tca,
        "miss_distance_km": np.linalg.norm(r1 - r2),
        "rel_velocity_km_s": np.linalg.norm(v1 - v2),
        "pos1_tca_km": r1,
        "pos2_tca_km": r2,
        "vel1_tca_kms": v1,
        "vel2_tca_kms": v2,
    }
```

### 6.4 Coordinate Frames

| Frame | Full Name | Used For |
|-------|-----------|----------|
| **TEME** | True Equator, Mean Equinox | SGP4 output (native) |
| **ECI** | Earth-Centered Inertial (J2000/GCRF) | Standard inertial frame |
| **ECEF** | Earth-Centered, Earth-Fixed (ITRF) | Ground-based observations |
| **RIC/RTN** | Radial, In-track, Cross-track | Relative encounter geometry |

**TEME → ECI conversion** is handled by `astropy` or `skyfield`:

```python
from astropy.coordinates import TEME, GCRS, CartesianRepresentation
from astropy import units as u
from astropy.time import Time

def teme_to_eci(pos_teme_km, vel_teme_km_s, epoch_jd):
    """Convert SGP4 TEME output to ECI (GCRS/J2000)."""
    t = Time(epoch_jd, format='jd')
    teme_coord = TEME(
        CartesianRepresentation(
            x=pos_teme_km[0]*u.km,
            y=pos_teme_km[1]*u.km,
            z=pos_teme_km[2]*u.km
        ),
        obstime=t
    )
    eci_coord = teme_coord.transform_to(GCRS(obstime=t))
    return np.array([
        eci_coord.cartesian.x.to(u.km).value,
        eci_coord.cartesian.y.to(u.km).value,
        eci_coord.cartesian.z.to(u.km).value
    ])
```

---

## 7. Module 3: MOID Coarse Geometric Filter

### 7.1 What is MOID?

**MOID (Minimum Orbit Intersection Distance)** is the shortest distance between two Keplerian ellipses in 3D space, regardless of where the objects actually are on their orbits at any given time. It is purely geometric — it answers: "How close could these two orbits ever get?"

- If MOID > threshold → the orbits physically cannot bring the objects close enough → **discard the pair**
- If MOID ≤ threshold → the orbits overlap enough that a conjunction is geometrically possible → **keep the pair** for time-dependent analysis

### 7.2 MOID Calculation Methods

| Method | Description | Speed | Accuracy |
|--------|-------------|-------|----------|
| **Gronchi (2005)** | Polynomial root-finding (degree-16 system) | Medium | Exact |
| **Baluev & Mikryukov (2018)** | Iterative distance minimization (`distlink` library) | Fast | Exact |
| **Numerical Minimization** | `scipy.optimize.minimize` on parametric distance | Medium | Near-exact |
| **Perigee/Apogee Overlap** | Quick radial altitude check (pre-MOID screen) | Very Fast | Approximate |

### 7.3 Fast Pre-MOID Filter: Perigee/Apogee Overlap

Before computing full MOID, apply this O(1) geometric check:

```python
def radial_overlap_check(a1, e1, a2, e2):
    """
    Check if two orbits overlap radially.
    If perigee of one is above apogee of other, MOID is guaranteed > 0
    and the pair can be instantly discarded.

    Returns: True if orbits MAY intersect radially
    """
    r_perigee_1 = a1 * (1 - e1)  # km from Earth center
    r_apogee_1 = a1 * (1 + e1)
    r_perigee_2 = a2 * (1 - e2)
    r_apogee_2 = a2 * (1 + e2)

    # Orbits overlap radially if:
    # perigee of each is below apogee of the other
    overlap = min(r_apogee_1, r_apogee_2) - max(r_perigee_1, r_perigee_2)
    return overlap > 0
```

### 7.4 Full MOID Implementation

```python
"""
moid_calculator.py — Minimum Orbit Intersection Distance

Computes MOID between two Keplerian orbits using numerical optimization
on the parametric distance between points on two ellipses.
"""

import numpy as np
from scipy.optimize import differential_evolution, minimize
from typing import Tuple


def keplerian_to_position(
    a: float, e: float, i: float,
    raan: float, omega: float, nu: float
) -> np.ndarray:
    """
    Convert Keplerian elements + true anomaly to ECI position vector.

    Args:
        a: Semi-major axis (km)
        e: Eccentricity
        i: Inclination (radians)
        raan: Right Ascension of Ascending Node (radians)
        omega: Argument of perigee (radians)
        nu: True anomaly (radians)

    Returns:
        3D position vector in ECI frame (km)
    """
    # Radius at this true anomaly
    r = a * (1 - e**2) / (1 + e * np.cos(nu))

    # Position in orbital plane (perifocal frame)
    x_pf = r * np.cos(nu)
    y_pf = r * np.sin(nu)

    # Rotation matrix: Perifocal → ECI
    cos_o, sin_o = np.cos(omega), np.sin(omega)
    cos_O, sin_O = np.cos(raan), np.sin(raan)
    cos_i, sin_i = np.cos(i), np.sin(i)

    x_eci = (cos_O * cos_o - sin_O * sin_o * cos_i) * x_pf + \
            (-cos_O * sin_o - sin_O * cos_o * cos_i) * y_pf
    y_eci = (sin_O * cos_o + cos_O * sin_o * cos_i) * x_pf + \
            (-sin_O * sin_o + cos_O * cos_o * cos_i) * y_pf
    z_eci = (sin_o * sin_i) * x_pf + (cos_o * sin_i) * y_pf

    return np.array([x_eci, y_eci, z_eci])


def compute_moid(
    elements1: Tuple[float, ...],
    elements2: Tuple[float, ...],
    n_grid: int = 360
) -> float:
    """
    Compute MOID between two orbits using grid search + local refinement.

    Args:
        elements1: (a, e, i_rad, raan_rad, omega_rad) for orbit 1
        elements2: (a, e, i_rad, raan_rad, omega_rad) for orbit 2
        n_grid: Grid resolution for initial search (degrees)

    Returns:
        MOID in km
    """
    a1, e1, i1, raan1, omega1 = elements1
    a2, e2, i2, raan2, omega2 = elements2

    def distance(params):
        nu1, nu2 = params
        pos1 = keplerian_to_position(a1, e1, i1, raan1, omega1, nu1)
        pos2 = keplerian_to_position(a2, e2, i2, raan2, omega2, nu2)
        return np.linalg.norm(pos1 - pos2)

    # Phase 1: Coarse grid search
    nu_grid = np.linspace(0, 2 * np.pi, n_grid, endpoint=False)
    min_dist = float('inf')
    best_nu1, best_nu2 = 0.0, 0.0

    for nu1 in nu_grid:
        pos1 = keplerian_to_position(a1, e1, i1, raan1, omega1, nu1)
        for nu2 in nu_grid:
            pos2 = keplerian_to_position(a2, e2, i2, raan2, omega2, nu2)
            d = np.linalg.norm(pos1 - pos2)
            if d < min_dist:
                min_dist = d
                best_nu1, best_nu2 = nu1, nu2

    # Phase 2: Local refinement with L-BFGS-B
    result = minimize(
        distance,
        x0=[best_nu1, best_nu2],
        method='L-BFGS-B',
        bounds=[(0, 2 * np.pi), (0, 2 * np.pi)]
    )

    return result.fun


def screen_pairs_by_moid(
    catalog_df,
    moid_threshold_km: float = 10.0
) -> list:
    """
    Screen all pairs in catalog for MOID below threshold.
    Uses vectorized perigee/apogee pre-filter first.

    Returns: List of (idx1, idx2, moid_km) tuples
    """
    n = len(catalog_df)
    surviving_pairs = []

    for i in range(n):
        row_i = catalog_df.iloc[i]
        a1 = row_i['SEMI_MAJOR_AXIS_KM']
        e1 = row_i['ECCENTRICITY']

        for j in range(i + 1, n):
            row_j = catalog_df.iloc[j]
            a2 = row_j['SEMI_MAJOR_AXIS_KM']
            e2 = row_j['ECCENTRICITY']

            # Quick radial overlap check (O(1))
            if not radial_overlap_check(a1, e1, a2, e2):
                continue

            # Full MOID calculation
            elements1 = (
                a1, e1,
                np.radians(row_i['INCLINATION']),
                np.radians(row_i['RA_OF_ASC_NODE']),
                np.radians(row_i['ARG_OF_PERICENTER'])
            )
            elements2 = (
                a2, e2,
                np.radians(row_j['INCLINATION']),
                np.radians(row_j['RA_OF_ASC_NODE']),
                np.radians(row_j['ARG_OF_PERICENTER'])
            )

            moid = compute_moid(elements1, elements2)

            if moid <= moid_threshold_km:
                surviving_pairs.append((i, j, moid))

    return surviving_pairs
```

### 7.5 MOID Threshold Selection

| Threshold (km) | Typical Use | Pairs Surviving (est.) |
|:-:|:-:|:-:|
| 50 | Ultra-conservative (many false positives) | ~500,000 |
| 25 | Conservative | ~100,000 |
| **10** | **Standard conjunction screening** | **~50,000** |
| 5 | Aggressive filtering | ~10,000 |
| 1 | Only very close orbits | ~1,000 |

**Recommendation:** Use **10 km** for demonstration. This catches all realistic threats while providing meaningful filtering.

---

## 8. Module 4: Chan Formula — Probability of Collision

### 8.1 Mathematical Foundation

The **Chan/Foster 2D collision probability** method (Chan 1997, Foster 1992) is the industry standard for conjunction assessment. It works by:

1. **Projecting** the 3D relative encounter geometry onto the **B-plane** (perpendicular to relative velocity vector)
2. **Integrating** a 2D Gaussian probability density (from combined covariance) over a circular disk defined by the combined hard-body radius

### 8.2 Step-by-Step Derivation

#### Step 1: Relative State at TCA

At Time of Closest Approach (TCA):
- Relative position: $\Delta\mathbf{r} = \mathbf{r}_1 - \mathbf{r}_2$
- Relative velocity: $\Delta\mathbf{v} = \mathbf{v}_1 - \mathbf{v}_2$
- Miss distance: $d_{miss} = \|\Delta\mathbf{r}\|$

#### Step 2: B-Plane Projection

The B-plane is defined perpendicular to the relative velocity. Construct an orthonormal basis:

$$\hat{\mathbf{e}}_1 = \frac{\Delta\mathbf{v}}{\|\Delta\mathbf{v}\|}$$

$$\hat{\mathbf{e}}_2 = \frac{\Delta\mathbf{v} \times \Delta\mathbf{r}}{\|\Delta\mathbf{v} \times \Delta\mathbf{r}\|}$$

$$\hat{\mathbf{e}}_3 = \hat{\mathbf{e}}_1 \times \hat{\mathbf{e}}_2$$

Project the miss vector onto the B-plane:

$$\xi = \Delta\mathbf{r} \cdot \hat{\mathbf{e}}_2 \quad \text{(cross-track component)}$$
$$\zeta = \Delta\mathbf{r} \cdot \hat{\mathbf{e}}_3 \quad \text{(in-plane component)}$$

#### Step 3: Combined Covariance in B-Plane

Combined position covariance: $\mathbf{C} = \mathbf{C}_1 + \mathbf{C}_2$

Projection matrix: $\mathbf{P} = [\hat{\mathbf{e}}_2 \quad \hat{\mathbf{e}}_3]^T$ (2×3 matrix)

2D projected covariance: $\mathbf{C}_{2D} = \mathbf{P} \cdot \mathbf{C} \cdot \mathbf{P}^T$

$$\mathbf{C}_{2D} = \begin{bmatrix} \sigma_\xi^2 & \rho\sigma_\xi\sigma_\zeta \\ \rho\sigma_\xi\sigma_\zeta & \sigma_\zeta^2 \end{bmatrix}$$

#### Step 4: Integration Over Hard-Body Disk

The probability of collision is:

$$P_c = \frac{1}{2\pi\sqrt{\det(\mathbf{C}_{2D})}} \iint_{\text{Circle}(R_{HB})} \exp\left(-\frac{1}{2}\begin{bmatrix}x-\xi \\ y-\zeta\end{bmatrix}^T \mathbf{C}_{2D}^{-1} \begin{bmatrix}x-\xi \\ y-\zeta\end{bmatrix}\right) dx\, dy$$

Where $R_{HB} = R_1 + R_2$ (Combined Hard-Body Radius, typically 1–10 m).

### 8.3 Implementation: `chan_formula.py`

```python
"""
chan_formula.py — 2D Collision Probability Calculator

Implements the Chan/Foster method for computing probability of collision
at the B-plane (encounter plane) using combined covariance integration.
"""

import numpy as np
from scipy.integrate import dblquad
from scipy.stats import multivariate_normal
from typing import Tuple, Dict


def compute_bplane_projection(
    delta_r: np.ndarray,
    delta_v: np.ndarray,
    cov_combined: np.ndarray
) -> Dict:
    """
    Project 3D relative state onto the 2D B-plane.

    Args:
        delta_r: Relative position vector at TCA (km), shape (3,)
        delta_v: Relative velocity vector at TCA (km/s), shape (3,)
        cov_combined: Combined 3x3 position covariance (km²)

    Returns:
        Dict with B-plane coordinates and 2D covariance
    """
    # B-plane basis vectors
    e1 = delta_v / np.linalg.norm(delta_v)  # along relative velocity

    cross = np.cross(delta_v, delta_r)
    cross_norm = np.linalg.norm(cross)

    if cross_norm < 1e-15:
        # Degenerate case: head-on or nearly so
        # Use arbitrary perpendicular vector
        if abs(e1[0]) < 0.9:
            e2 = np.cross(e1, np.array([1, 0, 0]))
        else:
            e2 = np.cross(e1, np.array([0, 1, 0]))
        e2 = e2 / np.linalg.norm(e2)
    else:
        e2 = cross / cross_norm

    e3 = np.cross(e1, e2)

    # Projection matrix (2x3)
    P = np.array([e2, e3])

    # B-plane miss vector components
    xi = np.dot(delta_r, e2)    # cross-track
    zeta = np.dot(delta_r, e3)  # in-plane

    # 2D projected covariance
    cov_2d = P @ cov_combined @ P.T

    return {
        "xi": xi,               # km
        "zeta": zeta,            # km
        "miss_bplane": np.sqrt(xi**2 + zeta**2),  # km
        "cov_2d": cov_2d,        # km²
        "sigma_xi": np.sqrt(cov_2d[0, 0]),
        "sigma_zeta": np.sqrt(cov_2d[1, 1]),
        "correlation": cov_2d[0, 1] / np.sqrt(cov_2d[0, 0] * cov_2d[1, 1]),
    }


def chan_collision_probability(
    delta_r: np.ndarray,
    delta_v: np.ndarray,
    cov1: np.ndarray,
    cov2: np.ndarray,
    hbr: float = 0.010,  # km (= 10 meters)
    method: str = "numerical"
) -> Dict:
    """
    Compute 2D collision probability using the Chan/Foster method.

    Args:
        delta_r: Relative position at TCA (km), shape (3,)
        delta_v: Relative velocity at TCA (km/s), shape (3,)
        cov1: Primary 3x3 position covariance (km²)
        cov2: Secondary 3x3 position covariance (km²)
        hbr: Combined Hard-Body Radius (km). Default 10m = 0.01 km
        method: 'numerical' (dblquad) or 'analytical' (Chan series)

    Returns:
        Dict with Pc value and diagnostic info
    """
    # Combined covariance
    cov_combined = cov1 + cov2

    # B-plane projection
    bp = compute_bplane_projection(delta_r, delta_v, cov_combined)

    xi, zeta = bp["xi"], bp["zeta"]
    cov_2d = bp["cov_2d"]

    if method == "numerical":
        # Numerical 2D integration over HBR disk
        rv = multivariate_normal(mean=[xi, zeta], cov=cov_2d)

        def integrand(y, x):
            return rv.pdf([x, y])

        # Integration limits: circle of radius hbr centered at origin
        def y_lower(x):
            if abs(x) >= hbr:
                return 0.0
            return -np.sqrt(hbr**2 - x**2)

        def y_upper(x):
            if abs(x) >= hbr:
                return 0.0
            return np.sqrt(hbr**2 - x**2)

        pc, error = dblquad(
            integrand,
            -hbr, hbr,
            y_lower, y_upper,
            epsabs=1e-15, epsrel=1e-12
        )

    elif method == "analytical":
        # Chan's analytical upper bound approximation
        # Pc_max = HBR² / (e * d_miss²)  (Akella & Alfriend bound)
        d_miss_sq = xi**2 + zeta**2
        if d_miss_sq < 1e-20:
            pc = 1.0  # Head-on collision
        else:
            pc = hbr**2 / (np.e * d_miss_sq)
            pc = min(pc, 1.0)

    # Also compute the Foster maximum Pc
    sigma_bplane_sq = 0.5 * (cov_2d[0, 0] + cov_2d[1, 1])
    d_miss_sq = xi**2 + zeta**2
    if sigma_bplane_sq > 1e-20:
        pc_foster_approx = (hbr**2 / (2.0 * sigma_bplane_sq)) * \
                           np.exp(-0.5 * d_miss_sq / sigma_bplane_sq)
    else:
        pc_foster_approx = 1.0

    return {
        "pc": pc,
        "pc_foster_approx": pc_foster_approx,
        "miss_distance_km": np.sqrt(d_miss_sq),
        "miss_distance_m": np.sqrt(d_miss_sq) * 1000,
        "hbr_km": hbr,
        "bplane_xi_km": xi,
        "bplane_zeta_km": zeta,
        "sigma_xi_km": bp["sigma_xi"],
        "sigma_zeta_km": bp["sigma_zeta"],
        "is_critical": pc > 1e-4,  # Standard ISRO/NASA threshold
    }


def approximate_covariance(bstar: float, altitude_km: float) -> np.ndarray:
    """
    Generate an approximate position covariance when real CDM data
    is unavailable. Based on typical TLE-derived uncertainty models.

    Args:
        bstar: BSTAR drag coefficient from TLE
        altitude_km: Orbital altitude in km

    Returns:
        3x3 covariance matrix in km²
    """
    # Typical uncertainty scales (from TLE accuracy studies):
    # Radial: 0.05 - 0.5 km
    # In-track: 0.5 - 5.0 km (grows with drag uncertainty)
    # Cross-track: 0.1 - 1.0 km

    # Scale with altitude (lower = more drag = more uncertainty)
    drag_factor = max(1.0, 5.0 * abs(bstar) * 1e4)

    sigma_r = 0.1 * drag_factor      # Radial (km)
    sigma_t = 1.0 * drag_factor      # In-track (km)
    sigma_n = 0.2 * drag_factor      # Cross-track (km)

    # Diagonal covariance (simplified — no correlations)
    return np.diag([sigma_r**2, sigma_t**2, sigma_n**2])
```

### 8.4 Collision Probability Thresholds

| Threshold | Meaning | Action |
|:-:|:--|:--|
| $P_c > 10^{-2}$ | Extremely high risk | Immediate CAM required |
| $P_c > 10^{-4}$ | **Standard ISRO/NASA red threshold** | **CAM planning begins** |
| $P_c > 10^{-5}$ | Elevated risk (yellow) | Enhanced monitoring |
| $P_c > 10^{-7}$ | Low risk | Routine tracking |
| $P_c < 10^{-7}$ | Negligible | No action needed |

---

## 9. Module 5: Feature Engineering for ML

### 9.1 Complete Feature Vector

The ML model receives a tabular feature vector for each satellite pair that survives MOID screening and propagation. These features are chosen for their **physical meaning** and **predictive power**.

```python
"""
feature_engineer.py — Orbital Mechanics Feature Extraction

Transforms raw propagated state vectors into ML-ready features.
"""

import numpy as np
from typing import Dict


def extract_features(
    pos1: np.ndarray, vel1: np.ndarray,
    pos2: np.ndarray, vel2: np.ndarray,
    cov1: np.ndarray, cov2: np.ndarray,
    elements1: Dict, elements2: Dict,
    moid_km: float
) -> Dict[str, float]:
    """
    Extract the complete ML feature vector for a conjunction pair.

    Returns:
        Dictionary of named features
    """
    # ---- Kinematics at TCA ----
    delta_r = pos1 - pos2  # km
    delta_v = vel1 - vel2  # km/s

    miss_distance_km = np.linalg.norm(delta_r)
    rel_velocity_kms = np.linalg.norm(delta_v)

    # ---- RIC (Radial, In-track, Cross-track) Frame ----
    r_hat = pos1 / np.linalg.norm(pos1)
    h_vec = np.cross(pos1, vel1)
    c_hat = h_vec / np.linalg.norm(h_vec)
    i_hat = np.cross(c_hat, r_hat)

    delta_r_ric = np.array([
        np.dot(delta_r, r_hat),   # Radial
        np.dot(delta_r, i_hat),   # In-track
        np.dot(delta_r, c_hat),   # Cross-track
    ])

    delta_v_ric = np.array([
        np.dot(delta_v, r_hat),
        np.dot(delta_v, i_hat),
        np.dot(delta_v, c_hat),
    ])

    # ---- Encounter Angle ----
    cos_encounter = np.dot(vel1, vel2) / (
        np.linalg.norm(vel1) * np.linalg.norm(vel2)
    )
    encounter_angle_deg = np.degrees(np.arccos(np.clip(cos_encounter, -1, 1)))

    # ---- Covariance Features ----
    cov_combined = cov1 + cov2
    eigenvalues = np.linalg.eigvalsh(cov_combined)
    eigenvalues = np.sort(eigenvalues)[::-1]

    # Mahalanobis distance
    try:
        cov_inv = np.linalg.inv(cov_combined)
        mahalanobis = np.sqrt(delta_r @ cov_inv @ delta_r)
    except np.linalg.LinAlgError:
        mahalanobis = miss_distance_km / np.sqrt(np.trace(cov_combined) / 3)

    # Covariance volume (proxy for overall uncertainty)
    cov_det = np.linalg.det(cov_combined)
    cov_volume = np.sqrt(max(cov_det, 1e-30))

    # ---- Orbital Element Differences ----
    a1, a2 = elements1['a_km'], elements2['a_km']
    e1, e2 = elements1['ecc'], elements2['ecc']
    i1, i2 = elements1['inc_deg'], elements2['inc_deg']
    raan1, raan2 = elements1['raan_deg'], elements2['raan_deg']

    delta_a = abs(a1 - a2)
    delta_e = abs(e1 - e2)
    delta_inc = abs(i1 - i2)
    delta_raan = abs(raan1 - raan2)
    if delta_raan > 180:
        delta_raan = 360 - delta_raan

    # Perigee/Apogee overlap
    R_EARTH = 6378.137
    rp1 = a1 * (1 - e1) - R_EARTH
    ra1 = a1 * (1 + e1) - R_EARTH
    rp2 = a2 * (1 - e2) - R_EARTH
    ra2 = a2 * (1 + e2) - R_EARTH
    altitude_overlap = max(0, min(ra1, ra2) - max(rp1, rp2))

    # ---- B-Plane Features (simplified) ----
    sigma_bplane_sq = 0.5 * (cov_combined[1, 1] + cov_combined[2, 2])
    if sigma_bplane_sq > 1e-20:
        pc_foster_approx = (0.01**2 / (2 * sigma_bplane_sq)) * \
            np.exp(-0.5 * miss_distance_km**2 / sigma_bplane_sq)
    else:
        pc_foster_approx = 1.0

    # ---- Pc Upper Bound (Akella & Alfriend) ----
    hbr = 0.01  # 10 meters in km
    if miss_distance_km > 1e-10:
        pc_upper_bound = hbr**2 / (np.e * miss_distance_km**2)
    else:
        pc_upper_bound = 1.0

    return {
        # Kinematics (6 features)
        "miss_distance_km": miss_distance_km,
        "miss_distance_m": miss_distance_km * 1000,
        "rel_velocity_kms": rel_velocity_kms,
        "encounter_angle_deg": encounter_angle_deg,
        "closing_speed_kms": abs(np.dot(delta_v, delta_r / miss_distance_km)),
        "tangential_velocity_kms": np.sqrt(
            rel_velocity_kms**2 -
            (np.dot(delta_v, delta_r / miss_distance_km))**2
        ),

        # RIC Components (6 features)
        "delta_r_radial_km": delta_r_ric[0],
        "delta_r_intrack_km": delta_r_ric[1],
        "delta_r_crosstrack_km": delta_r_ric[2],
        "delta_v_radial_kms": delta_v_ric[0],
        "delta_v_intrack_kms": delta_v_ric[1],
        "delta_v_crosstrack_kms": delta_v_ric[2],

        # Covariance / Uncertainty (5 features)
        "mahalanobis_distance": mahalanobis,
        "cov_eigenvalue_1": eigenvalues[0],
        "cov_eigenvalue_2": eigenvalues[1],
        "cov_eigenvalue_3": eigenvalues[2],
        "cov_volume": cov_volume,

        # Orbital Element Differences (5 features)
        "delta_sma_km": delta_a,
        "delta_eccentricity": delta_e,
        "delta_inclination_deg": delta_inc,
        "delta_raan_deg": delta_raan,
        "altitude_overlap_km": altitude_overlap,

        # Geometry (3 features)
        "moid_km": moid_km,
        "pc_foster_approx": pc_foster_approx,
        "pc_upper_bound": pc_upper_bound,

        # Derived ratios (3 features)
        "miss_to_sigma_ratio": miss_distance_km / max(
            np.sqrt(np.trace(cov_combined) / 3), 1e-10
        ),
        "hbr_to_miss_ratio": hbr / max(miss_distance_km, 1e-10),
        "energy_ratio": rel_velocity_kms**2 / max(miss_distance_km, 1e-10),
    }
```

### 9.2 Feature Importance Ranking (Expected)

Based on conjunction assessment literature, expected feature importance:

| Rank | Feature | Why |
|:----:|---------|-----|
| 1 | `mahalanobis_distance` | Uncertainty-normalized miss distance — the single most predictive metric |
| 2 | `miss_distance_m` | Raw closest approach distance |
| 3 | `pc_foster_approx` | Analytical collision probability approximation |
| 4 | `cov_volume` | Overall positional uncertainty size |
| 5 | `rel_velocity_kms` | Encounter energy / severity |
| 6 | `encounter_angle_deg` | Head-on vs. overtaking geometry |
| 7 | `altitude_overlap_km` | Radial orbit intersection depth |
| 8 | `delta_r_intrack_km` | In-track separation (most uncertain direction) |
| 9 | `moid_km` | Geometric orbit proximity |
| 10 | `miss_to_sigma_ratio` | Signal-to-noise of the miss distance |

---

## 10. Module 6: Synthetic Data Generation

### 10.1 Why Synthetic Data?

**There is no public dataset of historical conjunction alerts or CDMs.** NASA/ISRO CDM archives are ITAR-restricted or classified. We must generate our own labeled training data by:

1. Running the full physics pipeline (MOID → SGP4 → Chan) on real TLEs
2. Recording the intermediate features (X) and final Pc labels (y)
3. Augmenting with physics-consistent synthetic collision events

### 10.2 Data Generation Strategy

```python
"""
data_generator.py — Synthetic Training Data Generation

Generates labeled conjunction data by running the full physics pipeline
on real TLE pairs and recording features + labels.
"""

import numpy as np
import pandas as pd
from tqdm import tqdm
from typing import List, Tuple

from src.tle_fetcher import fetch_all_groups, parse_json_to_orbital_elements
from src.moid_calculator import compute_moid, radial_overlap_check
from src.sgp4_propagator import propagate_pair
from src.feature_engineer import extract_features
from src.chan_formula import chan_collision_probability, approximate_covariance


def generate_training_data(
    n_pairs: int = 10000,
    pc_threshold: float = 1e-4,
    save_path: str = "data/training/"
) -> pd.DataFrame:
    """
    Generate labeled training data from real TLE catalog.

    Process:
    1. Fetch real TLEs from CelesTrak
    2. Randomly sample pairs
    3. Run full physics pipeline on each pair
    4. Record features (X) and label (y = 1 if Pc > threshold)
    """
    # Fetch and parse catalog
    catalog = fetch_all_groups()
    catalog = parse_json_to_orbital_elements(catalog)

    n_objects = len(catalog)
    records = []

    print(f"Generating {n_pairs} training samples from "
          f"{n_objects} catalog objects...")

    # Sample random pairs
    for _ in tqdm(range(n_pairs), desc="Generating pairs"):
        idx1, idx2 = np.random.choice(n_objects, 2, replace=False)
        obj1 = catalog.iloc[idx1]
        obj2 = catalog.iloc[idx2]

        try:
            # Step 1: Extract orbital elements
            a1 = obj1['SEMI_MAJOR_AXIS_KM']
            e1 = obj1['ECCENTRICITY']
            a2 = obj2['SEMI_MAJOR_AXIS_KM']
            e2 = obj2['ECCENTRICITY']

            # Quick radial check
            if not radial_overlap_check(a1, e1, a2, e2):
                continue

            # Step 2: Compute MOID
            elements1 = (
                a1, e1,
                np.radians(obj1['INCLINATION']),
                np.radians(obj1['RA_OF_ASC_NODE']),
                np.radians(obj1['ARG_OF_PERICENTER'])
            )
            elements2 = (
                a2, e2,
                np.radians(obj2['INCLINATION']),
                np.radians(obj2['RA_OF_ASC_NODE']),
                np.radians(obj2['ARG_OF_PERICENTER'])
            )
            moid = compute_moid(elements1, elements2, n_grid=180)

            if moid > 50:  # Skip if orbits are very far apart
                continue

            # Step 3: SGP4 propagation to find TCA
            from sgp4.api import Satrec, jday
            sat1 = Satrec.twoline2rv(obj1['TLE_LINE1'], obj1['TLE_LINE2'])
            sat2 = Satrec.twoline2rv(obj2['TLE_LINE1'], obj2['TLE_LINE2'])

            jd, fr = jday(2024, 1, 1, 0, 0, 0)
            encounter = propagate_pair(sat1, sat2, jd, fr, window_days=3.0)

            # Step 4: Extract features
            cov1 = approximate_covariance(obj1['BSTAR'],
                                          obj1['PERIGEE_ALT_KM'])
            cov2 = approximate_covariance(obj2['BSTAR'],
                                          obj2['PERIGEE_ALT_KM'])

            elements_dict1 = {
                'a_km': a1, 'ecc': e1,
                'inc_deg': obj1['INCLINATION'],
                'raan_deg': obj1['RA_OF_ASC_NODE']
            }
            elements_dict2 = {
                'a_km': a2, 'ecc': e2,
                'inc_deg': obj2['INCLINATION'],
                'raan_deg': obj2['RA_OF_ASC_NODE']
            }

            features = extract_features(
                encounter['pos1_tca_km'], encounter['vel1_tca_kms'],
                encounter['pos2_tca_km'], encounter['vel2_tca_kms'],
                cov1, cov2,
                elements_dict1, elements_dict2,
                moid
            )

            # Step 5: Compute full Chan Pc (= label)
            pc_result = chan_collision_probability(
                encounter['pos1_tca_km'] - encounter['pos2_tca_km'],
                encounter['vel1_tca_kms'] - encounter['vel2_tca_kms'],
                cov1, cov2, hbr=0.01
            )

            features['pc_chan'] = pc_result['pc']
            features['label'] = 1 if pc_result['pc'] > pc_threshold else 0
            features['norad_id_1'] = obj1['NORAD_CAT_ID']
            features['norad_id_2'] = obj2['NORAD_CAT_ID']

            records.append(features)

        except Exception as e:
            continue

    df = pd.DataFrame(records)

    # Save
    os.makedirs(save_path, exist_ok=True)
    df.to_parquet(f"{save_path}/features.parquet", index=False)

    print(f"\nGenerated {len(df)} training samples")
    print(f"Positive (threat) class: "
          f"{df['label'].sum()} ({df['label'].mean()*100:.2f}%)")
    print(f"Negative (safe) class: "
          f"{(1-df['label']).sum()} ({(1-df['label']).mean()*100:.2f}%)")

    return df


def augment_with_synthetic_threats(
    df: pd.DataFrame,
    n_synthetic: int = 5000
) -> pd.DataFrame:
    """
    Augment training data with physics-consistent synthetic collision threats
    to balance the dataset.

    Uses covariance Cholesky perturbation to generate realistic near-miss
    scenarios from existing safe pairs.
    """
    synthetic_rows = []
    safe_pairs = df[df['label'] == 0]

    for _ in range(n_synthetic):
        base = safe_pairs.sample(1).iloc[0].to_dict()

        # Shrink miss distance to create a threat
        base['miss_distance_m'] = np.random.exponential(scale=25.0)
        base['miss_distance_km'] = base['miss_distance_m'] / 1000.0

        # Adjust dependent features consistently
        base['mahalanobis_distance'] = base['miss_distance_m'] / max(
            np.sqrt(base['cov_eigenvalue_1']), 1.0) * 0.001

        # Recompute Foster Pc approximation
        sigma_sq = 0.5 * (base['cov_eigenvalue_1'] + base['cov_eigenvalue_2'])
        if sigma_sq > 1e-20:
            base['pc_foster_approx'] = (0.01**2 / (2 * sigma_sq)) * \
                np.exp(-0.5 * base['miss_distance_km']**2 / sigma_sq)

        base['label'] = 1
        synthetic_rows.append(base)

    synthetic_df = pd.DataFrame(synthetic_rows)
    combined = pd.concat([df, synthetic_df], ignore_index=True)

    print(f"Augmented dataset: {len(combined)} total")
    print(f"Positive class: {combined['label'].sum()} "
          f"({combined['label'].mean()*100:.1f}%)")

    return combined
```

### 10.3 Expected Class Distribution

| Stage | Positive (Threat) | Negative (Safe) | Ratio |
|-------|------------------:|----------------:|------:|
| Raw from pipeline | ~50 | ~9,950 | 1:199 |
| After synthetic augmentation | ~5,050 | ~9,950 | ~1:2 |
| After downsampling negatives | ~5,050 | ~5,050 | 1:1 |

**Note:** Even with balanced training data, the model will see the true skewed distribution at inference time. This is why threshold tuning (Section 13) is critical.

---

## 11. Module 7: ML Pre-Filter (XGBoost/LightGBM)

### 11.1 Model Selection: LightGBM vs XGBoost

| Dimension | LightGBM | XGBoost |
|-----------|----------|---------|
| Tree Growth | **Leaf-wise** (best-first) | Depth-wise (level-wise) |
| Split Finding | GOSS + EFB (gradient sampling) | Histogram / Exact greedy |
| Inference Latency | **~5–15 µs/sample** | ~15–35 µs/sample |
| Imbalance Handling | `is_unbalance=True` auto-weights | `scale_pos_weight` manual |
| Memory | **Lower** (integer-binned histograms) | Moderate |
| Training Speed | **2-3x faster** | Baseline |

**Primary model: LightGBM.** Train XGBoost as a comparison baseline.

### 11.2 Asymmetric Loss Function

Standard binary cross-entropy treats FP and FN equally. For safety-critical screening, we need $c_{FN} \gg c_{FP}$:

$$\mathcal{L}_{asym}(y, p) = -\left[c_{FN} \cdot y \ln(p) + c_{FP} \cdot (1-y) \ln(1-p)\right]$$

**Gradient:**
$$g_i = c_{FP}(1-y_i)p_i - c_{FN} y_i(1-p_i)$$

**Hessian:**
$$h_i = \left[c_{FP}(1-y_i) + c_{FN}y_i\right] p_i(1-p_i)$$

### 11.3 Full Training Implementation: `ml_model.py`

```python
"""
ml_model.py — ML Pre-Filter Training & Inference

Trains LightGBM and XGBoost models with asymmetric loss functions
optimized for ultra-high recall in conjunction screening.
"""

import numpy as np
import pandas as pd
import lightgbm as lgb
import xgboost as xgb
import json
import joblib
from pathlib import Path
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.metrics import (
    precision_recall_curve, classification_report,
    fbeta_score, average_precision_score, confusion_matrix
)
from typing import Tuple, Dict

# Feature columns (must match feature_engineer.py output)
FEATURE_COLUMNS = [
    "miss_distance_m",
    "rel_velocity_kms",
    "encounter_angle_deg",
    "closing_speed_kms",
    "tangential_velocity_kms",
    "delta_r_radial_km",
    "delta_r_intrack_km",
    "delta_r_crosstrack_km",
    "delta_v_radial_kms",
    "delta_v_intrack_kms",
    "delta_v_crosstrack_kms",
    "mahalanobis_distance",
    "cov_eigenvalue_1",
    "cov_eigenvalue_2",
    "cov_eigenvalue_3",
    "cov_volume",
    "delta_sma_km",
    "delta_eccentricity",
    "delta_inclination_deg",
    "delta_raan_deg",
    "altitude_overlap_km",
    "moid_km",
    "pc_foster_approx",
    "pc_upper_bound",
    "miss_to_sigma_ratio",
    "hbr_to_miss_ratio",
    "energy_ratio",
]

LABEL_COLUMN = "label"
MODEL_DIR = Path("models")


# ============================================================
# LightGBM Training
# ============================================================

def train_lightgbm(
    df: pd.DataFrame,
    target_recall: float = 0.999,
    c_fn: float = 50.0,
    c_fp: float = 1.0,
) -> Tuple[lgb.Booster, float]:
    """
    Train LightGBM with asymmetric loss for conjunction screening.

    Returns:
        (trained_model, optimal_threshold)
    """
    X = df[FEATURE_COLUMNS].values
    y = df[LABEL_COLUMN].values

    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )

    # LightGBM datasets
    dtrain = lgb.Dataset(X_train, label=y_train,
                         feature_name=FEATURE_COLUMNS)
    dval = lgb.Dataset(X_val, label=y_val, reference=dtrain,
                       feature_name=FEATURE_COLUMNS)

    # Custom asymmetric objective
    def asymmetric_objective(preds, train_data):
        labels = train_data.get_label()
        probs = 1.0 / (1.0 + np.exp(-preds))
        probs = np.clip(probs, 1e-15, 1.0 - 1e-15)
        grad = c_fp * (1.0 - labels) * probs - c_fn * labels * (1.0 - probs)
        hess = (c_fp * (1.0 - labels) + c_fn * labels) * probs * (1.0 - probs)
        return grad, hess

    # Custom evaluation metric: asymmetric cost
    def asymmetric_eval(preds, train_data):
        labels = train_data.get_label()
        probs = 1.0 / (1.0 + np.exp(-preds))
        preds_bin = (probs >= 0.5).astype(int)
        fn = np.sum((labels == 1) & (preds_bin == 0))
        fp = np.sum((labels == 0) & (preds_bin == 1))
        cost = c_fn * fn + c_fp * fp
        return 'asym_cost', cost, False  # lower is better

    params = {
        'num_leaves': 63,
        'max_depth': 8,
        'learning_rate': 0.05,
        'min_child_samples': 20,
        'subsample': 0.8,
        'colsample_bytree': 0.8,
        'reg_alpha': 0.1,
        'reg_lambda': 1.0,
        'verbose': -1,
        'n_jobs': -1,
        'seed': 42,
    }

    # Train
    model = lgb.train(
        params=params,
        train_set=dtrain,
        num_boost_round=500,
        valid_sets=[dtrain, dval],
        valid_names=['train', 'val'],
        fobj=asymmetric_objective,
        feval=asymmetric_eval,
        callbacks=[
            lgb.early_stopping(30),
            lgb.log_evaluation(50),
        ]
    )

    # Predict probabilities on validation set
    raw_preds = model.predict(X_val)
    val_probs = 1.0 / (1.0 + np.exp(-raw_preds))

    # Find optimal threshold for target recall
    optimal_threshold = find_optimal_threshold(
        y_val, val_probs, target_recall
    )

    # Print evaluation
    print_evaluation_report(y_val, val_probs, optimal_threshold)

    # Save model and threshold
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    model.save_model(str(MODEL_DIR / "stardust_lgbm.json"))

    with open(MODEL_DIR / "threshold.json", 'w') as f:
        json.dump({
            "optimal_threshold": optimal_threshold,
            "target_recall": target_recall,
            "c_fn": c_fn,
            "c_fp": c_fp,
        }, f, indent=2)

    with open(MODEL_DIR / "feature_names.json", 'w') as f:
        json.dump(FEATURE_COLUMNS, f, indent=2)

    return model, optimal_threshold


# ============================================================
# XGBoost Training (Comparison Baseline)
# ============================================================

def train_xgboost(
    df: pd.DataFrame,
    target_recall: float = 0.999,
    c_fn: float = 50.0,
    c_fp: float = 1.0,
) -> Tuple[xgb.Booster, float]:
    """Train XGBoost with asymmetric loss as comparison baseline."""

    X = df[FEATURE_COLUMNS].values
    y = df[LABEL_COLUMN].values

    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )

    dtrain = xgb.DMatrix(X_train, label=y_train,
                         feature_names=FEATURE_COLUMNS)
    dval = xgb.DMatrix(X_val, label=y_val,
                       feature_names=FEATURE_COLUMNS)

    def xgb_asymmetric_obj(preds, dtrain):
        labels = dtrain.get_label()
        probs = 1.0 / (1.0 + np.exp(-preds))
        probs = np.clip(probs, 1e-15, 1.0 - 1e-15)
        grad = c_fp * (1.0 - labels) * probs - c_fn * labels * (1.0 - probs)
        hess = (c_fp * (1.0 - labels) + c_fn * labels) * probs * (1.0 - probs)
        return grad, hess

    params = {
        'max_depth': 6,
        'learning_rate': 0.05,
        'max_delta_step': 1.0,
        'subsample': 0.8,
        'colsample_bytree': 0.8,
        'tree_method': 'hist',
        'eval_metric': 'aucpr',
    }

    model = xgb.train(
        params=params,
        dtrain=dtrain,
        num_boost_round=500,
        evals=[(dtrain, 'train'), (dval, 'val')],
        obj=xgb_asymmetric_obj,
        early_stopping_rounds=30,
        verbose_eval=50,
    )

    raw_preds = model.predict(dval, output_margin=True)
    val_probs = 1.0 / (1.0 + np.exp(-raw_preds))

    optimal_threshold = find_optimal_threshold(
        y_val, val_probs, target_recall
    )

    model.save_model(str(MODEL_DIR / "stardust_xgb.json"))
    return model, optimal_threshold


# ============================================================
# Threshold Optimization (Neyman-Pearson Criterion)
# ============================================================

def find_optimal_threshold(
    y_true: np.ndarray,
    y_probs: np.ndarray,
    target_recall: float = 0.999
) -> float:
    """
    Find the highest threshold that achieves >= target_recall.
    This maximizes precision subject to the recall constraint
    (Neyman-Pearson criterion).
    """
    precisions, recalls, thresholds = precision_recall_curve(y_true, y_probs)

    # Find all thresholds where recall >= target
    valid = np.where(recalls[:-1] >= target_recall)[0]

    if len(valid) > 0:
        # Among valid thresholds, pick the one with highest precision
        best_idx = valid[np.argmax(precisions[valid])]
        return float(thresholds[best_idx])
    else:
        # Fallback: use lowest possible threshold
        print(f"WARNING: Could not achieve {target_recall*100}% recall. "
              f"Using minimum threshold.")
        return float(thresholds[0])


def print_evaluation_report(
    y_true: np.ndarray,
    y_probs: np.ndarray,
    threshold: float
):
    """Print comprehensive evaluation metrics."""
    y_pred = (y_probs >= threshold).astype(int)

    print("\n" + "=" * 60)
    print("STARDUST ML MODEL EVALUATION REPORT")
    print("=" * 60)
    print(f"Decision Threshold: {threshold:.6f}")
    print(f"\n{classification_report(y_true, y_pred, "
          f"target_names=['Safe', 'Threat'])}")

    cm = confusion_matrix(y_true, y_pred)
    tn, fp, fn, tp = cm.ravel()

    print(f"Confusion Matrix:")
    print(f"  True Positives  (threats caught):  {tp}")
    print(f"  False Positives (false alarms):    {fp}")
    print(f"  True Negatives  (safe confirmed):  {tn}")
    print(f"  False Negatives (MISSED THREATS):  {fn}")

    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    f2 = fbeta_score(y_true, y_pred, beta=2)
    f5 = fbeta_score(y_true, y_pred, beta=5)
    pr_auc = average_precision_score(y_true, y_probs)

    print(f"\nKey Metrics:")
    print(f"  Recall (sensitivity):    {recall*100:.3f}%")
    print(f"  Precision:               {precision*100:.3f}%")
    print(f"  F2 Score (2x recall):    {f2:.4f}")
    print(f"  F5 Score (5x recall):    {f5:.4f}")
    print(f"  PR-AUC:                  {pr_auc:.4f}")

    if fn > 0:
        print(f"\n  ⚠️  WARNING: {fn} THREATS MISSED!")
    else:
        print(f"\n  ✅ ZERO MISSED THREATS — all positives caught")
    print("=" * 60)


# ============================================================
# Inference
# ============================================================

def load_model_and_predict(
    features: np.ndarray,
    model_path: str = "models/stardust_lgbm.json",
    threshold_path: str = "models/threshold.json"
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Load trained model and predict on new features.

    Returns:
        (probabilities, binary_predictions)
    """
    model = lgb.Booster(model_file=model_path)

    with open(threshold_path, 'r') as f:
        config = json.load(f)
    threshold = config['optimal_threshold']

    raw_preds = model.predict(features)
    probs = 1.0 / (1.0 + np.exp(-raw_preds))
    predictions = (probs >= threshold).astype(int)

    return probs, predictions
```

### 11.4 Hyperparameter Guide

| Parameter | LightGBM | XGBoost | Purpose |
|-----------|----------|---------|---------|
| `num_leaves` / `max_depth` | 63 / 8 | — / 6 | Tree complexity |
| `learning_rate` | 0.05 | 0.05 | Step size (lower = more trees needed) |
| `n_estimators` | 500 (early stop) | 500 (early stop) | Number of boosting rounds |
| `subsample` | 0.8 | 0.8 | Row sampling ratio |
| `colsample_bytree` | 0.8 | 0.8 | Feature sampling ratio |
| `max_delta_step` | — | **1.0** | Prevents explosive leaf updates (critical for XGB with imbalanced data) |
| `is_unbalance` | True | — | LightGBM auto-handles class weights |
| `scale_pos_weight` | — | `count(neg)/count(pos)` | XGBoost class weight |
| `reg_alpha` | 0.1 | — | L1 regularization |
| `reg_lambda` | 1.0 | — | L2 regularization |
| `min_child_samples` | 20 | — | Minimum data in leaf |

---

## 12. Module 8: Streamlit Triage Dashboard

### 12.1 Dashboard Layout Design

```
┌──────────────────────────────────────────────────────────────────────────┐
│  🛰️ STARDUST — Real-Time Orbital Conjunction Screening & Triage        │
├──────────────────┬───────────────────────────────────────────────────────┤
│ SIDEBAR          │  [Metric]          [Metric]        [Metric]  [Metric]│
│                  │  Active CDMs: 250  Flagged: 4     Min Miss: 32.4m  │
│ Screening        │  Next TCA: 1.2h                                     │
│ Controls         │─────────────────────────────────────────────────────│
│                  │                                                     │
│ ◎ ML Threshold   │  ┌─ Screening Funnel ──┐  ┌─ 3D Encounter ────────┐│
│   slider (τ)     │  │                      │  │                        ││
│                  │  │ 150,000 → 3,200 →    │  │    Primary ●           ││
│ ◎ Max TCA (hrs)  │  │   250 → 4 → 1        │  │        ╲  Covariance  ││
│                  │  │                      │  │         ╲ Ellipsoid    ││
│ ◎ Primary Asset  │  │  [Plotly Funnel]     │  │    Debris ●            ││
│   multiselect    │  │                      │  │                        ││
│                  │  └──────────────────────┘  └────────────────────────┘│
│ ◎ Confidence     │─────────────────────────────────────────────────────│
│   filter         │                                                     │
│                  │  ┌─ Pipeline Speed Comparison ──────────────────────┐│
│                  │  │ Traditional: ████████████████████ 45 min         ││
│                  │  │ STARDUST:    ████ 8 min                          ││
│                  │  └─────────────────────────────────────────────────┘│
│                  │─────────────────────────────────────────────────────│
│                  │                                                     │
│                  │  ┌─ Active Conjunction Data Messages (CDMs) ────────┐│
│                  │  │ [Interactive sortable/filterable table]          ││
│                  │  │  Event ID | Primary | Debris | Miss Dist | Pc   ││
│                  │  │  CDM-001  | ISS     | DEB-x  | 32.4m    | 4e-3 ││
│                  │  └─────────────────────────────────────────────────┘│
└──────────────────┴───────────────────────────────────────────────────────┘
```

### 12.2 Implementation: `dashboard/app.py`

```python
"""
dashboard/app.py — STARDUST Triage Dashboard

Streamlit-based real-time conjunction screening visualization.
Run with: streamlit run dashboard/app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import json
from pathlib import Path

# ---- Page Configuration ----
st.set_page_config(
    page_title="STARDUST — Conjunction Screening",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---- Load Model Config ----
@st.cache_resource
def load_model_config():
    threshold_path = Path("models/threshold.json")
    if threshold_path.exists():
        with open(threshold_path) as f:
            return json.load(f)
    return {"optimal_threshold": 0.08, "target_recall": 0.999}


config = load_model_config()


# ---- Mock Data (replace with pipeline output in production) ----
@st.cache_data(ttl=60)
def load_screening_results():
    """Load or simulate screening results."""
    np.random.seed(42)
    n = 250

    df = pd.DataFrame({
        'event_id': [f"CDM-2026-{1000+i}" for i in range(n)],
        'primary': np.random.choice(
            ['CARTOSAT-3', 'OCEANSAT-3', 'EOS-06', 'RISAT-2BR1',
             'RESOURCESAT-2A'], n),
        'secondary': [f"DEB-{np.random.randint(10000,99999)}"
                      for _ in range(n)],
        'tca_hours': np.random.uniform(1.2, 72.0, n),
        'miss_distance_m': np.random.exponential(1200, n) + 15,
        'rel_velocity_kms': np.random.uniform(1.2, 14.8, n),
        'pc_chan': np.random.uniform(1e-9, 1e-3, n),
        'ml_score': np.random.beta(0.5, 5.0, n),
        'moid_km': np.random.uniform(0.1, 10.0, n),
    })

    # Inject 2 critical events
    df.loc[0] = ['CDM-2026-CRIT-1', 'CARTOSAT-3', 'DEB-42857', 4.2,
                 32.4, 12.3, 4.2e-3, 0.985, 0.8]
    df.loc[1] = ['CDM-2026-CRIT-2', 'EOS-06', 'DEB-51923', 8.1,
                 18.1, 7.6, 8.9e-3, 0.994, 0.3]

    return df


df = load_screening_results()


# ---- Sidebar Controls ----
st.sidebar.title("🛡️ Screening Controls")
st.sidebar.markdown("---")

threshold = st.sidebar.slider(
    "ML Decision Threshold (τ)",
    min_value=0.01, max_value=0.50,
    value=float(config['optimal_threshold']),
    step=0.01,
    help="Optimized via Neyman-Pearson criterion for ≥99.9% recall"
)

max_tca = st.sidebar.slider(
    "Max Time to TCA (Hours)",
    min_value=6, max_value=72, value=48
)

primary_filter = st.sidebar.multiselect(
    "Primary Asset",
    options=sorted(df['primary'].unique()),
    default=sorted(df['primary'].unique())
)

st.sidebar.markdown("---")
st.sidebar.markdown("**STARDUST v1.0** | Team DEFCON")
st.sidebar.markdown("SIH 2026 — Space Technology")

# ---- Filter ----
filtered = df[
    (df['tca_hours'] <= max_tca) &
    (df['primary'].isin(primary_filter))
].copy()
filtered['flagged'] = filtered['ml_score'] >= threshold


# ---- Header ----
st.title("🛰️ STARDUST — Real-Time Conjunction Screening & Triage")
st.caption("ML-Accelerated Pre-Filter for ISRO Space Situational Awareness")


# ---- Top Metrics Bar ----
c1, c2, c3, c4 = st.columns(4)
n_flagged = filtered['flagged'].sum()
c1.metric("Active Conjunctions", len(filtered), delta="-12 vs last epoch")
c2.metric("ML Flagged Threats", n_flagged,
          delta=f"+{n_flagged}", delta_color="inverse")
c3.metric("Min Miss Distance", f"{filtered['miss_distance_m'].min():.1f} m")
c4.metric("Next TCA", f"{filtered['tca_hours'].min():.1f} h")

st.divider()


# ---- Middle Row: Funnel + 3D Encounter ----
left, right = st.columns([1, 1.2])

with left:
    st.subheader("📊 Screening Funnel")
    stages = [
        "Total Catalog Pairs",
        "MOID Filter (< 10 km)",
        "SGP4 Propagation Window",
        f"ML Threshold (τ = {threshold:.2f})",
        "Critical (Pc > 1e-4)"
    ]
    values = [
        150000, 3200, 250, int(n_flagged),
        max(1, int(n_flagged * 0.25))
    ]
    colors = ["#1f77b4", "#aec7e8", "#ffbb78", "#ff7f0e", "#d62728"]

    fig_funnel = go.Figure(go.Funnel(
        y=stages, x=values,
        textinfo="value+percent previous",
        marker={"color": colors}
    ))
    fig_funnel.update_layout(
        margin=dict(l=20, r=20, t=10, b=10), height=380
    )
    st.plotly_chart(fig_funnel, use_container_width=True)

with right:
    st.subheader("🌐 3D Encounter Geometry")
    closest = filtered.sort_values('miss_distance_m').iloc[0]

    # Covariance ellipsoid (3σ)
    u = np.linspace(0, 2*np.pi, 20)
    v = np.linspace(0, np.pi, 20)
    rx, ry, rz = 80, 300, 120
    x_e = rx * np.outer(np.cos(u), np.sin(v))
    y_e = ry * np.outer(np.sin(u), np.sin(v))
    z_e = rz * np.outer(np.ones(np.size(u)), np.cos(v))

    fig3d = go.Figure()
    fig3d.add_trace(go.Surface(
        x=x_e, y=y_e, z=z_e, opacity=0.25,
        colorscale='Reds', showscale=False, name="3σ Covariance"
    ))
    fig3d.add_trace(go.Scatter3d(
        x=[0], y=[0], z=[0], mode='markers+text',
        marker=dict(size=8, color='blue'),
        text=[closest['primary']], name="Primary"
    ))
    dm = closest['miss_distance_m']
    fig3d.add_trace(go.Scatter3d(
        x=[dm*0.3], y=[dm*0.8], z=[dm*0.2], mode='markers+text',
        marker=dict(size=6, color='red'),
        text=[closest['secondary']], name="Debris"
    ))
    fig3d.update_layout(
        scene=dict(
            xaxis_title="Radial (m)",
            yaxis_title="In-Track (m)",
            zaxis_title="Cross-Track (m)"
        ),
        margin=dict(l=0, r=0, t=10, b=10), height=380
    )
    st.plotly_chart(fig3d, use_container_width=True)


# ---- Speed Comparison ----
st.subheader("⚡ Pipeline Speed Comparison")
speed_col1, speed_col2 = st.columns(2)
with speed_col1:
    fig_speed = go.Figure()
    fig_speed.add_trace(go.Bar(
        y=["Traditional Pipeline", "STARDUST Pipeline"],
        x=[45, 8],
        orientation='h',
        marker_color=['#ff6b6b', '#51cf66'],
        text=["45 min", "8 min"],
        textposition='auto'
    ))
    fig_speed.update_layout(
        xaxis_title="Processing Time (minutes)",
        margin=dict(l=20, r=20, t=10, b=10), height=200
    )
    st.plotly_chart(fig_speed, use_container_width=True)

with speed_col2:
    st.metric("Speedup Factor", "5.6x", delta="82% compute reduction")
    st.metric("Pairs Screened by ML", "250 → 4", delta="98.4% reduction")


# ---- CDM Table ----
st.divider()
st.subheader("📋 Active Conjunction Data Messages")

st.dataframe(
    filtered.sort_values('ml_score', ascending=False),
    column_config={
        "ml_score": st.column_config.ProgressColumn(
            "ML Threat Score", format="%.3f",
            min_value=0.0, max_value=1.0
        ),
        "pc_chan": st.column_config.NumberColumn(
            "Chan Pc", format="%.2e"
        ),
        "miss_distance_m": st.column_config.NumberColumn(
            "Miss Distance", format="%.1f m"
        ),
        "flagged": st.column_config.CheckboxColumn("⚠️ Action Required"),
    },
    use_container_width=True,
    hide_index=True,
)
```

### 12.3 Running the Dashboard

```bash
# From project root
streamlit run dashboard/app.py --server.port 8501

# Or with custom config
streamlit run dashboard/app.py \
    --server.port 8501 \
    --theme.primaryColor "#ff4b4b" \
    --theme.backgroundColor "#0e1117"
```

---

## 13. Evaluation Metrics for Safety-Critical ML

### 13.1 Why Standard Metrics Fail

**Accuracy Paradox:** With 0.02% positive rate, a model that predicts "safe" for everything achieves 99.98% accuracy — while missing every collision.

**ROC-AUC Distortion:** With 100,000 true negatives, even 1,000 false alarms give FPR = 1%. ROC looks near-perfect while precision is terrible.

### 13.2 Correct Metrics

| Metric | Formula | Target |
|--------|---------|--------|
| **Recall** | $\frac{TP}{TP + FN}$ | **≥ 99.9%** |
| **Precision** | $\frac{TP}{TP + FP}$ | As high as possible (secondary) |
| **PR-AUC** | Area under Precision-Recall curve | > 0.9 |
| **F₂ Score** | $(1+4)\frac{P \cdot R}{4P + R}$ | > 0.95 (2x recall weight) |
| **F₅ Score** | $(1+25)\frac{P \cdot R}{25P + R}$ | > 0.95 (5x recall weight) |

### 13.3 Decision Threshold Strategy

**Neyman-Pearson Criterion:** Fix Recall ≥ 99.9%, then maximize Precision.

```
Find τ* = argmax_{τ} Precision(τ)  subject to  Recall(τ) ≥ 0.999
```

**Bayes Cost Minimization:**

$$\tau^* = \frac{C_{FP}}{C_{FN} + C_{FP}}$$

With $C_{FN}$ = \$100M (satellite loss) and $C_{FP}$ = \$10K (maneuver fuel):

$$\tau^* = \frac{10{,}000}{100{,}000{,}000 + 10{,}000} \approx 10^{-4}$$

This extremely low threshold means: **flag everything that has even a tiny signal**.

---

## 14. 36-Hour Hackathon Execution Timeline

### Phase 1: Physics Baseline & Data Engineering (Hours 0–8)

| Hour | Task | Owner | Output |
|:----:|------|:-----:|--------|
| 0-1 | Environment setup, `pip install`, project scaffold | All | `requirements.txt`, directory structure |
| 1-3 | `tle_fetcher.py` — CelesTrak API client | Dev A | Working TLE fetch + parse |
| 1-3 | `sgp4_propagator.py` — propagation + TCA finder | Dev B | Working propagation |
| 3-5 | `moid_calculator.py` — coarse filter | Dev A | MOID screening pipeline |
| 3-5 | `chan_formula.py` — Pc calculation | Dev B | Working Pc calculator |
| 5-7 | `feature_engineer.py` — integrate all modules | Dev A | End-to-end physics pipeline |
| 7-8 | Test full pipeline on 100 TLE pairs | Dev B | Verified baseline |

**Milestone:** Full physics pipeline runs (slowly) and produces labeled data.

### Phase 2: Synthetic Data Generation (Hours 8–12)

| Hour | Task | Owner | Output |
|:----:|------|:-----:|--------|
| 8-10 | `data_generator.py` — run pipeline on 10K pairs | Dev A | Raw features + labels |
| 10-12 | `augment_with_synthetic_threats()` | Dev B | Balanced training set |

**Milestone:** ~15K labeled training samples.

### Phase 3: ML Model Training & Tuning (Hours 12–20)

| Hour | Task | Owner | Output |
|:----:|------|:-----:|--------|
| 12-14 | LightGBM training with asymmetric loss | Dev A | Trained model v1 |
| 14-16 | XGBoost baseline training | Dev B | Comparison model |
| 16-18 | Threshold optimization (Neyman-Pearson) | Dev A | `threshold.json` |
| 18-20 | Feature importance analysis, model evaluation report | Dev B | Evaluation report |

**Milestone:** Trained model achieving ≥99.9% recall.

### Phase 4: Integration & Benchmarking (Hours 20–28)

| Hour | Task | Owner | Output |
|:----:|------|:-----:|--------|
| 20-23 | `main.py` — full pipeline orchestrator | Dev A | Integrated pipeline |
| 23-26 | Speed benchmarking (with vs without ML) | Dev B | Benchmark results |
| 26-28 | Bug fixes, edge case handling | All | Stable system |

**Milestone:** Demonstrated 5-10x speedup.

### Phase 5: Dashboard & Presentation (Hours 28–36)

| Hour | Task | Owner | Output |
|:----:|------|:-----:|--------|
| 28-32 | `dashboard/app.py` — full Streamlit dashboard | Dev A | Working dashboard |
| 32-34 | Presentation deck preparation | Dev B | Slide deck |
| 34-36 | Demo rehearsal, final polish | All | Presentation-ready |

**Milestone:** Live demo showing funnel from 150K → handful of threats.

---

## 15. Risk Register & Mitigations

| # | Risk | Severity | Likelihood | Mitigation |
|:-:|------|:--------:|:----------:|------------|
| 1 | **ML model misses a real threat (False Negative)** | CRITICAL | Low (after tuning) | Ultra-high recall target (99.9%), asymmetric loss ($c_{FN}=50 \times c_{FP}$), Neyman-Pearson threshold, position as decision-support not autonomous |
| 2 | **No public historical conjunction data** | HIGH | Certain | Generate synthetic labeled data from real TLEs + full physics pipeline |
| 3 | **TLE-derived covariance is unrealistic** | MEDIUM | High | Use literature-based uncertainty models scaled by BSTAR and altitude; explicitly acknowledge limitation |
| 4 | **CelesTrak API downtime during demo** | MEDIUM | Low | Pre-cache TLE data locally; design for offline operation |
| 5 | **MOID computation too slow for 30K+ objects** | MEDIUM | Medium | Pre-filter with perigee/apogee overlap (O(1)); limit demo to subset (e.g., 5K objects) |
| 6 | **Judges perceive as "invented" problem** | MEDIUM | Low | Cite exact Lok Sabha reply data (150K alerts, 29 CAMs), DFSM 2030 target, NETRA project |
| 7 | **SGP4 accuracy degrades beyond 7 days** | LOW | Certain | Hard-limit propagation to 7-day window; document limitation |

---

## 16. Presentation & Judging Strategy

### 16.1 Key Narrative Points

1. **Open with the ISRO data:** "150,000 alerts. 29 actual manoeuvres. That's a 99.98% false alarm rate."
2. **Frame the problem clearly:** "The bottleneck isn't detecting threats — it's drowning in non-threats."
3. **Position correctly:** "STARDUST is a triage assistant. It doesn't replace orbital mechanics. It tells analysts which 500 out of 150,000 alerts deserve their attention."
4. **Show the funnel:** Live demo of 150K → handful of critical alerts
5. **Connect to India's goals:** DFSM 2030, NETRA, protecting 20 active LEO satellites

### 16.2 Demo Flow (5 minutes)

1. Show CelesTrak data loading (30s)
2. Show MOID filter reducing pairs (30s)
3. Show ML model flagging threats (30s)
4. Show Chan formula results on flagged pairs (30s)
5. Live Streamlit dashboard walkthrough (2 min)
6. Speed comparison chart (30s)

### 16.3 Questions to Prepare For

| Question | Answer |
|----------|--------|
| "What if the ML model is wrong?" | "The model is a pre-filter, not a final arbiter. All flagged pairs still go through rigorous physics-based Pc calculation. The model's job is only to reduce what gets screened, not to make final decisions." |
| "Why not use deep learning?" | "Tabular data with 28 features and interpretable physics. Gradient-boosted trees (LightGBM) are state-of-the-art for this regime. We need microsecond inference, not GPU batches." |
| "Where's the real data?" | "CDM archives are ITAR-restricted. We use real current TLEs from CelesTrak and generate ground-truth labels by running the full validated physics pipeline. Our labels are as real as the physics allows." |
| "How do you handle covariance?" | "TLEs don't include covariance. We approximate using literature-based models scaled by BSTAR drag and altitude. For production, ISRO's CDMs would provide real covariance matrices." |

---

## 17. Key Constants & Thresholds Reference

### 17.1 Physical Constants

```python
# config.py — Project Constants

# Earth parameters
MU_EARTH = 398600.4418        # Gravitational parameter (km³/s²)
R_EARTH = 6378.137            # Equatorial radius (km)
J2 = 1.08263e-3               # J2 oblateness coefficient
OMEGA_EARTH = 7.2921159e-5    # Earth rotation rate (rad/s)

# Screening thresholds
MOID_THRESHOLD_KM = 10.0      # Max MOID for pair to survive coarse filter
PROPAGATION_WINDOW_DAYS = 7.0  # SGP4 propagation window
PROPAGATION_STEP_SEC = 60.0    # Time step for coarse TCA search

# Collision probability thresholds
PC_RED_THRESHOLD = 1e-4        # Collision probability: CAM required
PC_YELLOW_THRESHOLD = 1e-5     # Elevated monitoring
PC_GREEN_THRESHOLD = 1e-7      # Routine tracking

# Hard-body radius
HBR_DEFAULT_KM = 0.010         # 10 meters (typical for LEO satellites)
HBR_ISS_KM = 0.050             # 50 meters (ISS is much larger)

# ML model parameters
ML_TARGET_RECALL = 0.999       # Neyman-Pearson recall constraint
ML_C_FN = 50.0                 # False negative cost multiplier
ML_C_FP = 1.0                  # False positive cost multiplier
ML_DEFAULT_THRESHOLD = 0.08    # Default decision threshold (tuned)

# CelesTrak
CELESTRAK_BASE_URL = "https://celestrak.org/NORAD/elements/gp.php"
CELESTRAK_CACHE_HOURS = 2      # Don't poll more often than this
```

### 17.2 Typical LEO Encounter Parameters

| Parameter | Typical Range | Units |
|-----------|:------------:|:-----:|
| Relative velocity | 1–15 | km/s |
| Miss distance (alert) | 0.01–100 | km |
| Miss distance (threat) | 0.001–0.1 | km |
| TCA window | 2–168 | hours |
| Combined covariance (radial) | 0.005–0.5 | km |
| Combined covariance (in-track) | 0.05–5.0 | km |
| Combined covariance (cross-track) | 0.01–1.0 | km |
| Hard-body radius | 1–50 | meters |

---

## 18. References & Papers

### 18.1 Core Algorithms

1. **SGP4:** Vallado, D.A., Crawford, P., Hujsak, R., Kelso, T.S. (2006). *Revisiting Spacetrack Report #3*. AIAA/AAS Astrodynamics Specialist Conference.
2. **Chan Pc Formula:** Chan, F.K. (1997). *Spacecraft Collision Probability*. The Aerospace Press.
3. **Foster Pc Method:** Foster, J.L., Estes, H.S. (1992). *A parametric analysis of orbital debris collision probability and maneuver rate for space vehicles*. NASA JSC-25898.
4. **MOID:** Gronchi, G.F. (2005). *An algebraic method to compute the critical points of the distance function between two Keplerian orbits*. Celestial Mechanics and Dynamical Astronomy.
5. **Baluev & Mikryukov MOID:** Baluev, R.V., Mikryukov, D.V. (2018). *Fast error-controlling MOID computation for confocal elliptic orbits*. Astronomy & Computing.

### 18.2 ML for Space Safety

6. **XGBoost:** Chen, T., Guestrin, C. (2016). *XGBoost: A Scalable Tree Boosting System*. KDD '16.
7. **LightGBM:** Ke, G. et al. (2017). *LightGBM: A Highly Efficient Gradient Boosting Decision Tree*. NeurIPS '17.
8. **Imbalanced Learning:** He, H., Garcia, E.A. (2009). *Learning from Imbalanced Data*. IEEE TKDE.
9. **Neyman-Pearson:** Tong, X. et al. (2018). *Neyman-Pearson classification: parametrics and sample size requirement*. JMLR.

### 18.3 ISRO & Policy

10. **ISRO SSA:** PIB India (August 2026). *Lok Sabha Reply on Space Debris and Collision Avoidance*. Ministry of Science & Technology.
11. **DFSM 2030:** ISRO (2024). *Debris-Free Space Mission Initiative*. isro.gov.in.
12. **NETRA:** ISRO (2024). *Network for Space Object Tracking and Analysis*. isro.gov.in.

---

> **This document is the complete technical reference for Project STARDUST. Every algorithm, formula, API endpoint, library, feature, threshold, and implementation detail needed to build the ML-accelerated conjunction screening triage engine is contained here. Use it as the single source of truth for development.**
