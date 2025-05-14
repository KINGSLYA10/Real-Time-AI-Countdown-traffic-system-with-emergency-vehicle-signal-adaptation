import serial
import time
import cv2
import numpy as np

# ✅ Initialize Serial Communication
try:
    ser = serial.Serial('COM6', 115200, timeout=1)  # Change COM port if needed
    time.sleep(2)
    print("✅ Serial Port Opened Successfully!")
except serial.SerialException:
    print("❌ Serial Port Error: Could not open COM6. Check connection.")
    ser = None

# ✅ Load YOLO Model
net = cv2.dnn.readNet("yolov3.weights", "yolov3.cfg")
layer_names = net.getLayerNames()
output_layers = [layer_names[i - 1] for i in net.getUnconnectedOutLayers()]


# ✅ COCO Classes
coco_classes = ["person", "bicycle", "car", "motorbike", "aeroplane", "bus", 
                "train", "truck", "boat", "traffic light", "fire hydrant", 
                "stop sign", "parking meter", "bench", "bird", "cat", "dog", 
                "horse", "sheep", "cow", "elephant", "bear", "zebra", 
                "giraffe", "backpack", "umbrella", "handbag", "tie", "suitcase", 
                "frisbee", "skis", "snowboard", "sports ball", "kite", "baseball bat", 
                "baseball glove", "skateboard", "surfboard", "tennis racket", 
                "bottle", "wine glass", "cup", "fork", "knife", "spoon", 
                "bowl", "banana", "apple", "sandwich", "orange", "broccoli", 
                "carrot", "hot dog", "pizza", "donut", "cake", "chair", 
                "sofa", "pottedplant", "bed", "diningtable", "toilet", 
                "tvmonitor", "laptop", "mouse", "remote", "keyboard", "cell phone", 
                "microwave", "oven", "toaster", "sink", "refrigerator", 
                "book", "clock", "vase", "scissors", "teddy bear", "hair drier", "toothbrush", 
                "ambulance", "fire engine"]

# ✅ Vehicle Classes (including emergency vehicles) 
vehicle_classes = ["car", "motorbike", "bus", "truck", "ambulance", "fire engine"]

# ✅ Video List (First & Second Video)
video_files = ["traffic cars.mp4", "traffic cars5.mp4", "traffic cars7.mp4"]

# ✅ Global Stop Flag
stop_processing = False  # If 'Q' is pressed, set this to True to stop the program

# ✅ Function to Process Video
def process_video(video_path):
    global predicted_countdown, stop_processing
    print(f"🎥 Processing Video: {video_path}")
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        print(f"❌ Error: Cannot open video {video_path}")
        return  # Skip to the next video

    while cap.isOpened():
        if stop_processing:
            break  # Stop the video loop if 'Q' was pressed

        ret, frame = cap.read()
        if not ret:
            break  # Exit when the video ends

        height, width, _ = frame.shape
        frame = cv2.resize(frame, (600, 600))

        # 🔍 Preprocess Image for YOLOq
        blob = cv2.dnn.blobFromImage(frame, 0.00392, (416, 416), (0, 0, 0), True, crop=False)
        net.setInput(blob)
        outs = net.forward(output_layers)

        # ✅ Object Detection
        vehicle_count = {key: 0 for key in vehicle_classes}
        emergency_detected = False

        for out in outs:
            for detection in out:
                scores = detection[5:]
                class_id = np.argmax(scores)

                # ✅ Prevent IndexError
                if class_id >= len(coco_classes):
                    continue  # Skip invalid detections

                confidence = scores[class_id]
                detected_class = coco_classes[class_id]

                if confidence > 0.5 and detected_class in vehicle_count:
                    vehicle_count[detected_class] += 1
                    if detected_class in ["ambulance", "fire engine"]:
                        emergency_detected = True  # Emergency vehicle detected

        total_vehicles = sum(vehicle_count.values())

        # ✅ Stable Countdown Logic
        if predicted_countdown is None:
            # Set the first detected countdown as the final countdown value
            total_distance = total_vehicles * 6.5  # Assuming 6.5 meters per vehicle
            predicted_countdown = int(total_distance / 3)  # Assume 3 m/s speed
            print(f"📊 Stable Countdown Set: {predicted_countdown} sec")

        # ✅ Decrement Countdown until it reaches 0
        if predicted_countdown > 0:
            predicted_countdown -= 1  # Reduce countdown by 1 second
        else:
            predicted_countdown = 0  # Keep countdown at 0
            print("✅ Countdown Reached 0, Switching to Next Video")
            break  # Exit this video and move to the next one

        # ✅ Send Data to ESP32 (Countdown + Vehicle Count)
        if ser:
            send_data = f"{predicted_countdown},{vehicle_count['car']},{vehicle_count['motorbike']},{vehicle_count['bus']},{vehicle_count['truck']},{vehicle_count['ambulance']},{vehicle_count['fire engine']}"
            ser.write(send_data.encode())
            ser.write(b'\n')
            print(f"📡 Sent Data: {send_data}")

        # ✅ Display on Video
        cv2.putText(frame, f"Countdown: {predicted_countdown} sec", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(frame, f"Cars: {vehicle_count['car']}", (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
        cv2.putText(frame, f"Bikes: {vehicle_count['motorbike']}", (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
        cv2.putText(frame, f"Buses: {vehicle_count['bus']}", (10, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
        cv2.putText(frame, f"Trucks: {vehicle_count['truck']}", (10, 170), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
        cv2.putText(frame, f"Ambulances: {vehicle_count['ambulance']}", (10, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
        cv2.putText(frame, f"Fire Engines: {vehicle_count['fire engine']}", (10, 230), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)

        # ✅ Show Video Output
        cv2.imshow("Traffic Detection", frame)

        time.sleep(1)  # Wait 1 second to sync countdown

        # ✅ Check for 'Q' Press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            stop_processing = True  # Set flag to stop program
            break  # Exit the video processing loop

    cap.release()
    print(f"✅ Finished Processing: {video_path}")

# ✅ Process Videos in Loop
while not stop_processing:
    for video in video_files:
        predicted_countdown = None  # Reset countdown for the new video
        process_video(video)  # Process each video
        if stop_processing:
            break  # Stop processing if 'Q' was pressed

# ✅ Close Everything
cv2.destroyAllWindows()
if ser:
    ser.close()
    print("✅ Serial Port Closed")
