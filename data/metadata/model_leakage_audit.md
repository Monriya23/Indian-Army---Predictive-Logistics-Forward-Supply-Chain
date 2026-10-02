# Model Data Leakage & Feature Timestamp Audit

## 1. Objective of the Leakage Audit
To mathematically and programmatically verify that none of the three ML-ready training datasets contain future-data leakage (temporal look-ahead bias), target leakage, or unshifted rolling statistics.

---

## 2. Dataset 1: Demand Forecasting (`demand_training.csv`)

### Feature Timestamp & Leakage Matrix
| Column Name | Role | Timestamp Used | Computation Method | Leakage Status |
| :--- | :--- | :---: | :--- | :---: |
| `date` | Index / Identifier | $t$ | Observation date | **CLEAN** |
| `node_id` | Static Category | N/A | Node identifier | **CLEAN** |
| `region` | Static Category | N/A | Regional corridor | **CLEAN** |
| `supply_category` | Static Category | N/A | Commodity type | **CLEAN** |
| `baseline_demand` | Static Feature | N/A | Base capacity allocation | **CLEAN** |
| `elevation_m` | Static Feature | N/A | Copernicus DEM 90m | **CLEAN** |
| `terrain_difficulty` | Static Feature | N/A | Derived topographical index | **CLEAN** |
| `criticality_level` | Static Feature | N/A | Node priority score | **CLEAN** |
| `temperature_c` | Weather Covariate | $t$ | Observed ground temp on date $t$ | **CLEAN** |
| `precipitation_mm` | Weather Covariate | $t$ | Observed precipitation on date $t$ | **CLEAN** |
| `snowfall_cm` | Weather Covariate | $t$ | Derived snowfall on date $t$ | **CLEAN** |
| `wind_speed_kmh` | Weather Covariate | $t$ | Observed wind speed on date $t$ | **CLEAN** |
| `weather_severity` | Weather Covariate | $t$ | Derived severity index on date $t$ | **CLEAN** |
| `rainfall_3d` | Weather Covariate | $[t-2, t]$ | Rolling sum of precipitation $(t-2, t-1, t)$ | **CLEAN** |
| `rainfall_7d` | Weather Covariate | $[t-6, t]$ | Rolling sum of precipitation $(t-6, \dots, t)$ | **CLEAN** |
| `temperature_7d_avg` | Weather Covariate | $[t-6, t]$ | Rolling mean of temperature $(t-6, \dots, t)$ | **CLEAN** |
| `lag_1` | Time-Series Feature | $t-1$ | `final_demand.shift(1)` | **CLEAN** |
| `lag_7` | Time-Series Feature | $t-7$ | `final_demand.shift(7)` | **CLEAN** |
| `lag_14` | Time-Series Feature | $t-14$ | `final_demand.shift(14)` | **CLEAN** |
| `lag_30` | Time-Series Feature | $t-30$ | `final_demand.shift(30)` | **CLEAN** |
| `rolling_mean_7` | Time-Series Feature | $[t-7, t-1]$ | `final_demand.shift(1).rolling(7).mean()` | **CLEAN** |
| `rolling_mean_14` | Time-Series Feature | $[t-14, t-1]$ | `final_demand.shift(1).rolling(14).mean()` | **CLEAN** |
| `rolling_mean_30` | Time-Series Feature | $[t-30, t-1]$ | `final_demand.shift(1).rolling(30).mean()` | **CLEAN** |
| `rolling_std_7` | Time-Series Feature | $[t-7, t-1]$ | `final_demand.shift(1).rolling(7).std()` | **CLEAN** |
| `rolling_std_30` | Time-Series Feature | $[t-30, t-1]$ | `final_demand.shift(1).rolling(30).std()` | **CLEAN** |
| `day_of_week`, `month` | Temporal Covariates | $t$ | Date calendar components | **CLEAN** |
| **`demand_next_day`** | **Target 1** | $t+1$ | `final_demand.shift(-1)` | **VALID TARGET** |
| **`demand_next_7_days`**| **Target 2** | $[t+1, t+7]$ | $\sum_{i=1}^7 \text{final\_demand}[t+i]$ | **VALID TARGET** |

* **Code Verification**: In [`data_pipeline/features/demand_features.py`](file:///c:/Users/riyam/Indian%20Army%20Logistics/data_pipeline/features/demand_features.py#L48-L62), `past_demand = grp["final_demand"].shift(1)` is explicitly used prior to `.rolling()`. The current day's demand `final_demand[t]` is strictly omitted from the rolling features, preventing any same-day leakage into historical moving averages.

---

## 3. Dataset 2: Travel-Time Prediction (`travel_time_training.csv`)

### Feature Timestamp & Leakage Matrix
| Column Name | Role | Availability at Dispatch | Leakage Status |
| :--- | :--- | :---: | :---: |
| `shipment_id`, `date`, `route_id` | Identifiers | Pre-dispatch | **CLEAN** |
| `vehicle_id`, `vehicle_class` | Fleet Assigned | Pre-dispatch | **CLEAN** |
| `quantity_kg`, `payload_utilization_ratio` | Manifest Weight | Pre-dispatch | **CLEAN** |
| `distance_km`, `elevation_change_m`, `terrain_difficulty` | Static Route Geometry | Pre-dispatch | **CLEAN** |
| `road_classification`, `road_condition`, `lanes` | Route Physical Specs | Pre-dispatch | **CLEAN** |
| `speed_factor`, `operating_range_km` | Vehicle Mechanics | Pre-dispatch | **CLEAN** |
| `planned_departure_hour`, `day_of_week`, `month` | Schedule | Pre-dispatch | **CLEAN** |
| `temperature_c`, `precipitation_mm`, `snowfall_cm`, `wind_speed_kmh` | Morning Weather Conditions | Available at dispatch | **CLEAN** |
| `weather_severity`, `extreme_weather_indicator` | Morning Weather Conditions | Available at dispatch | **CLEAN** |
| `disruption_active`, `disruption_severity`, `travel_time_multiplier` | Active En-Route Advisories | Available at dispatch | **CLEAN** |
| `planned_travel_time_hr` | Baseline Scheduled Duration | Computed at dispatch | **CLEAN** |
| **`actual_travel_time_hr`** | **Target** | **Realized Post-Trip** | **VALID TARGET** |

* **Code Verification**: In [`data_pipeline/features/travel_time_features.py`](file:///c:/Users/riyam/Indian%20Army%20Logistics/data_pipeline/features/travel_time_features.py#L38-L100), `actual_arrival`, `actual_departure`, and `delay_hours` are **strictly excluded** from the feature set. Only pre-dispatch known attributes (`planned_departure_hour`, `planned_travel_time_hr`, morning weather, road characteristics, vehicle specs) are provided as features.

---

## 4. Dataset 3: Shortage-Risk Prediction (`shortage_risk_training.csv`)

### Feature Timestamp & Leakage Matrix
| Column Name | Role | Timestamp Used | Computation Method | Leakage Status |
| :--- | :--- | :---: | :--- | :---: |
| `date`, `node_id`, `region`, `supply_category` | Identifiers | $t$ | Day $t$ observation | **CLEAN** |
| `closing_inventory` | Current State | $t$ | Warehouse stock at close of day $t$ | **CLEAN** |
| `storage_capacity`, `critical_threshold` | Static Bounds | $t$ | Capacity limits | **CLEAN** |
| `capacity_utilization_pct` | Current State | $t$ | $\text{closing} / \text{capacity} \times 100$ | **CLEAN** |
| `days_of_supply` | Current State | $t$ | $\text{closing} / \text{consumed}$ on day $t$ | **CLEAN** |
| `consumed_lag_1` | Consumption Lag | $t-1$ | `consumed_quantity.shift(1)` | **CLEAN** |
| `consumed_lag_7` | Consumption Lag | $t-7$ | `consumed_quantity.shift(7)` | **CLEAN** |
| `consumed_rolling_mean_7` | Consumption Rolling | $[t-7, t-1]$ | `consumed_quantity.shift(1).rolling(7).mean()` | **CLEAN** |
| `consumed_rolling_mean_14` | Consumption Rolling | $[t-14, t-1]$ | `consumed_quantity.shift(1).rolling(14).mean()` | **CLEAN** |
| `consumed_rolling_std_7` | Consumption Rolling | $[t-7, t-1]$ | `consumed_quantity.shift(1).rolling(7).std()` | **CLEAN** |
| `temperature_c`, `weather_severity`, `rainfall_7d` | Environmental State | $t$ | Observed on day $t$ | **CLEAN** |
| `elevation_m`, `terrain_difficulty`, `road_accessibility` | Topographical State | N/A | Static node features | **CLEAN** |
| `criticality_level` | Priority State | N/A | Strategic hierarchy | **CLEAN** |
| **`shortage_in_next_7_days`** | **Target** | $[t+1, t+7]$ | $\max_{i=1..7}(\text{shortage\_flag}[t+i])$ | **VALID TARGET** |

* **Code Verification**: In [`data_pipeline/features/shortage_features.py`](file:///c:/Users/riyam/Indian%20Army%20Logistics/data_pipeline/features/shortage_features.py#L48-L70), the target is computed by shifting the forward window backwards into the target column only. No future inventory values, future arrivals, or future demands are present in any input column.
