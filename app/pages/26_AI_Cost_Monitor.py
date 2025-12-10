"""AI Cost Monitor Page - Admin dashboard for tracking AI usage and costs.

Shows:
- Daily/weekly/monthly cost breakdown
- Usage by model type
- Usage by user vs admin
- Cost trends over time
"""

import streamlit as st
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import get_session, init_db
from database.models import User

st.set_page_config(
    page_title="AI Cost Monitor - Patient Explorer",
    page_icon="💰",
    layout="wide",
)

# Initialize database
init_db()

# Import auth after database init
from auth import require_login, require_permission, show_user_menu

# Require login and admin permission
user = require_login()
require_permission("admin")
show_user_menu()

st.title("💰 AI Cost Monitor")
st.markdown("Track Azure OpenAI usage and costs across all AutoScribe operations.")
st.divider()

# Import cost tracking
try:
    from autoscribe.cost_tracking import get_cost_tracker, MODEL_PRICING, ModelType
    cost_tracker = get_cost_tracker()
except ImportError as e:
    st.error(f"Failed to import cost tracking module: {e}")
    st.stop()

# =============================================================================
# Sidebar - Time Period Selection
# =============================================================================
with st.sidebar:
    st.subheader("📅 Time Period")

    period = st.radio(
        "Select period",
        ["Today", "Last 7 Days", "Last 30 Days", "This Month", "Custom"],
        index=1,
    )

    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    if period == "Today":
        start_date = today
        end_date = datetime.now()
    elif period == "Last 7 Days":
        start_date = today - timedelta(days=7)
        end_date = datetime.now()
    elif period == "Last 30 Days":
        start_date = today - timedelta(days=30)
        end_date = datetime.now()
    elif period == "This Month":
        start_date = today.replace(day=1)
        end_date = datetime.now()
    else:  # Custom
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start", value=today - timedelta(days=30))
            start_date = datetime.combine(start_date, datetime.min.time())
        with col2:
            end_date = st.date_input("End", value=today)
            end_date = datetime.combine(end_date, datetime.max.time())

    st.divider()

    # Pricing Reference
    st.subheader("💵 Pricing Reference")
    st.caption("Current Azure OpenAI rates:")

    pricing_data = [
        ("GPT-4.1 (Summarize)", "$2.00 / 1M in", "$8.00 / 1M out"),
        ("GPT-4o Transcribe", "$0.006 / min", ""),
        ("GPT-4o Mini Transcribe", "$0.003 / min", ""),
        ("GPT-4o Mini TTS", "$15 / 1M chars", ""),
        ("Azure Speech-to-Text", "$0.016 / min", ""),
    ]

    for model, rate1, rate2 in pricing_data:
        st.caption(f"**{model}**")
        st.caption(f"  {rate1}")
        if rate2:
            st.caption(f"  {rate2}")

# =============================================================================
# Main Content - Summary Cards
# =============================================================================

# Get usage summary
summary = cost_tracker.get_summary(start_date, end_date)

# Top metrics row
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Total Cost",
        f"${summary.total_cost:.2f}",
        help="Total Azure OpenAI costs for period",
    )

with col2:
    st.metric(
        "Total Requests",
        f"{summary.total_requests:,}",
        help="Number of API calls",
    )

with col3:
    st.metric(
        "Admin Usage",
        f"${summary.admin_cost:.2f}",
        help="Costs from admin accounts",
    )

with col4:
    st.metric(
        "User Usage",
        f"${summary.user_cost:.2f}",
        help="Costs from non-admin users",
    )

st.divider()

# =============================================================================
# Cost by Model Type
# =============================================================================
col1, col2 = st.columns(2)

with col1:
    st.subheader("📊 Cost by Model")

    if summary.by_model:
        import pandas as pd

        model_df = pd.DataFrame([
            {
                "Model": model_type.replace("_", " ").title(),
                "Requests": data["requests"],
                "Cost": f"${data['cost']:.4f}",
                "Tokens In": f"{data['input_tokens']:,}",
                "Tokens Out": f"{data['output_tokens']:,}",
                "Audio (min)": f"{data['audio_seconds'] / 60:.1f}" if data['audio_seconds'] > 0 else "-",
            }
            for model_type, data in summary.by_model.items()
        ])

        st.dataframe(
            model_df,
            use_container_width=True,
            hide_index=True,
        )

        # Pie chart
        if len(summary.by_model) > 0:
            try:
                import plotly.express as px

                pie_data = [
                    {"Model": k.replace("_", " ").title(), "Cost": v["cost"]}
                    for k, v in summary.by_model.items()
                    if v["cost"] > 0
                ]

                if pie_data:
                    fig = px.pie(
                        pie_data,
                        values="Cost",
                        names="Model",
                        title="Cost Distribution by Model",
                    )
                    fig.update_traces(textposition='inside', textinfo='percent+label')
                    st.plotly_chart(fig, use_container_width=True)
            except ImportError:
                st.info("Install plotly for charts: pip install plotly")
    else:
        st.info("No usage data for selected period")

with col2:
    st.subheader("👥 Cost by User")

    user_breakdown = cost_tracker.get_user_breakdown(start_date, end_date)

    if user_breakdown:
        import pandas as pd

        user_df = pd.DataFrame([
            {
                "User": u["user_email"] or u["user_id"],
                "Type": "Admin" if u["is_admin"] else "User",
                "Requests": u["requests"],
                "Cost": f"${u['total_cost']:.4f}",
            }
            for u in user_breakdown
        ])

        st.dataframe(
            user_df,
            use_container_width=True,
            hide_index=True,
        )

        # Admin vs User pie chart
        try:
            import plotly.express as px

            admin_user_data = [
                {"Type": "Admin", "Cost": summary.admin_cost},
                {"Type": "Users", "Cost": summary.user_cost},
            ]

            if summary.admin_cost > 0 or summary.user_cost > 0:
                fig = px.pie(
                    admin_user_data,
                    values="Cost",
                    names="Type",
                    title="Admin vs User Costs",
                    color="Type",
                    color_discrete_map={"Admin": "#1f77b4", "Users": "#2ca02c"},
                )
                fig.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)
        except ImportError:
            pass
    else:
        st.info("No user data for selected period")

st.divider()

# =============================================================================
# Daily Cost Trend
# =============================================================================
st.subheader("📈 Daily Cost Trend")

daily_costs = cost_tracker.get_daily_costs(days=30)

if daily_costs:
    import pandas as pd

    daily_df = pd.DataFrame(daily_costs)
    daily_df["date"] = pd.to_datetime(daily_df["date"])

    try:
        import plotly.express as px

        fig = px.bar(
            daily_df,
            x="date",
            y="total_cost",
            title="Daily Costs (Last 30 Days)",
            labels={"date": "Date", "total_cost": "Cost ($)"},
        )
        fig.update_layout(xaxis_tickformat="%b %d")
        st.plotly_chart(fig, use_container_width=True)

    except ImportError:
        # Fallback to simple table
        st.dataframe(
            daily_df[["date", "total_cost", "requests"]].tail(14),
            use_container_width=True,
            hide_index=True,
        )
else:
    st.info("No daily data available yet")

st.divider()

# =============================================================================
# Cost Projections
# =============================================================================
st.subheader("🔮 Cost Projections")

col1, col2, col3 = st.columns(3)

# Calculate averages
if daily_costs:
    import pandas as pd
    daily_df = pd.DataFrame(daily_costs)
    avg_daily = daily_df["total_cost"].mean()
else:
    avg_daily = 0

with col1:
    st.metric(
        "Avg Daily Cost",
        f"${avg_daily:.2f}",
        help="Average daily cost over last 30 days",
    )

with col2:
    weekly_proj = avg_daily * 7
    st.metric(
        "Weekly Projection",
        f"${weekly_proj:.2f}",
        help="Projected weekly cost based on average",
    )

with col3:
    monthly_proj = avg_daily * 30
    st.metric(
        "Monthly Projection",
        f"${monthly_proj:.2f}",
        help="Projected monthly cost based on average",
    )

# Budget warning
st.markdown("---")
budget_limit = st.number_input(
    "Monthly Budget Alert ($)",
    min_value=0.0,
    value=100.0,
    step=10.0,
    help="Get warned if projected monthly cost exceeds this amount",
)

if monthly_proj > budget_limit:
    st.warning(
        f"⚠️ **Budget Alert**: Projected monthly cost (${monthly_proj:.2f}) "
        f"exceeds budget limit (${budget_limit:.2f})"
    )
else:
    remaining = budget_limit - monthly_proj
    st.success(
        f"✅ **On Budget**: ${remaining:.2f} remaining in projected monthly budget"
    )

# =============================================================================
# Raw Data Export
# =============================================================================
with st.expander("📥 Export Raw Data"):
    st.markdown("Download usage data for external analysis.")

    if daily_costs:
        import pandas as pd
        export_df = pd.DataFrame(daily_costs)

        csv = export_df.to_csv(index=False)
        st.download_button(
            "Download Daily Costs CSV",
            data=csv,
            file_name=f"ai_costs_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.csv",
            mime="text/csv",
        )

    if user_breakdown:
        user_export_df = pd.DataFrame(user_breakdown)
        user_csv = user_export_df.to_csv(index=False)
        st.download_button(
            "Download User Breakdown CSV",
            data=user_csv,
            file_name=f"ai_costs_by_user_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.csv",
            mime="text/csv",
        )

# =============================================================================
# Footer
# =============================================================================
st.divider()
st.caption(
    f"Data period: {start_date.strftime('%Y-%m-%d %H:%M')} to {end_date.strftime('%Y-%m-%d %H:%M')} | "
    f"Pricing source: [Azure OpenAI Pricing](https://azure.microsoft.com/en-us/pricing/details/cognitive-services/openai-service/)"
)
