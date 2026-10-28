/**
 * AI Smart Manhole Safety Monitoring System - Main Dashboard Controller.
 * Handles state management, simulated telemetry generation, DNN analysis,
 * GenAI UI updates, auto-polling (5s interval), and incident reporting.
 */

document.addEventListener('DOMContentLoaded', () => {
    // State Variables
    let currentReading = null;
    let autoPollTimer = null;
    let isAutoPolling = false;
    const POLL_INTERVAL_MS = 5000;

    // DOM Elements
    const btnSimulate = document.getElementById('btnSimulate');
    const btnAnalyze = document.getElementById('btnAnalyze');
    const scenarioSelect = document.getElementById('scenarioSelect');
    const autoPollToggle = document.getElementById('autoPollToggle');
    const pollStatusText = document.getElementById('pollStatusText');
    const btnAudioToggle = document.getElementById('btnAudioToggle');
    const emergencyBanner = document.getElementById('emergencyBanner');
    const emergencyBannerText = document.getElementById('emergencyBannerText');
    const btnOpenReport = document.getElementById('btnOpenReport');
    const reportModal = document.getElementById('reportModal');
    const btnCloseModal = document.getElementById('btnCloseModal');
    const btnPrintReport = document.getElementById('btnPrintReport');
    const btnManualModal = document.getElementById('btnManualModal');
    const manualModal = document.getElementById('manualModal');
    const btnCloseManualModal = document.getElementById('btnCloseManualModal');
    const formManual = document.getElementById('formManual');

    // Telemetry DOM
    const valGas = document.getElementById('valGas');
    const barGas = document.getElementById('barGas');
    const deltaGas = document.getElementById('deltaGas');

    const valWater = document.getElementById('valWater');
    const valWaterDepth = document.getElementById('valWaterDepth');
    const barWater = document.getElementById('barWater');
    const deltaWater = document.getElementById('deltaWater');

    const valTemp = document.getElementById('valTemp');
    const barTemp = document.getElementById('barTemp');

    const valHumidity = document.getElementById('valHumidity');
    const barHumidity = document.getElementById('barHumidity');

    // DNN & GenAI DOM
    const riskBadge = document.getElementById('riskBadge');
    const confidenceVal = document.getElementById('confidenceVal');
    const barProbSafe = document.getElementById('barProbSafe');
    const barProbWarn = document.getElementById('barProbWarn');
    const barProbCrit = document.getElementById('barProbCrit');
    const txtProbSafe = document.getElementById('txtProbSafe');
    const txtProbWarn = document.getElementById('txtProbWarn');
    const txtProbCrit = document.getElementById('txtProbCrit');

    const aiHeadline = document.getElementById('aiHeadline');
    const aiExplanation = document.getElementById('aiExplanation');
    const actionsChecklist = document.getElementById('actionsChecklist');
    const ppeContainer = document.getElementById('ppeContainer');
    const oshaTag = document.getElementById('oshaTag');
    const evacRadiusTag = document.getElementById('evacRadiusTag');

    // History Table DOM
    const historyTableBody = document.getElementById('historyTableBody');

    // System Clock
    function updateClock() {
        const now = new Date();
        const clockEl = document.getElementById('systemClock');
        if (clockEl) {
            clockEl.textContent = now.toLocaleTimeString();
        }
    }
    setInterval(updateClock, 1000);
    updateClock();

    // --------------------------------------------------------------------------
    // 1. Toast Notification Helper
    // --------------------------------------------------------------------------
    function showToast(message, type = 'info') {
        const container = document.getElementById('toastContainer');
        if (!container) return;

        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        
        let icon = 'ℹ️';
        if (type === 'critical') icon = '🚨';
        else if (type === 'warning') icon = '⚠️';
        else if (type === 'safe') icon = '✅';

        toast.innerHTML = `<span>${icon}</span> <div>${message}</div>`;
        container.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transition = 'opacity 0.4s ease';
            setTimeout(() => toast.remove(), 400);
        }, 4000);
    }

    // --------------------------------------------------------------------------
    // 2. Audio Toggle
    // --------------------------------------------------------------------------
    if (btnAudioToggle) {
        btnAudioToggle.addEventListener('click', () => {
            const isMuted = window.soundAlerts.toggleMute();
            if (isMuted) {
                btnAudioToggle.innerHTML = '🔇 <span>Audio: Muted</span>';
                btnAudioToggle.classList.remove('active');
            } else {
                btnAudioToggle.innerHTML = '🔊 <span>Audio: On</span>';
                btnAudioToggle.classList.add('active');
                window.soundAlerts.playSafe();
            }
        });
    }

    // --------------------------------------------------------------------------
    // 3. UI Update Helpers
    // --------------------------------------------------------------------------
    function updateTelemetryCards(reading) {
        currentReading = reading;

        // Gas
        valGas.textContent = reading.gas_ppm.toFixed(1);
        const gasPct = Math.min(100, (reading.gas_ppm / 100) * 100);
        barGas.style.width = `${gasPct}%`;
        updateDeltaBadge(deltaGas, reading.delta_gas, 'PPM');

        // Water
        valWater.textContent = reading.water_level_pct.toFixed(1);
        if (valWaterDepth) {
            valWaterDepth.textContent = `${reading.water_depth_cm || (reading.water_level_pct * 3.8).toFixed(0)} cm`;
        }
        barWater.style.width = `${reading.water_level_pct}%`;
        updateDeltaBadge(deltaWater, reading.delta_water, '%');

        // Temp
        valTemp.textContent = reading.temperature_c.toFixed(1);
        const tempPct = Math.min(100, Math.max(0, ((reading.temperature_c - 10) / 50) * 100));
        barTemp.style.width = `${tempPct}%`;

        // Humidity
        valHumidity.textContent = reading.humidity_pct.toFixed(1);
        barHumidity.style.width = `${reading.humidity_pct}%`;

        // Update Chart
        if (typeof updateTelemetryChart === 'function') {
            updateTelemetryChart(reading);
        }
    }

    function updateDeltaBadge(element, delta, unit) {
        if (!element) return;
        const d = parseFloat(delta) || 0;
        if (d > 0.05) {
            element.className = 'rate-of-change rate-up';
            element.textContent = `▲ +${d.toFixed(1)} ${unit}`;
        } else if (d < -0.05) {
            element.className = 'rate-of-change rate-down';
            element.textContent = `▼ ${d.toFixed(1)} ${unit}`;
        } else {
            element.className = 'rate-of-change rate-flat';
            element.textContent = `◆ 0.0 ${unit}`;
        }
    }

    function updateAISection(dnn, genai) {
        if (!dnn || !genai) return;

        // Risk Level Badge
        riskBadge.className = `risk-badge risk-${dnn.risk_level.toLowerCase()}`;
        riskBadge.innerHTML = `<span class="pulse-dot"></span> ${dnn.risk_level}`;

        // Confidence
        confidenceVal.textContent = `${(dnn.confidence * 100).toFixed(1)}%`;

        // DNN Probability Bars
        const pSafe = (dnn.probabilities.SAFE * 100).toFixed(1);
        const pWarn = (dnn.probabilities.WARNING * 100).toFixed(1);
        const pCrit = (dnn.probabilities.CRITICAL * 100).toFixed(1);

        barProbSafe.style.width = `${pSafe}%`;
        barProbWarn.style.width = `${pWarn}%`;
        barProbCrit.style.width = `${pCrit}%`;

        txtProbSafe.textContent = `${pSafe}%`;
        txtProbWarn.textContent = `${pWarn}%`;
        txtProbCrit.textContent = `${pCrit}%`;

        // GenAI Explanation
        aiHeadline.textContent = genai.headline;
        aiExplanation.textContent = genai.explanation;

        if (oshaTag) oshaTag.textContent = genai.osha_compliance || 'OSHA Standard';
        if (evacRadiusTag) {
            if (genai.evacuation_radius_meters > 0) {
                evacRadiusTag.textContent = `Perimeter: ${genai.evacuation_radius_meters}m`;
                evacRadiusTag.classList.add('danger');
            } else {
                evacRadiusTag.textContent = 'Perimeter: Nominal';
                evacRadiusTag.classList.remove('danger');
            }
        }

        // Checklist Actions
        actionsChecklist.innerHTML = '';
        (genai.recommended_actions || []).forEach((actionText, idx) => {
            const item = document.createElement('label');
            item.className = 'action-item';
            item.innerHTML = `
                <input type="checkbox" class="action-checkbox" id="chk_${idx}">
                <span>${actionText}</span>
            `;
            actionsChecklist.appendChild(item);
        });

        // PPE Tags
        ppeContainer.innerHTML = '';
        (genai.ppe_requirements || []).forEach(ppe => {
            const tag = document.createElement('span');
            tag.className = 'ppe-tag';
            tag.textContent = ppe;
            ppeContainer.appendChild(tag);
        });

        // Handle Audio & Banners according to risk level
        if (dnn.risk_level === 'CRITICAL') {
            emergencyBanner.classList.add('visible');
            emergencyBannerText.textContent = `🚨 CRITICAL SAFETY ALERT: HAZARDOUS SEWER ENVIRONMENT DETECTED IN MH-001 - EVACUATE ${genai.evacuation_radius_meters}M PERIMETER`;
            window.soundAlerts.playCritical();
            showToast(`CRITICAL ALERT: ${genai.headline}`, 'critical');
        } else if (dnn.risk_level === 'WARNING') {
            emergencyBanner.classList.remove('visible');
            window.soundAlerts.playWarning();
            showToast(`Safety Warning: Elevated parameters in MH-001`, 'warning');
        } else {
            emergencyBanner.classList.remove('visible');
            window.soundAlerts.playSafe();
        }
    }

    function prependHistoryRow(reading, riskLevel) {
        if (!historyTableBody) return;
        const row = document.createElement('tr');
        const badgeClass = riskLevel ? riskLevel.toUpperCase() : 'PENDING';
        
        row.innerHTML = `
            <td>${reading.timestamp}</td>
            <td><strong style="color: #93c5fd;">${reading.manhole_id}</strong></td>
            <td>${reading.gas_ppm.toFixed(1)} PPM</td>
            <td>${reading.water_level_pct.toFixed(1)}% (${(reading.water_level_pct * 3.8).toFixed(0)}cm)</td>
            <td>${reading.temperature_c.toFixed(1)}°C</td>
            <td>${reading.humidity_pct.toFixed(1)}%</td>
            <td><span class="badge-status ${badgeClass}">${badgeClass}</span></td>
        `;

        historyTableBody.insertBefore(row, historyTableBody.firstChild);
        if (historyTableBody.children.length > 25) {
            historyTableBody.removeChild(historyTableBody.lastChild);
        }
    }

    // --------------------------------------------------------------------------
    // 4. API Actions: Simulate Sensor Telemetry
    // --------------------------------------------------------------------------
    async function triggerSimulation(scenario, autoAnalyze = false, manualValues = null) {
        try {
            btnSimulate.disabled = true;
            btnSimulate.innerHTML = '<span class="spinner"></span> Simulating...';

            const response = await fetch('/api/sensors/simulate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    scenario: scenario || scenarioSelect.value,
                    auto_analyze: autoAnalyze,
                    manual_values: manualValues
                })
            });

            const data = await response.json();
            if (data.success) {
                updateTelemetryCards(data.reading);
                
                if (data.assessment) {
                    updateAISection(data.assessment.dnn, data.assessment.genai);
                    prependHistoryRow(data.reading, data.assessment.dnn.risk_level);
                } else {
                    prependHistoryRow(data.reading, 'UNTESTED');
                }

                showToast(`New sensor telemetry simulated [${data.reading.scenario.toUpperCase()}]`, 'info');
            }
        } catch (err) {
            console.error('Simulation error:', err);
            showToast('Failed to simulate sensor telemetry.', 'warning');
        } finally {
            btnSimulate.disabled = false;
            btnSimulate.innerHTML = '⚡ <span>Simulate Sensor Data</span>';
        }
    }

    // --------------------------------------------------------------------------
    // 5. API Actions: Analyze Safety (DNN + GenAI)
    // --------------------------------------------------------------------------
    async function triggerSafetyAnalysis() {
        try {
            btnAnalyze.disabled = true;
            btnAnalyze.innerHTML = '<span class="spinner"></span> Analyzing Safety...';

            const readingId = currentReading ? currentReading.id : null;
            const response = await fetch('/api/safety/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ reading_id: readingId })
            });

            const data = await response.json();
            if (data.success) {
                updateAISection(data.dnn, data.genai);
                // Update top row in history with evaluated status
                if (historyTableBody && historyTableBody.firstChild) {
                    const statusTd = historyTableBody.firstChild.querySelector('td:last-child');
                    if (statusTd) {
                        statusTd.innerHTML = `<span class="badge-status ${data.dnn.risk_level}">${data.dnn.risk_level}</span>`;
                    }
                }
            } else {
                showToast(data.error || 'Failed to complete safety analysis.', 'warning');
            }
        } catch (err) {
            console.error('Safety Analysis Error:', err);
            showToast('Error communicating with AI Safety Advisor.', 'critical');
        } finally {
            btnAnalyze.disabled = false;
            btnAnalyze.innerHTML = '🧠 <span>Analyze Safety</span>';
        }
    }

    // --------------------------------------------------------------------------
    // 6. Auto-Polling Toggle (Every 5 seconds)
    // --------------------------------------------------------------------------
    if (autoPollToggle) {
        autoPollToggle.addEventListener('change', (e) => {
            isAutoPolling = e.target.checked;
            if (isAutoPolling) {
                pollStatusText.textContent = 'Auto-Polling: ON (5s)';
                pollStatusText.style.color = '#34d399';
                showToast('Auto-Polling enabled. Sensors update every 5 seconds.', 'safe');

                // Trigger immediate then loop
                triggerSimulation(scenarioSelect.value, true);
                autoPollTimer = setInterval(() => {
                    triggerSimulation(scenarioSelect.value, true);
                }, POLL_INTERVAL_MS);
            } else {
                pollStatusText.textContent = 'Auto-Polling: OFF';
                pollStatusText.style.color = '#9ca3af';
                clearInterval(autoPollTimer);
                autoPollTimer = null;
                showToast('Auto-Polling disabled.', 'info');
            }
        });
    }

    // --------------------------------------------------------------------------
    // 7. Incident Report Generation & Modal
    // --------------------------------------------------------------------------
    async function openIncidentReport() {
        try {
            const response = await fetch('/api/incident/report');
            const data = await response.json();
            if (!data.success) return;

            const rep = data.report;
            document.getElementById('repId').textContent = rep.incident_id;
            document.getElementById('repTime').textContent = rep.timestamp;
            document.getElementById('repLocation').textContent = rep.location;
            document.getElementById('repCatchment').textContent = rep.catchment_area;
            
            const sevEl = document.getElementById('repSeverity');
            sevEl.textContent = rep.severity;
            sevEl.className = `report-badge-${rep.severity === 'CRITICAL' ? 'danger' : (rep.severity === 'WARNING' ? 'warning' : 'safe')}`;

            document.getElementById('repGas').textContent = `${rep.peak_gas.toFixed(1)} PPM`;
            document.getElementById('repWater').textContent = `${rep.peak_water.toFixed(1)}%`;
            document.getElementById('repTemp').textContent = `${rep.peak_temp.toFixed(1)}°C`;
            document.getElementById('repRootCause').textContent = rep.root_cause;

            const actionsList = document.getElementById('repActionsList');
            actionsList.innerHTML = '';
            (rep.action_log || []).forEach(act => {
                const li = document.createElement('li');
                li.textContent = act;
                actionsList.appendChild(li);
            });

            reportModal.classList.add('active');
        } catch (err) {
            console.error('Failed to load report:', err);
            showToast('Failed to compile incident report.', 'warning');
        }
    }

    if (btnOpenReport) btnOpenReport.addEventListener('click', openIncidentReport);
    if (btnCloseModal) btnCloseModal.addEventListener('click', () => reportModal.classList.remove('active'));
    if (btnPrintReport) btnPrintReport.addEventListener('click', () => window.print());

    // Manual Injection Modal
    if (btnManualModal) btnManualModal.addEventListener('click', () => manualModal.classList.add('active'));
    if (btnCloseManualModal) btnCloseManualModal.addEventListener('click', () => manualModal.classList.remove('active'));

    if (formManual) {
        formManual.addEventListener('submit', (e) => {
            e.preventDefault();
            const manualVals = {
                gas_ppm: parseFloat(document.getElementById('manualGas').value),
                water_level_pct: parseFloat(document.getElementById('manualWater').value),
                temperature_c: parseFloat(document.getElementById('manualTemp').value),
                humidity_pct: parseFloat(document.getElementById('manualHumidity').value)
            };
            manualModal.classList.remove('active');
            triggerSimulation('manual', false, manualVals);
        });
    }

    // --------------------------------------------------------------------------
    // 8. Event Listeners for Toolbar Buttons
    // --------------------------------------------------------------------------
    if (btnSimulate) {
        btnSimulate.addEventListener('click', () => triggerSimulation(scenarioSelect.value, false));
    }

    if (btnAnalyze) {
        btnAnalyze.addEventListener('click', triggerSafetyAnalysis);
    }

    // Initialize telemetry chart from initial history fetched via API
    fetch('/api/history?limit=25')
        .then(res => res.json())
        .then(data => {
            if (data.success && data.history) {
                initTelemetryChart('telemetryChartCanvas', data.history);
                if (data.history.length > 0) {
                    currentReading = data.history[data.history.length - 1];
                }
            }
        })
        .catch(err => console.error('Error fetching history:', err));
});
