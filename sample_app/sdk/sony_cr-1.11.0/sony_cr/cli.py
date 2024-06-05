import sys
import sony_cr

def main():
    print("Sony Camera Remote CLI. Version {}".format( sony_cr.__version__ ))
           
    print("Finding connected camera devices...")
    camera_info = sony_cr.find_cameras()

    if len(camera_info) == 0:
        print("No cameras detected. Connect a camera and retry")
        return
        
    print("Found {} connected camera(s):".format(len(camera_info)))
    
    for i, info in enumerate(camera_info):
        model = info["model"]
        id = info["id"]
        print(f"[{i}] {model} ({id})")
    
    print("Connect to camera with input number...")
    
    done = False
    while not done:
        selection = input("input> ")
        try:
            if selection == 'q':
                print("Quitting")
                break
            camera_index = int(selection)
            if camera_index >= 0 and camera_index < len(camera_info):
                done = True
                break
            print("Invalid index {}".format(camera_index))
        except:
            print("Not a valid number")
        print("Enter a number between 0 and {} or 'q' to quit".format(len(camera_info) - 1))

    if not done:
        return
        
        

if __name__=="__main__":
    main()