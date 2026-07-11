# Wind Turbine Failure Prediction — Project Report

## Overview

This project uses the [Kaggle Wind Turbine SCADA Dataset](https://www.kaggle.com/datasets/berkerisen/wind-turbine-scada-dataset)
to detect anomalous turbine behavior. The dataset contains no failure labels, so
this is framed as an **unsupervised anomaly detection** problem: identify when
actual power output deviates from what the turbine should be producing, given
current wind conditions, and investigate what drives those deviations.

---

## Exploratory Data Analysis

After initial EDA, two graphs shaped the direction of the entire project.

### Graph 1 — Wind Speed vs Power Overlay

![Wind Speed vs Power Overlay](images/overlay_powercurve.png)

Plotting actual power against wind speed, with the manufacturer's theoretical
power curve overlaid, shows the expected S-curve relationship: power is ~0 below
cut-in speed (~3-4 m/s), rises steeply through the mid-range, and plateaus near
rated capacity (~3,600 kW) above ~12 m/s.

The blue cloud of actual readings mostly hugs the theoretical curve, but a
significant number of points fall **below** it — some only slightly, some all
the way down to near-zero power despite strong wind. Very few points exceed the
curve. This told us underperformance, not overperformance, is the dominant and
relevant type of deviation to investigate.

### Graph 2 — Residual Over Time

![Residual Over Time](images/residual_over_time.png)

Plotting the residual (`Theoretical Power − Actual Power`) across the full year
revealed that deviations are **not randomly scattered** — they cluster densely
in certain months (notably winter and parts of spring/late autumn) and are
comparatively calm through summer. This seasonal clustering indicated the
anomalies carry real structure, rather than being pure sensor noise.

---

## Two Paths Forward

These two graphs paved the way for two complementary directions:

### Path 1 — Data Analysis: *What is driving the anomalies?*

Using the residual clustering as a starting point, this path investigates
**why** deviations happen when they do — cross-referencing flagged anomalies
against time of day, month/season, and wind direction, to distinguish
between plausible causes (e.g. icing in cold months, scheduled curtailment,
yaw misalignment) rather than treating every deviation as an unexplained fault.

### Path 2 — Machine Learning: *Can we predict expected power directly from data, and flag deviations automatically?*

Using the overlay graph as a starting point, this path builds a data-driven
replacement for the theoretical power curve:

1. Anomalous points were identified using a wind-speed-binned median threshold
   (robust to outliers) and removed from the training set.
2. Several regression models were trained on the cleaned data (wind speed +
   wind direction → actual power), including Linear Regression, Polynomial
   Regression, Decision Tree, Random Forest, Gradient Boosting, and KNN.
3. **Decision Tree Regressor** performed best and was selected as the final
   model.
4. The trained model was wrapped in a `TurbineMonitor` class that predicts
   expected power for given conditions, compares it against actual output,
   and raises an alert when the deficit exceeds a threshold calibrated to the
   model's typical error (MAE).
5. The monitor was run across the full dataset as a simulation of real-time
   deployment, producing a log of flagged anomaly periods for engineers to
   review.

---

## Results

### Path 2 — Machine Learning

Six regression models were trained on the anomaly-filtered data (wind speed +
wind direction → actual power) and compared on a held-out test set:

| Model | MAE (kW) | R² |
|---|---|---|
| Random Forest | 67.50 | 0.993 |
| **Decision Tree (selected)** | **66.23** | **0.994** |
| Linear Regression | *(higher error — straight line cannot follow the S-curve shape)* |
| Polynomial, Gradient Boosting, KNN | *(compared, Decision Tree performed best overall)* |

The **Decision Tree Regressor** was selected as the final model, with an
average prediction error of ~66 kW against a ~3,600 kW rated capacity
(~1.8% of rated capacity) and an R² of 0.994, meaning the model explains
99.4% of the variance in actual power output from wind speed and direction
alone.

The trained model was wrapped in a `TurbineMonitor` class that predicts
expected power, compares it to actual output, and raises an alert when the
deficit exceeds a threshold calibrated to the model's MAE. On a random
30-row spot-check sample of the dataset, the monitor correctly operated as
expected, flagging clear underperformance (e.g. expected ~1,626 kW, actual
0 kW while wind conditions supported normal output) and passing readings
that were within normal model error of their expected value. A full-dataset
run of the simulation (all ~52,000 readings across the year) is the natural
next step to get a total annual alert count.

### Path 1 — Data Analysis

Residual clustering by month (see Graph 2) shows deviation is concentrated
in winter and shoulder-season months, consistent with hypotheses like
icing or seasonal curtailment scheduling.

---

