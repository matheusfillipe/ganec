import json

from PyQt5 import QtCore, QtWidgets, QtWebEngineWidgets, QtWebChannel, QtNetwork, QtGui, QtCore
from lib.hidden.constants import API_KEY

JS = '''
// main var
var map;
var markers = [];
var qtWidget;
var paths=[];
var coordInfoWindow = new google.maps.InfoWindow();
var Mtext;

// main init function
function initialize() {

    var myOptions = {
        center: {lat: -34.397, lng: 150.644},
        streetViewControl: false,
        mapTypeId: google.maps.MapTypeId.ROADMAP,
        zoom: 8
    };

    map = new google.maps.Map(document.getElementById('map_canvas'),
        myOptions);

    new QWebChannel(qt.webChannelTransport, function (channel) {
        qtWidget = channel.objects.qGoogleMap;
    });

    google.maps.event.addListener(map, 'dragend', function () {
        var center = map.getCenter();
        qtWidget.mapIsMoved(center.lat(), center.lng());
    });
    google.maps.event.addListener(map, 'click', function (ev) {
        qtWidget.mapIsClicked(ev.latLng.lat(), ev.latLng.lng());
    });
    google.maps.event.addListener(map, 'rightclick', function (ev) {
        qtWidget.mapIsRightClicked(ev.latLng.lat(), ev.latLng.lng());
    });
    google.maps.event.addListener(map, 'dblclick', function (ev) {
        qtWidget.mapIsDoubleClicked(ev.latLng.lat(), ev.latLng.lng());
    });
}

 map.data.setStyle(function(feature) {
    var strokeColor = feature.getProperty('color');
    var dist = feature.getProperty('distance');
    dist = parseFloat(dist).toFixed(2);
    coordInfoWindow.setContent(Mtext + "<br>Distância: "+ dist + "m");    
    feature.getGeometry().forEachLatLng(function(latlng){
        coordInfoWindow.setPosition(latlng);
    });
    coordInfoWindow.open(map);
    return {
      strokeColor: strokeColor,
      strokeWeight: 3
    };
  });

// custom functions
function gmap_addPath(filepath, text) {    
    paths.push(map.data.addGeoJson(filepath));
    Mtext=text;
}

function gmap_clearPaths() {
    for (var i = 0; i < paths.length; i++){
        features=paths[i];
        for (var j = 0; j < features.length; j++)
            map.data.remove(features[j]);
    }
    paths=[];
}

function gmap_setCenter(lat, lng) {
    map.setCenter(new google.maps.LatLng(lat, lng));
}
function gmap_getCenter() {
    return [map.getCenter().lat(), map.getCenter().lng()];
}
function gmap_setZoom(zoom) {
    map.setZoom(zoom);
}
function gmap_addMarker(key, latitude, longitude, parameters) {

    if (key in markers) {
        gmap_deleteMarker(key);
    }
    var coords = new google.maps.LatLng(latitude, longitude);
    parameters['map'] = map
    parameters['position'] = coords;
    var marker = new google.maps.Marker(parameters);
    google.maps.event.addListener(marker, 'dragend', function () {
        qtWidget.markerIsMoved(key, marker.position.lat(), marker.position.lng())
    });
    google.maps.event.addListener(marker, 'click', function () {
        qtWidget.markerIsClicked(key, marker.position.lat(), marker.position.lng())
    });
    google.maps.event.addListener(marker, 'dblclick', function () {
        qtWidget.markerIsDoubleClicked(key, marker.position.lat(), marker.position.lng())
    });
    google.maps.event.addListener(marker, 'rightclick', function () {
        qtWidget.markerIsRightClicked(key, marker.position.lat(), marker.position.lng())
    });
    markers[key] = marker;
    return key;
}
function gmap_moveMarker(key, latitude, longitude) {
    var coords = new google.maps.LatLng(latitude, longitude);
    markers[key].setPosition(coords);
}
function gmap_deleteMarker(key) {
    markers[key].setMap(null);
    delete markers[key]
}
function gmap_changeMarker(key, extras) {
    if (!(key in markers)) {
        return
    }
    markers[key].setOptions(extras);
}

'''

HTML = '''
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="initial-scale=1.0, user-scalable=no"/>
    <style type="text/css">
        html {
            height: 100%;
        }
        body {
            height: 100%;
            margin: 0;
            padding: 0
        }
        #map_canvas {
            height: 100%
        }
    </style>
    <script type="text/javascript" src="qrc:///qtwebchannel/qwebchannel.js"></script>
    <script async defer
            src="https://maps.googleapis.com/maps/api/js?key=API_KEY"
            type="text/javascript"></script>
    <script>
    '''

HTML2 = '''
    </script>
   
</head>
<body onload="initialize()">
<div id="map_canvas" style="width:100%; height:100%"></div>
</body>
</html>
'''
HTML=HTML+JS+HTML2


class GeoCoder(QtNetwork.QNetworkAccessManager):
    class NotFoundError(Exception):
        pass

    def geocode(self, location, api_key):
        url = QtCore.QUrl("https://maps.googleapis.com/maps/api/geocode/xml")
        query = QtCore.QUrlQuery()
        query.addQueryItem("key", api_key)
        query.addQueryItem("address", location)
        url.setQuery(query)
        request = QtNetwork.QNetworkRequest(url)
        reply = self.get(request)
        loop = QtCore.QEventLoop()
        reply.finished.connect(loop.quit)
        loop.exec_()
        reply.deleteLater()
        self.deleteLater()
        return self._parseResult(reply)

    def _parseResult(self, reply):
        xml = reply.readAll()
        reader = QtCore.QXmlStreamReader(xml)
        while not reader.atEnd():
            reader.readNext()
            if reader.name() != "geometry": continue
            reader.readNextStartElement()
            if reader.name() != "location": continue
            reader.readNextStartElement()
            if reader.name() != "lat": continue
            latitude = float(reader.readElementText())
            reader.readNextStartElement()
            if reader.name() != "lng": continue
            longitude = float(reader.readElementText())
            return latitude, longitude
        raise GeoCoder.NotFoundError

    def geoFind(self,location):
        try:
            return self.geocode(location)
        except GeoCoder.NotFoundError:
            return [False, False]




class QGoogleMap(QtWebEngineWidgets.QWebEngineView):

    mapMoved = QtCore.pyqtSignal(float, float)
    mapClicked = QtCore.pyqtSignal(float, float)
    mapRightClicked = QtCore.pyqtSignal(float, float)
    mapDoubleClicked = QtCore.pyqtSignal(float, float)

    markerMoved = QtCore.pyqtSignal(str, float, float)
    markerClicked = QtCore.pyqtSignal(str, float, float)
    markerDoubleClicked = QtCore.pyqtSignal(str, float, float)
    markerRightClicked = QtCore.pyqtSignal(str, float, float)

    closed = QtCore.pyqtSignal()

    def __init__(self, api_key=API_KEY, parent=None, lat=None, lng=None):
        super(QGoogleMap, self).__init__(parent)
        self._api_key = api_key
        channel = QtWebChannel.QWebChannel(self)
        self.page().setWebChannel(channel)
        channel.registerObject("qGoogleMap", self)
        self.lat=lat
        self.lng=lng

        html = HTML.replace("API_KEY", api_key)
        self.setHtml(html)
        self.loadFinished.connect(self.on_loadFinished)
        self.initialized = False

        self._manager = QtNetwork.QNetworkAccessManager(self)
    
    def closeEvent(self, CloseEvent):
        self.closed.emit()
        return super().closeEvent(CloseEvent)

    def saveImage(self, filepath):
        p = QtGui.QGuiApplication.primaryScreen()
        p.grabWindow(self.winId()).save(filepath, 'jpg')

    def show(self):
        self.waitUntilReady()
        self.setZoom(16)       
        lat=self.lat
        lng=self.lng
        if lat is None and lng is None:
            lng, lat = -46.30973, -19.00009 
        self.centerAt(lat, lng)

        self.addMarker("Centro", lat, lng, **dict(
            icon="http://maps.gstatic.com/mapfiles/ridefinder-images/mm_20_red.png",
            draggable=True,
            title="Centro"
        ))

#        for place in ["Plaza Ramon Castilla", "Plaza San Martin", ]:
#            self.addMarkerAtAddress(place, icon="http://maps.gstatic.com/mapfiles/ridefinder-images/mm_20_gray.png")

    #    self.mapMoved.connect(print)
    #    self.mapClicked.connect(print)
    #    self.mapRightClicked.connect(print)
    #    self.mapDoubleClicked.connect(print)
        self.markerMoved.connect(print)

        return super().show()

    @QtCore.pyqtSlot()
    def on_loadFinished(self):
        self.initialized = True
        self.page().runJavaScript(JS)

    def waitUntilReady(self):
        if not self.initialized:
            loop = QtCore.QEventLoop()
            self.loadFinished.connect(loop.quit)
            loop.exec_()

    def geocode(self, location):
        return GeoCoder(self).geocode(location, self._api_key)


    def centerAtAddress(self, location):
        try:
            latitude, longitude = self.geocode(location)
        except GeoCoder.NotFoundError:
            print("Not found {}".format(location))
            return None, None
        self.centerAt(latitude, longitude)
        return latitude, longitude

    def addMarkerAtAddress(self, location, **extra):
        if 'title' not in extra:
            extra['title'] = location
        try:
            latitude, longitude = self.geocode(location)
        except GeoCoder.NotFoundError:
            return None
        return self.addMarker(location, latitude, longitude, **extra)
    
    @QtCore.pyqtSlot(float, float)
    def mapIsMoved(self, lat, lng):
        self.mapMoved.emit(lat, lng)

    @QtCore.pyqtSlot(float, float)
    def mapIsClicked(self, lat, lng):
        self.mapClicked.emit(lat, lng)

    @QtCore.pyqtSlot(float, float)
    def mapIsRightClicked(self, lat, lng):
        self.mapRightClicked.emit(lat, lng)

    @QtCore.pyqtSlot(float, float)
    def mapIsDoubleClicked(self, lat, lng):
        self.mapDoubleClicked.emit(lat, lng)

    # markers
    @QtCore.pyqtSlot(str, float, float)
    def markerIsMoved(self, key, lat, lng):
        self.markerMoved.emit(key, lat, lng)

    @QtCore.pyqtSlot(str, float, float)
    def markerIsClicked(self, key, lat, lng):
        self.markerClicked.emit(key, lat, lng)

    @QtCore.pyqtSlot(str, float, float)
    def markerIsRightClicked(self, key, lat, lng):
        self.markerRightClicked.emit(key, lat, lng)

    @QtCore.pyqtSlot(str, float, float)
    def markerIsDoubleClicked(self, key, lat, lng):
        self.markerDoubleClicked.emit(key, lat, lng)

    def runScript(self, script, callback=None):
        if callback is None:
            self.page().runJavaScript(script)
        else:
            self.page().runJavaScript(script, callback)

    def centerAt(self, latitude, longitude):
        self.runScript("gmap_setCenter({},{})".format(latitude, longitude))

    def addPath(self, filepath, text=""):
      #  print(filepath)
        self.runScript('gmap_addPath({},"{}")'.format(filepath, text))
    
    def clearPaths(self):
        self.runScript("gmap_clearPaths()")

    def center(self):
        self._center = {}
        loop = QtCore.QEventLoop()

        def callback(*args):
            self._center = tuple(args[0])
            loop.quit()

        self.runScript("gmap_getCenter()", callback)
        loop.exec_()
        return self._center

    def setZoom(self, zoom):
        self.runScript("gmap_setZoom({})".format(zoom))

    def addMarker(self, key, latitude, longitude, **extra):
        return self.runScript(
            "gmap_addMarker("
            "key={!r}, "
            "latitude={}, "
            "longitude={}, "
            "{}"
            "); ".format(key, latitude, longitude, json.dumps(extra)))

    def moveMarker(self, key, latitude, longitude):
        return self.runScript(
            "gmap_moveMarker({!r}, {}, {});".format(key, latitude, longitude))

    def setMarkerOptions(self, keys, **extra):
        return self.runScript(
            "gmap_changeMarker("
            "key={!r}, "
            "{}"
            "); "
                .format(keys, json.dumps(extra)))

    def deleteMarker(self, key):
        return self.runScript(
            "gmap_deleteMarker("
            "key={!r} "
            "); ".format(key))
ptAg=[0,0]
ptBg=[0,0]
net=0
count=0
def basicWin(ptA, ptB, filepath):
    from lib.osmNet import netHandler
    import tempfile   
    global ptAg
    ptAg=[ptA[1],ptA[0]]
    global ptBg
    ptBg=[ptB[1],ptB[0]]

    f=tempfile.gettempdir()
    w = QGoogleMap(api_key=API_KEY)
    w.show()
    w.resize(900, 720)
    w.waitUntilReady()
    w.setZoom(16)
    w.centerAt(ptA[0], ptA[1])
    

    w.addMarker("Aluno", ptA[0], ptA[1], **dict(
        icon="http://maps.gstatic.com/mapfiles/ridefinder-images/mm_20_green.png",
        draggable=True,
        title="Aluno"
    ))   
    w.addMarker("Escola", ptB[0], ptB[1], **dict(
        icon="http://maps.gstatic.com/mapfiles/ridefinder-images/mm_20_yellow.png",
        draggable=True,
        title="Escola Atribuída"
    ))   
 

    net=netHandler(osmpath=filepath)
    
    def update(n, x, y):
        global count
        global ptAg
        global ptBg
        if n=='Aluno':
            ptAg=[y,x]
        else:
            ptBg=[y,x]
        if ptAg == ptBg:
            return
           
        parts, dist = net.shortest_path(source=net.addNode(ptAg, "aluno"+str(count)), target=net.addNode(ptBg, "escola"+str(count)))
        print("DIST: ", dist)    
        w.clearPaths()       
        count+=1
        with open(net.save_geojson(f+"/temp.geojson"), 'r') as file:
            geo = file.read().replace("\"","\'")    
      #  print(geo)
        w.addPath(geo)
       # net.save_kml("/home/matheus/test.kml")
       # w.saveImage("/home/matheus/test.jpg")
        #return ptAg, ptBg

    w.mapMoved.connect(print)
    w.mapClicked.connect(print)
    w.mapRightClicked.connect(print)
    w.mapDoubleClicked.connect(print)
    w.markerMoved.connect(lambda n,x,y: update(n,x,y))
    w.markerClicked.connect(lambda n,x,y: update(n,x,y) if n!="Aluno" else lambda: 0)
    update("Aluno", ptA[0], ptA[1])
    return w,net

 
def test():
    global ptAg, ptBg, net
    import sys
    lng, lat = -46.30973, -19.00009 
    filepath='/home/matheus/map.osm'
    app = QtWidgets.QApplication(sys.argv)
    ptB=[lat, lng]
    ptA=[lat, lng]  
    basicWin(ptA, ptB, filepath)
    app.exec_()         

if __name__ == '__main__':
    test()