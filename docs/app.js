/**
 * ICH Blood Pressure Management App
 * SMART on FHIR Web Application
 */

// ========================================
// Configuration
// ========================================
const CONFIG = {
    // Target BP ranges (can be customized per patient)
    targetSystolic: { min: 120, max: 140 },
    targetDiastolic: { min: 70, max: 90 },

    // Analysis window
    stabilityWindowDays: 14,
    minReadingsForAnalysis: 10,

    // Stability score thresholds
    stabilityExcellent: 80,
    stabilityGood: 60,
    stabilityFair: 40,

    // Alert thresholds
    hypertensiveEmergencySBP: 180,
    hypertensiveEmergencyDBP: 120,
    severeHypotensionSBP: 80,
    hypotensionSBP: 90,

    // Score weights
    weights: {
        targetAchievement: 40,
        variability: 30,
        hypotension: 20,
        trend: 10
    },

    // Medications
    medications: {
        norvasc: {
            name: "Norvasc (脈優)",
            doses: ["2.5mg", "5mg", "10mg"]
        },
        exforge: {
            name: "Exforge (易安穩)",
            doses: ["80/5mg", "160/5mg", "160/10mg"]
        }
    }
};

// ========================================
// Global State
// ========================================
let fhirClient = null;
let currentPatient = null;
let bpReadings = [];
let bpChart = null;

// ========================================
// SMART on FHIR Initialization
// ========================================
document.addEventListener('DOMContentLoaded', function() {
    // Set default time for input
    const now = new Date();
    now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
    document.getElementById('inputTime').value = now.toISOString().slice(0, 16);

    // Initialize SMART client
    FHIR.oauth2.ready()
        .then(client => {
            fhirClient = client;
            console.log("SMART client ready");
            return loadPatientData();
        })
        .then(() => {
            hideLoading();
        })
        .catch(error => {
            console.error("Error initializing SMART client:", error);
            // For demo/testing without SMART
            loadDemoData();
            hideLoading();
        });
});

function hideLoading() {
    document.getElementById('loadingOverlay').style.display = 'none';
}

// ========================================
// Data Loading
// ========================================
async function loadPatientData() {
    try {
        // Load patient info
        const patient = await fhirClient.patient.read();
        currentPatient = patient;
        displayPatientInfo(patient);

        // Load BP observations
        const bpData = await fhirClient.request(
            `/Observation?patient=${fhirClient.patient.id}&code=85354-9&_sort=-date&_count=100`
        );

        if (bpData.entry && bpData.entry.length > 0) {
            bpReadings = parseBPObservations(bpData.entry);
            updateDashboard();
        } else {
            showAlert("warning", "尚無血壓紀錄，請開始記錄您的血壓");
        }

        // Load ICH condition if exists
        await loadICHCondition();

    } catch (error) {
        console.error("Error loading patient data:", error);
        showAlert("danger", "載入資料時發生錯誤");
    }
}

async function loadICHCondition() {
    try {
        const conditions = await fhirClient.request(
            `/Condition?patient=${fhirClient.patient.id}&code=I61`
        );

        if (conditions.entry && conditions.entry.length > 0) {
            const ichCondition = conditions.entry[0].resource;
            const onsetDate = new Date(ichCondition.onsetDateTime);
            const daysSinceOnset = Math.floor((new Date() - onsetDate) / (1000 * 60 * 60 * 24));

            let phase = "stable";
            let phaseText = "穩定期";

            if (daysSinceOnset <= 14) {
                phase = "acute";
                phaseText = "急性期 (需謹慎)";
            } else if (daysSinceOnset <= 84) {
                phase = "subacute";
                phaseText = "亞急性期";
            }

            document.getElementById('ichPhase').innerHTML =
                `<span class="badge bg-${phase === 'acute' ? 'danger' : phase === 'subacute' ? 'warning' : 'success'}">${phaseText}</span>`;
        }
    } catch (error) {
        console.log("No ICH condition found or error:", error);
    }
}

function loadDemoData() {
    // Demo patient
    currentPatient = {
        name: [{ given: ["王"], family: "大明" }],
        birthDate: "1960-01-15",
        gender: "male"
    };
    displayPatientInfo(currentPatient);

    // Demo BP readings (14 days of data)
    const now = new Date();
    bpReadings = [];

    for (let i = 13; i >= 0; i--) {
        const date = new Date(now);
        date.setDate(date.getDate() - i);

        // Morning reading
        date.setHours(8, 0, 0, 0);
        bpReadings.push({
            timestamp: new Date(date),
            systolic: 125 + Math.floor(Math.random() * 10) - 5,
            diastolic: 78 + Math.floor(Math.random() * 6) - 3
        });

        // Evening reading
        date.setHours(20, 0, 0, 0);
        bpReadings.push({
            timestamp: new Date(date),
            systolic: 128 + Math.floor(Math.random() * 10) - 5,
            diastolic: 80 + Math.floor(Math.random() * 6) - 3
        });
    }

    document.getElementById('ichPhase').innerHTML =
        '<span class="badge bg-success">穩定期 (Demo)</span>';

    updateDashboard();
}

// ========================================
// FHIR Parsing
// ========================================
function parseBPObservations(entries) {
    return entries.map(entry => {
        const obs = entry.resource;
        let systolic = null;
        let diastolic = null;

        if (obs.component) {
            obs.component.forEach(comp => {
                const code = comp.code?.coding?.[0]?.code;
                if (code === "8480-6") {  // Systolic
                    systolic = comp.valueQuantity?.value;
                } else if (code === "8462-4") {  // Diastolic
                    diastolic = comp.valueQuantity?.value;
                }
            });
        }

        return {
            timestamp: new Date(obs.effectiveDateTime),
            systolic: systolic,
            diastolic: diastolic,
            id: obs.id
        };
    }).filter(r => r.systolic && r.diastolic)
      .sort((a, b) => a.timestamp - b.timestamp);
}

// ========================================
// Display Functions
// ========================================
function displayPatientInfo(patient) {
    let name = "患者";
    if (patient.name && patient.name.length > 0) {
        const n = patient.name[0];
        name = (n.family || "") + (n.given ? n.given.join("") : "");
    }
    document.getElementById('patientName').textContent = `${name} 的血壓管理`;
}

function updateDashboard() {
    if (bpReadings.length === 0) return;

    // Latest BP
    const latest = bpReadings[bpReadings.length - 1];
    document.getElementById('latestBP').textContent = `${latest.systolic}/${latest.diastolic}`;
    document.getElementById('latestBPTime').textContent = formatDateTime(latest.timestamp);

    // Check for alerts
    checkBPAlerts(latest);

    // Calculate statistics
    const windowReadings = getWindowReadings(CONFIG.stabilityWindowDays);
    if (windowReadings.length >= 2) {
        const avgSys = Math.round(windowReadings.reduce((sum, r) => sum + r.systolic, 0) / windowReadings.length);
        const avgDia = Math.round(windowReadings.reduce((sum, r) => sum + r.diastolic, 0) / windowReadings.length);
        document.getElementById('avgBP').textContent = `${avgSys}/${avgDia}`;

        // Trend
        const trend = calculateTrend(windowReadings);
        const trendEl = document.getElementById('bpTrend');
        if (trend === 'improving') {
            trendEl.innerHTML = '<span class="trend-down">↓ 改善中</span>';
        } else if (trend === 'worsening') {
            trendEl.innerHTML = '<span class="trend-up">↑ 需注意</span>';
        } else {
            trendEl.innerHTML = '<span class="trend-stable">→ 穩定</span>';
        }
    }

    // Target range display
    document.getElementById('targetRange').textContent =
        `${CONFIG.targetSystolic.min}-${CONFIG.targetSystolic.max}`;

    // Calculate and display stability score
    const stabilityResult = calculateStabilityScore(windowReadings);
    displayStabilityScore(stabilityResult);

    // Generate recommendation
    const recommendation = generateRecommendation(stabilityResult);
    displayRecommendation(recommendation);

    // Update chart
    updateBPChart();

    // Update history table
    updateHistoryTable();
}

function checkBPAlerts(reading) {
    const alertArea = document.getElementById('alertArea');
    alertArea.innerHTML = '';

    if (reading.systolic >= CONFIG.hypertensiveEmergencySBP ||
        reading.diastolic >= CONFIG.hypertensiveEmergencyDBP) {
        showAlert("danger",
            `⚠️ 高血壓危象警告！血壓 ${reading.systolic}/${reading.diastolic} mmHg 過高，請立即就醫！`,
            true);
    } else if (reading.systolic < CONFIG.severeHypotensionSBP) {
        showAlert("danger",
            `⚠️ 嚴重低血壓警告！血壓 ${reading.systolic}/${reading.diastolic} mmHg 過低，請立即就醫！`,
            true);
    } else if (reading.systolic < CONFIG.hypotensionSBP) {
        showAlert("warning",
            `注意：血壓 ${reading.systolic}/${reading.diastolic} mmHg 偏低，請留意是否有頭暈症狀`);
    }
}

function showAlert(type, message, persistent = false) {
    const alertArea = document.getElementById('alertArea');
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} ${persistent ? 'alert-bp' : ''} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    alertArea.appendChild(alertDiv);
}

// ========================================
// Stability Score Calculation
// ========================================
function getWindowReadings(days) {
    const cutoff = new Date();
    cutoff.setDate(cutoff.getDate() - days);
    return bpReadings.filter(r => r.timestamp >= cutoff);
}

function calculateStabilityScore(readings) {
    if (readings.length < CONFIG.minReadingsForAnalysis) {
        return {
            score: 0,
            insufficientData: true,
            message: `需要至少 ${CONFIG.minReadingsForAnalysis} 筆資料進行分析`
        };
    }

    const systolicValues = readings.map(r => r.systolic);
    const diastolicValues = readings.map(r => r.diastolic);

    // 1. Target Achievement (40 points)
    let onTarget = 0;
    readings.forEach(r => {
        if (r.systolic >= CONFIG.targetSystolic.min && r.systolic <= CONFIG.targetSystolic.max &&
            r.diastolic >= CONFIG.targetDiastolic.min && r.diastolic <= CONFIG.targetDiastolic.max) {
            onTarget++;
        }
    });
    const targetRate = (onTarget / readings.length) * 100;
    const targetScore = (targetRate / 100) * CONFIG.weights.targetAchievement;

    // 2. Variability - CV (30 points)
    const meanSys = systolicValues.reduce((a, b) => a + b, 0) / systolicValues.length;
    const stdSys = Math.sqrt(
        systolicValues.reduce((sum, val) => sum + Math.pow(val - meanSys, 2), 0) / systolicValues.length
    );
    const cv = (stdSys / meanSys) * 100;

    let variabilityScore = 0;
    if (cv <= 10) {
        variabilityScore = CONFIG.weights.variability;
    } else if (cv <= 20) {
        variabilityScore = CONFIG.weights.variability * (1 - (cv - 10) / 10);
    }

    // 3. Hypotension Safety (20 points)
    const hypotensionEvents = readings.filter(r => r.systolic < CONFIG.hypotensionSBP).length;
    const hypotensionScore = Math.max(0, CONFIG.weights.hypotension - (hypotensionEvents * 5));

    // 4. Trend (10 points)
    const trend = calculateTrend(readings);
    let trendScore = 0;
    if (trend === 'stable') {
        trendScore = CONFIG.weights.trend;
    } else if (trend === 'improving') {
        trendScore = CONFIG.weights.trend;
    } else {
        trendScore = CONFIG.weights.trend * 0.3;
    }

    const totalScore = targetScore + variabilityScore + hypotensionScore + trendScore;

    return {
        score: Math.round(totalScore),
        insufficientData: false,
        components: {
            targetRate: Math.round(targetRate),
            targetScore: Math.round(targetScore * 10) / 10,
            cv: Math.round(cv * 10) / 10,
            variabilityScore: Math.round(variabilityScore * 10) / 10,
            hypotensionEvents: hypotensionEvents,
            hypotensionScore: Math.round(hypotensionScore * 10) / 10,
            trend: trend,
            trendScore: Math.round(trendScore * 10) / 10
        },
        stats: {
            mean: Math.round(meanSys),
            std: Math.round(stdSys * 10) / 10,
            readings: readings.length
        }
    };
}

function calculateTrend(readings) {
    if (readings.length < 4) return 'insufficient';

    const half = Math.floor(readings.length / 2);
    const firstHalf = readings.slice(0, half);
    const secondHalf = readings.slice(half);

    const avgFirst = firstHalf.reduce((sum, r) => sum + r.systolic, 0) / firstHalf.length;
    const avgSecond = secondHalf.reduce((sum, r) => sum + r.systolic, 0) / secondHalf.length;

    const diff = avgSecond - avgFirst;

    if (diff < -5) return 'improving';
    if (diff > 5) return 'worsening';
    return 'stable';
}

function displayStabilityScore(result) {
    const scoreEl = document.getElementById('stabilityScore');
    const categoryEl = document.getElementById('stabilityCategory');

    if (result.insufficientData) {
        scoreEl.textContent = '--';
        categoryEl.textContent = result.message;
        return;
    }

    scoreEl.textContent = result.score;

    // Set color based on score
    let category, color;
    if (result.score >= CONFIG.stabilityExcellent) {
        category = '優良';
        color = '#28a745';
    } else if (result.score >= CONFIG.stabilityGood) {
        category = '良好';
        color = '#2196f3';
    } else if (result.score >= CONFIG.stabilityFair) {
        category = '普通';
        color = '#ffc107';
    } else {
        category = '需注意';
        color = '#dc3545';
    }

    scoreEl.style.color = color;
    categoryEl.textContent = category;

    // Display components
    const comp = result.components;
    document.getElementById('scoreTarget').textContent = `${comp.targetScore}/${CONFIG.weights.targetAchievement}`;
    document.getElementById('scoreVariability').textContent = `${comp.variabilityScore}/${CONFIG.weights.variability}`;
    document.getElementById('scoreHypotension').textContent = `${comp.hypotensionScore}/${CONFIG.weights.hypotension}`;
    document.getElementById('scoreTrend').textContent = `${comp.trendScore}/${CONFIG.weights.trend}`;

    // Target achievement display
    document.getElementById('targetAchievement').textContent = `達成率: ${comp.targetRate}%`;
}

// ========================================
// Recommendation Generation
// ========================================
function generateRecommendation(stabilityResult) {
    if (stabilityResult.insufficientData) {
        return {
            type: 'maintain',
            title: '建議維持',
            message: '血壓資料不足，無法評估穩定度，建議維持目前劑量並持續記錄血壓',
            details: '請每日測量血壓至少兩次（早晚各一次）',
            followUp: 7
        };
    }

    const score = stabilityResult.score;

    if (score >= CONFIG.stabilityExcellent) {
        return {
            type: 'reduce',
            title: '可考慮減量',
            message: `穩定度分數 ${score}/100 達優良，血壓控制穩定`,
            details: '建議與醫師討論是否可以減少藥物劑量',
            followUp: 14,
            requiresApproval: true
        };
    } else if (score >= CONFIG.stabilityGood) {
        return {
            type: 'maintain',
            title: '建議維持',
            message: `穩定度分數 ${score}/100，血壓控制良好`,
            details: '目前藥物劑量適當，建議繼續維持',
            followUp: 14
        };
    } else if (score >= CONFIG.stabilityFair) {
        return {
            type: 'visit',
            title: '建議回診',
            message: `穩定度分數 ${score}/100，血壓控制不理想`,
            details: '建議儘早回診評估是否需要調整藥物',
            followUp: 7
        };
    } else {
        return {
            type: 'urgent',
            title: '需緊急評估',
            message: `穩定度分數 ${score}/100 偏低，血壓控制不佳`,
            details: '請儘速回診，評估用藥方案',
            followUp: 3
        };
    }
}

function displayRecommendation(rec) {
    const area = document.getElementById('recommendationArea');

    const typeClass = {
        'reduce': 'recommendation-reduce',
        'maintain': 'recommendation-maintain',
        'visit': 'recommendation-visit',
        'urgent': 'recommendation-urgent'
    };

    const icon = {
        'reduce': '✅',
        'maintain': '➡️',
        'visit': '🏥',
        'urgent': '⚠️'
    };

    area.innerHTML = `
        <div class="recommendation-card ${typeClass[rec.type]}">
            <h5>${icon[rec.type]} ${rec.title}</h5>
            <p class="mb-2">${rec.message}</p>
            <p class="text-muted small mb-2">${rec.details}</p>
            <p class="mb-0"><strong>追蹤：</strong>${rec.followUp} 天後複查</p>
            ${rec.requiresApproval ? '<p class="mt-2 text-info"><small>📋 此建議需要醫師確認後執行</small></p>' : ''}
        </div>
    `;
}

// ========================================
// Chart
// ========================================
function updateBPChart() {
    const ctx = document.getElementById('bpChart').getContext('2d');

    // Get last 14 days of readings
    const chartReadings = getWindowReadings(14);

    const labels = chartReadings.map(r => formatDate(r.timestamp));
    const systolicData = chartReadings.map(r => r.systolic);
    const diastolicData = chartReadings.map(r => r.diastolic);

    if (bpChart) {
        bpChart.destroy();
    }

    bpChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: '收縮壓',
                    data: systolicData,
                    borderColor: '#e74c3c',
                    backgroundColor: 'rgba(231, 76, 60, 0.1)',
                    fill: false,
                    tension: 0.3
                },
                {
                    label: '舒張壓',
                    data: diastolicData,
                    borderColor: '#3498db',
                    backgroundColor: 'rgba(52, 152, 219, 0.1)',
                    fill: false,
                    tension: 0.3
                },
                {
                    label: '目標上限',
                    data: Array(labels.length).fill(CONFIG.targetSystolic.max),
                    borderColor: 'rgba(40, 167, 69, 0.5)',
                    borderDash: [5, 5],
                    pointRadius: 0,
                    fill: false
                },
                {
                    label: '目標下限',
                    data: Array(labels.length).fill(CONFIG.targetSystolic.min),
                    borderColor: 'rgba(40, 167, 69, 0.5)',
                    borderDash: [5, 5],
                    pointRadius: 0,
                    fill: false
                }
            ]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top',
                }
            },
            scales: {
                y: {
                    min: 60,
                    max: 180,
                    title: {
                        display: true,
                        text: 'mmHg'
                    }
                }
            }
        }
    });
}

// ========================================
// History Table
// ========================================
function updateHistoryTable() {
    const tbody = document.getElementById('historyTable');
    const sortedReadings = [...bpReadings].sort((a, b) => b.timestamp - a.timestamp);

    tbody.innerHTML = sortedReadings.slice(0, 50).map(r => {
        let status = '';
        let statusClass = '';

        if (r.systolic >= CONFIG.hypertensiveEmergencySBP || r.diastolic >= CONFIG.hypertensiveEmergencyDBP) {
            status = '⚠️ 過高';
            statusClass = 'text-danger';
        } else if (r.systolic < CONFIG.hypotensionSBP) {
            status = '⚡ 偏低';
            statusClass = 'text-warning';
        } else if (r.systolic >= CONFIG.targetSystolic.min && r.systolic <= CONFIG.targetSystolic.max) {
            status = '✓ 達標';
            statusClass = 'text-success';
        } else {
            status = '● 正常';
            statusClass = 'text-muted';
        }

        return `
            <tr>
                <td>${formatDateTime(r.timestamp)}</td>
                <td><strong>${r.systolic}</strong></td>
                <td><strong>${r.diastolic}</strong></td>
                <td class="${statusClass}">${status}</td>
            </tr>
        `;
    }).join('');
}

// ========================================
// BP Input / Submission
// ========================================
async function submitBPReading() {
    const systolic = parseInt(document.getElementById('inputSystolic').value);
    const diastolic = parseInt(document.getElementById('inputDiastolic').value);
    const timeValue = document.getElementById('inputTime').value;

    // Validation
    if (!systolic || !diastolic) {
        showSubmitResult('danger', '請輸入收縮壓和舒張壓');
        return;
    }

    if (systolic < 60 || systolic > 250 || diastolic < 40 || diastolic > 150) {
        showSubmitResult('danger', '血壓數值超出合理範圍，請確認');
        return;
    }

    if (diastolic >= systolic) {
        showSubmitResult('danger', '舒張壓應小於收縮壓，請確認');
        return;
    }

    const timestamp = timeValue ? new Date(timeValue) : new Date();

    // Create FHIR Observation
    const observation = {
        resourceType: "Observation",
        status: "final",
        category: [{
            coding: [{
                system: "http://terminology.hl7.org/CodeSystem/observation-category",
                code: "vital-signs",
                display: "Vital Signs"
            }]
        }],
        code: {
            coding: [{
                system: "http://loinc.org",
                code: "85354-9",
                display: "Blood pressure panel"
            }],
            text: "Blood Pressure"
        },
        subject: {
            reference: fhirClient ? `Patient/${fhirClient.patient.id}` : "Patient/demo"
        },
        effectiveDateTime: timestamp.toISOString(),
        component: [
            {
                code: {
                    coding: [{
                        system: "http://loinc.org",
                        code: "8480-6",
                        display: "Systolic blood pressure"
                    }]
                },
                valueQuantity: {
                    value: systolic,
                    unit: "mmHg",
                    system: "http://unitsofmeasure.org",
                    code: "mm[Hg]"
                }
            },
            {
                code: {
                    coding: [{
                        system: "http://loinc.org",
                        code: "8462-4",
                        display: "Diastolic blood pressure"
                    }]
                },
                valueQuantity: {
                    value: diastolic,
                    unit: "mmHg",
                    system: "http://unitsofmeasure.org",
                    code: "mm[Hg]"
                }
            }
        ]
    };

    try {
        if (fhirClient) {
            // Submit to FHIR server
            await fhirClient.create(observation);
            showSubmitResult('success', '血壓紀錄已儲存');

            // Reload data
            await loadPatientData();
        } else {
            // Demo mode - add to local array
            bpReadings.push({
                timestamp: timestamp,
                systolic: systolic,
                diastolic: diastolic
            });
            bpReadings.sort((a, b) => a.timestamp - b.timestamp);

            showSubmitResult('success', '血壓紀錄已儲存 (Demo模式)');
            updateDashboard();
        }

        // Clear form
        document.getElementById('inputSystolic').value = '';
        document.getElementById('inputDiastolic').value = '';

    } catch (error) {
        console.error("Error submitting BP:", error);
        showSubmitResult('danger', '儲存失敗，請稍後再試');
    }
}

function showSubmitResult(type, message) {
    const resultDiv = document.getElementById('submitResult');
    resultDiv.innerHTML = `<div class="alert alert-${type}">${message}</div>`;
    setTimeout(() => { resultDiv.innerHTML = ''; }, 3000);
}

// ========================================
// Utility Functions
// ========================================
function formatDate(date) {
    const d = new Date(date);
    return `${d.getMonth() + 1}/${d.getDate()}`;
}

function formatDateTime(date) {
    const d = new Date(date);
    return `${d.getMonth() + 1}/${d.getDate()} ${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`;
}

// ========================================
// Logout Function
// ========================================
function logout() {
    if (confirm('確定要登出嗎？')) {
        // Clear session storage
        sessionStorage.clear();
        localStorage.clear();

        // Redirect back to launch page
        window.location.href = 'launch.html';
    }
}
