import os
import functools
from PyQt5 import QtCore, QtGui, QtWidgets, QtWebEngineWidgets, QtWebChannel

class MapWidget(QtWidgets.QWidget):
    def __init__(self):
        super(MapWidget, self).__init__()
        self.setupUi()

    def setupUi(self):
        from lib.hidden import constants
       # self.setFixedSize(800, 500)
        vbox = QtWidgets.QVBoxLayout()
        self.setLayout(vbox)

        label = self.label = QtWidgets.QLabel()
        sp = QtWidgets.QSizePolicy()
        sp.setVerticalStretch(0)
        label.setSizePolicy(sp)
        vbox.addWidget(label)
        view = self.view = QtWebEngineWidgets.QWebEngineView()
        channel = self.channel = QtWebChannel.QWebChannel()

        channel.registerObject("MainWindow", self)
        view.page().setWebChannel(channel)
        file = os.path.join(
            os.path.dirname(os.path.realpath(__file__).split(constants.NAME)[0]),
            constants.NAME,
            "src/main/assets/map.html",
        )
        print(file)
        self.view.setUrl(QtCore.QUrl.fromLocalFile(file))

        vbox.addWidget(view)

        button = QtWidgets.QPushButton("Centralizar no Carmo do Paranaíba")
        panToParis = functools.partial(self.panMap, -46.30973, -19.00009)
        button.clicked.connect(panToParis)
        vbox.addWidget(button)

    @QtCore.pyqtSlot(float, float)
    def onMapMove(self, lat, lng):
        self.label.setText("Lng: {:.5f}, Lat: {:.5f}".format(lng, lat))

    def panMap(self, lng, lat):
        page = self.view.page()
        page.runJavaScript("map.panTo(L.latLng({}, {}));".format(lat, lng))


def _test():
    from hidden import constants
    import sys
    app = QtWidgets.QApplication(sys.argv)
    w = MapWidget()
    w.show()
    print("RUNNING TEST!!!")
    sys.exit(app.exec_())
    

if __name__ == "__main__":
    _test()
