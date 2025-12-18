import cv2
import math
import requests
import threading
from ultralytics import YOLO

IP_ESP_PLASTIK = "10.56.183.212"   # ESP PLastik
IP_ESP_NON_PLASTIK = "10.56.183.171"   # ESP Non Plastik

URL_PLASTIK = f"http://{IP_ESP_PLASTIK}/control"
URL_NON_PLASTIK = f"http://{IP_ESP_NON_PLASTIK}/control"

CAMERA_INDEX = 0 
MODEL_PATH = r"C:\Users\Kristama\OneDrive\AI_Waster_Guardian\runs\detect\ai_waste_guardian_200_epoch3\weights\best.pt"
# cek path model
print("Loading model...")
try:
    model = YOLO(MODEL_PATH)
except:
    print("Model Error. Path salah")
    exit()

classNames = ["Non-Plastic", "Plastic"] 
cap = cv2.VideoCapture(CAMERA_INDEX)
cap.set(3, 640); cap.set(4, 480)

print(f"Sistem siap!")
print(f"Indikator Plastik: {IP_ESP_PLASTIK}")
print(f"Indikator Non-Plastik: {IP_ESP_NON_PLASTIK}")

last_state = "NETRAL" 


def update_lights(jenis_sampah):
    # Kontrol lampu 
    try:
        if jenis_sampah == "PLASTIK":
            # Lampu merah ESP Plastik on
            requests.get(f"{URL_PLASTIK}?action=1", timeout=0.2)
            requests.get(f"{URL_NON_PLASTIK}?action=0", timeout=0.2)
            print("🔴 Lampu Plastik nyala")
            
        elif jenis_sampah == "NON-PLASTIK":
            # Lampu hijau ESP Non-Plastik on
            requests.get(f"{URL_PLASTIK}?action=0", timeout=0.2)
            requests.get(f"{URL_NON_PLASTIK}?action=1", timeout=0.2)
            print("🟢 Lampu Non-Plastik nyala")
            
        else: 
            # State netral 
            requests.get(f"{URL_PLASTIK}?action=0", timeout=0.2)
            requests.get(f"{URL_NON_PLASTIK}?action=0", timeout=0.2)
            
    except:
        pass 

while True:
    success, img = cap.read()
    if not success: break

    results = model(img, stream=True, verbose=False)
    
    is_plastic = False
    obj_detected = False
    # Bounding box
    for r in results:
        boxes = r.boxes
        for box in boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            conf = math.ceil((box.conf[0] * 100)) / 100
            cls = int(box.cls[0])
            currentClass = classNames[cls]
            # box color
            if conf > 0.5:
                obj_detected = True
                if currentClass == "Plastic":
                    is_plastic = True
                    color = (0, 0, 255)
                else:
                    color = (0, 255, 0)

                cv2.rectangle(img, (x1, y1), (x2, y2), color, 3)
                cv2.putText(img, f'{currentClass} {int(conf*100)}%', (x1, y1-10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

    current_state = "NETRAL"
    status_msg = "MENUNGGU..."
    
    if obj_detected:
        if is_plastic:
            current_state = "PLASTIK"
            status_msg = "TERDETEKSI: PLASTIK"
        else:
            current_state = "NON-PLASTIK"
            status_msg = "TERDETEKSI: NON-PLASTIK"

    if current_state != last_state:
        threading.Thread(target=update_lights, args=(current_state,)).start()
        last_state = current_state

    cv2.rectangle(img, (0, 0), (640, 40), (0,0,0), -1)
    cv2.putText(img, status_msg, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    cv2.imshow("Dual ESP32 System", img)
    if cv2.waitKey(1) & 0xFF == ord('q'): break

cap.release()
cv2.destroyAllWindows()
