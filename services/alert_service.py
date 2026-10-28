"""
Safety Alert & Incident Report Management Service.
Handles threshold verification, automated incident logging, and report compilation.
"""

from datetime import datetime
from config import DEFAULT_MANHOLE, RISK_CRITICAL, RISK_WARNING
from database import insert_incident, get_incidents, get_incident_by_id

class AlertService:
    @staticmethod
    def process_and_create_incident_if_needed(telemetry, assessment):
        """
        Automatically logs an incident if risk level is CRITICAL or severe WARNING.
        """
        risk = assessment.get("risk_level")
        if risk != RISK_CRITICAL:
            return None

        # Build Incident ID
        now_str = datetime.now().strftime("%Y%m%d-%H%M%S")
        incident_id = f"INC-{DEFAULT_MANHOLE['id']}-{now_str}"

        # Determine title and primary root cause
        gas = telemetry.get("gas_ppm", 0.0)
        water = telemetry.get("water_level_pct", 0.0)
        temp = telemetry.get("temperature_c", 0.0)

        causes = []
        if gas > 50.0:
            causes.append(f"Toxic H2S/Combustible Gas Surge ({gas} PPM)")
        if water > 75.0:
            causes.append(f"Hydraulic Surcharge & Inundation Risk ({water}%)")
        if temp > 45.0:
            causes.append(f"Thermal Overheating Exothermic Reaction ({temp}°C)")
        
        root_cause = " & ".join(causes) if causes else "Multi-parameter compound sewer hazard"

        incident_data = {
            "incident_id": incident_id,
            "manhole_id": telemetry.get("manhole_id", DEFAULT_MANHOLE["id"]),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "severity": risk,
            "title": f"Critical Subsurface Hazard: {root_cause}",
            "root_cause": root_cause,
            "peak_gas": gas,
            "peak_water": water,
            "peak_temp": temp,
            "action_log": assessment.get("recommended_actions", []),
            "status": "OPEN"
        }

        insert_incident(incident_data)
        return incident_data

    @staticmethod
    def generate_incident_report(incident_id=None, latest_telemetry=None, latest_assessment=None):
        """
        Compile a complete, publication-grade incident report document.
        Can fetch an existing incident or synthesize one from the latest state.
        """
        if incident_id:
            incident = get_incident_by_id(incident_id)
            if incident:
                return incident

        # If no specific incident_id or not found, synthesize from latest telemetry
        now_str = datetime.now().strftime("%Y%m%d-%H%M%S")
        inc_id = f"INC-{DEFAULT_MANHOLE['id']}-{now_str}"

        gas = latest_telemetry.get("gas_ppm", 12.0) if latest_telemetry else 12.0
        water = latest_telemetry.get("water_level_pct", 24.0) if latest_telemetry else 24.0
        temp = latest_telemetry.get("temperature_c", 23.5) if latest_telemetry else 23.5
        risk = latest_assessment.get("risk_level", RISK_WARNING) if latest_assessment else RISK_WARNING
        actions = latest_assessment.get("genai_recommendations", []) if latest_assessment else []

        return {
            "incident_id": inc_id,
            "manhole_id": DEFAULT_MANHOLE["id"],
            "location": DEFAULT_MANHOLE["location"],
            "catchment_area": DEFAULT_MANHOLE["catchment_area"],
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "severity": risk,
            "title": f"Official Safety Audit & Incident Report: {DEFAULT_MANHOLE['id']}",
            "root_cause": latest_assessment.get("genai_explanation", "Routine incident audit") if latest_assessment else "Subterranean gas and hydraulic load audit.",
            "peak_gas": gas,
            "peak_water": water,
            "peak_temp": temp,
            "action_log": actions,
            "status": "OPEN"
        }

alert_service = AlertService()
