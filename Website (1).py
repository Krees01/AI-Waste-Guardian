import streamlit as st
import cv2
import av
import math
import time
from ultralytics import YOLO
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase, RTCConfiguration, WebRtcMode

# website setup
st.set_page_config(
    page_title="AI Waste Guardian (Real-Time)",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; }
    
    .css-card {
        background-color: #1E1E1E; border-radius: 15px; padding: 20px;
        border: 1px solid #333; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.5);
        margin-bottom: 20px; text-align: center;
    }
    
    .section-title {
        font-size: 18px; font-weight: 600; color: #cfcfcf;
        margin-bottom: 15px; text-transform: uppercase; letter-spacing: 1px;
    }

    .lamp-wrapper { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; }
    .led { width: 80px; height: 80px; border-radius: 50%; background: radial-gradient(circle, #333 30%, #111 100%); border: 2px solid #444; margin-bottom: 15px; transition: all 0.1s ease; }
    
    /* Efek Glow diperkuat biar responsif */
    .led-red { background: radial-gradient(circle, #ff4b4b 30%, #990000 100%); border: 2px solid #fff; box-shadow: 0 0 50px #ff4b4b; transform: scale(1.1); }
    .led-green { background: radial-gradient(circle, #00ff66 30%, #009933 100%); border: 2px solid #fff; box-shadow: 0 0 50px #00ff66; transform: scale(1.1); }
    
    .status-label { font-size: 16px; font-weight: bold; color: #666; }
    .status-active-red { color: #ff4b4b; text-shadow: 0 0 10px #ff4b4b; }
    .status-active-green { color: #00ff66; text-shadow: 0 0 10px #00ff66; }
    </style>
    """, unsafe_allow_html=True)

class WasteDetector(VideoProcessorBase):
    def __init__(self):
        try:

            self.model = YOLO(r"best.pt")
        except:
            self.model = None
            
        self.latest_status = "NETRAL"

    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")
        
        if self.model is None: 
            return av.VideoFrame.from_ndarray(img, format="bgr24")
        
        img_small = cv2.resize(img, (320, 240))
        results = self.model(img_small, verbose=False)
        classNames = ["Non-Plastic", "Plastic"]
        
        h_orig, w_orig, _ = img.shape
        scale_x = w_orig / 320
        scale_y = h_orig / 240
        
        detected_status = "NETRAL"

        for r in results:
            boxes = r.boxes
            for box in boxes:
                x1 = int(box.xyxy[0][0] * scale_x)
                y1 = int(box.xyxy[0][1] * scale_y)
                x2 = int(box.xyxy[0][2] * scale_x)
                y2 = int(box.xyxy[0][3] * scale_y)

                conf = math.ceil((box.conf[0] * 100)) / 100
                cls = int(box.cls[0])
                currentClass = classNames[cls]
                

                if ((x2-x1)*(y2-y1)) / (w_orig*h_orig) > 0.8: continue

                if conf > 0.45:
                    if currentClass == "Plastic":
                        detected_status = "PLASTIK"
                        color = (0, 0, 255)
                    elif currentClass == "Non-Plastic":
                        detected_status = "NON-PLASTIK"
                        color = (0, 255, 0)
                    else:
                        color = (255, 0, 0)

                    cv2.rectangle(img, (x1, y1), (x2, y2), color, 3)
                    cv2.putText(img, f"{currentClass} {int(conf*100)}%", (x1, y1 - 10), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        
        self.latest_status = detected_status
        return av.VideoFrame.from_ndarray(img, format="bgr24")

st.markdown("<h1 style='text-align: center; color: white;'>AI WASTE GUARDIAN (REAL-TIME)</h1>", unsafe_allow_html=True)

col_video, col_panel = st.columns([2.5, 1.2])

with col_video:
    st.markdown("<div class='section-title'>Kamera</div>", unsafe_allow_html=True)
    
    rtc_configuration = RTCConfiguration({"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]})
    
    ctx = webrtc_streamer(
        key="waste-realtime",
        mode=WebRtcMode.SENDRECV,
        rtc_configuration=rtc_configuration,
        video_processor_factory=WasteDetector,
        media_stream_constraints={"video": True, "audio": False},
        async_processing=True,
    )

with col_panel:
    st.markdown("<div class='section-title'>Status Indikator</div>", unsafe_allow_html=True)
    lampu_merah_placeholder = st.empty()
    st.write("") 
    lampu_hijau_placeholder = st.empty()

def render_lamp(placeholder, color_type, is_on, label_top, label_bottom):
    css_class = "led"
    text_class = "status-label"
    
    if is_on:
        if color_type == "red":
            css_class = "led led-red"
            text_class = "status-label status-active-red"
        elif color_type == "green":
            css_class = "led led-green"
            text_class = "status-label status-active-green"
            
    html_code = f"""
    <div class="css-card">
        <div style="color: #888; font-size: 12px; margin-bottom: 10px;">{label_top}</div>
        <div class="lamp-wrapper">
            <div class="{css_class}"></div>
            <div class="{text_class}">{label_bottom}</div>
        </div>
    </div>
    """
    placeholder.markdown(html_code, unsafe_allow_html=True)

if ctx.state.playing:
    last_status = None
    
    while True:
        if ctx.video_processor:
            current_status = ctx.video_processor.latest_status
        else:
            current_status = "NETRAL"

        if current_status != last_status:
            if current_status == "PLASTIK":
                render_lamp(lampu_merah_placeholder, "red", True, "KATEGORI 1", "PLASTIK DETECTED")
                render_lamp(lampu_hijau_placeholder, "green", False, "KATEGORI 2", "STANDBY")
            elif current_status == "NON-PLASTIK":
                render_lamp(lampu_merah_placeholder, "red", False, "KATEGORI 1", "STANDBY")
                render_lamp(lampu_hijau_placeholder, "green", True, "KATEGORI 2", "NON-PLASTIK DETECTED")
            else:
                render_lamp(lampu_merah_placeholder, "red", False, "KATEGORI 1", "WAITING...")
                render_lamp(lampu_hijau_placeholder, "green", False, "KATEGORI 2", "WAITING...")
            
            last_status = current_status

        time.sleep(0.05)

else:
    render_lamp(lampu_merah_placeholder, "red", False, "KATEGORI 1", "OFF")
    render_lamp(lampu_hijau_placeholder, "green", False, "KATEGORI 2", "OFF")