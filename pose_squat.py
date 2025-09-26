import cv2
import mediapipe as mp
import numpy as np
import PoseModule as pm

def squat(reps=0):
    cap = cv2.VideoCapture(0)
    detector = pm.poseDetector()
    count = 0
    direction = 0
    form = 0
    feedback = "ENDEREZA TU ESPALDA"
    errores = 0
    error_flag = False

    with detector.pose:
        while True:
            cap.set(3, 1280)  # Set width to 1280
            cap.set(4, 720)   # Set height to 720  
            ret, img = cap.read() #640 x 480


            img = detector.findPose(img, False)
            lmList = detector.findPosition(img, False)
            # print(lmList)
            
            if len(lmList) != 0:
                shoulder = detector.findAngle(img, 7, 11, 23)
                knee = detector.findAngle(img, 23, 25, 27)
                per = np.interp(knee, (90, 160), (0, 100))
                bar = np.interp(knee, (90, 160), (380, 50))
                if shoulder > 160:
                    form = 1
                if form == 1:
                    if per == 0:
                        if knee <= 90 and shoulder > 160:
                            feedback = "SUBE"
                            if direction == 0:
                                count += 0.5
                                direction = 1
                            error_flag = False
                        else:
                            feedback = "ENDEREZA TU ESPALDA"
                            if not error_flag:
                                errores += 1
                                error_flag = True
                    if per == 100:
                        if shoulder > 160 and knee > 160:
                            feedback = "BAJA"
                            if direction == 1:
                                count += 0.5
                                direction = 0
                            error_flag = False
                        else:
                            feedback = "ENDEREZA TU ESPALDA"
                            if not error_flag:
                                errores += 1
                                error_flag = True
                    cv2.rectangle(img, (1080, 50), (1100, 380), (0, 255, 0), 3)
                    cv2.rectangle(img, (1080, int(bar)), (1100, 380), (0, 255, 0), cv2.FILLED)
                    cv2.putText(img, f'{int(per)}%', (950, 230), cv2.FONT_HERSHEY_PLAIN, 2,
                                (255, 255, 0), 2)
                cv2.rectangle(img, (0, 380), (100, 480), (0, 255, 0), cv2.FILLED)
                cv2.putText(img, str(int(count)), (25, 455), cv2.FONT_HERSHEY_PLAIN, 5,
                            (255, 0, 0), 5)
                cv2.putText(img, feedback, (500, 40), cv2.FONT_HERSHEY_PLAIN, 2,
                            (255, 255, 0), 2)
                x_knee = lmList[25][1]
                x_ankle = lmList[27][1]
                if x_knee - x_ankle < 5:
                    detector.correctPoseSquat(form, shoulder, knee, img, 11, 25, 27)
            # Convert the frame to JPEG format
                ret, jpeg = cv2.imencode('.jpg', img)

                # Yield the frame and error count
                yield (b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n\r\n', errores)
            if reps > 0 and int(count) >= reps:
                break
    cap.release()
    cv2.destroyAllWindows()