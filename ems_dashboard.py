import streamlit as st
import json
import os

st.set_page_config(page_title="EMS Command Center", layout="wide", page_icon="🚑")
LOG_FILE = "accident_history.json"

st.title("🚑 Regional Emergency Dispatch [SIMULATED]")
st.divider()

@st.fragment(run_every="2s")
def incident_stream():
    if not os.path.exists(LOG_FILE):
        st.info("No active incidents in the history log.")
        return

    with open(LOG_FILE, "r") as f:
        try: 
            alerts = json.load(f)
        except: 
            alerts = []

    if not alerts:
        st.warning("History file is empty or corrupted.")
        return
  
    for alert in reversed(alerts):
        analysis = alert.get("analysis", {})
        telemetry = alert.get("telemetry", {})
        vehicle = alert.get("vehicle_details", {})
        loc = alert.get("location", {})
        severity = analysis.get("severity", "PENDING")
        status = alert.get("status") 

        # 2. ENHANCED STATUS LOGIC: Detecting Structural Blackout
        analysis_text = analysis.get("analysis_summary", "").upper()
        # Check if the vehicle.py signaled a sensor death
        is_sensor_failure = "HARDWARE_BLACKOUT" in analysis_text
        is_error = "ERROR" in analysis_text
        
        if status == "USER_CONFIRMED_SAFE":
            status_label = "✅ DRIVER SAFE (MANUAL)"
            color = "green"
        elif is_sensor_failure:
            # NO Triage, assume structural compromise
            status_label = "💀 BLACKOUT: STRUCTURAL FAILURE"
            color = "red"
            severity = "CRITICAL"
        elif is_error:
            status_label = "⚠️ SYSTEM INFERENCE ERROR"
            color = "red"
        elif status == "TRIAGE_COMPLETE":
            status_label = "🔍 AI VERIFIED"
            color = "blue" if severity == "LOW" else "orange"
        else:
            status_label = "🚨 IMPACT DETECTED"
            color = "red"

        # UI RENDERING
        with st.container(border=True):
            # Dynamic background color for total blackouts
            if is_sensor_failure:
                st.error("### 📢 CRITICAL: NO SENSOR DATA - ASSUME MAXIMUM SEVERITY")

            c_header1, c_header2 = st.columns([2, 1])
            with c_header1:
                st.subheader(f"🆔 Vehicle: {vehicle.get('plate_number', 'UNKNOWN')}")
            with c_header2:
                lat, lng = loc.get('lat', -1.2863), loc.get('lng', 36.8172)
                st.markdown(f"### 📍 [GO TO MAP](https://www.google.com/maps?q={lat},{lng})")
                st.caption(f"GPS: {lat}, {lng}")

            col_id, col_det, col_stats = st.columns([1, 2, 1])
            
            with col_id:
                st.markdown(f"**Status:**")
                st.markdown(f"### :{color}[{status_label}]") 
                st.caption(f"🕒 {alert.get('timestamp')}")
            
            with col_det:
                st.markdown(f"**Incident Summary:**")
                
                if is_sensor_failure:
                    st.warning("**HARDWARE BLACKOUT:** Visual sensors were destroyed or disconnected on impact. AI Triage was bypassed to prevent misleading data. Immediate physical intervention is required.")
                else:
                    st.write(analysis.get("analysis_summary", "Awaiting triage details..."))
                
                # Only show images if they exist and it's not a blackout
                if status == "TRIAGE_COMPLETE" and not is_sensor_failure:
                    pics = analysis.get("processed_images", [])
                    if pics:
                        cols = st.columns(len(pics))
                        for i, p in enumerate(pics):
                            cols[i].image(f"data:image/jpeg;base64,{p}", use_container_width=True)

            with col_stats:
                # If speed_at_impact is available in the JSON, show it here
                impact_speed = telemetry.get("speed_at_impact", "N/A")
                st.metric("Impact Speed", f"{impact_speed} km/h")
                st.metric("Impact Force", f"{telemetry.get('impact_g', 0)} G")
                st.metric("Priority", severity)

incident_stream()

if st.sidebar.button("Clear Incident History"):
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)
        st.sidebar.success("Logs cleared!")
        st.rerun()