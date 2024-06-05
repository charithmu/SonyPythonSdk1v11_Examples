from typing import Any, Union
import io

from PySide6.QtWidgets import (
    QWidget,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QComboBox,
    QDialog,
    QSizePolicy,
)
from PySide6.QtCore import (
    Qt,
    Slot,
    QAbstractItemModel,
    QAbstractTableModel,
    QModelIndex,
    QPersistentModelIndex,
    QRect,
    QTimer,
    QSize,
)
from PySide6.QtGui import QPainter, QPixmap, QColor

from PIL import Image
from PIL.ImageQt import ImageQt
from pillow_heif import register_heif_opener

from camera import QCamera

register_heif_opener()


class CameraSelectDialogue(QDialog):
    def __init__(self, cameras: dict):
        super().__init__()

        self.currentIndex = 0
        self.setWindowTitle("Select Camera")
        self.cb = QComboBox(self)
        self.cb.currentIndexChanged.connect(self.indexChanged)
        self.cb.setMinimumHeight(32)
        self.cb.setMinimumWidth(200)

        for i in cameras:
            self.camera = QCamera(self, i["id"])
            self.cb.addItem("{}".format(self.camera.cameraModel()))

    def indexChanged(self, i):
        self.currentIndex = i

    def getCurrentIndex(self):
        return self.currentIndex


class ComboBoxItemDelegate(QStyledItemDelegate):
    def __init__(self):
        super().__init__()

        self.editor = None

    def createEditor(
        self,
        parent: QWidget,
        option: QStyleOptionViewItem,
        index: Union[QModelIndex, QPersistentModelIndex],
    ) -> QWidget:
        cb = QComboBox(parent)

        possible = index.data(Qt.ItemDataRole.EditRole)

        for p in possible:
            cb.addItem(p)

        return cb

    def destroyEditor(
        self, editor: QWidget, index: Union[QModelIndex, QPersistentModelIndex]
    ) -> None:
        self.editor = None
        return super().destroyEditor(editor, index)

    Slot(int)

    def indexChanged(self, index):
        self.commitData.emit(self.editor)

    def setEditorData(
        self, editor: QWidget, index: Union[QModelIndex, QPersistentModelIndex]
    ) -> None:
        comboIndex = editor.findText(index.data(Qt.ItemDataRole.DisplayRole))
        if comboIndex >= 0:
            editor.setCurrentIndex(comboIndex)

        # commit data whenever the index is changed, rather than the default which is when
        # the combobox loses focus
        editor.currentIndexChanged.connect(self.indexChanged)
        self.editor = editor

    def setModelData(
        self,
        editor: QWidget,
        model: QAbstractItemModel,
        index: Union[QModelIndex, QPersistentModelIndex],
    ) -> None:
        model.setData(index, editor.currentText(), Qt.ItemDataRole.EditRole)


def draw_image_maintain_aspect(painter: QPainter, image: QPixmap, rect: QRect):
    if image.width() == 0 or image.height() == 0:
        return

    aspect_ratio = image.width() / image.height()

    draw_width = rect.width()
    draw_height = int(draw_width / aspect_ratio)

    if draw_height > rect.height():
        draw_height = rect.height()
        draw_width = int(draw_height * aspect_ratio)

    draw_x = rect.x() + (rect.width() - draw_width) // 2
    draw_y = rect.y() + (rect.height() - draw_height) // 2

    image_rect = QRect(draw_x, draw_y, draw_width, draw_height)

    painter.drawPixmap(image_rect, image)

    return image_rect


class ThumbnailItemDelegate(QStyledItemDelegate):
    def __init__(self):
        super().__init__()

    def paint(self, painter, option, index):
        pixmap = index.data(Qt.ItemDataRole.DisplayRole)
        draw_image_maintain_aspect(painter, pixmap, option.rect)


class CameraPropertyTableModel(QAbstractTableModel):
    columns = ["Name", "Value"]

    def __init__(self):
        super().__init__()
        self.camera: QCamera = None
        self.rows = []

    def setCamera(self, camera: QCamera):
        if self.camera is not None:
            self.camera.cameraPropertyChanged.disconnect(self.updateProperty)
            self.clear()

        self.camera = camera
        self.camera.cameraPropertyChanged.connect(self.updateProperty)

    def resetCamera(self):
        if self.camera is not None:
            self.camera.cameraPropertyChanged.disconnect(self.updateProperty)
            self.clear()
            self.camera = None

    def clear(self):
        if len(self.rows):
            self.beginRemoveRows(QModelIndex(), 0, len(self.rows) - 1)
            self.rows = []
            self.endRemoveRows()

    def _propertyRow(self, name):
        for i, row in enumerate(self.rows):
            if row[0] == name:
                return i
        return -1

    @Slot(str, dict)
    def updateProperty(self, name: str, value: dict):
        row_num = self._propertyRow(name)

        if row_num == -1:
            row_names = [row[0] for row in self.rows]
            row_names.append(name)
            row_names = sorted(row_names)
            insert_index = row_names.index(name)

            self.beginInsertRows(QModelIndex(), insert_index, insert_index)
            self.rows.insert(insert_index, (name, value))
            self.endInsertRows()
        else:
            self.rows[row_num] = (name, value)
            self.dataChanged.emit(
                self.index(row_num, 0),
                self.index(row_num, 1),
                [Qt.ItemDataRole.DisplayRole],
            )

    def columnCount(self, parent) -> int:
        return len(self.columns)

    def rowCount(self, parent) -> int:
        return len(self.rows)

    def data(self, index: QModelIndex, role: int) -> Any:
        if role == Qt.ItemDataRole.DisplayRole:
            row = self.rows[index.row()]
            if index.column() == 0:
                return row[0]
            if index.column() == 1:
                return row[1]["value"]
        elif role == Qt.ItemDataRole.EditRole:
            row = self.rows[index.row()]
            if index.column() == 1:
                return row[1]["possible"]

        return None

    def setData(
        self, index: Union[QModelIndex, QPersistentModelIndex], value: Any, role: int
    ) -> bool:
        if role == Qt.ItemDataRole.EditRole:
            row_name, _ = self.rows[index.row()]
            self.camera.setCameraProperty(row_name, value)
            return True
        return super().setData(index, value, role)

    def flags(self, index: QModelIndex) -> Qt.ItemFlag:
        f = Qt.ItemFlag.ItemIsEnabled
        if index.column() == 1:
            row = self.rows[index.row()]
            if row[1]["writable"]:
                f |= Qt.ItemFlag.ItemIsEditable | Qt.ItemFlag.ItemIsSelectable
        return f

    def headerData(self, section: int, orientation: Qt.Orientation, role: int) -> Any:
        if (
            orientation == Qt.Orientation.Horizontal
            and role == Qt.ItemDataRole.DisplayRole
        ):
            return self.columns[section]

        return super().headerData(section, orientation, role)


class LiveViewWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.setSizePolicy(
            QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        )

        self.camera: QCamera = None

        self.liveViewProperties = {}
        self.liveViewPropsFailed = False

    def setCamera(self, camera: QCamera):
        self.camera = camera

        self.camera.cameraLiveViewPropertyChanged.connect(self.updateLiveViewProperty)

        self.updateTimer = QTimer(self)
        self.updateTimer.timeout.connect(self.update)
        self.updateTimer.start(40)

    def resetCamera(self):
        if self.camera is not None:
            self.updateTimer.stop()
            self.updateTimer.timeout.disconnect()
            self.updateTimer = None
            self.camera.cameraLiveViewPropertyChanged.disconnect(
                self.updateLiveViewProperty
            )
            self.camera = None

            self.update()

    def paintEvent(self, event):
        if self.camera is None:
            return

        try:
            image = self.camera.getLiveView()
        except:
            return

        painter = QPainter(self)

        image_rect = draw_image_maintain_aspect(
            painter, image, QRect(0, 0, self.width(), self.height())
        )

        self.drawLiveViewProperties(painter, image_rect, image.size())

        painter.end()

    def _getLiveViewValuePosition(self, value, image_rect: QRect):
        val_x = value["x"]
        val_y = value["y"]

        x_real = val_x[0] / val_x[1]
        y_real = val_y[0] / val_y[1]

        x = int(image_rect.x() + x_real * image_rect.width())
        y = int(image_rect.y() + y_real * image_rect.height())

        return x, y

    def _getLiveViewValueSize(
        self, value, image_rect: QRect, live_view_image_size: QSize
    ):
        val_w = value["width"]
        val_h = value["height"]
        w = int(image_rect.width() * val_w / live_view_image_size.width())
        h = int(image_rect.height() * val_h / live_view_image_size.height())
        return w, h

    def drawLiveViewProperties(
        self, painter: QPainter, image_rect: QRect, live_view_image_size: QSize
    ):
        for name, values in self.liveViewProperties.items():
            if name == "TrackingFrame":
                for value in values:
                    self.drawTrackingFrame(
                        value, painter, image_rect, live_view_image_size
                    )
            elif name == "FaceFrame":
                for value in values:
                    self.drawFaceFrame(value, painter, image_rect, live_view_image_size)
            elif name == "AF_Area_Position":
                for value in values:
                    self.drawAFAreaPosition(value, painter, image_rect, live_view_image_size)
            elif name == "Focus_Magnifier_Position":
                for value in values:
                    self.drawMagnifierPosition(value, painter, image_rect)

    def drawTrackingFrame(
        self, value, painter: QPainter, image_rect: QRect, live_view_image_size: QSize
    ):
        x, y = self._getLiveViewValuePosition(value, image_rect)
        w, h = self._getLiveViewValueSize(value, image_rect, live_view_image_size)

        painter.setPen(QColor("#FFFF0000"))
        painter.drawRect(int(x - w/2), int(y-h/2), w, h)

    def drawFaceFrame(
        self, value, painter: QPainter, image_rect: QRect, live_view_image_size: QSize
    ):
        x, y = self._getLiveViewValuePosition(value, image_rect)
        w, h = self._getLiveViewValueSize(value, image_rect, live_view_image_size)
        painter.setPen(QColor("#FFFFFFFF"))
        painter.drawRect(int(x - w/2), int(y-h/2), w, h)

    def drawAFAreaPosition(
        self, value, painter: QPainter, image_rect: QRect, live_view_image_size: QSize
    ):
        x, y = self._getLiveViewValuePosition(value, image_rect)
        w, h = self._getLiveViewValueSize(value, image_rect, live_view_image_size)

        painter.setPen(QColor("#FF00FF00"))
        painter.drawRect(int(x - w/2), int(y-h/2), w, h)

    def drawMagnifierPosition(self, value, painter: QPainter, image_rect: QRect):
        x, y = self._getLiveViewValuePosition(value, image_rect)
        painter.setPen(QColor("#FFFF0000"))
        painter.drawLine(x - 4, y, x + 4, y)
        painter.drawLine(x, y - 4, x, y + 4)

    @Slot(str, list)
    def updateLiveViewProperty(self, name, value):
        self.liveViewProperties[name] = value


KILO = 1024
MEGA = 1024 * KILO


def format_size(size):
    if size < KILO:
        return f"{size}"
    if size < MEGA:
        size = size / KILO
        return f"{size:.2f}KB"
    size = size / MEGA
    return f"{size:.2f}MB"


class CameraContentsTableModel(QAbstractTableModel):
    columns = ["Thumbnail", "Filename", "Timestamp", "Size", "Resolution"]

    def __init__(self):
        super().__init__()
        self.camera: QCamera = None
        self.rows = []

    def setCamera(self, camera: QCamera):
        if self.camera is not None:
            self.clear()

        self.camera = camera

        folders = self.camera.camera.get_folders()

        index = 0
        for folder in folders:
            files = self.camera.camera.get_folder_contents(folder)

            self.beginInsertRows(QModelIndex(), index, index + len(files))
            for item in files:
                self.rows.append([folder, item, None])
            self.endInsertRows()

            index += len(files)

    def resetCamera(self):
        self.clear()
        self.camera = None

    def loadImageForRow(self, index):
        folder, item, _ = self.rows[index]
        path = f"{folder}/{item.filename}"
        thumbnail, format = self.camera.camera.get_thumbnail_image(path)

        image = Image.open(io.BytesIO(thumbnail), formats=[format])
        pixmap = QPixmap.fromImage(ImageQt(image))

        self.rows[index][2] = pixmap

        return pixmap

    def clear(self):
        if len(self.rows):
            self.beginRemoveRows(QModelIndex(), 0, len(self.rows) - 1)
            self.rows = []
            self.endRemoveRows()

    def columnCount(self, parent) -> int:
        return len(self.columns)

    def rowCount(self, parent) -> int:
        return len(self.rows)

    def data(self, index: QModelIndex, role: int) -> Any:
        folder, item, image = self.rows[index.row()]
        if role == Qt.ItemDataRole.DisplayRole:
            if index.column() == 0:
                if image is None:
                    image = self.loadImageForRow(index.row())
                return image
            if index.column() == 1:
                return item.filename
            if index.column() == 2:
                return item.timestamp.strftime("%d/%m/%Y %H:%M:%S")
            if index.column() == 3:
                return format_size(item.content_size)
            if index.column() == 4:
                return f"{item.width}x{item.height}"

        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int) -> Any:
        if (
            orientation == Qt.Orientation.Horizontal
            and role == Qt.ItemDataRole.DisplayRole
        ):
            return self.columns[section]

        return super().headerData(section, orientation, role)
