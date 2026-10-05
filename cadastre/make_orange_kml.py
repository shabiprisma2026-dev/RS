"""Digitise the orange (yellow-drawn) strip from the cadastre.mimt.gov.ir screenshot
and write it as KML.

v2 georeferencing: both screenshots were matched against Sentinel-2 (2024-08-15,
tile 40SEC) by masked normalised cross-correlation (prospect/match_screenshot.py).
The two independent fits agree within ~50 m; CENTRE_UTM is their mean.
Strip width 42 m is the end width the site's measure tool reported.
(v1 used the Lng/Lat box + 2.05 km perimeter; it put the NE end within ~15 m but
made the strip ~165 m too long at the SW end.)
"""
from pyproj import Transformer
from shapely.geometry import LineString

WIDTH_M = 42.0
ANCHOR_LL = (57.318081, 33.613867)    # Lng/Lat box shown by the site (mouse position)
# centreline of the strip in UTM 40N: SW end -> bend -> NE end
CENTRE_UTM = [(529321, 3719337), (529697, 3719595), (529852, 3719923)]

to_utm = Transformer.from_crs(4326, 32640, always_xy=True)
to_ll = Transformer.from_crs(32640, 4326, always_xy=True)

centre = LineString(CENTRE_UTM)
strip = centre.buffer(WIDTH_M / 2, cap_style=2, join_style=2)
ring = [to_ll.transform(x, y) for x, y in strip.exterior.coords]
line = [to_ll.transform(x, y) for x, y in centre.coords]

print(f"length {centre.length:.0f} m | perimeter {strip.length:.0f} m | area {strip.area/1e4:.2f} ha")
for i, (lon, lat) in enumerate(ring[:-1], 1):
    x, y = to_utm.transform(lon, lat)
    print(f"P{i}: {lon:.6f}, {lat:.6f}  | UTM40N E {x:.1f} N {y:.1f}")

fmt = lambda pts: " ".join(f"{lon:.7f},{lat:.7f},0" for lon, lat in pts)
kml = f"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2"><Document><name>Orange area (v2, Sentinel-2 matched)</name>
<Style id="orange"><LineStyle><color>ff0080ff</color><width>2</width></LineStyle><PolyStyle><color>800080ff</color></PolyStyle></Style>
<Placemark><name>Orange area</name><description>Digitised from cadastre screenshots, georeferenced by matching to Sentinel-2 (~50 m); perimeter {strip.length:.0f} m, area {strip.area/1e4:.2f} ha. Check against the cadastre map before use.</description>
<styleUrl>#orange</styleUrl><Polygon><outerBoundaryIs><LinearRing><coordinates>{fmt(ring)}</coordinates></LinearRing></outerBoundaryIs></Polygon></Placemark>
<Placemark><name>Centreline</name><styleUrl>#orange</styleUrl><LineString><coordinates>{fmt(line)}</coordinates></LineString></Placemark>
<Placemark><name>Anchor (Lng/Lat from site)</name><Point><coordinates>{ANCHOR_LL[0]},{ANCHOR_LL[1]},0</coordinates></Point></Placemark>
</Document></kml>
"""
open(__file__.replace("make_orange_kml.py", "orange_area.kml"), "w", encoding="utf-8").write(kml)
