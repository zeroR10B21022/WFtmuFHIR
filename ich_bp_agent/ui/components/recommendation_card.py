"""
Medication Recommendation Card Component
"""
import streamlit as st
from ich_bp_agent.models.stability import MedicationRecommendation, RecommendationType


def show_recommendation_card(recommendation: MedicationRecommendation):
    """
    Display a medication recommendation card

    Args:
        recommendation: MedicationRecommendation object
    """
    # Determine card style based on recommendation type
    type_config = {
        RecommendationType.REDUCE_DOSE: {
            "icon": "✅",
            "color": "#4caf50",
            "bg_color": "#e8f5e9",
            "title": "可考慮減量",
        },
        RecommendationType.MAINTAIN_CURRENT: {
            "icon": "➡️",
            "color": "#2196f3",
            "bg_color": "#e3f2fd",
            "title": "建議維持",
        },
        RecommendationType.INCREASE_DOSE: {
            "icon": "⬆️",
            "color": "#ff9800",
            "bg_color": "#fff3e0",
            "title": "可能需要增量",
        },
        RecommendationType.CLINIC_VISIT: {
            "icon": "🏥",
            "color": "#ff9800",
            "bg_color": "#fff3e0",
            "title": "建議回診",
        },
        RecommendationType.URGENT_REVIEW: {
            "icon": "⚠️",
            "color": "#f44336",
            "bg_color": "#ffebee",
            "title": "需緊急評估",
        },
        RecommendationType.EMERGENCY: {
            "icon": "🚨",
            "color": "#d32f2f",
            "bg_color": "#ffcdd2",
            "title": "緊急狀況",
        },
    }

    config = type_config.get(recommendation.type, type_config[RecommendationType.MAINTAIN_CURRENT])

    # Create card
    st.markdown(f"""
    <div style="
        background-color: {config['bg_color']};
        border-left: 4px solid {config['color']};
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
    ">
        <h4 style="margin: 0; color: {config['color']};">
            {config['icon']} {config['title']}
        </h4>
    </div>
    """, unsafe_allow_html=True)

    # Medication info
    st.markdown(f"**藥物**: {recommendation.medication_name}")
    st.markdown(f"**目前劑量**: {recommendation.current_dose}")

    if recommendation.recommended_dose:
        st.markdown(f"**建議調整為**: {recommendation.recommended_dose}")

    # Rationale
    st.markdown(f"**說明**: {recommendation.rationale_chinese}")

    # Warnings
    if recommendation.warnings:
        st.markdown("**注意事項**:")
        for warning in recommendation.warnings:
            st.markdown(f"- ⚠️ {warning}")

    # Follow-up
    if recommendation.follow_up_days > 0:
        st.markdown(f"**追蹤**: {recommendation.follow_up_days} 天後複查")

    # Approval status
    if recommendation.requires_physician_approval:
        st.info("📋 此建議需要醫師確認後執行")

    # Confidence
    confidence_pct = recommendation.confidence * 100
    st.progress(
        recommendation.confidence,
        text=f"建議信心度: {confidence_pct:.0f}%",
    )


def show_recommendation_summary(recommendation: MedicationRecommendation):
    """
    Display a compact recommendation summary

    Args:
        recommendation: MedicationRecommendation object
    """
    type_emoji = {
        RecommendationType.REDUCE_DOSE: "✅",
        RecommendationType.MAINTAIN_CURRENT: "➡️",
        RecommendationType.INCREASE_DOSE: "⬆️",
        RecommendationType.CLINIC_VISIT: "🏥",
        RecommendationType.URGENT_REVIEW: "⚠️",
        RecommendationType.EMERGENCY: "🚨",
    }

    emoji = type_emoji.get(recommendation.type, "ℹ️")

    st.markdown(f"""
    **{emoji} {recommendation.type_chinese}**

    {recommendation.medication_name} {recommendation.current_dose}
    {"→ " + recommendation.recommended_dose if recommendation.recommended_dose else ""}

    _{recommendation.rationale_chinese}_
    """)
