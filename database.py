"""
Database Access Layer for Smart Manhole Safety System.
Uses SQLite for persistent storage of telemetry, risk assessments, and incident records.
"""

import sqlite3
import json
from datetime import datetime
from config import DATABASE_PATH, DEFAULT_MANHOLE

def get_connection():
    """Create a thread-safe connection to the SQLite database."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize SQLite database tables and seed the default monitored manhole."""
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Manhole Infrastructure Assets
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS manholes (
        id TEXT PRIMARY KEY,
        location TEXT NOT NULL,
        depth_meters REAL NOT NULL,
        diameter_cm REAL NOT NULL,
        catchment_area TEXT NOT NULL,
        installed_date TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'OPERATIONAL'
    );
    """)

    # 2. Time-series Sensor Readings
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sensor_readings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        manhole_id TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        gas_ppm REAL NOT NULL,
        water_level_pct REAL NOT NULL,
        temperature_c REAL NOT NULL,
        humidity_pct REAL NOT NULL,
        battery_pct REAL NOT NULL DEFAULT 98.5,
        scenario TEXT DEFAULT 'normal',
        FOREIGN KEY (manhole_id) REFERENCES manholes (id)
    );
    """)

    # 3. DNN Risk Predictions & GenAI Explanations
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS risk_assessments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        reading_id INTEGER NOT NULL,
        manhole_id TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        risk_level TEXT NOT NULL,
        confidence REAL NOT NULL,
        prob_safe REAL NOT NULL,
        prob_warning REAL NOT NULL,
        prob_critical REAL NOT NULL,
        genai_explanation TEXT NOT NULL,
        genai_recommendations TEXT NOT NULL,
        ppe_requirements TEXT,
        evacuation_radius_m INTEGER DEFAULT 0,
        FOREIGN KEY (reading_id) REFERENCES sensor_readings (id),
        FOREIGN KEY (manhole_id) REFERENCES manholes (id)
    );
    """)

    # 4. Critical Incidents Log
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS incidents (
        incident_id TEXT PRIMARY KEY,
        manhole_id TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        severity TEXT NOT NULL,
        title TEXT NOT NULL,
        root_cause TEXT NOT NULL,
        peak_gas REAL NOT NULL,
        peak_water REAL NOT NULL,
        peak_temp REAL NOT NULL,
        action_log TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'OPEN',
        FOREIGN KEY (manhole_id) REFERENCES manholes (id)
    );
    """)

    # Insert default manhole if not exists
    cursor.execute("""
    INSERT OR IGNORE INTO manholes (id, location, depth_meters, diameter_cm, catchment_area, installed_date, status)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        DEFAULT_MANHOLE["id"],
        DEFAULT_MANHOLE["location"],
        DEFAULT_MANHOLE["depth_meters"],
        DEFAULT_MANHOLE["diameter_cm"],
        DEFAULT_MANHOLE["catchment_area"],
        DEFAULT_MANHOLE["installed_date"],
        DEFAULT_MANHOLE["status"]
    ))

    conn.commit()
    conn.close()

def insert_reading(data):
    """Insert a new sensor telemetry reading."""
    conn = get_connection()
    cursor = conn.cursor()
    timestamp = data.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    cursor.execute("""
    INSERT INTO sensor_readings (manhole_id, timestamp, gas_ppm, water_level_pct, temperature_c, humidity_pct, battery_pct, scenario)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get("manhole_id", DEFAULT_MANHOLE["id"]),
        timestamp,
        round(float(data["gas_ppm"]), 2),
        round(float(data["water_level_pct"]), 2),
        round(float(data["temperature_c"]), 2),
        round(float(data["humidity_pct"]), 2),
        round(float(data.get("battery_pct", 98.0)), 1),
        data.get("scenario", "normal")
    ))
    reading_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return reading_id

def get_latest_reading(manhole_id=DEFAULT_MANHOLE["id"]):
    """Fetch the most recent sensor reading for the specified manhole."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT * FROM sensor_readings 
    WHERE manhole_id = ? 
    ORDER BY id DESC LIMIT 1
    """, (manhole_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_reading_history(manhole_id=DEFAULT_MANHOLE["id"], limit=30):
    """Fetch the historical sensor readings in ascending order for charting."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT * FROM (
        SELECT r.*, a.risk_level
        FROM sensor_readings r
        LEFT JOIN risk_assessments a ON r.id = a.reading_id
        WHERE r.manhole_id = ?
        ORDER BY r.id DESC
        LIMIT ?
    ) ORDER BY id ASC
    """, (manhole_id, limit))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def insert_assessment(data):
    """Store DNN risk prediction and GenAI safety recommendations."""
    conn = get_connection()
    cursor = conn.cursor()
    timestamp = data.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    recs = data.get("genai_recommendations", [])
    if isinstance(recs, list):
        recs = json.dumps(recs)

    ppe = data.get("ppe_requirements", [])
    if isinstance(ppe, list):
        ppe = json.dumps(ppe)

    cursor.execute("""
    INSERT INTO risk_assessments (
        reading_id, manhole_id, timestamp, risk_level, confidence,
        prob_safe, prob_warning, prob_critical, genai_explanation,
        genai_recommendations, ppe_requirements, evacuation_radius_m
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["reading_id"],
        data.get("manhole_id", DEFAULT_MANHOLE["id"]),
        timestamp,
        data["risk_level"],
        round(float(data["confidence"]), 4),
        round(float(data.get("prob_safe", 0.0)), 4),
        round(float(data.get("prob_warning", 0.0)), 4),
        round(float(data.get("prob_critical", 0.0)), 4),
        data["genai_explanation"],
        recs,
        ppe,
        int(data.get("evacuation_radius_m", 0))
    ))
    assessment_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return assessment_id

def get_latest_assessment(manhole_id=DEFAULT_MANHOLE["id"]):
    """Fetch the latest safety assessment for the specified manhole."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT * FROM risk_assessments
    WHERE manhole_id = ?
    ORDER BY id DESC LIMIT 1
    """, (manhole_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    try:
        d["genai_recommendations"] = json.loads(d["genai_recommendations"])
    except Exception:
        pass
    try:
        d["ppe_requirements"] = json.loads(d["ppe_requirements"])
    except Exception:
        pass
    return d

def insert_incident(data):
    """Log an incident report entry."""
    conn = get_connection()
    cursor = conn.cursor()
    actions = data.get("action_log", [])
    if isinstance(actions, list):
        actions = json.dumps(actions)

    cursor.execute("""
    INSERT OR REPLACE INTO incidents (
        incident_id, manhole_id, timestamp, severity, title,
        root_cause, peak_gas, peak_water, peak_temp, action_log, status
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["incident_id"],
        data.get("manhole_id", DEFAULT_MANHOLE["id"]),
        data.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        data["severity"],
        data["title"],
        data["root_cause"],
        round(float(data["peak_gas"]), 2),
        round(float(data["peak_water"]), 2),
        round(float(data["peak_temp"]), 2),
        actions,
        data.get("status", "OPEN")
    ))
    conn.commit()
    conn.close()
    return data["incident_id"]

def get_incidents(manhole_id=DEFAULT_MANHOLE["id"], limit=10):
    """Retrieve recent incident reports."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT * FROM incidents
    WHERE manhole_id = ?
    ORDER BY timestamp DESC
    LIMIT ?
    """, (manhole_id, limit))
    rows = cursor.fetchall()
    conn.close()
    results = []
    for r in rows:
        d = dict(r)
        try:
            d["action_log"] = json.loads(d["action_log"])
        except Exception:
            pass
        results.append(d)
    return results

def get_incident_by_id(incident_id):
    """Retrieve single incident report by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT * FROM incidents WHERE incident_id = ?
    """, (incident_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    try:
        d["action_log"] = json.loads(d["action_log"])
    except Exception:
        pass
    return d
