# Phase 1 Final Environmental & Data Quality Validation Report
**Project**: SIH 2026 PS 26251 — Indian Army: Predictive Logistics & Forward Supply Chain  
**Classification**: Public-Environment-Conditioned Synthetic Logistics Simulation  
**Audit Completion Date**: 2026-10-02  
**Status**: PHASE 1 FROZEN & VALIDATED (100% Pass Rate)

> **Mandatory Statement**: No classified or operational military logistics data was used in this research. The dataset combines real-world public civilian meteorological and topographical observations with a causally conditioned synthetic logistics simulation. All nodes (`LAD-A01`–`LAD-A05`, `SIK-B01`–`SIK-B05`, `RAJ-C01`–`RAJ-C05`) are fictional logistics designations mapped to civilian coordinates.

---

## 1. Real Public Data Sources

| Data Source | Primary Provider | URL / Endpoint | Spatial Resolution | Variables Extracted | License / Terms |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **NASA POWER** (CERES/MERRA-2) | NASA Langley Research Center | [power.larc.nasa.gov](https://power.larc.nasa.gov/) | 0.5° × 0.5° (~50km) | `T2M` (Mean Temp), `T2M_MAX` (Max Temp), `T2M_MIN` (Min Temp), `PRECTOTCORR` (Precipitation), `WS10M` (Wind Speed), `RH2M` (Relative Humidity) | NASA Open Data Policy (Public Domain / Free unrestricted) |
| **ERA5-Land Reanalysis** | ECMWF / Copernicus CDS | [cds.climate.copernicus.eu](https://cds.climate.copernicus.eu/) | 9km (0.1°) | `snowfall_sum` (Daily snowfall water equivalent in cm) | Copernicus Open Access / Open Data Terms |
| **Copernicus DEM (GLO-90)** | European Space Agency (ESA) | [dataspace.copernicus.eu](https://dataspace.copernicus.eu/) | 90m Global Elevation Model | `elevation_m` (AMSL), `slope_degree` (Finite difference gradient), local elevation variance | EU Copernicus Open Access (Free / CC-BY-4.0) |
| **OpenStreetMap & OSRM** | OpenStreetMap Contributors | [www.openstreetmap.org](https://www.openstreetmap.org/) | Vector road geometry | `road_distance_km`, `road_classification`, `lanes`, `surface_type`, network topology | Open Database License (ODbL) |
| **IMD Gridded Data** (Standby) | India Meteorological Department | [mausam.imd.gov.in](https://mausam.imd.gov.in/) | 0.25° (Rain) / 1.0° (Temp) | Daily gridded precipitation & surface temperature | MoES / IMD Open Data Policy |

---

## 2. Node-Level Weather Coverage

Rather than using regional centroids, meteorological observations were acquired for each of the **15 distinct study node coordinates** over the full 3-year timeline (2022-01-01 to 2024-12-31, 1,096 days per node = 16,440 total node-days):

| Node ID | Region | Role | Latitude (°N) | Longitude (°E) | Elevation (m AMSL) | 3-Year Mean Temp (°C) | 3-Year Total Precip (mm) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `LAD-A01` | Ladakh | Regional Depot | 34.2000 | 75.0000 | 2,750 | 5.2 | 1,420 |
| `LAD-A02` | Ladakh | Transit Hub | 34.2800 | 75.6000 | 3,100 | 3.1 | 1,180 |
| `LAD-A03` | Ladakh | Forward Depot | 34.5500 | 76.1300 | 2,850 | 4.8 | 950 |
| `LAD-A04` | Ladakh | Tactical Node | 34.3000 | 76.8000 | 4,120 | -3.8 | 710 |
| `LAD-A05` | Ladakh | Main Hub | 34.1500 | 77.5800 | 3,500 | 1.9 | 540 |
| `SIK-B01` | Sikkim | Regional Depot | 26.7200 | 88.4300 | 125 | 24.1 | 3,240 |
| `SIK-B02` | Sikkim | Transit Hub | 26.8800 | 88.4700 | 280 | 22.8 | 3,450 |
| `SIK-B03` | Sikkim | Forward Depot | 27.0600 | 88.4700 | 650 | 20.1 | 3,680 |
| `SIK-B04` | Sikkim | Tactical Node | 27.2300 | 88.5000 | 1,420 | 15.6 | 3,890 |
| `SIK-B05` | Sikkim | Main Hub | 27.3500 | 88.6200 | 1,850 | 12.9 | 4,120 |
| `RAJ-C01` | Rajasthan | Regional Depot | 26.2800 | 73.0200 | 231 | 27.6 | 380 |
| `RAJ-C02` | Rajasthan | Transit Hub | 26.9200 | 71.9100 | 215 | 27.2 | 290 |
| `RAJ-C03` | Rajasthan | Forward Depot | 26.9100 | 70.9100 | 225 | 27.4 | 240 |
| `RAJ-C04` | Rajasthan | Tactical Node | 25.7500 | 71.4000 | 175 | 28.1 | 310 |
| `RAJ-C05` | Rajasthan | Main Hub | 26.3000 | 71.1000 | 190 | 27.8 | 260 |

---

## 3. Snowfall Source & Fallback Documentation

1. **ECMWF ERA5-Land Reanalysis (`snowfall_era5_cm`)**:
   * Direct reanalysis physical observation extracted from ECMWF ERA5-Land 9km reanalysis.
   * Successfully integrated into all 15 node records.
2. **Synthetic Snowfall Proxy (`snowfall_proxy_cm`)**:
   * Defined as:
     $$\text{snowfall\_proxy\_cm} = \begin{cases} \text{precipitation\_mm} \times 1.0, & \text{if } \text{temperature\_elevation\_adjusted\_c} \le 0.5^\circ\text{C} \\ 0.0, & \text{otherwise} \end{cases}$$
   * **Explicit Provenance Warning**: *"Derived synthetic proxy from precipitation and temperature threshold; not observed snowfall."*
3. **Operational Snowfall Field (`snowfall_cm`)**:
   * Uses ERA5-Land reanalysis as primary observed input, maintaining synthetic proxy as explicit documented fallback.

---

## 4. Weather Severity Formula & Elevation Correction

### A. Elevation Lapse-Rate Adjustment
* **Raw Public Temperature (`temperature_c`)**: Direct NASA POWER 2m observed temperature preserved unchanged.
* **Derived Temperature (`temperature_elevation_adjusted_c`)**:
  $$\text{temperature\_elevation\_adjusted\_c} = \text{temperature\_c} - 0.0065 \cdot (z_{\text{node}} - z_{\text{ref}})$$
  - Reference Elevations ($z_{\text{ref}}$): Ladakh = 3,200m, Sikkim = 1,000m, Rajasthan = 250m.
  - Standard atmospheric lapse rate $\Gamma = 0.0065^\circ\text{C}/\text{m}$.
  - Assumption Status: *Prototype Modelling Assumption (Standard Tropospheric Lapse Rate)*.

### B. Weather Severity Index ($WS$)
* **Formula Weights**: Strictly normalized such that $\sum w_i = 1.00$:
  $$WS = 0.25 \cdot \text{ColdPenalty} + 0.20 \cdot \text{HeatPenalty} + 0.25 \cdot \text{RainPenalty} + 0.20 \cdot \text{SnowPenalty} + 0.10 \cdot \text{WindPenalty}$$
* **Penalty Components**:
  - $\text{ColdPenalty} = \text{clip}\left(\frac{-T_{\text{adj}}}{25}, 0, 1\right)$ (Sub-zero hazard: 0°C to -25°C)
  - $\text{HeatPenalty} = \text{clip}\left(\frac{T_{\text{adj}} - 38}{12}, 0, 1\right)$ (Extreme heat stress: 38°C to 50°C)
  - $\text{RainPenalty} = \text{clip}\left(\frac{\text{Precip}}{50}, 0, 1\right)$ (Flash flood/landslide moisture: 0mm to 50mm)
  - $\text{SnowPenalty} = \text{clip}\left(\frac{\text{Snow}}{20}, 0, 1\right)$ (Snow accumulation: 0cm to 20cm)
  - $\text{WindPenalty} = \text{clip}\left(\frac{\text{Wind} - 25}{40}, 0, 1\right)$ (Gale wind friction: 25 km/h to 65 km/h)
* **Automated Consistency Validation**:
  - Independently evaluated across all 16,440 rows in `weather_processed.csv`.
  - Result: **PASS** (Maximum numerical deviation: `0.0000`).

---

## 5. Synthetic Causal Chain

The entire logistics layer is causally grounded in the physical and environmental inputs:

```
REAL WEATHER (NASA POWER + ERA5-Land) + REAL TOPOGRAPHY (Copernicus DEM)
    ↓
DERIVED TOPOCLIMATE (Elevation Adjusted Temp + Weather Severity Index)
    ↓
CONDITIONED DISRUPTIONS (Landslide, Blizzard, Heatwave, Flood)
    ↓
TRAVEL TIME FRICTION & CONVOY SHIPMENT DELAYS
    ↓
CONDITIONED SUPPLY DEMAND (Fuel cold surge, Water heat surge)
    ↓
CHRONOLOGICAL INVENTORY CONSERVATION (Opening + Received - Consumed)
    ↓
FORWARD 7-DAY SHORTAGE RISK TARGET GENERATION
```

---

## 6. Dataset Row Counts & Schema Summary

| Dataset File | Category | Row Count | Column Count | File Size (KB) | Key Columns |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `weather_processed.csv` | Processed Environmental | 16,440 | 25 | 3,555.4 | `date`, `node_id`, `temperature_c`, `temperature_elevation_adjusted_c`, `precipitation_mm`, `snowfall_cm`, `wind_speed_kmh`, `weather_severity` |
| `terrain_features.csv` | Processed Geographic | 15 | 12 | 2.6 | `node_id`, `elevation_m`, `slope_degree`, `terrain_difficulty`, `terrain_type` |
| `road_network_features.csv` | Processed Infrastructure | 42 | 19 | 7.7 | `route_id`, `distance_km`, `elevation_change_m`, `road_classification`, `route_accessibility`, `route_reliability` |
| `nodes.csv` | Synthetic Simulation | 15 | 14 | 2.3 | `node_id`, `storage_capacity_kg`, `criticality_level`, `role`, `region` |
| `fleet.csv` | Synthetic Simulation | 80 | 11 | 7.4 | `vehicle_id`, `vehicle_class`, `capacity_kg`, `weather_resilience`, `max_slope_deg` |
| `routes.csv` | Synthetic Simulation | 42 | 15 | 5.6 | `route_id`, `source_node`, `dest_node`, `distance_km`, `normal_travel_time_hr` |
| `demand.csv` | Synthetic Simulation | 82,200 | 14 | 9,105.5 | `date`, `node_id`, `supply_category`, `final_demand`, `actual_consumption` |
| `disruptions.csv` | Synthetic Simulation | 4,844 | 11 | 605.9 | `event_id`, `route_id`, `start_date`, `event_type`, `severity`, `travel_time_multiplier` |
| `shipments.csv` | Synthetic Simulation | 19,381 | 20 | 4,009.1 | `shipment_id`, `route_id`, `vehicle_id`, `planned_travel_time_hr`, `actual_travel_time_hr`, `delay_hours` |
| `inventory.csv` | Synthetic Simulation | 82,200 | 11 | 5,874.8 | `date`, `node_id`, `supply_category`, `opening_inventory`, `received_quantity`, `closing_inventory`, `shortage_flag` |
| `demand_training.csv` | ML Training | 79,425 | 44 | 20,987.9 | `demand_next_day`, `demand_next_7_days`, lag features, rolling means/stds |
| `travel_time_training.csv` | ML Training | 19,381 | 38 | 4,792.3 | `actual_travel_time_hr`, vehicle features, weather severity, disruption features |
| `shortage_risk_training.csv` | ML Training | 81,675 | 33 | 14,414.0 | `shortage_in_next_7_days`, days of supply, closing inventory, weather features |

---

## 7. Inventory Conservation Validation

* **Conservation Law**:
  $$\text{Closing Inventory}_{n, c, t} = \min\left(\text{Storage Capacity}_{n, c}, \, \text{Opening Inventory}_{n, c, t} + \text{Received Quantity}_{n, c, t} - \text{Consumed Quantity}_{n, c, t}\right)$$
  $$\text{Opening Inventory}_{n, c, t+1} = \text{Closing Inventory}_{n, c, t}$$
* **Validation Outcome**:
  - Across all 82,200 records (15 nodes × 5 categories × 1,096 days):
  - Maximum mass balance discrepancy: **`0.0000 kg`** (Exact Conservation).
  - Maximum transition delta between $t$ and $t+1$: **`0.0000 kg`** (Zero Teleportation).
  - Minimum closing inventory: **`0.0000 kg`** (No negative stock).

---

## 8. Leakage Validation

* **Demand Forecasting Training**:
  - Target: Forward demand at $t+1$ and $t+1 \dots t+7$.
  - Features: Lags shifted by $\ge 1$ day into the past; rolling stats calculated strictly over prior observations.
  - Verification: **PASS** (Zero NaNs, strict causal temporal separation).
* **Travel-Time Training**:
  - Target: Realized `actual_travel_time_hr`.
  - Features: Scheduled planned time, pre-departure environmental conditions, active route disruptions.
  - Verification: **PASS** (Zero post-arrival features).
* **Shortage Risk Training**:
  - Target: Binary flag of stock depletion within the forward 7-day window ($t+1 \dots t+7$).
  - Features: Day-$t$ closing stock, historical consumption stats, current weather.
  - Verification: **PASS** (Zero future inventory leakage).

---

## 9. Realism Statistics & Operational Distributions

### A. Disruption Event Distribution by Region
* **Ladakh (Western Himalayas)**: 1,532 total events
  - `ROAD_CLOSURE`: 696 (45.4%)
  - `SNOW`: 596 (38.9%)
  - `LANDSLIDE`: 150 (9.8%)
  - `SECURITY_RELATED_ROUTE_RESTRICTION`: 28 (1.8%)
  - `TRANSPORT_CAPACITY_REDUCTION`: 25 (1.6%)
  - `VEHICLE_BREAKDOWN`: 19 (1.2%)
* **Sikkim (Eastern Himalayas)**: 3,263 total events
  - `LANDSLIDE`: 3,078 (94.3%) — reflects high monsoon precipitation on steep terrain
  - `ROAD_CLOSURE`: 84 (2.6%)
  - `SNOW`: 34 (1.0%)
  - `TRANSPORT_CAPACITY_REDUCTION`: 24 (0.7%)
  - `SECURITY_RELATED_ROUTE_RESTRICTION`: 22 (0.7%)
  - `VEHICLE_BREAKDOWN`: 21 (0.6%)
* **Rajasthan (Western Desert)**: 67 total events
  - `TRANSPORT_CAPACITY_REDUCTION`: 24 (35.8%)
  - `VEHICLE_BREAKDOWN`: 22 (32.8%)
  - `SECURITY_RELATED_ROUTE_RESTRICTION`: 21 (31.3%)

### B. Travel Time & Delay Metrics by Region
* **Ladakh**: Planned Mean = 6.10h | Actual Mean = 9.82h | Avg Delay = 3.97h | Delayed Convoys = 98.8%
* **Sikkim**: Planned Mean = 2.20h | Actual Mean = 5.50h | Avg Delay = 3.54h | Delayed Convoys = 70.0%
* **Rajasthan**: Planned Mean = 3.07h | Actual Mean = 3.21h | Avg Delay = 0.39h | Delayed Convoys = 27.7%

### C. Stock-Out & Critical Buffer Depletion Rate by Category
* **FOOD**: Stockout Rate = 27.81% | Below Critical Buffer = 40.7%
* **WATER**: Stockout Rate = 33.22% | Below Critical Buffer = 45.9%
* **FUEL**: Stockout Rate = 31.58% | Below Critical Buffer = 45.6%
* **MEDICAL**: Stockout Rate = 21.37% | Below Critical Buffer = 29.8%
* **GENERAL_SUPPLIES**: Stockout Rate = 30.54% | Below Critical Buffer = 41.7%

### D. Shortage Risk Classification Label Balance
* **Class 0 (No Shortage in Next 7 Days)**: 41,818 records (**51.2%**)
* **Class 1 (Shortage in Next 7 Days)**: 39,857 records (**48.8%**)
* Natural balance provides an ideal foundation for supervised binary classification.

---

## 10. Geographic Validation

* **Bounding Boxes**:
  - Ladakh Nodes: Lat [34.15°N – 34.55°N], Lon [75.00°E – 77.58°E] — **VALID**
  - Sikkim Nodes: Lat [26.72°N – 27.35°N], Lon [88.43°E – 88.62°E] — **VALID**
  - Rajasthan Nodes: Lat [25.75°N – 26.92°N], Lon [70.91°E – 73.02°E] — **VALID**
* **Topological Connectivity**:
  - Regional road graphs exhibit complete connectivity with redundant alternative routes in primary highway sectors.

---

## 11. Known Limitations & Environmental Assumptions

1. **Synthetic Logistics Layer**: All dispatch schedules, warehouse capacities, consumption ratios, and vehicle fleets are synthetic prototypes conditioned on environmental inputs.
2. **Spatial Resolution**: NASA POWER is provided on a 0.5° × 0.5° grid; microclimatic valley inversions below this scale are approximated via the Copernicus DEM lapse-rate adjustment.
3. **OSM Highway Abstraction**: Road geometries follow public civilian national highways; local tactical track conditions are simulated via terrain slope and surface quality factors.
4. **No Real Operational Data**: The simulation does not represent actual Indian Army force dispositions, unit rosters, or classified ammunition/payload movements.

---

## 12. Exact Reproducibility Command

To completely reproduce the entire data foundation from scratch with online data refresh:
```powershell
python main.py --refresh-raw
```
To run the full pipeline using existing raw data caches:
```powershell
python main.py
```
* **Python Runtime**: Python 3.14.3
* **Random Seed**: `42` (ensuring deterministic reproducibility across all simulation modules)
* **Metadata & Hashes**: Checksums and configuration parameters stored in `data/metadata/reproducibility_config.json`.
