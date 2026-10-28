"""
IoT Sensor Telemetry Simulator.
Simulates environmental sensors installed inside underground sewer manhole MH-001.
Includes realistic physical drift, rate-of-change computation, and standard hazard scenarios.
"""

import random
from datetime import datetime
from config import DEFAULT_MANHOLE, THRESHOLDS
from database import get_latest_reading

class SensorSimulator:
    def __init__(self, manhole_id=DEFAULT_MANHOLE["id"]):
        self.manhole_id = manhole_id

    def generate(self, scenario="normal", manual_values=None):
        """
        Generate sensor readings for the specified scenario or use manual overrides.
        Calculates delta (rate of change) from the previous reading.
        """
        previous_reading = get_latest_reading(self.manhole_id)

        if manual_values:
            gas_ppm = float(manual_values.get("gas_ppm", 5.0))
            water_level_pct = float(manual_values.get("water_level_pct", 20.0))
            temperature_c = float(manual_values.get("temperature_c", 24.0))
            humidity_pct = float(manual_values.get("humidity_pct", 65.0))
            battery_pct = float(manual_values.get("battery_pct", 98.2))
            scenario_name = "manual"
        else:
            scenario_name = scenario.lower()
            if scenario_name == "gas_leak":
                # Toxic gas buildup (H2S / Methane surge)
                gas_ppm = random.uniform(55.0, 98.0)
                water_level_pct = random.uniform(22.0, 45.0)
                temperature_c = random.uniform(29.0, 36.5)
                humidity_pct = random.uniform(75.0, 88.0)
            elif scenario_name == "flood":
                # Stormwater inundation / hydraulic overflow
                gas_ppm = random.uniform(8.0, 22.0)
                water_level_pct = random.uniform(78.0, 96.5)
                temperature_c = random.uniform(19.0, 25.0)
                humidity_pct = random.uniform(92.0, 99.5)
            elif scenario_name == "hazardous":
                # Multi-variable catastrophic failure
                gas_ppm = random.uniform(65.0, 115.0)
                water_level_pct = random.uniform(76.0, 94.0)
                temperature_c = random.uniform(38.0, 48.0)
                humidity_pct = random.uniform(90.0, 99.0)
            elif scenario_name == "warning_gas":
                # Moderate elevated gas
                gas_ppm = random.uniform(25.0, 48.0)
                water_level_pct = random.uniform(20.0, 40.0)
                temperature_c = random.uniform(24.0, 32.0)
                humidity_pct = random.uniform(65.0, 80.0)
            elif scenario_name == "warning_water":
                # Moderate rising water
                gas_ppm = random.uniform(5.0, 18.0)
                water_level_pct = random.uniform(50.0, 72.0)
                temperature_c = random.uniform(21.0, 27.0)
                humidity_pct = random.uniform(75.0, 89.0)
            elif scenario_name == "random":
                # Continuous random walk
                if previous_reading:
                    gas_ppm = max(0.5, min(140.0, previous_reading["gas_ppm"] + random.uniform(-4.0, 6.0)))
                    water_level_pct = max(2.0, min(99.0, previous_reading["water_level_pct"] + random.uniform(-3.0, 5.0)))
                    temperature_c = max(15.0, min(50.0, previous_reading["temperature_c"] + random.uniform(-0.8, 1.2)))
                    humidity_pct = max(35.0, min(99.0, previous_reading["humidity_pct"] + random.uniform(-2.0, 2.5)))
                else:
                    gas_ppm = random.uniform(3.0, 12.0)
                    water_level_pct = random.uniform(15.0, 35.0)
                    temperature_c = random.uniform(22.0, 26.0)
                    humidity_pct = random.uniform(58.0, 72.0)
            else:
                # Normal nominal baseline
                gas_ppm = random.uniform(2.5, 9.5)
                water_level_pct = random.uniform(14.0, 32.0)
                temperature_c = random.uniform(22.0, 26.5)
                humidity_pct = random.uniform(58.0, 72.0)

            battery_pct = 98.5 - random.uniform(0.1, 0.9)

        # Compute rate of change (delta) if previous reading exists
        if previous_reading:
            delta_gas = gas_ppm - previous_reading["gas_ppm"]
            delta_water = water_level_pct - previous_reading["water_level_pct"]
        else:
            delta_gas = 0.0
            delta_water = 0.0

        # Calculate estimated water depth in cm from manhole total depth (e.g., 3.8m = 380cm)
        total_depth_cm = DEFAULT_MANHOLE["depth_meters"] * 100.0
        water_depth_cm = round((water_level_pct / 100.0) * total_depth_cm, 1)

        return {
            "manhole_id": self.manhole_id,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "gas_ppm": round(gas_ppm, 2),
            "water_level_pct": round(water_level_pct, 2),
            "water_depth_cm": water_depth_cm,
            "temperature_c": round(temperature_c, 2),
            "humidity_pct": round(humidity_pct, 2),
            "battery_pct": round(battery_pct, 1),
            "delta_gas": round(delta_gas, 2),
            "delta_water": round(delta_water, 2),
            "scenario": scenario_name
        }

# Global simulator instance
simulator = SensorSimulator()
