"""
AI Smart Manhole Safety Monitoring System - Primary Flask Application.
Provides RESTful APIs for sensor simulation, DNN risk prediction, GenAI safety advisories,
and incident reporting, along with the real-time operational dashboard.
"""

from flask import Flask, render_template, jsonify, request
from config import DEFAULT_MANHOLE, THRESHOLDS, AUTO_POLL_INTERVAL_SECONDS
from database import (
    init_db,
    insert_reading,
    get_latest_reading,
    get_reading_history,
    insert_assessment,
    get_latest_assessment,
    get_incidents,
    get_incident_by_id
)
from models.dnn_model import dnn_engine
from services.sensor_simulator import simulator
from services.genai_advisor import genai_advisor
from services.alert_service import alert_service
from seed_data import seed_database

app = Flask(__name__)
app.config["SECRET_KEY"] = "smart-manhole-prototype-key-2026"

# Ensure DB is initialized on boot
init_db()

@app.route("/")
def index():
    """Render the primary real-time operations dashboard."""
    latest_reading = get_latest_reading(DEFAULT_MANHOLE["id"])
    latest_assessment = get_latest_assessment(DEFAULT_MANHOLE["id"])
    return render_template(
        "index.html",
        manhole=DEFAULT_MANHOLE,
        thresholds=THRESHOLDS,
        latest_reading=latest_reading,
        latest_assessment=latest_assessment,
        poll_interval=AUTO_POLL_INTERVAL_SECONDS
    )

@app.route("/api/sensors/simulate", methods=["POST"])
def simulate_sensor_data():
    """
    Simulate new sensor telemetry.
    Body JSON:
        scenario: "normal" | "gas_leak" | "flood" | "hazardous" | "warning_gas" | "random"
        manual_values: optional dict with custom values
        auto_analyze: boolean (if True, runs DNN & GenAI automatically)
    """
    payload = request.get_json() or {}
    scenario = payload.get("scenario", "normal")
    manual_values = payload.get("manual_values")
    auto_analyze = payload.get("auto_analyze", False)

    # Generate telemetry
    reading_data = simulator.generate(scenario=scenario, manual_values=manual_values)
    reading_id = insert_reading(reading_data)
    reading_data["id"] = reading_id

    response = {
        "success": True,
        "reading": reading_data,
        "assessment": None,
        "incident": None
    }

    # If auto_analyze requested (e.g. during auto-polling)
    if auto_analyze:
        dnn_result = dnn_engine.predict(
            reading_data["gas_ppm"],
            reading_data["water_level_pct"],
            reading_data["temperature_c"],
            reading_data["humidity_pct"],
            reading_data.get("delta_gas", 0.0),
            reading_data.get("delta_water", 0.0)
        )
        ai_assessment = genai_advisor.explain_and_recommend(reading_data, dnn_result)

        assessment_record = {
            "reading_id": reading_id,
            "manhole_id": reading_data["manhole_id"],
            "timestamp": reading_data["timestamp"],
            "risk_level": dnn_result["risk_level"],
            "confidence": dnn_result["confidence"],
            "prob_safe": dnn_result["probabilities"]["SAFE"],
            "prob_warning": dnn_result["probabilities"]["WARNING"],
            "prob_critical": dnn_result["probabilities"]["CRITICAL"],
            "genai_explanation": ai_assessment["explanation"],
            "genai_recommendations": ai_assessment["recommended_actions"],
            "ppe_requirements": ai_assessment["ppe_requirements"],
            "evacuation_radius_m": ai_assessment["evacuation_radius_meters"]
        }
        insert_assessment(assessment_record)

        incident_record = None
        if dnn_result["risk_level"] == "CRITICAL":
            incident_record = alert_service.process_and_create_incident_if_needed(reading_data, ai_assessment)

        response["assessment"] = {
            "dnn": dnn_result,
            "genai": ai_assessment
        }
        response["incident"] = incident_record

    return jsonify(response)

@app.route("/api/sensors/latest", methods=["GET"])
def get_latest():
    """Fetch current sensor state and latest safety assessment."""
    reading = get_latest_reading(DEFAULT_MANHOLE["id"])
    assessment = get_latest_assessment(DEFAULT_MANHOLE["id"])
    return jsonify({
        "success": True,
        "reading": reading,
        "assessment": assessment,
        "manhole": DEFAULT_MANHOLE
    })

@app.route("/api/safety/analyze", methods=["POST"])
def analyze_safety():
    """
    Execute DNN Risk Classification & Local GenAI Explanations on the latest sensor telemetry.
    """
    payload = request.get_json() or {}
    reading_id = payload.get("reading_id")

    if reading_id:
        from database import get_connection
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM sensor_readings WHERE id = ?", (reading_id,))
        row = c.fetchone()
        conn.close()
        reading = dict(row) if row else None
    else:
        reading = get_latest_reading(DEFAULT_MANHOLE["id"])

    if not reading:
        return jsonify({"success": False, "error": "No sensor readings available to analyze."}), 404

    # 1. Run DNN Risk Prediction
    dnn_result = dnn_engine.predict(
        reading["gas_ppm"],
        reading["water_level_pct"],
        reading["temperature_c"],
        reading["humidity_pct"],
        reading.get("delta_gas", 0.0),
        reading.get("delta_water", 0.0)
    )

    # 2. Run Autonomous Local Generative AI Advisor
    genai_result = genai_advisor.explain_and_recommend(reading, dnn_result)

    # 3. Store assessment in SQLite
    assessment_data = {
        "reading_id": reading["id"],
        "manhole_id": reading["manhole_id"],
        "timestamp": reading["timestamp"],
        "risk_level": dnn_result["risk_level"],
        "confidence": dnn_result["confidence"],
        "prob_safe": dnn_result["probabilities"]["SAFE"],
        "prob_warning": dnn_result["probabilities"]["WARNING"],
        "prob_critical": dnn_result["probabilities"]["CRITICAL"],
        "genai_explanation": genai_result["explanation"],
        "genai_recommendations": genai_result["recommended_actions"],
        "ppe_requirements": genai_result["ppe_requirements"],
        "evacuation_radius_m": genai_result["evacuation_radius_meters"]
    }
    assessment_id = insert_assessment(assessment_data)

    # 4. Check if Incident Report should be auto-created
    incident = None
    if dnn_result["risk_level"] == "CRITICAL":
        incident = alert_service.process_and_create_incident_if_needed(reading, genai_result)

    return jsonify({
        "success": True,
        "assessment_id": assessment_id,
        "dnn": dnn_result,
        "genai": genai_result,
        "reading": reading,
        "incident": incident
    })

@app.route("/api/history", methods=["GET"])
def get_history():
    """Retrieve historical telemetry readings for Chart.js & data table."""
    limit = request.args.get("limit", default=30, type=int)
    history = get_reading_history(DEFAULT_MANHOLE["id"], limit=limit)
    return jsonify({
        "success": True,
        "count": len(history),
        "history": history
    })

@app.route("/api/incidents", methods=["GET"])
def list_incidents():
    """Retrieve list of logged incidents."""
    incidents = get_incidents(DEFAULT_MANHOLE["id"], limit=10)
    return jsonify({
        "success": True,
        "incidents": incidents
    })

@app.route("/api/incident/report", methods=["GET", "POST"])
def incident_report():
    """
    Retrieve or synthesize a printable Incident Report.
    Query/Body param: incident_id (optional)
    """
    incident_id = request.args.get("incident_id")
    if not incident_id and request.is_json:
        incident_id = request.get_json().get("incident_id")

    latest_reading = get_latest_reading(DEFAULT_MANHOLE["id"])
    latest_assessment = get_latest_assessment(DEFAULT_MANHOLE["id"])

    report_data = alert_service.generate_incident_report(
        incident_id=incident_id,
        latest_telemetry=latest_reading,
        latest_assessment=latest_assessment
    )

    return jsonify({
        "success": True,
        "report": report_data
    })

@app.route("/api/system/reset", methods=["POST"])
def system_reset():
    """Reset and re-seed the telemetry system for fresh testing demonstrations."""
    seed_database()
    return jsonify({"success": True, "message": "System re-initialized and seeded with baseline telemetry."})

if __name__ == "__main__":
    print("=" * 60)
    print("AI SMART MANHOLE SAFETY MONITORING SYSTEM")
    print(f"Monitored Asset: {DEFAULT_MANHOLE['id']} ({DEFAULT_MANHOLE['location']})")
    print("Local GenAI Engine: ACTIVE (Strictly Offline Mode)")
    print("Starting Flask Server at http://127.0.0.1:5000")
    print("=" * 60)
    app.run(host="127.0.0.1", port=5000, debug=True)
