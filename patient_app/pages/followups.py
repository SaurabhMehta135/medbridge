"""Patient App — Follow-up Tracker Page"""

import streamlit as st
from datetime import datetime
from core.api_client import api_client
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from shared.icons import icon, icon_label, status_icon


def show_followup_page(api_base, api_headers_fn):
    st.markdown(f"""
    <div class="page-header">
        <h1>{icon('calendar', size=28, color='#0891B2')} Follow-up Tracker</h1>
        <p>Keep track of all your upcoming medical appointments, lab tests, and actions.</p>
    </div>
    """, unsafe_allow_html=True)

    try:
        fups = api_client.get_patient_followups()
    except Exception:
        fups = []
        st.error("Could not load follow-ups. Please try again later.")
        return

    if not fups:
        # Show filter pills (disabled) so user understands the structure
        st.markdown("""
        <div style="margin-bottom: 16px;">
            <span class="filter-pill">All</span>
            <span class="filter-pill">Overdue</span>
            <span class="filter-pill">Upcoming</span>
            <span class="filter-pill">Scheduled</span>
            <span class="filter-pill">Completed</span>
        </div>
        """, unsafe_allow_html=True)

        # Softened empty state
        st.markdown(f"""
        <div style="background: #DCFCE7; border: 2px solid #BBF7D0; border-radius: 12px; text-align: center; padding: 40px;">
            <div style="font-size: 2.5rem; margin-bottom: 12px;">{icon('circle-check', size=36, color='#16A34A')}</div>
            <strong style="font-size: 1.1rem; color: #166534;">You're all caught up!</strong><br>
            <span style="color: #15803D;">No follow-ups pending. Upload documents to extract follow-up items.</span>
        </div>
        """, unsafe_allow_html=True)
        return

    # Categorize
    today = datetime.utcnow().date()
    for f in fups:
        if f["status"] == "pending" and f["due_date"]:
            due_obj = datetime.strptime(f["due_date"], "%Y-%m-%d").date()
            if due_obj < today:
                f["status"] = "overdue"

    emergency_items = [f for f in fups if f["urgency"] == "urgent"]
    overdue_items = [f for f in fups if f["status"] == "overdue" and f["urgency"] != "urgent"]
    pending_items = [f for f in fups if f["status"] == "pending" and f["urgency"] != "urgent"]
    completed_items = [f for f in fups if f["status"] == "completed" and f["urgency"] != "urgent"]

    upcoming_items, scheduled_items, no_date_items = [], [], []
    for p in pending_items:
        if p["due_date"]:
            delta = (datetime.strptime(p["due_date"], "%Y-%m-%d").date() - today).days
            (upcoming_items if delta <= 28 else scheduled_items).append(p)
        else:
            no_date_items.append(p)

    # Stats row
    col1, col2, col3, col4 = st.columns(4)
    total_pending = len(overdue_items) + len(upcoming_items) + len(scheduled_items) + len(no_date_items)
    with col1:
        st.markdown(f"""<div class="metric-card"><div class="metric-stripe" style="background: #2563EB;"></div>
            <div class="metric-value">{total_pending}</div><div class="metric-label">Total Pending</div></div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""<div class="metric-card"><div class="metric-stripe" style="background: #DC2626;"></div>
            <div class="metric-value" style="color:#DC2626;">{len(overdue_items)}</div><div class="metric-label">Overdue</div></div>""", unsafe_allow_html=True)
    with col3:
        st.markdown(f"""<div class="metric-card"><div class="metric-stripe" style="background: #EA580C;"></div>
            <div class="metric-value" style="color:#EA580C;">{len(upcoming_items)}</div><div class="metric-label">Due This Month</div></div>""", unsafe_allow_html=True)
    with col4:
        st.markdown(f"""<div class="metric-card"><div class="metric-stripe" style="background: #16A34A;"></div>
            <div class="metric-value" style="color:#16A34A;">{len(completed_items)}</div><div class="metric-label">Completed</div></div>""", unsafe_allow_html=True)

    st.markdown("")

    # Emergency Warning
    if emergency_items:
        st.markdown(f"""<div class="alert-danger"><h4 style="margin:0 0 8px 0; color:#991B1B;">{icon('triangle-alert', size=18, color='#991B1B')} WHEN TO SEEK IMMEDIATE CARE</h4>
            <p style="color:#991B1B; margin:0;">Return to the emergency room or call 911 if you experience:</p></div>""", unsafe_allow_html=True)
        for e in emergency_items:
            st.markdown(f'<div class="alert-danger" style="margin-left:16px;">• <strong>{e["description"]}</strong></div>', unsafe_allow_html=True)

    # Helper to render follow-up items
    def _render_items(items, section_icon_html, label):
        if not items:
            return
        st.markdown(f'<p class="section-header">{section_icon_html} {label} — {len(items)} item(s)</p>', unsafe_allow_html=True)
        for f in items:
            due_text = ""
            if f.get("due_date"):
                due_obj = datetime.strptime(f["due_date"], "%Y-%m-%d").date()
                delta = (due_obj - today).days
                if delta < 0:
                    due_text = f" — {abs(delta)} days overdue"
                elif delta == 0:
                    due_text = " — Due today"
                else:
                    due_text = f" — Due in {delta} days"

            with st.expander(f"{f['description']}{due_text}"):
                st.caption(f"Source: Document ID #{f['document_id']}" if f['document_id'] else "Source: Manual Entry")
                notes = st.text_input("Notes (Optional)", key=f"notes_{f['id']}")
                if st.button("Mark as Completed", key=f"btn_comp_{f['id']}", use_container_width=True, type="primary"):
                    try:
                        api_client.mark_followup_complete(f['id'], notes)
                        st.success("Great job! Follow-up completed.")
                        st.rerun()
                    except Exception:
                        st.error("Failed to update status")

    _render_items(overdue_items, status_icon('overdue'), "OVERDUE")
    _render_items(upcoming_items, status_icon('upcoming'), "UPCOMING")
    _render_items(scheduled_items, status_icon('scheduled'), "SCHEDULED")
    _render_items(no_date_items, status_icon('no_date'), "NO DATE SPECIFIED")

    # Completed
    if completed_items:
        st.markdown(f'<p class="section-header">{status_icon("completed")} COMPLETED — {len(completed_items)} item(s)</p>', unsafe_allow_html=True)
        for f in completed_items:
            with st.expander(f"~~{f['description']}~~ (Completed: {f['completed_at'].split('T')[0]})"):
                st.write(f"**Notes:** {f['notes'] or 'No notes provided.'}")
                st.caption(f"Source: Document ID #{f['document_id']}" if f['document_id'] else "Source: Manual Entry")
