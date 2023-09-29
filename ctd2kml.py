import sys, csv
#
# KML template strings
#
KML_TEMPLATE_HEADER = \
"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2"
     xmlns:gx="http://www.google.com/kml/ext/2.2"
     xmlns:kml="http://www.opengis.net/kml/2.2"
     xmlns:atom="http://www.w3.org/2005/Atom">
 <Document>
  <name>%s</name>
  <Style id="normPointStyle">
   <IconStyle>
    <scale>1.0</scale>
    <color>ff0000ff</color>
    <Icon>
     <href>http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png</href>
    </Icon>
   </IconStyle>
   <LineStyle>
    <color>ffffffff</color>
    <width>10.0</width>
   </LineStyle>
   <LabelStyle>
    <scale>0.5</scale>
   </LabelStyle>
  </Style>

  <Style id="highlightPointStyle">
   <IconStyle>
    <scale>0.5</scale>
    <Icon>
     <href>http://maps.google.com/mapfiles/kml/shapes/placemark_circle_highlight.png</href>
    </Icon>
   </IconStyle>
   <LineStyle>
    <color>ffffffff</color>
    <width>10.0</width>
   </LineStyle>
   <LabelStyle>
    <scale>0.5</scale>
   </LabelStyle>
  </Style>

  <Style id="lineStyle">
   <LineStyle>
    <color>ffffffff</color>
    <width>10.0</width>
   </LineStyle>
  </Style>

  <StyleMap id="pointStyleMap">
   <Pair>
    <key>normal</key>
    <styleUrl>#normPointStyle</styleUrl>
   </Pair>
  <Pair>
   <key>highlight</key>
   <styleUrl>#highlightPointStyle</styleUrl>
  </Pair>
 </StyleMap>

"""

KML_TEMPLATE_TAIL = \
""" </Document>
</kml>"""


KML_POINT_TEMPLATE = \
""" <Placemark>
  <name>%s</name>
  <styleUrl>#normPointStyle</styleUrl>
  <Point>
   <coordinates>%s</coordinates>
  </Point>
 </Placemark>
"""

KML_FLAGGED_POINT_TEMPLATE = \
""" <Placemark>
  <name>%s</name>
  <styleUrl>#highlightPointStyle</styleUrl>
%s
  <Point>
   <coordinates>%s</coordinates>
  </Point>
 </Placemark>
"""

KML_LINESTRING_TEMPLATE = \
""" <Placemark>
  <name>%s</name>
  <Snippet maxLines="0"></Snippet>
  <styleUrl>#lineStyle</styleUrl>
  <LineString>
   <altitudeMode>clampToGround</altitudeMode>
   <tessellate>0</tessellate>
   <extrude>0</extrude>
   <coordinates>
%s
   </coordinates>
  </LineString>
 </Placemark>
"""

print KML_TEMPLATE_HEADER%sys.argv[1]

fp = open(sys.argv[1],'r')
dialect = csv.Sniffer().sniff(fp.readline())
fp.seek(0)
reader = csv.reader(fp, dialect)
headers = [x.strip() for x in reader.next()]
for line in reader:
   vals = [x.strip() for x in line]
   rowData = dict(zip(headers,vals))
   dtg = '%s %s'%(rowData['DateUTC'], rowData['TimeUTC'])
   lat = float(rowData['Latitude'])
   lon = float(rowData['Longitude'])
   print KML_POINT_TEMPLATE%(dtg, '%.4f,%.4f,0.0'%(lon,lat))

print KML_TEMPLATE_TAIL
