import streamlit as st
import can
import time
import json
import os
import threading
import base64
import cv2
import numpy as np
import random
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage
from ultralytics import YOLO

# --- 1. PERSISTENT SHARED STATE ---
class SharedState:
    def __init__(self):
        self.telemetry = {"speed": 85, "impact_g": 0.0}
        self.stop_event = threading.Event()

st.set_page_config(page_title="Black Box Gem", layout="wide", page_icon="🚗")

@st.cache_resource
def get_state():
    return SharedState()

state = get_state()
LOG_FILE = "accident_history.json"

# --- 2. MODELS & CONFIGURATION ---
@st.cache_resource
def load_models():
    # Load OpenCV Haar Cascade and YOLO Privacy Model
    face = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    lp = YOLO("/home/pabl0/Music/Black_Box_Gem/models/LP-detection.pt")
    return face, lp

face_cascade, lp_model = load_models()
# Ensure model name matches exactly what is in 'ollama list'
llm = ChatOllama(model="gemma4:e4b ", temperature=0.0)

# --- 3. BACKGROUND CAN BUS MANAGER ---
def can_bus_manager(state):
    try:
        bus = can.interface.Bus(channel='vcan0', bustype='socketcan')
        while getattr(threading.current_thread(), "do_run", True):
            if state.stop_event.is_set():
                state.telemetry["speed"] = 0 
            else:
                state.telemetry["speed"] += random.choice([-1, 0, 1])
                state.telemetry["speed"] = max(60, min(state.telemetry["speed"], 110))
            
            msg = can.Message(arbitration_id=0x101, data=[int(state.telemetry["speed"])], is_extended_id=False)
            bus.send(msg)
            time.sleep(0.5)
        bus.shutdown()
    except Exception as e:
        print(f"CAN Bus Error: {e}")

if "bg_thread" not in st.session_state:
    t = threading.Thread(target=can_bus_manager, args=(state,))
    t.do_run = True
    t.daemon = True
    t.start()
    st.session_state.bg_thread = t

# --- 4. WORKERS ---
def save_event_data(data):
    history = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            try: history = json.load(f)
            except: history = []
    
    event_id = data.get("event_id")
    idx = next((i for i, item in enumerate(history) if item["event_id"] == event_id), None)
    if idx is not None: history[idx].update(data)
    else: history.append(data)
        
    with open(LOG_FILE, "w") as f:
        json.dump(history, f, indent=4)

def blur_privacy(img):
    """Optimized privacy filter with smaller kernels for faster processing."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.1, 4)
    for (x, y, w, h) in faces:
        roi = img[y:y+h, x:x+w]
        # Optimized Kernel size (25, 25) vs previous (99, 99)
        img[y:y+h, x:x+w] = cv2.GaussianBlur(roi, (25, 25), 30)
    
    results = lp_model(img, conf=0.3, verbose=False)
    for res in results:
        for box in res.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            roi = img[max(0,y1):y2, max(0,x1):x2]
            if roi.size > 0:
                # Optimized Kernel size (25, 25) vs previous (151, 151)
                img[y1:y2, x1:x2] = cv2.GaussianBlur(roi, (25, 25), 0)
    return img

def prep_frame(img_file):
    if not img_file: return None
    try:
        img_file.seek(0)
        nparr = np.frombuffer(img_file.read(), np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        img = blur_privacy(img)
        # 224x224 is the sweet spot for Gemma Vision speed/accuracy
        img = cv2.resize(img, (224, 224)) 
        _, buffer = cv2.imencode('.jpg', img)
        return base64.b64encode(buffer).decode('utf-8')
    except: return None

# --- 5. UI FRAGMENTS ---
@st.fragment(run_every="0.5s")
def telemetry_dashboard():
    c1, c2 = st.columns(2)
    c1.metric("Live Speed", f"{state.telemetry['speed']} km/h")
    c2.metric("Impact G-Force", f"{state.telemetry['impact_g']} G")

@st.fragment(run_every="1s")
def triage_timer():
    if st.session_state.accident_detected and not st.session_state.ai_started and not st.session_state.user_safe:
        elapsed = time.time() - st.session_state.accident_timestamp
        timer_val = max(0, int(10 - elapsed))
        st.progress(timer_val / 10.0, text=f"🚨 AUTO-TRIAGE IN: {timer_val}s")
        if timer_val <= 0:
            st.session_state.ai_started = True
            st.rerun()

# --- 6. MAIN LAYOUT ---
defaults = {"accident_detected": False, "ai_started": False, "ai_complete": False, "user_safe": False, "current_event_id": None}
for key, val in defaults.items():
    if key not in st.session_state: st.session_state[key] = val

with st.sidebar:
    st.header("🛠️ System Health")
    import subprocess
    vcan_status = "vcan0" in subprocess.run(["ip", "link"], capture_output=True, text=True).stdout
    st.write(f"{'🟢' if vcan_status else '🔴'} **CAN Interface**")
    st.write(f"{'🟢' if lp_model else '🔴'} **Privacy Models**")
    st.write(f"{'🟢' if llm else '🔴'} **AI Engine**")

    if st.button("🔄 RESET SYSTEM"):
        state.stop_event.clear()
        state.telemetry["impact_g"] = 0.0
        for key in defaults: st.session_state[key] = defaults[key]
        st.rerun()

st.title("💎 Black Box Gem: Edge Triage")
ui_locked = st.session_state.ai_started or st.session_state.ai_complete or st.session_state.user_safe

col_vid, col_data = st.columns([1, 2])

with col_vid:
    st.subheader("📸 Sensor Feed")
    f1 = st.file_uploader("T-5s", type=['jpg','png'], key="f1", disabled=ui_locked)
    f2 = st.file_uploader("Impact", type=['jpg','png'], key="f2", disabled=ui_locked)
    f3 = st.file_uploader("T+2s", type=['jpg','png'], key="f3", disabled=ui_locked)
   
    if st.button("🚨 SIMULATE ACCIDENT", type="primary", disabled=st.session_state.accident_detected):
        state.stop_event.set() 
        st.session_state.accident_detected = True
        st.session_state.accident_timestamp = time.time()
        state.telemetry["impact_g"] = round(random.uniform(6.5, 12.8), 1)
        st.session_state.current_event_id = f"VX-{random.randint(1000, 9999)}"
        
        save_event_data({
            "event_id": st.session_state.current_event_id,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "status": "IMPACT_ALERT",
            "location": {"lat": 42.7111, "lng": -81.2581}, # Updated to Dutton, Ontario
            "vehicle_details": {"plate_number": "GEM-789", "passengers": 2},
            "telemetry": {"impact_g": state.telemetry["impact_g"], "speed_at_impact": 85}
        })
        st.rerun()

with col_data:
    telemetry_dashboard()
    
    if st.session_state.accident_detected and not ui_locked:
        triage_timer()
        st.warning("Confirm Safety or Request Help immediately.")
        c1, c2 = st.columns(2)
        if c1.button("✅ I'm Okay", use_container_width=True):
            st.session_state.user_safe = True
            save_event_data({
                "event_id": st.session_state.current_event_id,
                "status": "USER_CONFIRMED_SAFE",
                "analysis": {"severity": "LOW", "analysis_summary": "✅ Driver manually reported safe."}
            })
            st.rerun()
        if c2.button("🚑 Request EMS Now", use_container_width=True):
            st.session_state.ai_started = True
            st.rerun()

    if st.session_state.ai_started and not st.session_state.ai_complete:
        with st.status("💎 Black Box Gem: Triage Reasoning...", expanded=True) as status:
            st.write("1. 🛠️ Checking Sensor Integrity...")

            provided_files = [f1, f2, f3]
            valid_files = [f for f in provided_files if f is not None]
            sensor_death = len(valid_files) < 3 

            if sensor_death:
                st.error(f"⚠️ SENSOR ALERT: {3 - len(valid_files)} feed(s) missing.")
                analysis_dict = {
                    "severity": "HIGH",
                    "analysis_summary": "HARDWARE_BLACKOUT: Physical sensor disconnection detected. AI bypassed.",
                    "processed_images": [prep_frame(f) for f in valid_files]
                }
            else:
                st.write("✅ All sensors responsive.")
                
                # 2. PARALLEL PRIVACY PIPELINE
                st.write("2. 🛡️ Running Local Privacy Filter Concurrently...")
                with ThreadPoolExecutor() as executor:
                    frames_iter = executor.map(prep_frame, valid_files)
                    frames = list(frames_iter)
                
                # 3. AI REASONING
                st.write("3. 🧠 Gemma Analyzing Telemetry + Visual Context...")
                prompt = """
                TASK: Analyze these 3 dashcam frames from an Ontario Blizzard pileup.
                Output ONLY valid JSON: 
                {"severity": "LOW/MED/HIGH", "victims": int, "fire_risk": bool, "analysis_summary": "short text"}
                """
                
                msg = HumanMessage(content=[{"type": "text", "text": prompt}] + 
                    [{"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{f}"}} for f in frames if f])
                
                try:
                    res = llm.invoke([msg]).content
                    start, end = res.find('{'), res.rfind('}') + 1
                    analysis_dict = json.loads(res[start:end])
                    analysis_dict["processed_images"] = frames
                    st.write("4. 📡 Triage Data Compressed & Transmitted.")
                    
                except Exception:
                    analysis_dict = {
                        "severity": "HIGH", 
                        "analysis_summary": "COMPUTE_TIMEOUT: System overloaded. Manual assessment required.", 
                        "processed_images": frames
                    }
                    st.warning("Inference timeout. Sending raw telemetry.")

            save_event_data({
                "event_id": st.session_state.current_event_id,
                "status": "TRIAGE_COMPLETE",
                "analysis": analysis_dict
            })
            
            st.session_state.ai_complete = True
            status.update(label="✅ Triage Protocol Finalized", state="complete")
            st.rerun()