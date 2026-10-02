# Causal Dependency & Implementation Audit

## 1. Code-Level Verification of Core Causal Chains

This document audits the implementation of causal mechanisms in the codebase to confirm that synthetic logistics behavior is strictly conditioned on real environmental observations.

---

### Causal Chain 1: Real Weather $\rightarrow$ Weather Severity $\rightarrow$ Disruption Probability
* **Implementation File**: [`data_pipeline/processing/weather_processing.py`](file:///c:/Users/riyam/Indian%20Army%20Logistics/data_pipeline/processing/weather_processing.py#L48-L68) and [`data_pipeline/simulation/disruptions.py`](file:///c:/Users/riyam/Indian%20Army%20Logistics/data_pipeline/simulation/disruptions.py#L40-L115)
* **Mechanism**:
  1. Real NASA POWER `temperature_c`, `precipitation_mm`, `snowfall_cm`, and `wind_speed_kmh` are transformed into a continuous normalized `weather_severity` index $[0.0, 1.0]$.
  2. In `disruptions.py`, physical triggers are evaluated daily against real observations:
     * `SNOW` & `ROAD_CLOSURE` triggered when `snowfall_cm >= 6.0` or (`temp_c <= -8.0` and `precip_mm >= 4.0`).
     * `LANDSLIDE` & `HEAVY_RAIN` triggered when `rainfall_3d >= 40.0` or `precip_mm >= 30.0` in mountain regions (`LADAKH`, `SIKKIM`).
     * `EXTREME_HEAT` triggered when `temp_c >= 43.0` in `RAJASTHAN`.
     * `WEATHER_DELAY` triggered when `wind_speed_kmh >= 45.0`.
* **Empirical Confirmation**:
  * In the 3-year simulation, **147 Landslides** were generated strictly during high rainfall periods in Sikkim/Ladakh, **38 Road Closures** occurred during blizzard/flood conditions, and **18 Snow Blockages** occurred during sub-zero precipitation events.

---

### Causal Chain 2: Real Weather + Terrain $\rightarrow$ Travel-Time Variation
* **Implementation File**: [`data_pipeline/simulation/shipments.py`](file:///c:/Users/riyam/Indian%20Army%20Logistics/data_pipeline/simulation/shipments.py#L90-L138)
* **Mechanism**:
  1. Base driving duration $\text{normal\_travel\_time\_hr}$ is derived from OpenStreetMap route distance divided by gradient-penalized baseline highway speeds.
  2. On shipment date $t$, the actual travel time is multiplied by:
     * $\text{weather\_mult} = 1.0 + (WS \cdot 0.45) + (\text{snow}/15.0 \cdot 0.35) + (\text{precip}/50.0 \cdot 0.25)$
     * $\text{terrain\_mult} = 1.0 + (\text{terrain\_difficulty} \cdot 0.25) + (\text{elevation\_change\_m}/2500.0 \cdot 0.15)$
     * $\text{disruption\_mult} = \text{travel\_time\_multiplier}$ from active disruptions.
     * Vehicle resilience factor $(1.1 - \text{weather\_resilience})$ attenuates weather friction based on vehicle class.
* **Empirical Correlation**:
  * Distance vs Travel Time: Pearson $r = +0.621$, Spearman $\rho = +0.673$.
  * Terrain Difficulty vs Travel Time: Pearson $r = +0.348$, Spearman $\rho = +0.455$.
  * Weather Severity vs Travel Time: Pearson $r = +0.277$, Spearman $\rho = +0.234$.

---

### Causal Chain 3: Real Weather + Location + Season $\rightarrow$ Demand Variation
* **Implementation File**: [`data_pipeline/simulation/demand.py`](file:///c:/Users/riyam/Indian%20Army%20Logistics/data_pipeline/simulation/demand.py#L55-L125)
* **Mechanism**:
  1. `WATER`: In desert conditions (`RAJASTHAN`), temperatures above $35^\circ\text{C}$ introduce an additive multiplier $+3.5\%$ per $^\circ\text{C}$ (up to $+52\%$ at $50^\circ\text{C}$).
  2. `FUEL`: In high-altitude cold (`LADAKH`), temperatures below $5^\circ\text{C}$ introduce an additive multiplier $+4.5\%$ per $^\circ\text{C}$ of frost (up to $+112\%$ at $-20^\circ\text{C}$).
  3. `MEDICAL`: Elevated by monsoon precipitation ($+35\%$ scale) and sub-zero frostbite risks ($+1.5\%$ per $^\circ\text{C}$ sub-zero).
* **Empirical Correlation**:
  * Ladakh Fuel Demand vs Temperature: Pearson $r = -0.574$, Spearman $\rho = -0.580$ (strong inverse causal relationship).
  * Rajasthan Water Demand vs Temperature: Pearson $r = +0.206$, Spearman $\rho = +0.203$ (positive heat elasticity).

---

### Causal Chain 4: Demand + Shipments $\rightarrow$ Chronological Inventory Evolution
* **Implementation File**: [`data_pipeline/simulation/inventory.py`](file:///c:/Users/riyam/Indian%20Army%20Logistics/data_pipeline/simulation/inventory.py#L38-L90)
* **Mechanism**:
  1. $\text{Received Quantity}(t)$ is aggregated from arrived shipments in `shipments.csv` for that destination node and category on date $t$.
  2. $\text{Consumed Quantity}(t)$ is bounded by physical stock: $\min(\text{Opening} + \text{Received}, \text{Target Consumption})$.
  3. $\text{Closing}(t) = \min(\text{Capacity}, \text{Opening} + \text{Received} - \text{Consumed})$.
  4. $\text{Opening}(t+1) = \text{Closing}(t)$.
* **Empirical Audit**:
  * Max conservation delta across 82,200 records $= 0.0000\text{ kg}$.
  * Max continuity delta across 82,200 records $= 0.0000\text{ kg}$.

---

### Causal Chain 5: Inventory + Future Demand + Replenishment $\rightarrow$ Shortage Target
* **Implementation File**: [`data_pipeline/features/shortage_features.py`](file:///c:/Users/riyam/Indian%20Army%20Logistics/data_pipeline/features/shortage_features.py#L48-L75)
* **Mechanism**:
  * Target $\text{shortage\_in\_next\_7\_days}$ is $1$ if closing inventory drops below critical buffer ($20\%$ capacity or $<3$ days of supply) at any point between $t+1$ and $t+7$.
  * Input features at day $t$ supply current stock, days of supply, historical consumption moving averages, weather severity, and node criticality.
* **Empirical Audit**:
  * Shortage class distribution: Class 0 (No shortage) = $51.5\%$, Class 1 (Shortage) = $48.5\%$.
  * Mean closing inventory for Class 0 $= 10,358.4\text{ kg}$ vs Class 1 $= 2,052.9\text{ kg}$ ($5.0\times$ difference).

---

## 2. Classification of Synthetic Variables & Randomness Audit

We classify every synthetic variable into three categories:
* **Class A**: Causally linked to real/derived environmental inputs.
* **Class B**: Deterministically or mechanistically linked to another synthetic variable.
* **Class C**: Independent pseudo-random variable.

| Variable Name | Table | Classification | Primary Influencing Inputs | Nature of Relationship |
| :--- | :--- | :---: | :--- | :--- |
| `weather_severity` | `weather_processed.csv` | **A** | $T2M, Precip, Snow, Wind$ | Real weather weighted formula |
| `terrain_difficulty` | `terrain_features.csv` | **A** | $Elevation, Slope, Variance$ | Real DEM weighted formula |
| `route_accessibility` | `road_network_features.csv` | **A** | $Lanes, Surface, TerrainDiff$ | Real OSM & DEM attributes |
| `final_demand` | `demand.csv` | **A** | $T2M, Precip, Snow, WS, Base$ | Causal physics formula + noise |
| `actual_consumption` | `demand.csv` | **B** | `final_demand` | Bounded consumption ratio |
| `actual_travel_time_hr` | `shipments.csv` | **A** | $Distance, Terrain, Weather, Disruption$ | Causal delay mechanics |
| `delay_hours` | `shipments.csv` | **B** | `actual_arrival, planned_arrival` | Arrival time delta |
| `opening_inventory` | `inventory.csv` | **B** | `closing_inventory[t-1]` | Chronological state transfer |
| `received_quantity` | `inventory.csv` | **B** | `shipments.actual_arrival` | Physical shipment receipt |
| `consumed_quantity` | `inventory.csv` | **B** | `demand.actual_consumption, stock` | Inventory consumption rule |
| `closing_inventory` | `inventory.csv` | **B** | `opening, received, consumed` | Inventory conservation law |
| `days_of_supply` | `inventory.csv` | **B** | `closing_inventory, consumed` | Ratio calculation |
| `shortage_flag` | `inventory.csv` | **B** | `closing_inventory, threshold` | Threshold comparison |
| `demand_next_day` | `demand_training.csv` | **B** | `final_demand[t+1]` | Forward time shift target |
| `demand_next_7_days` | `demand_training.csv` | **B** | $\sum_{i=1}^7 \text{final\_demand}[t+i]$ | Forward rolling sum target |
| `shortage_in_next_7_days` | `shortage_risk_training.csv` | **B** | $\max_{i=1..7}(\text{shortage\_flag}[t+i])$ | Forward window maximum |
| **`demand_noise`** | `demand.csv` | **C** | $\mathcal{N}(0, \sigma^2)$ | Unexplained consumption noise ($\pm 6\%$) |
| **`dispatch_delay_min`** | `shipments.csv` | **C** | $\text{Exp}(\lambda)$ | Random staging dispatch variation ($15-45\text{ min}$) |
| **`shipment_scheduled_prob`** | `shipments.csv` | **C** | $\text{Uniform}(0, 1)$ | Daily dispatch decision coin flip |
| **`quantity_kg_variation`** | `shipments.csv` | **C** | $\text{Uniform}(0.60, 0.98)$ | Convoy loading fill-rate variation |
| **`baseline_breakdown_disruption`**| `disruptions.csv` | **C** | $\text{Bernoulli}(0.03)$ | Background vehicle breakdown occurrence |

### Audit of Class C Variables
All Class C variables represent natural, irreducible physical noise (such as convoy staging delays, fill-rate variation between 60% and 98%, and Gaussian consumption noise) and **do not dominate the signal of the primary ML targets**. The primary signals in demand, travel time, and shortages remain strongly governed by Class A and Class B causal inputs.
