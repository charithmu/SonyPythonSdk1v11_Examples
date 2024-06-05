from PySide6.QtWidgets import  QApplication
from PySide6.QtCore import QObject, QEvent, Signal
from PySide6.QtGui import QPixmap

import sony_cr

PropertyChangedEventType = QEvent.registerEventType()
ConnectionStatusEventType = QEvent.registerEventType()

class PropertyChangedEvent(QEvent):
    def __init__(self, name: str, value: dict, is_live_view: bool):
        super().__init__( QEvent.Type(PropertyChangedEventType) )

        self.property_name = name
        self.property_value = value
        self.is_live_view = is_live_view

class ConnectionStatusChangedEvent(QEvent):
    def __init__(self, connected: bool):
        super().__init__(QEvent.Type(ConnectionStatusEventType))
        self.connected = connected

class QCamera(QObject):

    cameraPropertyChanged = Signal(str, dict, arguments=['name', 'value'])
    cameraLiveViewPropertyChanged = Signal(str, list, arguments=['name', 'value'])
    connectionStatusChanged = Signal(bool)

    def __init__(self, parent, camera_id: str):
        super().__init__(parent)

        self.camera = sony_cr.get_camera(camera_id)
        self.camera.on_property_changed(self._camera_property_changed)
        self.camera.on_live_view_property_changed(self._camera_live_view_property_changed)
        self.camera.on_connection_status_changed(self._camera_connection_status_changed)

    def cameraId(self) -> str:
        return self.camera.id()

    def cameraModel(self) -> str:
        return self.camera.model()

    def connectToCamera(self, transferMode: bool = False):
        if transferMode:
            self.camera.connect_transfer()
        else:
            self.camera.connect(0)

    def disconnectFromCamera(self):
        self.camera.disconnect()

    def setCameraProperty(self, name, value):
        self.camera.set_property(name, value)

    def getLiveView(self) -> QPixmap:
        """Get the camera's live view image as a QPixmap"""

        jpegData = self.camera.get_live_view()

        image = QPixmap()
        image.loadFromData(jpegData, "jpeg")

        return image

    def event(self, e: QEvent):
        if e.type() == PropertyChangedEventType:
            if e.is_live_view:
                self.cameraLiveViewPropertyChanged.emit(e.property_name, e.property_value)    
            else :
                self.cameraPropertyChanged.emit(e.property_name, e.property_value)
            e.accept()
            return True                    
        if e.type() == ConnectionStatusEventType:
            self.connectionStatusChanged.emit(e.connected)
            e.accept()
            return True
            
        return super().event(e)

    def _camera_property_changed(self, name: str, value: dict):
        # this comes from the camera's callback thread, so we
        # need to post to the main Qt thread
        QApplication.instance().postEvent( self, PropertyChangedEvent(name, value, False) )

    def _camera_live_view_property_changed(self, name: str, value: dict):        
        QApplication.instance().postEvent( self, PropertyChangedEvent(name, value, True) )

    def _camera_connection_status_changed(self, connected: bool):
        QApplication.instance().postEvent( self, ConnectionStatusChangedEvent(connected) )
