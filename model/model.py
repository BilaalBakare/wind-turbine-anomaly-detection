import joblib

class TurbineMonitor:
    def __init__(self, model_path, alert_threshold=300):
        """
        model_path: path to the saved .pkl model
        alert_threshold: kW deviation above which we consider it anomalous
                          (we chose 300 kW = ~4-5x the model's MAE of ~67 kW)
        """
        self.model = joblib.load(model_path)
        self.alert_threshold = alert_threshold

    def predict_expected_power(self, wind_speed, wind_direction):
        """Returns the model's expected 'normal' power output for given conditions."""
        # model expects a 2D array-like input, even for a single row
        X = [[wind_speed, wind_direction]]
        return self.model.predict(X)[0]

    def check_status(self, wind_speed, wind_direction, actual_power):
        """
        Compares actual power against expected power.
        Returns a dict with the result, so callers can use it programmatically
        (not just print it) — this makes the class usable in the simulation loop
        without forcing text-parsing.
        """
        expected = self.predict_expected_power(wind_speed, wind_direction)
        residual = expected - actual_power
        is_anomaly = residual > self.alert_threshold

        return {
            'expected_power': expected,
            'actual_power': actual_power,
            'residual': residual,
            'is_anomaly': is_anomaly
        }

    def report(self, wind_speed, wind_direction, actual_power):
        """
        Runs the check and prints an engineer-facing message.
        Separated from check_status so you can get either the raw dict
        (for logging/looping) or the human message (for alerting), independently.
        """
        result = self.check_status(wind_speed, wind_direction, actual_power)

        if result['is_anomaly']:
            print(
                f"⚠️ ALERT: Turbine underperforming. "
                f"Expected ~{result['expected_power']:.0f} kW, "
                f"actual {result['actual_power']:.0f} kW "
                f"(deficit: {result['residual']:.0f} kW). "
                f"Recommend inspection."
            )
        else:
            print(
                f"✅ Normal operation. "
                f"Expected ~{result['expected_power']:.0f} kW, "
                f"actual {result['actual_power']:.0f} kW."
            )

        return result