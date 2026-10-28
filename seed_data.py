"""
Database Seeding Utility.
Initializes tables and seeds realistic historical telemetry records for MH-001.
"""

from datetime import datetime, timedelta
import random
from database import init_db, insert_reading, insert_assessment, insert_incident
from models.dnn_model import dnn_engine
from services.genai_advisor import genai_advisor
from config import DEFAULT_MANHOLE

def seed_database():
    print("Initializing database tables...")
    init_db()

    print("Generating initial historical telemetry readings for MH-001...")
    now = datetime.now()

    # Create 25 historical data points over the last 2 hours
    base_gas = 4.5
    base_water = 18.0
    base_temp = 23.0
    base_humidity = 64.0

    readings = []
    for i in range(25, 0, -1):
        ts = (now - timedelta(minutes=i * 4)).strftime("%Y-%m-%d %H:%M:%S")

        # Fluctuation pattern: occasional small bump around reading 15
        if 8 <= i <= 12:
            gas = round(base_gas + random.uniform(8.0, 18.0), 2)
            water = round(base_water + random.uniform(10.0, 22.0), 2)
            temp = round(base_temp + random.uniform(2.0, 5.0), 2)
            humidity = round(base_humidity + random.uniform(8.0, 14.0), 2)
            scenario = "warning_gas"
        else:
            gas = round(base_gas + random.uniform(-1.0, 2.5), 2)
            water = round(base_water + random.uniform(-2.0, 4.0), 2)
            temp = round(base_temp + random.uniform(-0.8, 1.2), 2)
            humidity = round(base_humidity + random.uniform(-3.0, 4.0), 2)
            scenario = "normal"

        reading_data = {
            "manhole_id": DEFAULT_MANHOLE["id"],
            "timestamp": ts,
            "gas_ppm": max(1.0, gas),
            "water_level_pct": max(5.0, water),
            "temperature_c": temp,
            "humidity_pct": min(99.0, humidity),
            "battery_pct": round(98.8 - (25 - i) * 0.02, 1),
            "scenario": scenario
        }

        r_id = insert_reading(reading_data)

        # Run DNN prediction
        dnn_result = dnn_engine.predict(
            reading_data["gas_ppm"],
            reading_data["water_level_pct"],
            reading_data["temperature_c"],
            reading_data["humidity_pct"]
        )

        # Run GenAI Advisor
        ai_result = genai_advisor.explain_and_recommend(reading_data, dnn_result)

        assessment_data = {
            "reading_id": r_id,
            "manhole_id": DEFAULT_MANHOLE["id"],
            "timestamp": ts,
            "risk_level": dnn_result["risk_level"],
            "confidence": dnn_result["confidence"],
            "prob_safe": dnn_result["probabilities"]["SAFE"],
            "prob_warning": dnn_result["probabilities"]["WARNING"],
            "prob_critical": dnn_result["probabilities"]["CRITICAL"],
            "genai_explanation": ai_result["explanation"],
            "genai_recommendations": ai_result["recommended_actions"],
            "ppe_requirements": ai_result["ppe_requirements"],
            "evacuation_radius_m": ai_result["evacuation_radius_meters"]
        }

        insert_assessment(assessment_data)

    print("Historical data seeded successfully! 25 records generated.")

if __name__ == "__main__":
    seed_database()
