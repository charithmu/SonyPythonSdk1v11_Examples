import os
import shutil
import platform
import importlib
from sony_cr._sony_cr import __version__, CameraManager, python_executable

if platform.system() == "Windows":
    def _install_dlls():
        here = os.path.dirname(os.path.abspath(__file__))
        python_exe_dir = os.path.dirname(python_executable)
        src_adapter_dir = os.path.join(here, "CrAdapter")
        dst_adapter_dir = os.path.join(python_exe_dir, "CrAdapter")
        
        upgrade_required = False
        create_required = not os.path.exists(dst_adapter_dir)
        
        if os.path.exists(dst_adapter_dir):            
            for f in os.listdir(src_adapter_dir):
                dst_file = os.path.join(dst_adapter_dir, f)
                if not os.path.exists(dst_file):
                    # skip Cr_PTP_IP.dll if it has been removed manually to improve startup time
                    continue
                    
                src_file = os.path.join(src_adapter_dir, f)                               
                src_mtime = os.path.getmtime(src_file)
                dst_mtime = os.path.getmtime(dst_file)
                
                if src_mtime > dst_mtime:
                    upgrade_required = True
                    break
                
        if create_required or upgrade_required:
            install_mode = "Upgrading" if upgrade_required else "Installing"
            print(f"{install_mode} CrAdapter dlls in {dst_adapter_dir}")
            if create_required:
                os.makedirs(dst_adapter_dir)
            for f in os.listdir(src_adapter_dir):
                shutil.copyfile(os.path.join(src_adapter_dir, f), os.path.join(dst_adapter_dir, f))
            
    _install_dlls()
            
_cm = CameraManager()

def find_cameras():
    """Find all cameras connected to this computer.
    
       Returns a list of dicts with the following keys:
            "id"        : the camera's ID
            "model"     : the camera's model name
            "conn_type" : the connection type, either "USB" or "IP"     
    """

    return _cm.find_cameras()
    
def get_camera(camera_id):
    """Get the controller object for a camera.    
    """
    
    return _cm.get_camera(camera_id)
