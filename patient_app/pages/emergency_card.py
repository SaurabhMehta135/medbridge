"""Patient App — Emergency Card Page"""

import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime
import io


def show_emergency_card():
    st.markdown("""
    <div class="main-header" style="background: linear-gradient(135deg, #991B1B 0%, #DC2626 60%, #EF4444 100%); box-shadow: 0 4px 16px rgba(220,38,38,0.15);">
        <h1>🚨 Emergency Card</h1>
        <p>Quick-access card with your critical medical information</p>
    </div>
    """, unsafe_allow_html=True)

    user = st.session_state.user

    allergies = user.get("allergies") or "None recorded"
    medications = user.get("medications") or "None recorded"
    blood_type = user.get("blood_type") or "Unknown"
    ec_name = user.get("emergency_contact_name") or "Not set"
    ec_phone = user.get("emergency_contact_phone") or "Not set"
    dob_raw = user.get("date_of_birth") or ""
    initials = "".join(w[0] for w in user["full_name"].split()[:2]).upper()

    # Format DOB nicely
    dob = "Not set"
    if dob_raw:
        try:
            dob = datetime.strptime(dob_raw, "%Y-%m-%d").strftime("%B %d, %Y")
        except Exception:
            dob = dob_raw

    # Generate QR code
    qr_image = None
    try:
        import qrcode
        qr = qrcode.QRCode(version=1, box_size=5, border=2)
        qr.add_data(f"medbridge://patient/{user['id']}")
        qr.make(fit=True)
        qr_image = qr.make_image(fill_color="black", back_color="white")
    except Exception:
        pass

    st.markdown(f"""
    <div class="emergency-card">
        <div class="emergency-card-header">
            <h3>🏥 MEDBRIDGE — EMERGENCY HEALTH CARD</h3>
        </div>
        <div class="emergency-card-body">
            <div style="display:flex; align-items:center; gap:16px; margin-bottom:20px;">
                <div style="width:56px; height:56px; border-radius:50%; background:#2563EB; display:flex; align-items:center; justify-content:center; color:white; font-weight:800; font-size:1.2rem; flex-shrink:0;">{initials}</div>
                <div>
                    <div style="font-size:1.3rem; font-weight:800; color:#0F172A;">{user["full_name"]}</div>
                    <div style="font-size:0.85rem; color:#64748B;">Date of Birth: {dob}</div>
                </div>
            </div>
            <div style="text-align:center; padding:16px; background:#FEF2F2; border-radius:12px; margin-bottom:20px;">
                <div style="font-size:0.75rem; font-weight:700; color:#94A3B8; text-transform:uppercase; letter-spacing:1px;">Blood Type</div>
                <div style="font-size:2.5rem; font-weight:900; color:#DC2626;">{blood_type}</div>
            </div>
            <div class="emergency-card-field">
                <div class="label">⚠️ Allergies</div>
                <div class="value" style="color:#DC2626;">{allergies}</div>
            </div>
            <div class="emergency-card-field">
                <div class="label">💊 Current Medications</div>
                <div class="value">{medications}</div>
            </div>
            <div class="emergency-card-field" style="border-bottom:none;">
                <div class="label">📞 Emergency Contact</div>
                <div class="value">{ec_name} — {ec_phone}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Render QR code using st.image (avoids HTML escaping)
    if qr_image:
        _, qr_col, _ = st.columns([2, 1, 2])
        with qr_col:
            buf = io.BytesIO()
            qr_image.save(buf, format="PNG")
            st.image(buf.getvalue(), caption="Scan for digital access", width=150)

    st.markdown("")

    # Print button via JS
    _, col_center, _ = st.columns([1, 2, 1])
    with col_center:
        components.html("""
        <button onclick="window.parent.print()"
            style="width:100%; padding:14px 28px; border-radius:12px; border:2px solid #DC2626;
            background:white; color:#DC2626; font-weight:700; font-size:1rem; cursor:pointer;
            font-family:'Inter',sans-serif; transition: all 0.2s;"
            onmouseover="this.style.background='#FEF2F2'"
            onmouseout="this.style.background='white'">
            🖨️ Print Emergency Card
        </button>
        """, height=60)

        st.markdown("""
        <div style="text-align:center; margin-top:8px;">
            <span style="font-size:0.8rem; color:#94A3B8;">Keep it in your wallet for emergencies.</span>
        </div>
        """, unsafe_allow_html=True)
