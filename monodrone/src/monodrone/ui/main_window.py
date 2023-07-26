from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QPainter, QPaintEvent, QBrush, QMouseEvent
from PySide6.QtNetwork import QNetworkReply
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget

from monodrone.interface.outer_event_handler import OuterEventHandler
from monodrone.ui.dialog_bubble import DialogBubble


class MainWindow(QMainWindow):
    def __init__(self, parent: QWidget = None, background_image_path: str = ""):
        super().__init__(parent, Qt.FramelessWindowHint | Qt.WindowSystemMenuHint)

        self.background_image_path = background_image_path
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.outer_event_handler = OuterEventHandler()

        self.outer_event_timer = QTimer(self)
        self.outer_event_timer.timeout.connect(self.consume_outer_event)
        self.outer_event_timer.start(1000)

        # move the window
        self.moving_counter = 0
        self.moving_flag = False
        # t = QTimer(self)
        # t.timeout.connect(self.auto_move)
        # t.start(100)

    def auto_move(self):
        geo = self.geometry()
        self.moving_counter += 1
        if self.moving_counter % 30 > 15:
            self.moving_flag = True
        else:
            self.moving_flag = False

        if self.moving_flag:
            self.setGeometry(geo.x() - 10, geo.y(), geo.width(), geo.height())
        else:
            self.setGeometry(geo.x() + 10, geo.y(), geo.width(), geo.height())

    def paintEvent(self, event: QPaintEvent) -> None:
        backgnd = QPixmap()
        backgnd.load(self.background_image_path)
        self.setFixedSize(backgnd.size())
        painter = QPainter(self)
        painter.fillRect(0, 0, self.width(), self.height(), QBrush(backgnd))

    def mousePressEvent(self, event: QMouseEvent) -> None:
        DialogBubble(self, "haha").show()

    def handle_network_reply(self, reply: QNetworkReply):
        reply.deleteLater()
        reply.finished.connect(self.handle_slow_server_response)

    def handle_slow_server_response(self, resp: QNetworkReply):
        DialogBubble(self, str(resp.readAll())).show()

    def consume_outer_event(self):
        if event := self.outer_event_handler.get():
            print(f'qt receive: {event}')
            DialogBubble(self, event).show()


def start_main_window():
    app = QApplication([])
    w = MainWindow(background_image_path=r'../../data/python.png')
    w.show()
    return app.exec()


if __name__ == '__main__':
    start_main_window()