import sony_cr
import io
import sys
import time

cm = sony_cr.CameraManager()

cameras = cm.find_cameras()

print("Found {} camera(s)".format(len(cameras)))
for i, cam in enumerate(cameras):
    print("[{}]: {} {}".format(i+1, cam['model'], cam['id']))

if len(cameras) == 0:
    sys.exit(0)

cam = cm.get_camera(cameras[0]['id'])

cam.connect()

print("Saving images to ", cam.get_save_folder())

cam.capture_image(100)

# wait for the images to be downloaded from the camera
time.sleep(2)