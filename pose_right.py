import cv2
import mediapipe as mp
import numpy as np
import PoseModule as pm

def right_curl(reps=0):
    cap = cv2.VideoCapture(0)
    detector = pm.poseDetector()
    count = 0
    direction = 0
    form = 0
    feedback = "BAJA EL BRAZO"
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
                elbow = detector.findAngle(img, 12, 14, 16)
                shoulder = detector.findAngle(img, 14, 12, 24)
                per = np.interp(elbow, (40, 160), (100, 0))
                bar = np.interp(elbow, (40, 160), (50, 380))
                if shoulder < 40:
                    form = 1
                if form == 1:
                    if per == 0:
                        if elbow > 160 and shoulder < 40:
                            feedback = "SUBE"
                            if direction == 0:
                                count += 0.5
                                direction = 1
                            error_flag = False
                        else:
                            feedback = "BAJA EL BRAZO"
                            if not error_flag:
                                errores += 1
                                error_flag = True
                    if per == 100:
                        if elbow < 40 and shoulder < 40:
                            feedback = "BAJA"
                            if direction == 1:
                                count += 0.5
                                direction = 0
                            error_flag = False
                        else:
                            feedback = "BAJA EL BRAZO"
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
                detector.correctPoseArm(form, elbow, shoulder, img, 12, 14, 16)

            # Convert the frame to JPEG format
                ret, jpeg = cv2.imencode('.jpg', img)

                # Yield the frame and error count
                yield (b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n\r\n', errores)
            if reps > 0 and int(count) >= reps:
                break
    cap.release()
    cv2.destroyAllWindows()