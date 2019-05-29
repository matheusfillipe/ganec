var map;

function initialize(){
    map = L.map('map').setView([-19.00009,-46.30973], 15);

    L.tileLayer('http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: 'Map data &copy; <a href="http://openstreetmap.org">OpenStreetMap</a> contributors, <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, Imagery © <a href="http://cloudmade.com">CloudMade</a>',
        maxZoom: 18
    }).addTo(map);

    var marker = L.marker(map.getCenter()).addTo(map);
    marker.bindPopup("Carmo").openPopup();
    new QWebChannel(qt.webChannelTransport, function (channel) {
        window.MainWindow = channel.objects.MainWindow;
        if(typeof MainWindow != 'undefined') {
            var onMapMove = function() { MainWindow.onMapMove(map.getCenter().lat, map.getCenter().lng) };
            map.on('move', onMapMove);
            onMapMove();
        }
    });
}