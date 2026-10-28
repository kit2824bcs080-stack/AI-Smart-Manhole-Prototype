"""
Unit tests for SensorSimulator service.
"""

import unittest
from services.sensor_simulator import simulator

class TestSensorSimulator(unittest.TestCase):
    def test_normal_scenario_bounds(self):
        reading = simulator.generate(scenario="normal")
        self.assertGreaterEqual(reading["gas_ppm"], 0.0)
        self.assertLessEqual(reading["gas_ppm"], 25.0)
        self.assertGreaterEqual(reading["water_level_pct"], 0.0)
        self.assertLessEqual(reading["water_level_pct"], 50.0)
        self.assertEqual(reading["manhole_id"], "MH-001")

    def test_gas_leak_scenario(self):
        reading = simulator.generate(scenario="gas_leak")
        self.assertGreater(reading["gas_ppm"], 50.0)
        self.assertEqual(reading["scenario"], "gas_leak")

    def test_flood_scenario(self):
        reading = simulator.generate(scenario="flood")
        self.assertGreater(reading["water_level_pct"], 70.0)
        self.assertEqual(reading["scenario"], "flood")

    def test_manual_overrides(self):
        manual = {
            "gas_ppm": 88.5,
            "water_level_pct": 92.0,
            "temperature_c": 37.0,
            "humidity_pct": 95.0
        }
        reading = simulator.generate(manual_values=manual)
        self.assertEqual(reading["gas_ppm"], 88.5)
        self.assertEqual(reading["water_level_pct"], 92.0)
        self.assertEqual(reading["temperature_c"], 37.0)
        self.assertEqual(reading["humidity_pct"], 95.0)
        self.assertEqual(reading["scenario"], "manual")

if __name__ == "__main__":
    unittest.main()
