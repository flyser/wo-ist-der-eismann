#!/bin/sh

cd "$(dirname "$0")"

curl -s "http://www.openlayers.org/api/2.9.1/OpenLayers.js"        > ./contents/html/OpenLayers.js.new
diff -u ./contents/html/OpenLayers.js ./contents/html/OpenLayers.js.new
mv ./contents/html/OpenLayers.js.new ./contents/html/OpenLayers.js

curl -s "http://www.openstreetmap.org/openlayers/OpenStreetMap.js" > ./contents/html/OpenStreetMap.js.new
diff -u ./contents/html/OpenStreetMap.js ./contents/html/OpenStreetMap.js.new
mv ./contents/html/OpenStreetMap.js.new ./contents/html/OpenStreetMap.js

curl -s "http://www.openstreetmap.org/openlayers/img/marker.png"   > ./contents/html/marker.png.new
diff -u ./contents/html/marker.png ./contents/html/marker.png.new
mv ./contents/html/marker.png.new ./contents/html/marker.png
