import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from core.api_client import api_client
from components.auth import logout
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.icons import icon, icon_label, status_icon

def show_dashboard():
    user = st.session_state.dr_user
    if not user:
        logout()
        st.rerun()

    with st.sidebar:
        st.markdown(f"### {user['full_name']}")
        st.caption(f"{user.get('specialty', '')} • {user['email']}")
        st.divider()
        nav_options = ["My Patients", "Enter Access Code", "Dashboard", "Clinical Chat"]
        
        # Override navigation if needed (e.g. from a quick action button)
        default_idx = 2
        if "_dr_nav_override" in st.session_state:
            try:
                default_idx = nav_options.index(st.session_state["_dr_nav_override"])
            except ValueError:
                pass
            del st.session_state["_dr_nav_override"]
            
        page = st.radio(
            "Navigate",
            nav_options,
            index=default_idx,
            label_visibility="collapsed",
        )
        st.divider()
        if st.button("Logout", use_container_width=True):
            logout()
            st.rerun()

    if page == "Dashboard":
        show_dashboard_page()
    elif page == "Enter Access Code":
        show_access_code_page()
    elif page == "My Patients":
        # Keep old import format for now
        from pages.patient_list import show_patient_list
        from core.config import config
        def dummy_header():
            return api_client._get_headers()
        show_patient_list(config.API_BASE, dummy_header)
    elif page == "Clinical Chat":
        from pages.clinical_chat import show_clinical_chat
        from core.config import config
        def dummy_header():
            return api_client._get_headers()
        show_clinical_chat(config.API_BASE, dummy_header)


def show_dashboard_page():
    user = st.session_state.dr_user

    st.markdown("""
    <div class="main-header">
        <h1>Welcome, {name}</h1>
        <p>Population Analytics Dashboard — MedBridge</p>
    </div>
    """.format(name=user["full_name"]), unsafe_allow_html=True)
    
    # Quick Actions Row
    qa1, qa2, qa3 = st.columns(3)
    with qa1:
        if st.button("View All Patients", use_container_width=True):
            st.session_state["_dr_nav_override"] = "My Patients"
            st.rerun()
    with qa2:
        if st.button("Enter Access Code", use_container_width=True, key="qa_code"):
            st.session_state["_dr_nav_override"] = "Enter Access Code"
            st.rerun()
    with qa3:
        # Trigger FHIR ZIP download
        try:
            r_zip = api_client.get_fhir_export_all()
            st.download_button("Export All Data as FHIR", data=r_zip.content, file_name=r_zip.headers.get("Content-Disposition", "fhir.zip").split("filename=")[-1], mime="application/zip", use_container_width=True)
        except Exception:
            st.button("Export All Data as FHIR", use_container_width=True, disabled=True, help="No patients available for export")

    st.markdown("<br>", unsafe_allow_html=True)

    # Fetch Analytics
    try:
        analytics = api_client.get_analytics()
    except Exception:
        analytics = {}
        
    if not analytics or analytics.get("total_patients", 0) == 0:
        st.info("No patients linked yet. Enter an Access Code to build your patient panel.")
        return

    # SECTION 1 - Top Stats Row
    s1, s2, s3, s4 = st.columns(4)
    with s1:
        st.markdown(f"""<div class="metric-card"><div class="metric-stripe" style="background: #0891B2;"></div>
            <div class="metric-value" style="color:#0891B2;">{analytics.get('total_patients', 0)}</div>
            <div class="metric-label">Total Patients</div></div>""", unsafe_allow_html=True)
    with s2:
        hi_risk = analytics.get('high_risk_patients', 0)
        st.markdown(f"""<div class="metric-card"><div class="metric-stripe" style="background: #DC2626;"></div>
            <div class="metric-value" style="color:#DC2626;">{hi_risk}</div>
            <div class="metric-label">High Risk Patients</div></div>""", unsafe_allow_html=True)
    with s3:
        due = analytics.get('followups_due_week', 0)
        st.markdown(f"""<div class="metric-card"><div class="metric-stripe" style="background: #EA580C;"></div>
            <div class="metric-value" style="color:#EA580C;">{due}</div>
            <div class="metric-label">Follow-ups Due This Week</div></div>""", unsafe_allow_html=True)
    with s4:
        overdue = analytics.get('overdue_followups', 0)
        st.markdown(f"""<div class="metric-card"><div class="metric-stripe" style="background: #DC2626;"></div>
            <div class="metric-value" style="color:#DC2626;">{overdue}</div>
            <div class="metric-label">Overdue Follow-ups</div></div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    # Charts & Patients Needing Attention Row
    col_charts, col_attention = st.columns([2, 1], gap="large")
    
    with col_charts:
        # SECTION 3 & 4 - Condition & Risk Charts
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f'<p style="font-weight:700; color:#0F172A; font-size:1.1rem; margin-bottom:10px;">{icon_label("bar-chart-3", "Condition Prevalence", color="#0F172A")}</p>', unsafe_allow_html=True)
            cond = analytics.get("condition_dist", {})
            if cond:
                df_cond = pd.DataFrame(list(cond.items()), columns=["Condition", "Count"]).sort_values("Count", ascending=True)
                fig_cond = px.bar(df_cond, x="Count", y="Condition", orientation='h', text="Count", color_discrete_sequence=["#3B82F6"])
                fig_cond.update_layout(margin=dict(l=0, r=0, t=10, b=0), plot_bgcolor="white", paper_bgcolor="white", xaxis=dict(showgrid=False, visible=False), yaxis=dict(title="", tickfont=dict(size=12, color="#475569")))
                fig_cond.update_traces(textposition='outside', textfont=dict(size=14, color="#0F172A", weight="bold"), marker_line_width=0, opacity=0.9)
                st.plotly_chart(fig_cond, use_container_width=True, config={"displayModeBar": False})
            else:
                st.info("No condition data available yet.")
                
        with c2:
            st.markdown(f'<p style="font-weight:700; color:#0F172A; font-size:1.1rem; margin-bottom:10px;">{icon_label("shield", "Patient Risk Distribution", color="#0F172A")}</p>', unsafe_allow_html=True)
            risk = analytics.get("risk_dist", {})
            if risk:
                df_risk = pd.DataFrame(list(risk.items()), columns=["Risk Level", "Count"])
                df_risk = df_risk[df_risk["Count"] > 0]
                color_map = {"High Risk": "#EF4444", "Medium Risk": "#F59E0B", "Low Risk": "#10B981", "No Data": "#CBD5E1"}
                fig_risk = px.pie(df_risk, values="Count", names="Risk Level", hole=0.5, color="Risk Level", color_discrete_map=color_map)
                fig_risk.update_layout(margin=dict(l=0, r=0, t=10, b=0), showlegend=True, paper_bgcolor="white", legend=dict(orientation="h", y=-0.1, font=dict(color="#475569")))
                fig_risk.update_traces(textinfo='percent', textfont_size=14, hoverinfo='label+percent+value', marker=dict(line=dict(color='#FFFFFF', width=2)))
                st.plotly_chart(fig_risk, use_container_width=True, config={"displayModeBar": False})
            else:
                st.info("No risk data available yet.")
                
        # SECTION 5 - Follow-up Compliance Timeline
        st.markdown(f'<br><hr><p style="font-weight:700; color:#0F172A; font-size:1.1rem; margin-bottom:10px;">{icon_label("trending-up", "Follow-up Compliance Trends (6 Months)", color="#0F172A")}</p>', unsafe_allow_html=True)
        timeline = analytics.get("compliance_timeline", {})
        if timeline and (sum(timeline.get("completed", [])) > 0 or sum(timeline.get("missed", [])) > 0):
            df_line = pd.DataFrame({
                "Month": timeline["months"],
                "Completed On Time": timeline["completed"],
                "Overdue or Missed": timeline["missed"]
            })
            fig_line = go.Figure()
            fig_line.add_trace(go.Scatter(x=df_line["Month"], y=df_line["Completed On Time"], mode='lines+markers', name='Completed On Time', line=dict(color='#10B981', width=4), marker=dict(size=8)))
            fig_line.add_trace(go.Scatter(x=df_line["Month"], y=df_line["Overdue or Missed"], mode='lines+markers', name='Overdue or Missed', line=dict(color='#EF4444', width=4), marker=dict(size=8)))
            fig_line.update_layout(
                margin=dict(l=0, r=0, t=10, b=0), plot_bgcolor="white", paper_bgcolor="white",
                yaxis=dict(gridcolor="#F1F5F9", title="Count"), xaxis=dict(gridcolor="#F1F5F9"),
                legend=dict(orientation="h", y=-0.2), hovermode="x unified"
            )
            st.plotly_chart(fig_line, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("Not enough data yet — complete more follow-ups to see trends here.")
            
    with col_attention:
        # SECTION 2 - Patients Needing Attention
        st.markdown(f'<div style="background:linear-gradient(135deg, #0F172A, #1E293B); color:white; border-radius:14px 14px 0 0; padding:16px 20px;"><p style="font-weight:700; font-size:1.05rem; margin:0;">{icon("shield-alert", size=18, color="#EF4444")} Attention Needed</p><p style="font-size:0.8rem; color:#94A3B8; margin:0;">Overdue and high urgency</p></div>', unsafe_allow_html=True)
        st.markdown('<div style="background:white; border:1px solid #E2E8F0; border-top:none; border-radius:0 0 14px 14px; padding:16px; margin-bottom:24px; box-shadow:0 4px 12px rgba(0,0,0,0.03);">', unsafe_allow_html=True)
        attention = analytics.get("attention_needed", [])
        if attention:
            for p in attention:
                tags_html = ""
                for t in p["tags"]:
                    color = "#DC2626" if "High" in t or "Overdue" in t else "#EA580C" if "New" in t else "#0891B2"
                    bg = "#FEF2F2" if color=="#DC2626" else "#FFF7ED" if color=="#EA580C" else "#ECFEFF"
                    tags_html += f'<span style="background:{bg}; color:{color}; padding:2px 8px; border-radius:12px; font-size:0.75rem; font-weight:600; display:inline-block; margin-bottom:4px;">{t}</span><br>'
                    
                st.markdown(f"""
<div style="background:white; border:1px solid #E2E8F0; border-radius:14px; padding:16px; margin-bottom:12px; box-shadow:0 2px 8px rgba(0,0,0,0.02); transition:all 0.2s;">
    <div style="display:flex; justify-content:space-between; margin-bottom:12px;">
        <div style="display:flex; align-items:center; gap:12px;">
            <div style="width:40px;height:40px;border-radius:10px;background:#F8FAFC;color:#0F172A;border:1px solid #E2E8F0;display:flex;align-items:center;justify-content:center;font-weight:bold;font-size:0.9rem;">
                {p['initials']}
            </div>
            <div>
                <div style="font-weight:700; color:#0F172A; font-size:1rem;">{p['name']}</div>
                <div style="color:#64748B; font-size:0.8rem;">Last active: {p['last_active']}</div>
            </div>
        </div>
    </div>
    <div>{tags_html}</div>
</div>
""", unsafe_allow_html=True)
            if st.button("View All Patients", use_container_width=True, key="view_all_attn"):
                st.session_state["_dr_nav_override"] = "My Patients"
                st.rerun()
        else:
            st.success("All patients are up to date")
        st.markdown('</div>', unsafe_allow_html=True)
            
        # SECTION 6 - Recent Activity Feed
        st.markdown(f'<br><div style="background:white; border:1px solid #E2E8F0; border-radius:16px; padding:24px;"><p style="font-weight:700; color:#0F172A; font-size:1.1rem; margin-bottom:16px;">{icon_label("clock", "Recent Patient Activity", color="#0F172A")}</p>', unsafe_allow_html=True)
        recent = analytics.get("recent_activity", [])
        if recent:
            feed_html = '<div style="border-left: 2px solid #E2E8F0; margin-left:12px; padding-left:24px;">'
            for act in recent:
                feed_html += f"""
<div style="position:relative; margin-bottom:24px;">
    <div style="position:absolute; left:-31px; top:4px; width:14px; height:14px; border-radius:50%; background:#2563EB; border:3px solid white; box-shadow:0 0 0 1px #E2E8F0;"></div>
    <div style="font-size:0.8rem; font-weight:600; color:#94A3B8; text-transform:uppercase; letter-spacing:0.5px; margin-bottom:4px;">{act['time_ago']}</div>
    <div style="font-size:0.95rem; color:#1E293B; line-height:1.5;">
        <strong style="color:#0F172A;">{act['patient_name']}</strong> {act['action']}
    </div>
</div>"""
            feed_html += '</div></div>'
            st.markdown(feed_html, unsafe_allow_html=True)
        else:
            st.info("No recent activity.")
            



def show_access_code_page():
    st.markdown("""
    <div class="page-header">
        <h1>Enter Access Code</h1>
        <p>Enter a code shared by your patient to access their records</p>
    </div>
    """, unsafe_allow_html=True)

    # Instructions
    st.markdown("""
    <div class="alert alert-info">
        <div>
        <strong>How to get an access code</strong><br>
        Ask your patient to open MedBridge, go to <strong>Share Records</strong>,
        and generate an access code. They will share this code with you directly.
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.form("verify_code"):
        code = st.text_input("Access Code", placeholder="MB-XXXXXX", label_visibility="collapsed", help="Enter the 8-character code your patient shared with you")
        submitted = st.form_submit_button("Verify & Connect", use_container_width=True, type="primary")

        if submitted and code:
            try:
                data = api_client.verify_access_code(code.strip())
                st.success(f"Access granted! Patient ID: {data['patient_id']}")
            except Exception as e:
                detail = "Verification failed"
                if hasattr(e, "response") and e.response is not None:
                    try:
                        detail = e.response.json().get("detail", detail)
                    except:
                        pass
                st.error(detail)
