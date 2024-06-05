from PySide6.QtWidgets import  QApplication, QMainWindow, QTabWidget, QVBoxLayout, QHBoxLayout, QLabel, QWidget, QSplitter
from PySide6.QtWidgets import  QTableView, QSizePolicy
from PySide6.QtCore import Qt, Slot

import sys
import sony_cr

from camera import QCamera
from widgets import CameraPropertyTableModel, ComboBoxItemDelegate, CameraSelectDialogue, LiveViewWidget, CameraContentsTableModel, ThumbnailItemDelegate
class Window(QMainWindow):

    def __init__(self):
        super().__init__()
        self.resize(800, 600)
        self.setWindowTitle("Sony Camera Remote SDK - PySide6 Example")
         
        self.camera = None
                        
        toolbar = self.addToolBar("Toolbar")
        toolbar.setMinimumHeight(32)

        self.connect_control_action = toolbar.addAction("Connect Control", self.on_connect_to_camera_control)
        self.connect_transfer_action = toolbar.addAction("Connect Transfer", self.on_connect_to_camera_transfer)
        self.disconnect_action = toolbar.addAction("Disconnect", self.on_disconnect_from_camera)
        self.take_picture_action = toolbar.addAction("Take Picture", self.on_take_picture)

        self.take_picture_action.setEnabled(False)
        self.disconnect_action.setEnabled(False)

        self.status_label = QLabel("Not connected")
        
        self.property_table = QTableView()
        self.property_table.verticalHeader().hide()
        self.property_table.horizontalHeader().setStretchLastSection(True)
        self.property_table.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding))
        self.property_table_model = CameraPropertyTableModel()
        self.property_table.setModel(self.property_table_model)
        self.property_table.setItemDelegateForColumn(1, ComboBoxItemDelegate())

        self.live_view = LiveViewWidget()

        self.contents_table_model = CameraContentsTableModel()
        self.contents_table = QTableView()
        self.contents_table.verticalHeader().hide()
        self.contents_table.verticalHeader().setDefaultSectionSize(128)
        self.contents_table.horizontalHeader().setStretchLastSection(True)
        self.contents_table.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding))        
        self.contents_table.setModel(self.contents_table_model)
        self.contents_table.setItemDelegateForColumn(0, ThumbnailItemDelegate())
        self.contents_table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.contents_table.setSelectionMode(QTableView.SelectionMode.SingleSelection)

        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)

        control_widget = QSplitter()
        control_widget.addWidget(self.property_table)
        control_widget.addWidget(self.live_view)
        control_widget.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding))

        self.tab_widget = QTabWidget()
        self.tab_widget.addTab(control_widget, "Control")
        self.tab_widget.addTab(self.contents_table, "Contents")

        self.setCentralWidget(main_widget)
                
        main_layout.addWidget(self.tab_widget)
        main_layout.addWidget(self.status_label, 0, Qt.AlignmentFlag.AlignBottom)
        
    def on_connect_to_camera_transfer(self):
        self.on_connect_to_camera(True)

    def on_connect_to_camera_control(self):   
        self.on_connect_to_camera(False)

    def on_connect_to_camera(self, transfer_mode):        
        self.status_label.setText("Finding cameras...")

        cameras = sony_cr.find_cameras()

        if len(cameras) == 0:
            self.status_label.setText("No cameras connected to PC")
            return
        
        index = 0

        if len(cameras) > 1:
            self.status_label.setText("Multiple cameras connected")
            self.cameraSelectDlg = CameraSelectDialogue(cameras)
            self.cameraSelectDlg.exec()

            index = self.cameraSelectDlg.getCurrentIndex()

        # print the camera ids  and index
        for i, camera in enumerate(cameras):
            print(i, camera["id"])
        

        self.connect_to_camera(cameras[index]["id"], transfer_mode)
 
    def connect_to_camera(self, camera_id, transfer_mode):
        if self.camera:
            self.camera.disconnectFromCamera()

        self.transfer_mode = transfer_mode
        self.camera = QCamera(self, camera_id)
        self.status_label.setText("Connecting to camera {} {}".format(self.camera.cameraId(), self.camera.cameraModel()))
        self.camera.connectionStatusChanged.connect(self._camera_connection_status_changed)
        self.camera.connectToCamera(transfer_mode)

    def on_disconnect_from_camera(self):
        self.camera.disconnectFromCamera()

    def on_take_picture(self):
        self.camera.camera.capture_image(1000)

    @Slot(bool)
    def _camera_connection_status_changed(self, connected: bool):
        if connected:
            if self.transfer_mode:
                self.tab_widget.setCurrentIndex(1)
                self.contents_table_model.setCamera(self.camera)
            else:
                self.tab_widget.setCurrentIndex(0)
                self.property_table_model.setCamera(self.camera)
                self.live_view.setCamera(self.camera)
                
            self.status_label.setText("Connected to camera {} {}".format(self.camera.cameraId(), self.camera.cameraModel()))
        else:
            self.status_label.setText("Disconnected from camera")

            if self.transfer_mode:
                self.contents_table_model.resetCamera()
            else:
                self.property_table_model.resetCamera()
                self.live_view.resetCamera()
            self.camera = None

        self.take_picture_action.setEnabled(connected and not self.transfer_mode)
        self.connect_control_action.setEnabled(not connected)
        self.connect_transfer_action.setEnabled(not connected)
        self.disconnect_action.setEnabled(connected)

app = QApplication(sys.argv)
window = Window()
window.show()
sys.exit(app.exec())