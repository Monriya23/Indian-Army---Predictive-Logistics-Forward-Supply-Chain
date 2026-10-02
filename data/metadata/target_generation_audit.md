# Target Generation & Learnability Audit

## 1. Mathematical Formulation & Code Implementation of ML Targets

This document audits the generation of machine learning targets across the three predictive tasks to verify their physical realism, learnability, and absence of trivial recovery shortcuts.

---

### Target 1: `demand_next_day` (Next-Day Demand, kg)
* **Code Implementation**: [`data_pipeline/features/demand_features.py`](file:///c:/Users/riyam/Indian%20Army%20Logistics/data_pipeline/features/demand_features.py#L55)
* **Formula**:
  $$\text{demand\_next\_day}_{n, c, t} = \text{final\_demand}_{n, c, t+1}$$
* **Generation Mechanics**: Forward shift of $1$ day within grouped series $(\text{node\_id}, \text{supply\_category})$.
* **Distributional Summary ($N = 79,425$)**:
  * Mean: $1,558.32\text{ kg}$
  * Std Dev: $1,352.09\text{ kg}$
  * Min: $67.10\text{ kg}$ | 25th: $551.20\text{ kg}$ | Median: $1,098.90\text{ kg}$ | 75th: $2,240.10\text{ kg}$ | Max: $13,465.50\text{ kg}$
* **Learnability & Feature Correlations**:
  * Autoregressive Signal: $\text{lag\_1}$ vs $\text{demand\_next\_day}$ Pearson $r = +0.892$.
  * Rolling Trend Signal: $\text{rolling\_mean\_7}$ vs $\text{demand\_next\_day}$ Pearson $r = +0.901$.
  * Environmental Covariates: Significant non-linear seasonal and temperature coupling (e.g. Ladakh Fuel vs Temperature Pearson $r = -0.574$; Rajasthan Water vs Temperature Pearson $r = +0.206$).
* **Artificial Shortcut Evaluation**: **LOW RISK**. While historical demand provides an autoregressive baseline, future demand fluctuates based on forward weather variations, seasonal cycles, and stochastic noise. The model must learn both temporal trends and weather elasticities.

---

### Target 2: `demand_next_7_days` (Cumulative 7-Day Demand, kg)
* **Code Implementation**: [`data_pipeline/features/demand_features.py`](file:///c:/Users/riyam/Indian%20Army%20Logistics/data_pipeline/features/demand_features.py#L58-L60)
* **Formula**:
  $$\text{demand\_next\_7\_days}_{n, c, t} = \sum_{k=1}^7 \text{final\_demand}_{n, c, t+k}$$
* **Generation Mechanics**: Reverse-window rolling sum over 7 forward steps shifted by 1 day.
* **Distributional Summary ($N = 79,425$)**:
  * Mean: $10,907.83\text{ kg}$
  * Std Dev: $9,412.78\text{ kg}$
  * Min: $557.30\text{ kg}$ | Median: $7,628.30\text{ kg}$ | Max: $82,123.90\text{ kg}$
* **Learnability**: Strongly smoothed compared to daily demand, enabling long-range forward planning and replenishment scheduling.

---

### Target 3: `actual_travel_time_hr` (Actual Convoy Transit Time, Hours)
* **Code Implementation**: [`data_pipeline/simulation/shipments.py`](file:///c:/Users/riyam/Indian%20Army%20Logistics/data_pipeline/simulation/shipments.py#L125-L135)
* **Formula**:
  $$\text{actual\_travel\_time\_hr} = \text{planned\_travel\_time\_hr} \cdot (1 + \text{EnvFriction}) \cdot \text{TerrainPenalty} \cdot \text{DisruptionMult} + \epsilon_{\text{transit}}$$
  Where:
  * $\text{EnvFriction} = (WS \cdot 0.45 + \frac{\text{snow}}{15} \cdot 0.35 + \frac{\text{precip}}{50} \cdot 0.25) \cdot (1.1 - \text{weather\_resilience})$
  * $\text{TerrainPenalty} = 1.0 + (\text{terrain\_difficulty} \cdot 0.25) + (\frac{\text{elevation\_change\_m}}{2500} \cdot 0.15)$
* **Distributional Summary ($N = 19,381$)**:
  * Planned Duration Mean: $3.80\text{ hrs}$ (Std: $2.89\text{ hrs}$, Range: $0.62 - 13.93\text{ hrs}$)
  * Actual Duration Mean: $4.58\text{ hrs}$ (Std: $3.91\text{ hrs}$, Range: $0.50 - 86.11\text{ hrs}$)
* **Learnability & Feature Correlations**:
  * Planned Duration: Pearson $r = +0.921$, Spearman $\rho = +0.977$
  * Driving Distance: Pearson $r = +0.621$, Spearman $\rho = +0.673$
  * Terrain Difficulty: Pearson $r = +0.348$, Spearman $\rho = +0.455$
  * Weather Severity: Pearson $r = +0.277$, Spearman $\rho = +0.234$
* **Artificial Shortcut Evaluation**: **LOW RISK**. `actual_travel_time_hr` is non-linear and subject to interaction terms between vehicle weight utilization, terrain gradient, severe weather friction, and discrete disruption multipliers. A model cannot simply predict actual travel time from planned travel time alone without learning the weather and disruption penalties.

---

### Target 4: `shortage_in_next_7_days` (Binary Shortage Risk Flag)
* **Code Implementation**: [`data_pipeline/features/shortage_features.py`](file:///c:/Users/riyam/Indian%20Army%20Logistics/data_pipeline/features/shortage_features.py#L58-L62)
* **Formula**:
  $$\text{shortage\_in\_next\_7\_days}_{n, c, t} = \max_{k=1..7}\left(\mathbb{I}\left(\text{closing\_inventory}_{n, c, t+k} \le \text{critical\_threshold}_{n, c}\right)\right)$$
* **Distributional Summary ($N = 81,675$)**:
  * Class 0 (No Shortage in next 7 days): **$51.51\%$** ($42,074$ rows)
  * Class 1 (Shortage in next 7 days): **$48.49\%$** ($39,601$ rows)
* **Group Comparisons (Class 0 vs Class 1)**:
  * Mean Closing Inventory: Class 0 $= 10,358.4\text{ kg}$ vs Class 1 $= 2,052.9\text{ kg}$
  * Mean Capacity Utilization: Class 0 $= 63.8\%$ vs Class 1 $= 12.6\%$
  * Mean Weather Severity: Class 0 $= 0.0337$ vs Class 1 $= 0.0468$
* **Artificial Shortcut Evaluation**: **MODERATE / CONTROLLED RISK**.
  * *Question*: Does `days_of_supply` trivialize the prediction?
  * *Finding*: While `days_of_supply` has a strong negative correlation (Pearson $r = -0.832$), a static threshold on `days_of_supply` is **insufficient** because:
    1. A node with $4$ days of supply on day $t$ will *not* face a shortage if an inbound convoy arrives on day $2$ or $3$.
    2. A node with $6$ days of supply *will* face a shortage if a cold wave doubles fuel consumption or a landslide delays incoming shipments.
    3. Thus, predicting future shortage requires combining current stock, expected replenishment timing, and weather-driven demand surges.
