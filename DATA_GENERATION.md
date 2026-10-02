# Indian Army Predictive Logistics & Forward Supply Chain (Phase 1)
## Data Architecture, Environmental Acquisition & Synthetic Simulation Foundation

> **Mandatory Disclaimer**: Operational military logistics data is NOT used. This prototype is a **public-environment-conditioned synthetic logistics simulation** combining publicly available civilian environmental, meteorological, and geographical information with a synthetic forward logistics simulation. Logistics nodes (`LAD-A01`–`LAD-A05`, `SIK-B01`–`SIK-B05`, `RAJ-C01`–`RAJ-C05`) are fictional study points mapped to public civilian coordinates. All synthetic logistics variables are modelled using explicit prototype modelling assumptions and are not presented as actual Indian Army operational figures.

---

## 1. Project Objective & Context
* **Hackathon**: Smart India Hackathon 2026
* **Problem Statement ID**: 26251
* **Problem Title**: Indian Army – Predictive Logistics & Forward Supply Chain
* **Organization**: Ministry of Defence
* **Theme**: Transportation & Logistics
* **Phase Objective**: Develop a reproducible, scientifically defensible, hybrid data foundation combining real-world public meteorological and topographical datasets with a causal, weather-conditioned synthetic logistics simulation.

---

## 2. Why a Hybrid Data Architecture?
Traditional machine learning prototypes often rely on arbitrary random numbers that fail to capture the complex environmental dynamics of forward logistics. Real-world logistics in rugged border sectors are profoundly governed by:
* **Sub-zero cold and snowfall** that spike heating fuel demand and obstruct mountain passes.
* **Extreme desert heat** that accelerates water consumption and induces vehicle thermal breakdowns.
* **Monsoon rainfall and steep terrain gradients** that trigger flash landslides and delay supply convoys.

By coupling **real historical observations** (temperature, rainfall, humidity, wind, elevation, terrain slope, road geometry) with **causally conditioned synthetic logistics simulation** (demand, inventory conservation, fleet mechanics, shipment delays, disruptions), the system generates realistic, ML-ready datasets suitable for demand forecasting, travel-time prediction, and supply shortage risk estimation.

---

## 3. Real Public Data Sources & Provenance

| Source Name | Provider | Access Method | Variables Extracted | Temporal & Spatial Scope | License / Terms |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **NASA POWER** | NASA Langley Research Center | Automated Public REST API (No auth required) | `T2M`, `T2M_MAX`, `T2M_MIN`, `PRECTOTCORR`, `WS10M`, `RH2M` | 2022-01-01 to 2024-12-31 (1,096 days per node across all 15 nodes = 16,440 records) @ 0.5° resolution | NASA Open Data Policy (Public Domain / Free unrestricted) |
| **ECMWF ERA5-Land Reanalysis** | ECMWF / Copernicus CDS & Open-Meteo Archive | Automated Public Reanalysis Archive API | `snowfall_sum` (daily snowfall water equivalent in cm) | 2022-01-01 to 2024-12-31 across 15 node coordinates @ 9km (0.1°) resolution | Copernicus Open Access / Open Data Terms |
| **Copernicus DEM (GLO-90)** | European Space Agency (ESA) / Open-Meteo | Automated Public Elevation Endpoint | `elevation_m`, local gradients, slope in degrees, ruggedness | 90m global elevation grid sampled at 15 study node coordinates | European Union Copernicus Open Access (Free / CC-BY-4.0) |
| **OpenStreetMap & OSRM** | OpenStreetMap Contributors / Project OSRM | Public Routing & Overpass APIs | `road_distance_km`, `road_classification`, `lanes`, `surface_type`, graph connectivity | National Highway corridors (NH-1, NH-10, NH-11, NH-68) across 42 route links | Open Database License (ODbL) |
| **IMD Gridded Data** | India Meteorological Department (MoES) | Secondary Reference / Standby Workflow | Pan-India Rainfall & Temperature Grids | Pan-India Historical Grids | MoES / IMD Open Data Policy |

---

## 4. Geographical Study Regions & Node-Level Granularity

Rather than regional averages, the environmental pipeline fetches meteorological observations for **15 distinct fictional study nodes** mapped to public civilian coordinates:

### Region A: Ladakh / Western Himalayas (High Altitude Mountainous)
* **Study Corridor**: Public geographical corridor along Srinagar – Kargil – Leh Public Highway (NH-1).
* **Reference Baseline Elevation**: 3,200m AMSL.
* **Nodes & Coordinates**:
  - `LAD-A01`: Lat 34.2000°N, Lon 75.0000°E (Elevation: 2,750m AMSL)
  - `LAD-A02`: Lat 34.2800°N, Lon 75.6000°E (Elevation: 3,100m AMSL)
  - `LAD-A03`: Lat 34.5500°N, Lon 76.1300°E (Elevation: 2,850m AMSL)
  - `LAD-A04`: Lat 34.3000°N, Lon 76.8000°E (Elevation: 4,120m AMSL)
  - `LAD-A05`: Lat 34.1500°N, Lon 77.5800°E (Elevation: 3,500m AMSL)
* **Environmental Profile**: Sub-zero winter temperatures (down to -24°C), seasonal heavy snowfall, high terrain ruggedness.

### Region B: Sikkim / Eastern Himalayas (Steep Forested Mountain)
* **Study Corridor**: Public corridor along Siliguri – Sevoke – Singtam – Gangtok (NH-10).
* **Reference Baseline Elevation**: 1,000m AMSL.
* **Nodes & Coordinates**:
  - `SIK-B01`: Lat 26.7200°N, Lon 88.4300°E (Elevation: 125m AMSL)
  - `SIK-B02`: Lat 26.8800°N, Lon 88.4700°E (Elevation: 280m AMSL)
  - `SIK-B03`: Lat 27.0600°N, Lon 88.4700°E (Elevation: 650m AMSL)
  - `SIK-B04`: Lat 27.2300°N, Lon 88.5000°E (Elevation: 1,420m AMSL)
  - `SIK-B05`: Lat 27.3500°N, Lon 88.6200°E (Elevation: 1,850m AMSL)
* **Environmental Profile**: High annual monsoon precipitation (>3,000mm), steep river gorge topography, recurrent landslide susceptibility.

### Region C: Rajasthan / Western Desert (Arid Desert Plains)
* **Study Corridor**: Public corridor along Jodhpur – Pokhran – Jaisalmer – Barmer (NH-11 / NH-68).
* **Reference Baseline Elevation**: 250m AMSL.
* **Nodes & Coordinates**:
  - `RAJ-C01`: Lat 26.2800°N, Lon 73.0200°E (Elevation: 231m AMSL)
  - `RAJ-C02`: Lat 26.9200°N, Lon 71.9100°E (Elevation: 215m AMSL)
  - `RAJ-C03`: Lat 26.9100°N, Lon 70.9100°E (Elevation: 225m AMSL)
  - `RAJ-C04`: Lat 25.7500°N, Lon 71.4000°E (Elevation: 175m AMSL)
  - `RAJ-C05`: Lat 26.3000°N, Lon 71.1000°E (Elevation: 190m AMSL)
* **Environmental Profile**: High summer temperatures (exceeding 48°C), low precipitation, arid sandy terrain, heat stress on vehicles and water consumption.

---

## 5. Environmental Feature Engineering & Lapse Rate

### A. Raw vs Derived Temperature
1. **`temperature_c` (PUBLIC_REAL)**:
   * Direct 2-meter ambient air temperature observed by NASA POWER (CERES/MERRA-2) at node coordinates. Preserved unchanged.
2. **`temperature_elevation_adjusted_c` (DERIVED)**:
   * Topoclimatic correction accounting for the vertical altitude differential between the node elevation ($z_{\text{node}}$ from Copernicus DEM) and the regional reference baseline ($z_{\text{ref}}$):
   $$\text{temperature\_elevation\_adjusted\_c} = \text{temperature\_c} - 0.0065 \cdot (z_{\text{node}} - z_{\text{ref}})$$
   * **Assumption**: Standard environmental lapse rate ($\Gamma = 6.5^\circ\text{C} / 1,000\text{m}$). The original real temperature is never overwritten.

### B. Snowfall Observations & Synthetic Fallback
1. **`snowfall_era5_cm` (PUBLIC_REAL)**:
   * Daily snowfall water equivalent retrieved directly from ECMWF ERA5-Land Reanalysis (9km grid).
2. **`snowfall_proxy_cm` (SYNTHETIC PROXY)**:
   * Derived synthetic proxy:
   $$\text{snowfall\_proxy\_cm} = \begin{cases} \text{precipitation\_mm} \times 1.0, & \text{if } \text{temperature\_elevation\_adjusted\_c} \le 0.5^\circ\text{C} \\ 0.0, & \text{otherwise} \end{cases}$$
   * **Documentation**: "Derived synthetic proxy from precipitation and temperature threshold; not observed snowfall."
3. **`snowfall_cm` (OPERATIONAL)**:
   * Uses ERA5-Land reanalysis as primary observed input with fallback to proxy if unavailable.

### C. Weather Severity Index ($WS \in [0, 1]$)
The formula weights strictly sum to **1.00**:
$$WS = 0.25 \cdot \text{ColdPenalty} + 0.20 \cdot \text{HeatPenalty} + 0.25 \cdot \text{RainPenalty} + 0.20 \cdot \text{SnowPenalty} + 0.10 \cdot \text{WindPenalty}$$
Where:
* $\text{ColdPenalty} = \text{clip}\left(\frac{-T_{\text{adj}}}{25}, 0, 1\right)$
* $\text{HeatPenalty} = \text{clip}\left(\frac{T_{\text{adj}} - 38}{12}, 0, 1\right)$
* $\text{RainPenalty} = \text{clip}\left(\frac{\text{Precip}}{50}, 0, 1\right)$
* $\text{SnowPenalty} = \text{clip}\left(\frac{\text{Snow}}{20}, 0, 1\right)$
* $\text{WindPenalty} = \text{clip}\left(\frac{\text{Wind} - 25}{40}, 0, 1\right)$
* **Automated Consistency Check**: Independently verified by `weather_severity_formula_consistency` across all 16,440 node-days (Max deviation: $0.0000$).

---

## 6. Synthetic Logistics Simulation Causal Chain

The logistics simulation strictly follows physical, chronological, and environmental causality:

```
REAL WEATHER (NASA POWER + ERA5-Land) + COPERNICUS DEM ELEVATION
    ↓
DERIVED TOPOCLIMATE (Elevation Adjusted Temp + Weather Severity Index)
    ↓
CONDITIONED DISRUPTIONS & DEMAND
    ↓
DYNAMIC ROUTE TRAVEL TIMES & CONVOY SHIPMENTS
    ↓
CHRONOLOGICAL INVENTORY CONSERVATION
    ↓
FORWARD 7-DAY SHORTAGE RISK TARGET GENERATION
```

### A. Non-Sensitive Supply Categories
* `FOOD`: Calorie-dense rations; winter consumption surge in sub-zero alpine conditions.
* `WATER`: Hydration supply; strong positive causal elasticity with temperatures $>35^\circ\text{C}$ in desert zones.
* `FUEL`: Diesel/kerosene/heating fuel; massive spike ($+60\%$ to $+120\%$) during freezing winter in Ladakh.
* `MEDICAL`: First-aid & pharmaceuticals; spikes during monsoon seasons (waterborne/infection) and sub-zero frostbite risks.
* `GENERAL_SUPPLIES`: Tarpaulins, cold-weather gear, vehicle spares; spikes prior to extreme weather events.

### B. Explicit Synthetic Assumptions
* **Demand Elasticity**:
  - Fuel consumption increases by $+3.5\%$ per $^\circ\text{C}$ below $0^\circ\text{C}$.
  - Water consumption increases by $+3.0\%$ per $^\circ\text{C}$ above $30^\circ\text{C}$.
  - Food demand increases by $+1.0\%$ per $^\circ\text{C}$ below $0^\circ\text{C}$.
* **Disruption Trigger Thresholds**:
  - Landslides triggered when $\text{Precipitation} \ge 25\text{mm}$ and $\text{Slope} \ge 12^\circ$.
  - Blizzards triggered when $\text{Snowfall} \ge 6\text{cm}$ and $T \le -5^\circ\text{C}$.
  - Heatwaves triggered when $T \ge 42^\circ\text{C}$.
  - Flash Floods triggered when $\text{Precipitation} \ge 35\text{mm}$.
* **Travel Time Delays**:
  - Multiplicative compounding of terrain gradient, weather friction, vehicle resilience, and active disruption severity ($1.3\times$ to $5.0\times$).
* **Inventory Conservation**:
  $$\text{Closing Inventory}_{n, c, t} = \min\left(\text{Capacity}_{n, c}, \, \text{Opening Inventory}_{n, c, t} + \text{Received Quantity}_{n, c, t} - \text{Consumed Quantity}_{n, c, t}\right)$$
  $$\text{Opening Inventory}_{n, c, t+1} = \text{Closing Inventory}_{n, c, t}$$

---

## 7. Three ML-Ready Training Datasets

### Dataset 1: Demand Forecasting (`data/training/demand_training.csv`)
* **Objective**: Multi-horizon forward supply demand forecasting.
* **Records**: 79,425 rows (zero NaNs).
* **Targets**: `demand_next_day` ($t+1$), `demand_next_7_days` ($\sum_{i=1}^7 \text{demand}_{t+i}$).
* **Features**: Historical lags (`lag_1`, `lag_7`, `lag_14`, `lag_30`), rolling statistics (`rolling_mean_7`, `rolling_mean_14`, `rolling_mean_30`, `rolling_std_7`, `rolling_std_30`), node-level temperature, rainfall, snowfall, weather severity index, calendar temporal encodings.
* **Leakage Prevention**: All rolling windows and lag features are shifted by $\ge 1$ day into the past.

### Dataset 2: Travel-Time Prediction (`data/training/travel_time_training.csv`)
* **Objective**: Convoy transit duration prediction under variable environmental stress.
* **Records**: 19,381 shipments (zero NaNs).
* **Target**: `actual_travel_time_hr`.
* **Features**: Distance, elevation delta, terrain difficulty, lanes, surface quality, route connectivity, vehicle class, payload utilization ratio, operating range, weather severity, precipitation, snow, wind speed, active disruption severity and multiplier, planned departure hour.

### Dataset 3: Shortage-Risk Prediction (`data/training/shortage_risk_training.csv`)
* **Objective**: Early warning classification of critical warehouse stock depletion.
* **Records**: 81,675 rows (zero NaNs).
* **Target**: `shortage_in_next_7_days` (Binary 0/1: Flag indicating if closing inventory breaches critical threshold within the forward 7-day window).
* **Class Balance**: Class 0: $51.2\%$, Class 1: $48.8\%$.
* **Features**: Day-$t$ closing inventory, capacity utilization percentage, days of supply, historical consumption lags (`consumed_lag_1`, `consumed_lag_7`), rolling consumption means and standard deviations, weather severity, 7-day rainfall, terrain difficulty, node criticality level.

---

## 8. Directory Architecture & Data Governance

```
data/
├── raw/
│   ├── weather/
│   │   ├── nasa_power_raw_lad_a01.json ... nasa_power_raw_raj_c05.json (15 files)
│   │   ├── era5_land_raw_lad_a01.json ... era5_land_raw_raj_c05.json   (15 files)
│   │   └── weather_raw_lad_a01.csv ... weather_raw_raj_c05.csv         (15 files)
│   ├── elevation/
│   │   └── copernicus_dem_raw.csv
│   └── roads/
│   │   └── osm_public_roads_raw.csv
├── processed/
│   ├── weather_processed.csv       (16,440 rows | 15 nodes x 1,096 days)
│   ├── terrain_features.csv        (15 rows)
│   └── road_network_features.csv   (42 rows)
├── synthetic/
│   ├── nodes.csv                   (15 nodes)
│   ├── routes.csv                  (42 routes)
│   ├── fleet.csv                   (80 vehicles)
│   ├── demand.csv                  (82,200 rows)
│   ├── shipments.csv               (19,381 shipments)
│   ├── disruptions.csv             (4,844 events)
│   └── inventory.csv               (82,200 rows)
├── training/
│   ├── demand_training.csv         (79,425 rows)
│   ├── travel_time_training.csv    (19,381 rows)
│   └── shortage_risk_training.csv  (81,675 rows)
└── metadata/
    ├── data_dictionary.csv
    ├── data_source_register.csv
    ├── provenance_audit.csv
    ├── reproducibility_config.json
    ├── data_quality_report.txt
    └── phase1_final_validation.md
```

---

## 9. Data Quality & Integrity Validation Results
All 20 automated validation checks passed with $100\%$ compliance:
* **Formula Consistency**: Weather Severity Index recomputation confirmed $0.0000$ deviation across 16,440 rows.
* **Spatial Weather Variation**: Node temperatures exhibit distinct variance within regions ($\text{StdDev} > 6.6^\circ\text{C}$).
* **Geographic Bounds**: All 15 node coordinates strictly within real Indian territory.
* **Primary Key Uniqueness**: Zero duplicate keys across all 10 datasets.
* **Inventory Conservation**: Exact mass balance ($0.0000\text{ kg}$ deviation) across 82,200 node-days.
* **Payload Compliance**: Zero shipments exceed vehicle cargo limits.
* **Chronological Progression**: $100\%$ of shipments satisfy $\text{actual\_arrival} \ge \text{actual\_departure}$.
* **Leakage Check**: Zero future-data leakage in demand, travel time, and shortage training datasets.

---

## 10. Reproducibility & Pipeline Execution
To execute the complete pipeline and regenerate all datasets from scratch:
```powershell
python main.py --refresh-raw
```
Or to run without redownloading raw API caches:
```powershell
python main.py
```
* **Seed**: `RANDOM_SEED = 42`
* **Python Version**: `3.14.3`
* **Configuration**: Detailed in `data_pipeline/config.py` and `data/metadata/reproducibility_config.json`.
