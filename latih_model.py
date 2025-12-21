from ultralytics import YOLO
from roboflow import Roboflow

rf = Roboflow(api_key="lmF8QZBxuO5BAt9DOSgp")
project = rf.workspace("automated-waste-management-robotic-system-for-efficient-collection-and-segregation-of-dryandwetwaste").project("plastic-and-non-plastic")
version = project.version(1)
dataset = version.download("yolov8")

if __name__ == '__main__':
    model = YOLO('yolov8n.pt')

    print("Mulai training... Laptop akan bekerja keras, harap bersabar.")
    
    model.train(
        data=f'{dataset.location}/data.yaml',
        epochs=200,
        patience=40,
        imgsz=416,
        batch=32,
        lr0=0.001,
        workers=1,
        name='ai_waste_guardian_200_epoch'
    )