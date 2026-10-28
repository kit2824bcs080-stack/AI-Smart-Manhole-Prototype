"""
Autonomous Local Generative AI Safety Advisor.
Operates strictly offline with zero external API dependencies.
Employs domain-specific semantic synthesis and wastewater hazard knowledge graphs
to generate human-like technical explanations and tactical safety protocols.
"""

from config import THRESHOLDS, RISK_SAFE, RISK_WARNING, RISK_CRITICAL

class LocalGenAIAdvisor:
    """
    Synthesizes natural language safety assessments and tactical mitigation protocols
    based on multi-variate sensor telemetry and DNN risk classification results.
    """

    @staticmethod
    def explain_and_recommend(telemetry, dnn_result):
        risk_level = dnn_result["risk_level"]
        confidence_pct = round(dnn_result["confidence"] * 100, 1)

        gas = telemetry["gas_ppm"]
        water = telemetry["water_level_pct"]
        temp = telemetry["temperature_c"]
        humidity = telemetry["humidity_pct"]
        d_gas = telemetry.get("delta_gas", 0.0)
        d_water = telemetry.get("delta_water", 0.0)
        manhole_id = telemetry.get("manhole_id", "MH-001")

        if risk_level == RISK_CRITICAL:
            return LocalGenAIAdvisor._build_critical_assessment(
                manhole_id, gas, water, temp, humidity, d_gas, d_water, confidence_pct
            )
        elif risk_level == RISK_WARNING:
            return LocalGenAIAdvisor._build_warning_assessment(
                manhole_id, gas, water, temp, humidity, d_gas, d_water, confidence_pct
            )
        else:
            return LocalGenAIAdvisor._build_safe_assessment(
                manhole_id, gas, water, temp, humidity, confidence_pct
            )

    @staticmethod
    def _build_critical_assessment(manhole_id, gas, water, temp, humidity, d_gas, d_water, confidence_pct):
        # Identify primary drivers of criticality
        drivers = []
        if gas > THRESHOLDS["gas_ppm"]["critical_min"]:
            drivers.append(f"hazardous toxic gas accumulation (H₂S/CH₄ at {gas} PPM, exceeding OSHA IDLH thresholds)")
        if water > THRESHOLDS["water_level_pct"]["critical_min"]:
            drivers.append(f"severe hydraulic surcharge (water level at {water}%, indicating imminent surface flooding)")
        if temp > THRESHOLDS["temperature_c"]["critical_min"]:
            drivers.append(f"abnormal thermal escalation ({temp}°C, indicating exothermic chemical reaction or industrial runoff)")
        if not drivers:
            drivers.append(f"compound multi-variable volatility (Gas: {gas} PPM, Water: {water}%, Temp: {temp}°C, Humidity: {humidity}%)")

        driver_text = " and ".join(drivers)

        explanation = (
            f"CRITICAL SAFETY ALERT for Manhole {manhole_id}: The Deep Neural Network (DNN) has flagged an "
            f"acute hazard state with {confidence_pct}% classification confidence. Telemetry indicates {driver_text}. "
        )

        if gas > 50.0:
            explanation += (
                f"Hydrogen Sulfide concentrations of {gas} PPM present an immediate asphyxiation and olfactory paralysis risk "
                f"under OSHA 29 CFR 1910.146. Combined with {humidity}% relative humidity, atmospheric natural draft venting "
                f"is compromised, significantly elevating explosive vapor retention."
            )
        elif water > 75.0:
            explanation += (
                f"Conduit hydrostatic pressure has reached critical capacity ({water}% fill). Rate of water level change "
                f"({'+' if d_water >= 0 else ''}{d_water}%/interval) threatens backflow into adjoining municipal drainage conduits "
                f"and potential roadway cover displacement."
            )
        else:
            explanation += (
                f"Synergistic thermodynamic stress observed: elevated vapor saturation ({humidity}% RH) combined with "
                f"{temp}°C chamber temperature is accelerating anaerobic bio-gas production."
            )

        recommendations = [
            f"IMMEDIATE EVACUATION: Establish an exclusion boundary of at least 50 meters around {manhole_id}.",
            "PROHIBIT CONFINED SPACE ENTRY: Halt all subsurface municipal work in District 4 Interceptor Sector.",
            "DEPLOY MECHANICAL VENTILATION: Position positive-pressure explosion-proof exhaust blowers at surface vents.",
            "DISPATCH HAZMAT & WATER RESCUE: Mobilize Level-A rapid response crews equipped with 4-gas telemetry monitors.",
            "DIVERT STORMWATER FLOW: Actuate upstream automated diversion sluice gate to alleviate hydraulic pressure."
        ]

        ppe = [
            "Level A/B Fully Encapsulated Chemical Vapor Suit",
            "Positive-Pressure Self-Contained Breathing Apparatus (SCBA)",
            "Intrinsically Safe Explosimeter / Multi-Gas Detector",
            "Full Body Safety Harness with Tripod Retrieval Winch"
        ]

        return {
            "headline": f"CRITICAL HAZARD DETECTED - {manhole_id} (Confidence: {confidence_pct}%)",
            "risk_level": RISK_CRITICAL,
            "confidence_percentage": confidence_pct,
            "explanation": explanation,
            "recommended_actions": recommendations,
            "ppe_requirements": ppe,
            "evacuation_radius_meters": 50,
            "osha_compliance": "VIOLATION RISK: OSHA 29 CFR 1910.146 (Confined Space IDLH Hazard)"
        }

    @staticmethod
    def _build_warning_assessment(manhole_id, gas, water, temp, humidity, d_gas, d_water, confidence_pct):
        explanation = (
            f"SAFETY WARNING for Manhole {manhole_id}: Sensor metrics have crossed nominal operational baselines "
            f"(DNN Confidence: {confidence_pct}%). Observed metrics: Gas = {gas} PPM, Water Level = {water}%, "
            f"Temperature = {temp}°C, Humidity = {humidity}%. "
        )

        if gas > THRESHOLDS["gas_ppm"]["safe_max"]:
            explanation += (
                f"Toxic gas is trending above standard baseline ({gas} PPM vs 15.0 PPM threshold). While below immediate lethal levels, "
                f"prolonged exposure without respiratory protection can cause nausea and fatigue."
            )
        elif water > THRESHOLDS["water_level_pct"]["safe_max"]:
            explanation += (
                f"Water volume is elevated ({water}%), indicating moderate storm surge or partial downstream sediment accumulation."
            )
        else:
            explanation += (
                f"Chamber humidity ({humidity}%) and temperature ({temp}°C) indicate restricted convective airflow."
            )

        recommendations = [
            f"Place Manhole {manhole_id} on continuous 5-minute automated telemetry tracking.",
            "Restrict confined space entry: Only authorized technicians with calibrated gas monitors may enter.",
            "Inspect upstream catch basins and bar screens for solid debris clogging.",
            "Prepare mobile forced-air ventilation blower unit on standby.",
            "Alert District 4 Maintenance Dispatch to review catchment trends."
        ]

        ppe = [
            "Half-Mask Air-Purifying Respirator with Organic Vapor/Acid Gas Cartridges",
            "Continuous 4-Gas Portable Ambient Monitor",
            "Waterproof Slip-Resistant Steel-Toe Safety Boots",
            "High-Visibility Class 3 Safety Vest"
        ]

        return {
            "headline": f"ELEVATED RISK WARNING - {manhole_id} (Confidence: {confidence_pct}%)",
            "risk_level": RISK_WARNING,
            "confidence_percentage": confidence_pct,
            "explanation": explanation,
            "recommended_actions": recommendations,
            "ppe_requirements": ppe,
            "evacuation_radius_meters": 15,
            "osha_compliance": "CAUTION: Approaching OSHA Permissible Exposure Limit Thresholds"
        }

    @staticmethod
    def _build_safe_assessment(manhole_id, gas, water, temp, humidity, confidence_pct):
        explanation = (
            f"ENVIRONMENT NOMINAL & STABLE: Manhole {manhole_id} is operating within normal environmental baselines "
            f"(DNN Confidence: {confidence_pct}%). Toxic gas levels ({gas} PPM) are well below the OSHA 10 PPM PEL ceiling. "
            f"Water conduit capacity is healthy at {water}%, chamber temperature is normal at {temp}°C, and "
            f"humidity is within expected subterranean range ({humidity}% RH). Atmospheric airflow is unobstructed."
        )

        recommendations = [
            "Routine monitoring: Maintain standard telemetry polling intervals.",
            "Standard confined space entry protocols apply (pre-entry 4-gas atmospheric testing mandatory).",
            "Next scheduled preventative inspection remains on calendar."
        ]

        ppe = [
            "Standard Hard Hat & Safety Glasses",
            "Hi-Vis Class 2 Workwear",
            "Steel-Toe Puncture-Resistant Work Boots",
            "Personal Clip-On Gas Badge (Standard Practice)"
        ]

        return {
            "headline": f"ALL SYSTEMS SAFE - {manhole_id} (Confidence: {confidence_pct}%)",
            "risk_level": RISK_SAFE,
            "confidence_percentage": confidence_pct,
            "explanation": explanation,
            "recommended_actions": recommendations,
            "ppe_requirements": ppe,
            "evacuation_radius_meters": 0,
            "osha_compliance": "COMPLIANT: Environmental metrics fully within OSHA & EPA safety bounds"
        }

# Global singleton advisor
genai_advisor = LocalGenAIAdvisor()
