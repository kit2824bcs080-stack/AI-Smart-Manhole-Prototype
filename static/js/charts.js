/**
 * Telemetry Trends Visualization using Chart.js.
 * Displays real-time multi-variable environmental graphs for Gas, Water, Temp, and Humidity.
 */

let telemetryChart = null;

function initTelemetryChart(canvasId, initialData = []) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    const labels = initialData.map(d => {
        const timePart = d.timestamp.split(' ')[1] || d.timestamp;
        return timePart.substring(0, 5); // HH:MM
    });

    const gasData = initialData.map(d => d.gas_ppm);
    const waterData = initialData.map(d => d.water_level_pct);
    const tempData = initialData.map(d => d.temperature_c);
    const humidityData = initialData.map(d => d.humidity_pct);

    telemetryChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Toxic Gas (PPM)',
                    data: gasData,
                    borderColor: '#ef4444',
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    borderWidth: 2,
                    tension: 0.35,
                    fill: false,
                    pointRadius: 3,
                    pointHoverRadius: 6,
                    yAxisID: 'y'
                },
                {
                    label: 'Water Level (%)',
                    data: waterData,
                    borderColor: '#06b6d4',
                    backgroundColor: 'rgba(6, 182, 212, 0.1)',
                    borderWidth: 2,
                    tension: 0.35,
                    fill: false,
                    pointRadius: 3,
                    pointHoverRadius: 6,
                    yAxisID: 'y'
                },
                {
                    label: 'Temperature (°C)',
                    data: tempData,
                    borderColor: '#f59e0b',
                    borderWidth: 2,
                    borderDash: [4, 4],
                    tension: 0.35,
                    fill: false,
                    pointRadius: 2,
                    yAxisID: 'yTemp'
                },
                {
                    label: 'Humidity (%)',
                    data: humidityData,
                    borderColor: '#10b981',
                    borderWidth: 1.5,
                    tension: 0.35,
                    fill: false,
                    pointRadius: 2,
                    yAxisID: 'y'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        color: '#9ca3af',
                        font: { size: 11, family: 'ui-monospace, monospace' },
                        boxWidth: 12,
                        padding: 15
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(17, 24, 39, 0.95)',
                    titleColor: '#f9fafb',
                    bodyColor: '#e5e7eb',
                    borderColor: 'rgba(255, 255, 255, 0.1)',
                    borderWidth: 1,
                    padding: 10,
                    cornerRadius: 8
                }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(255, 255, 255, 0.04)' },
                    ticks: { color: '#6b7280', font: { size: 10 } }
                },
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    min: 0,
                    max: 120,
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: { color: '#9ca3af', font: { size: 10 } },
                    title: { display: true, text: 'Gas (PPM) / Water & Humidity (%)', color: '#6b7280', font: { size: 10 } }
                },
                yTemp: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    min: 10,
                    max: 60,
                    grid: { drawOnChartArea: false },
                    ticks: { color: '#f59e0b', font: { size: 10 } },
                    title: { display: true, text: 'Temperature (°C)', color: '#f59e0b', font: { size: 10 } }
                }
            }
        }
    });
}

function updateTelemetryChart(reading) {
    if (!telemetryChart) return;

    const timePart = reading.timestamp.split(' ')[1] || reading.timestamp;
    const label = timePart.substring(0, 5);

    // Keep max 30 points
    if (telemetryChart.data.labels.length >= 30) {
        telemetryChart.data.labels.shift();
        telemetryChart.data.datasets.forEach(ds => ds.data.shift());
    }

    telemetryChart.data.labels.push(label);
    telemetryChart.data.datasets[0].data.push(reading.gas_ppm);
    telemetryChart.data.datasets[1].data.push(reading.water_level_pct);
    telemetryChart.data.datasets[2].data.push(reading.temperature_c);
    telemetryChart.data.datasets[3].data.push(reading.humidity_pct);

    telemetryChart.update('none'); // Update without sluggish re-render
}
