"""
Integration tests for Flask REST API endpoints.
"""

import unittest
import json
from app import app

class TestAPIEndpoints(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True

    def test_index_page(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"AI SMART MANHOLE SAFETY SYSTEM", response.data)
        self.assertIn(b"MH-001", response.data)

    def test_simulate_sensor_data(self):
        response = self.client.post('/api/sensors/simulate', 
                                json={"scenario": "normal", "auto_analyze": True})
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["success"])
        self.assertIn("reading", data)
        self.assertIn("gas_ppm", data["reading"])
        self.assertIn("assessment", data)

    def test_analyze_safety(self):
        response = self.client.post('/api/safety/analyze', json={})
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["success"])
        self.assertIn("dnn", data)
        self.assertIn("genai", data)
        self.assertIn("risk_level", data["dnn"])

    def test_get_history(self):
        response = self.client.get('/api/history?limit=10')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["success"])
        self.assertIsInstance(data["history"], list)

    def test_incident_report(self):
        response = self.client.get('/api/incident/report')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["success"])
        self.assertIn("report", data)
        self.assertEqual(data["report"]["manhole_id"], "MH-001")

if __name__ == "__main__":
    unittest.main()
