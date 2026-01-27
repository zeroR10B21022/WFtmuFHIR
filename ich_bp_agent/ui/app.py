"""
ICH Blood Pressure Management - Streamlit Application

Main entry point for the SMART on FHIR application.
Provides patient and clinician dashboards for BP monitoring and medication management.
"""
import streamlit as st
import json
from datetime import datetime, date, timedelta
from pathlib import Path
import sys
import os

# Add parent directory to path for imports (works for both local and Streamlit Cloud)
current_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(current_dir))

# Also try the working directory (for Streamlit Cloud)
if os.path.exists("ich_bp_agent"):
    sys.path.insert(0, os.getcwd())

from ich_bp_agent.models.patient import ICHPatient, ICHCondition, ICHPhase, ICHLocation
from ich_bp_agent.models.medication import Medication, MedicationClass, create_norvasc, create_exforge
from ich_bp_agent.models.stability import StabilityScore, RecommendationType
from ich_bp_agent.analyzers.stability_analyzer import StabilityAnalyzer, BPReading, parse_bp_from_fhir
from ich_bp_agent.analyzers.medication_advisor import MedicationAdvisor
from ich_bp_agent.safety.guardrails import SafetyGuardrails
from ich_bp_agent.ui.components.bp_chart import create_bp_trend_chart
from ich_bp_agent.ui.components.stability_gauge import create_stability_gauge
from ich_bp_agent.ui.components.recommendation_card import show_recommendation_card

# Page configuration
st.set_page_config(
    page_title="ICH 血壓管理系統",
    page_icon="❤️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .alert-emergency {
        background-color: #ffebee;
        border-left: 4px solid #f44336;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .alert-warning {
        background-color: #fff3e0;
        border-left: 4px solid #ff9800;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .alert-success {
        background-color: #e8f5e9;
        border-left: 4px solid #4caf50;
        padding: 1rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables"""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "user_role" not in st.session_state:
        st.session_state.user_role = "patient"
    if "patient" not in st.session_state:
        st.session_state.patient = None
    if "bp_readings" not in st.session_state:
        st.session_state.bp_readings = []
    if "medications" not in st.session_state:
        st.session_state.medications = []


def load_demo_data():
    """Load demo patient and BP data"""
    # Create demo ICH patient
    ich_condition = ICHCondition(
        id="condition-ich-001",
        patient_id="patient-ich-001",
        onset_date=date(2024, 10, 1),
        location=ICHLocation.BASAL_GANGLIA,
        severity="moderate",
        icd_code="I61.0",
        notes="高血壓性腦出血，位於左側基底核",
    )

    patient = ICHPatient(
        patient_id="patient-ich-001",
        name="王大明",
        birth_date=date(1958, 3, 15),
        gender="male",
        ich_condition=ich_condition,
        target_systolic=(120, 140),
        target_diastolic=(70, 90),
        phone="0912345678",
        physician_name="陳醫師",
    )

    # Create demo medications
    norvasc = create_norvasc(patient.patient_id, "5mg")
    exforge = create_exforge(patient.patient_id, "160/5mg")

    # Load demo BP readings from sample file
    bp_readings = []
    sample_file = Path(__file__).parent.parent / "data" / "samples" / "bp_observations.json"

    if sample_file.exists():
        with open(sample_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            for entry in data.get("entry", []):
                obs = entry.get("resource", {})
                reading = parse_bp_from_fhir(obs)
                if reading:
                    bp_readings.append(reading)

    # If no sample data, generate demo readings
    if not bp_readings:
        bp_readings = generate_demo_bp_readings(patient.patient_id)

    return patient, [norvasc, exforge], bp_readings


def generate_demo_bp_readings(patient_id: str, days: int = 14) -> list:
    """Generate demo BP readings for testing"""
    import random
    readings = []
    base_date = datetime.now() - timedelta(days=days)

    for day in range(days):
        for time_slot in ["08:00", "20:00"]:
            timestamp = base_date + timedelta(days=day)
            hour = 8 if time_slot == "08:00" else 20
            timestamp = timestamp.replace(hour=hour, minute=0, second=0)

            # Simulate gradual improvement
            progress = day / days
            base_systolic = 145 - (progress * 20)  # 145 -> 125
            base_diastolic = 90 - (progress * 10)  # 90 -> 80

            readings.append(BPReading(
                timestamp=timestamp,
                systolic=int(base_systolic + random.randint(-5, 5)),
                diastolic=int(base_diastolic + random.randint(-3, 3)),
                patient_id=patient_id,
            ))

    return readings


def show_login_page():
    """Display login page"""
    st.markdown('<h1 class="main-header">🏥 ICH 血壓管理系統</h1>', unsafe_allow_html=True)
    st.markdown("### SMART on FHIR 應用程式")
    st.markdown("---")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("#### 登入方式")
        login_method = st.radio(
            "選擇登入方式",
            ["Demo 模式 (測試)", "SMART on FHIR 登入"],
            label_visibility="collapsed",
        )

        if login_method == "Demo 模式 (測試)":
            st.info("使用 Demo 模式將載入測試資料")
            if st.button("進入 Demo 模式", type="primary"):
                patient, medications, bp_readings = load_demo_data()
                st.session_state.authenticated = True
                st.session_state.patient = patient
                st.session_state.medications = medications
                st.session_state.bp_readings = bp_readings
                st.rerun()
        else:
            st.warning("SMART on FHIR 登入需要設定 Client ID")
            client_id = st.text_input("Client ID", type="password")
            if st.button("連接 FHIR 伺服器"):
                st.error("請先在衛服部 SMART Sandbox 註冊應用程式並取得 Client ID")

    with col2:
        st.markdown("#### 關於此應用程式")
        st.markdown("""
        本系統用於腦出血 (ICH) 患者的血壓藥物管理：

        - 📊 **血壓監測** - 追蹤每日血壓趨勢
        - 📈 **穩定度評分** - 評估血壓控制情況
        - 💊 **調藥建議** - 智能建議減量時機
        - 🛡️ **安全護欄** - 防止危險操作

        **支援藥物**：
        - Norvasc (脈優) - Amlodipine
        - Exforge (易安穩) - Valsartan/Amlodipine
        """)


def show_patient_dashboard():
    """Display patient dashboard"""
    patient = st.session_state.patient
    bp_readings = st.session_state.bp_readings
    medications = st.session_state.medications

    # Header
    st.markdown(f'<h1 class="main-header">❤️ {patient.name} 的血壓管理</h1>', unsafe_allow_html=True)

    # Initialize analyzers
    analyzer = StabilityAnalyzer()
    advisor = MedicationAdvisor()
    guardrails = SafetyGuardrails()

    # Calculate stability score
    stability_score = analyzer.calculate_stability_score(
        bp_readings,
        patient.target_systolic,
        patient.target_diastolic,
    )

    # Check latest BP for alerts
    if bp_readings:
        latest_bp = max(bp_readings, key=lambda x: x.timestamp)
        alert_message = guardrails.get_alert_message(latest_bp)
        if alert_message:
            alert_level = guardrails.get_alert_level(latest_bp)
            if alert_level == "emergency":
                st.error(f"🚨 {alert_message}")
            elif alert_level == "warning":
                st.warning(f"⚠️ {alert_message}")
            else:
                st.info(f"ℹ️ {alert_message}")

    # Metrics row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if bp_readings:
            latest = max(bp_readings, key=lambda x: x.timestamp)
            # Calculate delta from previous
            sorted_readings = sorted(bp_readings, key=lambda x: x.timestamp)
            if len(sorted_readings) >= 2:
                prev = sorted_readings[-2]
                delta = latest.systolic - prev.systolic
                delta_str = f"{delta:+d} mmHg"
            else:
                delta_str = None
            st.metric(
                label="最新血壓",
                value=f"{latest.systolic}/{latest.diastolic}",
                delta=delta_str,
                delta_color="inverse",
            )
        else:
            st.metric(label="最新血壓", value="--/--")

    with col2:
        if not stability_score.insufficient_data:
            category_emoji = {"excellent": "🌟", "good": "👍", "fair": "⚠️", "poor": "🔴"}
            emoji = category_emoji.get(stability_score.category, "")
            st.metric(
                label="穩定度分數",
                value=f"{stability_score.score:.0f}/100",
                delta=f"{emoji} {stability_score.category_chinese}",
            )
        else:
            st.metric(label="穩定度分數", value="資料不足")

    with col3:
        if stability_score.components:
            st.metric(
                label="連續達標天數",
                value=f"{stability_score.components.consecutive_days_on_target} 天",
                delta="目標: 14 天",
            )
        else:
            st.metric(label="連續達標天數", value="--")

    with col4:
        if medications:
            med_names = [f"{m.name} {m.current_dose}" for m in medications if m.is_active]
            st.metric(
                label="目前用藥",
                value=med_names[0] if med_names else "--",
                delta=f"+{len(med_names)-1} 種" if len(med_names) > 1 else None,
            )

    st.markdown("---")

    # Main content in two columns
    col_left, col_right = st.columns([2, 1])

    with col_left:
        # BP Trend Chart
        st.subheader("📈 血壓趨勢")
        if bp_readings:
            fig = create_bp_trend_chart(
                bp_readings,
                patient.target_systolic,
                patient.target_diastolic,
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("尚無血壓資料")

        # BP Input Form
        st.subheader("📝 輸入血壓")
        with st.form("bp_input_form"):
            input_col1, input_col2, input_col3 = st.columns(3)
            with input_col1:
                systolic = st.number_input("收縮壓 (mmHg)", min_value=60, max_value=250, value=120)
            with input_col2:
                diastolic = st.number_input("舒張壓 (mmHg)", min_value=40, max_value=150, value=80)
            with input_col3:
                bp_time = st.time_input("測量時間", value=datetime.now().time())

            submitted = st.form_submit_button("記錄血壓", type="primary")
            if submitted:
                new_reading = BPReading(
                    timestamp=datetime.combine(date.today(), bp_time),
                    systolic=systolic,
                    diastolic=diastolic,
                    patient_id=patient.patient_id,
                )
                st.session_state.bp_readings.append(new_reading)

                # Check for alerts
                alert = guardrails.get_alert_message(new_reading)
                if alert:
                    st.warning(alert)
                else:
                    st.success("血壓記錄成功！")
                st.rerun()

    with col_right:
        # Stability Gauge
        st.subheader("📊 穩定度評估")
        if not stability_score.insufficient_data:
            gauge_fig = create_stability_gauge(stability_score.score)
            st.plotly_chart(gauge_fig, use_container_width=True)

            # Component breakdown
            if stability_score.components:
                st.markdown("**評分組成**")
                components = stability_score.components
                st.progress(components.target_achievement_score / 40, text=f"目標達成: {components.target_achievement_rate:.0f}%")
                st.progress(components.variability_score / 30, text=f"穩定性: CV {components.variability_coefficient:.1f}%")
                st.progress(components.hypotension_score / 20, text=f"低血壓安全: {components.hypotension_events} 次事件")
                st.progress(components.trend_score / 10, text=f"趨勢: {components.trend_direction.value}")
        else:
            st.info("需要至少 7 筆血壓資料才能計算穩定度")

        # Medication Recommendation
        st.subheader("💊 調藥建議")
        if medications and not stability_score.insufficient_data:
            primary_med = medications[0]
            eligibility = analyzer.check_reduction_eligibility(
                stability_score,
                patient,
                guardrails.check_recent_hypotension(bp_readings),
            )
            recommendation = advisor.generate_recommendation(
                patient,
                primary_med,
                stability_score,
                eligibility,
            )
            show_recommendation_card(recommendation)
        else:
            st.info("資料不足，無法提供建議")


def show_sidebar():
    """Display sidebar navigation"""
    with st.sidebar:
        st.title("🏥 ICH 血壓管理")

        if st.session_state.authenticated:
            patient = st.session_state.patient
            st.markdown(f"**患者**: {patient.name}")
            st.markdown(f"**ICH 階段**: {patient.ich_phase.value}")
            st.markdown(f"**發病天數**: {patient.ich_condition.days_since_onset} 天")

            st.markdown("---")

            page = st.radio(
                "選擇頁面",
                ["儀表板", "用藥記錄", "病歷資訊", "設定"],
                label_visibility="collapsed",
            )

            st.markdown("---")

            if st.button("登出"):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()

            return page

        return None


def main():
    """Main application entry point"""
    init_session_state()

    if not st.session_state.authenticated:
        show_login_page()
    else:
        page = show_sidebar()

        if page == "儀表板":
            show_patient_dashboard()
        elif page == "用藥記錄":
            show_medication_history()
        elif page == "病歷資訊":
            show_patient_info()
        elif page == "設定":
            show_settings()


def show_medication_history():
    """Display medication history"""
    st.markdown('<h1 class="main-header">💊 用藥記錄</h1>', unsafe_allow_html=True)

    medications = st.session_state.medications

    for med in medications:
        with st.expander(f"{med.name} ({med.generic_name})", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**目前劑量**: {med.current_dose}")
                st.markdown(f"**服藥頻率**: {med.frequency}")
                st.markdown(f"**服藥時間**: {med.timing}")
            with col2:
                st.markdown(f"**藥物類型**: {med.drug_class.value}")
                st.markdown(f"**開始日期**: {med.start_date}")
                st.markdown(f"**使用天數**: {med.days_on_current_dose} 天")


def show_patient_info():
    """Display patient information"""
    st.markdown('<h1 class="main-header">📋 病歷資訊</h1>', unsafe_allow_html=True)

    patient = st.session_state.patient

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 基本資料")
        st.markdown(f"**姓名**: {patient.name}")
        st.markdown(f"**性別**: {'男' if patient.gender == 'male' else '女'}")
        st.markdown(f"**年齡**: {patient.age} 歲")
        st.markdown(f"**電話**: {patient.phone or '未提供'}")

    with col2:
        st.markdown("### 腦出血資訊")
        ich = patient.ich_condition
        st.markdown(f"**發病日期**: {ich.onset_date}")
        st.markdown(f"**發病天數**: {ich.days_since_onset} 天")
        st.markdown(f"**出血位置**: {ich.location.value}")
        st.markdown(f"**嚴重程度**: {ich.severity}")
        st.markdown(f"**目前階段**: {ich.current_phase.value}")

    st.markdown("### 血壓目標")
    st.markdown(f"**收縮壓目標**: {patient.target_systolic[0]}-{patient.target_systolic[1]} mmHg")
    st.markdown(f"**舒張壓目標**: {patient.target_diastolic[0]}-{patient.target_diastolic[1]} mmHg")


def show_settings():
    """Display settings page"""
    st.markdown('<h1 class="main-header">⚙️ 設定</h1>', unsafe_allow_html=True)

    st.markdown("### 血壓目標設定")
    st.info("血壓目標由醫師設定，如需調整請聯繫您的主治醫師")

    patient = st.session_state.patient

    col1, col2 = st.columns(2)
    with col1:
        st.number_input(
            "收縮壓下限",
            value=patient.target_systolic[0],
            disabled=True,
        )
        st.number_input(
            "收縮壓上限",
            value=patient.target_systolic[1],
            disabled=True,
        )
    with col2:
        st.number_input(
            "舒張壓下限",
            value=patient.target_diastolic[0],
            disabled=True,
        )
        st.number_input(
            "舒張壓上限",
            value=patient.target_diastolic[1],
            disabled=True,
        )

    st.markdown("### 通知設定")
    st.checkbox("啟用血壓異常通知", value=True)
    st.checkbox("啟用服藥提醒", value=True)


if __name__ == "__main__":
    main()
