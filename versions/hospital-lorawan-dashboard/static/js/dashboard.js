/**
 * dashboard.js - Lógica del frontend para el Dashboard Hospitalario LoRaWAN
 *
 * Funcionalidades:
 * - Polling cada 10s a /api/readings/current y /api/alerts
 * - Gráficos en tiempo real con Chart.js
 * - Filtros por tipo de dispositivo y búsqueda
 * - Visualización de alertas en tiempo real
 * - Cards de resumen actualizadas automáticamente
 */


// =============================================================================
// CONFIGURACIÓN
// =============================================================================
const POLL_INTERVAL = 10000; // 10 segundos

// =============================================================================
// ESTADO GLOBAL
// =============================================================================
const state = {
    currentReadings: [],
    alerts: [],
    stats: {},
    statusFilter: 'all',
    chart: null,
    isFirstLoad: true,
};

// =============================================================================
// INICIALIZACIÓN
// =============================================================================
document.addEventListener('DOMContentLoaded', () => {
    // Cargar datos iniciales
    loadInitialData();

    // Iniciar polling periódico
    setInterval(pollData, POLL_INTERVAL);

    // Actualizar reloj del footer
    updateFooterClock();
    setInterval(updateFooterClock, 1000);
});


// =============================================================================
// CARGA INICIAL DE DATOS
// =============================================================================
async function loadInitialData() {
    try {
        await Promise.all([
            fetchStats(),
            fetchDevicesForSelect(),
            fetchAndRenderReadings(),
            pollData(),
        ]);
        state.isFirstLoad = false;
    } catch (error) {
        console.error('Error en carga inicial:', error);
    }
}


// =============================================================================
// POLLING (cada 10 segundos)
// =============================================================================
async function pollData() {
    try {
        const [currentData, alertsData] = await Promise.all([
            fetchJSON('/api/readings/current'),
            fetchJSON('/api/alerts'),
            fetchStats(),
        ]);

        if (currentData.success) {
            state.currentReadings = currentData.data;
            renderDevicesTable(currentData.data);
            updateSummaryCards(currentData.data);
            updateDevicesCount(currentData.data);
        }

        if (alertsData.success) {
            state.alerts = alertsData.data;
            renderAlerts(alertsData.data);
            updateAlertsCount(alertsData.data);
        }

        // Actualizar timestamp de última actualización
        const now = new Date();
        document.getElementById('updateTime').textContent = now.toLocaleTimeString('es-CL');

    } catch (error) {
        console.error('Error en polling:', error);
    }
}


// =============================================================================
// HELPER: FETCH JSON
// =============================================================================
async function fetchJSON(url) {
    const response = await fetch(url);
    if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    return await response.json();
}


// =============================================================================
// ESTADÍSTICAS
// =============================================================================
async function fetchStats() {
    try {
        const data = await fetchJSON('/api/stats');
        if (data.success) {
            state.stats = data.data;
            renderStats(data.data);
        }
    } catch (error) {
        console.error('Error fetching stats:', error);
    }
}

function renderStats(stats) {
    document.getElementById('totalDevices').textContent = stats.total_devices || 0;
    document.getElementById('alertCount').textContent = stats.total_alerts || 0;
    document.getElementById('totalReadings').textContent = (stats.total_readings || 0).toLocaleString();
    document.getElementById('readings24h').textContent = (stats.readings_24h || 0).toLocaleString();

    // Última actualización
    if (stats.last_update) {
        const lastUpdate = new Date(stats.last_update + 'Z');
        document.getElementById('footerTime').textContent =
            'Última actualización: ' + lastUpdate.toLocaleString('es-CL');
    }
}


// =============================================================================
// CARDS DE RESUMEN
// =============================================================================
function updateSummaryCards(readings) {
    const activeOk = readings.filter(r => r.status === 'ok').length;
    document.getElementById('activeDevices').textContent = activeOk;
}


// =============================================================================
// CARGAR DISPOSITIVOS EN EL SELECT DEL GRÁFICO
// =============================================================================
async function fetchDevicesForSelect() {
    try {
        const data = await fetchJSON('/api/devices');
        if (data.success && data.data) {
            const select = document.getElementById('chartDeviceSelect');
            // Mantener la opción por defecto
            select.innerHTML = '<option value="">Seleccione un dispositivo...</option>';

            data.data.forEach(device => {
                const option = document.createElement('option');
                option.value = device.id;
                option.textContent = `${device.name} (${device.location || 'Sin ubicación'})`;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error fetching devices for select:', error);
    }
}


// =============================================================================
// GRÁFICO PRINCIPAL (Chart.js)
// =============================================================================
function getOrCreateChart() {
    const ctx = document.getElementById('mainChart').getContext('2d');

    if (state.chart) {
        return state.chart;
    }

    state.chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Temperatura (°C)',
                    data: [],
                    borderColor: '#1E88E5',
                    backgroundColor: 'rgba(30, 136, 229, 0.1)',
                    fill: true,
                    tension: 0.3,
                    pointRadius: 3,
                    pointHoverRadius: 6,
                    borderWidth: 2,
                },
                {
                    label: 'Humedad (%HR)',
                    data: [],
                    borderColor: '#26A69A',
                    backgroundColor: 'rgba(38, 166, 154, 0.1)',
                    fill: true,
                    tension: 0.3,
                    pointRadius: 3,
                    pointHoverRadius: 6,
                    borderWidth: 2,
                    yAxisID: 'y1',
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                intersect: false,
                mode: 'index',
            },
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        usePointStyle: true,
                        padding: 20,
                        font: { size: 12 },
                    },
                },
                tooltip: {
                    backgroundColor: 'rgba(26, 26, 46, 0.9)',
                    titleFont: { size: 13 },
                    bodyFont: { size: 12 },
                    padding: 12,
                    cornerRadius: 8,
                },
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: {
                        maxTicksLimit: 12,
                        font: { size: 10 },
                    },
                },
                y: {
                    position: 'left',
                    title: {
                        display: true,
                        text: 'Temperatura (°C)',
                        font: { size: 11 },
                    },
                    grid: { color: 'rgba(0,0,0,0.06)' },
                    ticks: {
                        font: { size: 10 },
                    },
                },
                y1: {
                    position: 'right',
                    title: {
                        display: true,
                        text: 'Humedad (%HR)',
                        font: { size: 11 },
                    },
                    grid: { display: false },
                    min: 0,
                    max: 100,
                    ticks: {
                        font: { size: 10 },
                    },
                },
            },
        },
    });

    return state.chart;
}


async function updateChart() {
    const select = document.getElementById('chartDeviceSelect');
    const deviceId = select.value;

    if (!deviceId) {
        // Sin selección: mostrar gráfico vacío o con datos globales
        const chart = getOrCreateChart();
        chart.data.labels = [];
        chart.data.datasets[0].data = [];
        chart.data.datasets[1].data = [];
        chart.update();
        return;
    }

    try {
        const data = await fetchJSON(`/api/readings/latest/${deviceId}`);
        if (data.success && data.data) {
            const readings = data.data;
            const chart = getOrCreateChart();

            chart.data.labels = readings.map(r => {
                const d = new Date(r.timestamp + 'Z');
                return d.toLocaleTimeString('es-CL', { hour: '2-digit', minute: '2-digit' });
            });

            chart.data.datasets[0].data = readings.map(r => r.temperature);

            // Humedad: si no hay datos, ocultar dataset
            const hasHumidity = readings.some(r => r.humidity != null);
            chart.data.datasets[1].data = readings.map(r => r.humidity);
            chart.data.datasets[1].hidden = !hasHumidity;

            chart.update();
        }
    } catch (error) {
        console.error('Error updating chart:', error);
    }
}


// =============================================================================
// TABLA DE DISPOSITIVOS
// =============================================================================
function renderDevicesTable(readings) {
    const tbody = document.getElementById('devicesBody');
    const filterType = document.getElementById('filterType').value;
    const searchTerm = document.getElementById('searchInput').value.toLowerCase().trim();

    let filtered = readings;

    // Filtro por tipo
    if (filterType) {
        filtered = filtered.filter(r => r.device_type === filterType);
    }

    // Filtro por búsqueda
    if (searchTerm) {
        filtered = filtered.filter(r =>
            (r.name && r.name.toLowerCase().includes(searchTerm)) ||
            (r.location && r.location.toLowerCase().includes(searchTerm))
        );
    }

    // Filtro por estado
    if (state.statusFilter !== 'all') {
        filtered = filtered.filter(r => r.status === state.statusFilter);
    }

    if (filtered.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8" style="text-align:center; padding: 30px; color: var(--text-light);">
                    <i class="fas fa-search" style="font-size:1.5rem; display:block; margin-bottom:8px;"></i>
                    No se encontraron dispositivos
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = filtered.map(r => {
        const statusClass = r.status === 'ok' ? 'status-ok' : 'status-alert';
        const statusText = r.status === 'ok' ? 'OK' : 'Alerta';
        const rowClass = r.status === 'alert' ? 'row-alert' : '';

        // Determinar clase de temperatura
        let tempClass = 'temp-ok';
        if (r.temperature != null) {
            if (r.temperature < r.temp_min || r.temperature > r.temp_max) {
                const diff = Math.abs(r.temperature - (r.temp_min + r.temp_max) / 2);
                tempClass = diff > 3 ? 'temp-critical' : 'temp-warning';
            }
        }

        const time = r.timestamp
            ? new Date(r.timestamp + 'Z').toLocaleTimeString('es-CL')
            : '--';

        const safeName = r.name.replace(/'/g, "\\'");
        return `
            <tr class="${rowClass}">
                <td>${r.device_id}</td>
                <td>
                    <a class="device-link" onclick="selectDeviceForChart(${r.device_id}, '${safeName}')">
                        ${r.name}
                    </a>
                </td>
                <td>${formatDeviceType(r.device_type)}</td>
                <td>${r.location || '---'}</td>
                <td class="temp-value ${tempClass}">
                    ${r.temperature != null ? r.temperature.toFixed(1) + '°C' : '---'}
                </td>
                <td>${r.humidity != null ? r.humidity.toFixed(1) + '%' : '---'}</td>
                <td><span class="status-badge ${statusClass}">${statusText}</span></td>
                <td>${time}</td>
            </tr>
        `;
    }).join('');
}


// =============================================================================
// PANEL DE ALERTAS
// =============================================================================
function renderAlerts(alerts) {
    const container = document.getElementById('alertsContainer');

    if (!alerts || alerts.length === 0) {
        container.innerHTML = `
            <div class="alerts-empty">
                <i class="fas fa-check-circle"></i>
                <p>No hay alertas activas</p>
            </div>
        `;
        return;
    }

    container.innerHTML = alerts.map(a => {
        const severityClass = a.severity === 'critical' ? 'alert-critical' : 'alert-warning';
        const severityLabel = a.severity === 'critical' ? 'Crítica' : 'Advertencia';
        const sevBadgeClass = a.severity === 'critical' ? 'severity-critical' : 'severity-warning';

        const time = a.created_at
            ? new Date(a.created_at + 'Z').toLocaleString('es-CL')
            : '';

        return `
            <div class="alert-card ${severityClass}">
                <div class="alert-header">
                    <span class="alert-device">
                        <i class="fas fa-exclamation-circle"></i>
                        ${a.device_name || 'Dispositivo #' + a.device_id}
                    </span>
                    <span class="alert-time">${time}</span>
                </div>
                <div class="alert-body">
                    ${a.message}
                </div>
                <span class="alert-severity ${sevBadgeClass}">${severityLabel}</span>
            </div>
        `;
    }).join('');
}


// =============================================================================
// ACTUALIZAR CONTADORES
// =============================================================================
function updateDevicesCount(readings) {
    const filterType = document.getElementById('filterType').value;
    const searchTerm = document.getElementById('searchInput').value.toLowerCase().trim();

    let filtered = readings;

    if (filterType) {
        filtered = filtered.filter(r => r.device_type === filterType);
    }
    if (searchTerm) {
        filtered = filtered.filter(r =>
            (r.name && r.name.toLowerCase().includes(searchTerm)) ||
            (r.location && r.location.toLowerCase().includes(searchTerm))
        );
    }

    document.getElementById('devicesCount').textContent = filtered.length;
}

function updateAlertsCount(alerts) {
    document.getElementById('alertsCount').textContent = alerts ? alerts.length : 0;
}


// =============================================================================
// FILTROS
// =============================================================================
function applyFilters() {
    renderDevicesTable(state.currentReadings);
    updateDevicesCount(state.currentReadings);
}

function setStatusFilter(status, btn) {
    state.statusFilter = status;

    // Actualizar botones activos
    document.querySelectorAll('.btn-status').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');

    applyFilters();
}


// =============================================================================
// SELECCIONAR DISPOSITIVO PARA GRÁFICO
// =============================================================================
function selectDeviceForChart(deviceId, deviceName) {
    const select = document.getElementById('chartDeviceSelect');
    // Buscar la opción y seleccionarla
    for (let i = 0; i < select.options.length; i++) {
        if (select.options[i].value == deviceId) {
            select.selectedIndex = i;
            break;
        }
    }
    updateChart();
}


// =============================================================================
// REFRESCAR DATOS MANUALMENTE
// =============================================================================
async function refreshData() {
    await pollData();
    // Animación en el botón
    const btn = document.querySelector('.top-bar-right .btn-refresh');
    btn.style.animation = 'none';
    btn.offsetHeight; // Trigger reflow
    btn.style.animation = 'spin 0.5s ease';
}

async function refreshReadings() {
    try {
        const data = await fetchJSON(`/api/readings?limit=100`);
        if (data.success && data.data) {
            renderReadingsTable(data.data);
        }
    } catch (error) {
        console.error('Error refreshing readings:', error);
    }
}


// =============================================================================
// TABLA DE LECTURAS RECIENTES
// =============================================================================
async function fetchAndRenderReadings() {
    try {
        const data = await fetchJSON('/api/readings?limit=100');
        if (data.success && data.data) {
            renderReadingsTable(data.data);
        }
    } catch (error) {
        console.error('Error fetching readings:', error);
    }
}

function renderReadingsTable(readings) {
    const tbody = document.getElementById('readingsBody');

    if (!readings || readings.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" style="text-align:center; padding: 30px; color: var(--text-light);">
                    No hay lecturas disponibles
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = readings.map(r => {
        const time = r.timestamp
            ? new Date(r.timestamp + 'Z').toLocaleString('es-CL')
            : '--';

        return `
            <tr>
                <td>${r.id}</td>
                <td>${r.device_name || 'Dispositivo #' + r.device_id}</td>
                <td>${formatDeviceType(r.device_type || '')}</td>
                <td class="temp-value">${r.temperature != null ? r.temperature.toFixed(1) + '°C' : '---'}</td>
                <td>${r.humidity != null ? r.humidity.toFixed(1) + '%' : '---'}</td>
                <td>${time}</td>
            </tr>
        `;
    }).join('');
}


// =============================================================================
// RELOJ DEL FOOTER
// =============================================================================
function updateFooterClock() {
    const now = new Date();
    const timeStr = now.toLocaleString('es-CL', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
    });
    const el = document.getElementById('footerTime');
    if (el) {
        el.textContent = 'Sistema activo — ' + timeStr;
    }
}


// =============================================================================
// UTILIDADES
// =============================================================================
function formatDeviceType(type) {
    const names = {
        vitrina_refrigerada: 'Vitrina Refr.',
        frigobar: 'Frigobar',
        refri_combinado_frio: 'Ref. Comb. Frío',
        refri_combinado_cong: 'Ref. Comb. Cong.',
        freezer_20: 'Freezer -20°C',
        vitrina_2p: 'Vitrina 2P',
        freezer_80: 'Freezer -80°C',
        freezer_horizontal: 'Freezer Horiz.',
        camara_mortuoria: 'Cámara Mort.',
        ambiental: 'Ambiental',
        termostato_sonda: 'Term. Sonda',
    };
    return names[type] || type;
}


// =============================================================================
// ANIMACIONES CSS ADICIONALES (inyectadas vía JS)
// =============================================================================
const styleSheet = document.createElement('style');
styleSheet.textContent = `
    @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
`;
document.head.appendChild(styleSheet);
