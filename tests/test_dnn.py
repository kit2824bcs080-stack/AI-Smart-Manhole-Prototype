"""
Unit tests for Deep Neural Network (DNN) Risk Prediction Model.
"""

import unittest
from models.dnn_model import dnn_engine

class TestDNNModel(unittest.TestCase):
    def test_probabilities_sum_to_one(self):
        result = dnn_engine.predict(15.0, 30.0, 24.0, 65.0)
        p = result["probabilities"]
        total = p["SAFE"] + p["WARNING"] + p["CRITICAL"]
        self.assertAlmostEqual(total, 1.0, places=3)

    def test_safe_classification(self):
        result = dnn_engine.predict(3.5, 18.0, 23.0, 60.0)
        self.assertEqual(result["risk_level"], "SAFE")
        self.assertGreater(result["confidence"], 0.70)

    def test_critical_gas_leak(self):
        result = dnn_engine.predict(85.0, 30.0, 28.0, 80.0)
        self.assertEqual(result["risk_level"], "CRITICAL")
        self.assertGreater(result["confidence"], 0.80)

    def test_critical_flood(self):
        result = dnn_engine.predict(8.0, 94.0, 22.0, 96.0)
        self.assertEqual(result["risk_level"], "CRITICAL")

if __name__ == "__main__":
    unittest.main()
