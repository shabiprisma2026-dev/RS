"""Digitise the orange (yellow-drawn) strip from the cadastre.mimt.gov.ir screenshot
and write it as KML.

Georeferencing is approximate (no corner coordinates were available):
  * anchor : the red marker on the strip, pixel (612.5, 511) in screenshot 2,
             assumed to be the point shown in the Lng/Lat box (57.318081, 33.613867)
  * scale  : set so the strip perimeter equals the 2.05 km the site's measure tool reported
             for this shape (screenshot 1), with the 42 m end width it reported
  * north-up map, Web-Mercator display (shape preserved locally)
"""
from pyproj import Transformer
from shapely.geometry import LineString

ANCHOR_PX = (612.5, 511.0)
ANCHOR_LL = (57.318081, 33.613867)
PERIM_M, WIDTH_M = 2050.0, 42.0
# centreline of the yellow strip in screenshot 2 (pixels): SW end -> bend -> NE end
CENTRE_PX = [(557.5, 541.0), (636.0, 484.5), (667.5, 418.0)]

px_len = LineString(CENTRE_PX).length
scale = ((PERIM_M - 2 * WIDTH_M) / 2) / px_len          # metres per screenshot pixel

to_utm = Transformer.from_crs(4326, 32640, always_xy=True)
to_ll = Transformer.from_crs(32640, 4326, always_xy=True)
ae, an = to_utm.transform(*ANCHOR_LL)
utm = lambda x, y: (ae + (x - ANCHOR_PX[0]) * scale, an - (y - ANCHOR_PX[1]) * scale)

centre = LineString([utm(*p) for p in CENTRE_PX])
strip = centre.buffer(WIDTH_M / 2, cap_style=2, join_style=2)
ring = [to_ll.transform(x, y) for x, y in strip.exterior.coords]
line = [to_ll.transform(x, y) for x, y in centre.coords]

print(f"scale {scale:.2f} m/px | length {centre.length:.0f} m | perimeter {strip.length:.0f} m | area {strip.area/1e4:.2f} ha")
for i, (lon, lat) in enumerate(ring[:-1], 1):
    x, y = to_utm.transform(lon, lat)
    print(f"P{i}: {lon:.6f}, {lat:.6f}  | UTM40N E {x:.1f} N {y:.1f}")

fmt = lambda pts: " ".join(f"{lon:.7f},{lat:.7f},0" for lon, lat in pts)
kml = f"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2"><Document><name>Orange area (approx.)</name>
<Style id="orange"><LineStyle><color>ff0080ff</color><width>2</width></LineStyle><PolyStyle><color>800080ff</color></PolyStyle></Style>
<Placemark><name>Orange area</name><description>Approximate digitisation from cadastre screenshot; perimeter {strip.length:.0f} m, area {strip.area/1e4:.2f} ha. Check against the cadastre map before use.</description>
<styleUrl>#orange</styleUrl><Polygon><outerBoundaryIs><LinearRing><coordinates>{fmt(ring)}</coordinates></LinearRing></outerBoundaryIs></Polygon></Placemark>
<Placemark><name>Centreline</name><styleUrl>#orange</styleUrl><LineString><coordinates>{fmt(line)}</coordinates></LineString></Placemark>
<Placemark><name>Anchor (Lng/Lat from site)</name><Point><coordinates>{ANCHOR_LL[0]},{ANCHOR_LL[1]},0</coordinates></Point></Placemark>
</Document></kml>
"""
open(__file__.replace("make_orange_kml.py", "orange_area.kml"), "w", encoding="utf-8").write(kml)
