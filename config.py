"""
AI Smart Manhole Safety Monitoring System - Configuration Module
Defines system-wide thresholds, OSHA limits, simulation presets, and DB paths.
"""

import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = str(BASE_DIR / "manhole_safety.db")

# Default Monitored Manhole
DEFAULT_MANHOLE = {
    "id": "MH-001",
    "location": "District 4 - Central Underground Interceptor 12B",
    "depth_meters": 3.8,
    "diameter_cm": 90.0,
    "catchment_area": "Downtown Commercial / Stormwater Zone",
    "installed_date": "2024-03-15",
    "status": "OPERATIONAL"
}

# Sensor Operational Ranges & Thresholds (Wastewater & OSHA Confined Space Standards)
THRESHOLDS = {
    "gas_ppm": {
        "unit": "PPM",
        "description": "Toxic Gases (H2S & Methane CH4 Index)",
        "safe_max": 15.0,     # Standard sewer ambient baseline
        "warning_max": 50.0,  # OSHA PEL / Evacuation caution
        "critical_min": 50.0, # OSHA STEL / IDLH approaching zone
        "abs_min": 0.0,
        "abs_max": 150.0
    },
    "water_level_pct": {
        "unit": "%",
        "description": "Sewer Pipe Fill Level & Surcharge Risk",
        "safe_max": 40.0,     # Dry weather nominal baseflow
        "warning_max": 75.0,  # Storm surge / Flow restriction
        "critical_min": 75.0, # Imminent surface overflow / Backflow
        "abs_min": 0.0,
        "abs_max": 100.0
    },
    "temperature_c": {
        "unit": "°C",
        "description": "Internal Manhole Chamber Temperature",
        "safe_max": 35.0,     # Ambient seasonal sewer temp
        "warning_max": 45.0,  # Elevated fermentation / Industrial runoff
        "critical_min": 45.0, # Extreme biological decomposition / Chemical reaction
        "abs_min": 10.0,
        "abs_max": 65.0
    },
    "humidity_pct": {
        "unit": "%",
        "description": "Relative Humidity (Vapor Saturation)",
        "safe_max": 75.0,
        "warning_max": 90.0,
        "critical_min": 90.0, # Saturated vapor, rapid condensation & misting
        "abs_min": 30.0,
        "abs_max": 100.0
    }
}

# Risk Labels
RISK_SAFE = "SAFE"
RISK_WARNING = "WARNING"
RISK_CRITICAL = "CRITICAL"

RISK_COLORS = {
    RISK_SAFE: "#10b981",      # Emerald Green
    RISK_WARNING: "#f59e0b",   # Amber / Orange
    RISK_CRITICAL: "#ef4444"   # Crimson Red
}

# Auto-polling Interval in seconds
AUTO_POLL_INTERVAL_SECONDS = 5
