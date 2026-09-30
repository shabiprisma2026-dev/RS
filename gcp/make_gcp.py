import csv, math, re
import numpy as np
from pyproj import Transformer
from shapely.geometry import Polygon, Point
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

KML = "/root/.claude/uploads/0d6da516-bf02-5788-a7ae-574705c2817c/eddf4ff8-_______________________.kml"
txt = open(KML, encoding="utf-8").read()
coords = re.search(r"<coordinates>(.*?)</coordinates>", txt, re.S).group(1).split()
ll = [tuple(map(float, c.split(",")[:2])) for c in coords]
to_utm = Transformer.from_crs(4326, 32639, always_xy=True)
to_ll = Transformer.from_crs(32639, 4326, always_xy=True)
poly = Polygon([to_utm.transform(x, y) for x, y in ll])
print("area ha", poly.area/1e4, "perimeter km", poly.length/1e3, "bounds", poly.bounds)

INSET = 30      # markers 30 m inside the boundary so the flight covers them
STEP = 380      # target spacing
inner = poly.buffer(-INSET)

cand = []
# boundary-densified candidates (inside the inset ring)
ring = inner.exterior if inner.geom_type == "Polygon" else max(inner.geoms, key=lambda g: g.area).exterior
n = int(ring.length // 120)
for i in range(n):
    p = ring.interpolate(i * ring.length / n); cand.append((p.x, p.y))
# vertices of the inset ring
for x, y in list(ring.coords)[:-1]: cand.append((x, y))
# interior grid
minx, miny, maxx, maxy = poly.bounds
for x in np.arange(minx, maxx, 100):
    for y in np.arange(miny, maxy, 100):
        if inner.contains(Point(x, y)): cand.append((x, y))
cand = np.array(cand)

def fps(cands, n, seed_idx, existing=None):
    chosen = [] if existing is None else list(existing)
    if not chosen:
        chosen = [cands[seed_idx]]
    d = np.min([np.hypot(*(cands - c).T) for c in chosen], axis=0)
    out = []
    while len(out) < n:
        i = int(np.argmax(d)); out.append(cands[i])
        d = np.minimum(d, np.hypot(*(cands - cands[i]).T))
    return chosen[:1] if existing is None else [], out

# GCP: farthest-point sampling starting from the top-left-most candidate
seed = int(np.argmin(cand[:, 0] - cand[:, 1]))
N_GCP, N_CHK = 20, 6
_, rest = fps(cand, N_GCP - 1, seed)
gcp = [cand[seed]] + rest
gcp = np.array(gcp)
# Checkpoints: candidates farthest from any GCP
dmin = np.min([np.hypot(*(cand - g).T) for g in gcp], axis=0)
chk = []
d = dmin.copy()
for _ in range(N_CHK):
    i = int(np.argmax(d)); chk.append(cand[i]); d = np.minimum(d, np.hypot(*(cand - cand[i]).T))
chk = np.array(chk)
# RTK subset: 8 GCPs by farthest-point sampling among GCPs
sub = [gcp[0]]; dd = np.hypot(*(gcp - gcp[0]).T)
for _ in range(7):
    i = int(np.argmax(dd)); sub.append(gcp[i]); dd = np.minimum(dd, np.hypot(*(gcp - gcp[i]).T))
subset = {tuple(np.round(p, 3)) for p in sub}

rows = []
for i, p in enumerate(gcp, 1):
    lon, lat = to_ll.transform(*p)
    rows.append(dict(id=f"GCP{i:02d}", type="GCP", E=round(p[0], 1), N=round(p[1], 1),
                     lon=round(lon, 7), lat=round(lat, 7),
                     RTK_set="yes" if tuple(np.round(p, 3)) in subset else ""))
for i, p in enumerate(chk, 1):
    lon, lat = to_ll.transform(*p)
    rows.append(dict(id=f"CHK{i:02d}", type="Check", E=round(p[0], 1), N=round(p[1], 1),
                     lon=round(lon, 7), lat=round(lat, 7), RTK_set=""))
with open("gcp_points.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

# nearest-neighbour spacing stats
allp = np.array([[r["E"], r["N"]] for r in rows])
nn = [sorted(np.hypot(*(allp - a).T))[1] for a in allp]
print("NN spacing m: min %.0f mean %.0f max %.0f" % (min(nn), np.mean(nn), max(nn)))

# KML
def pm(r):
    color = "ff0000ff" if r["type"] == "GCP" else "ff00ffff"
    return f"""<Placemark><name>{r['id']}</name><description>{r['type']} | UTM39N E {r['E']} N {r['N']}{' | RTK set' if r['RTK_set'] else ''}</description>
<Style><IconStyle><color>{color}</color><scale>0.9</scale><Icon><href>http://maps.google.com/mapfiles/kml/shapes/placemark_square.png</href></Icon></IconStyle></Style>
<Point><coordinates>{r['lon']},{r['lat']},0</coordinates></Point></Placemark>"""
bnd = " ".join(f"{x},{y},0" for x, y in ll)
kml = f"""<?xml version="1.0" encoding="UTF-8"?><kml xmlns="http://www.opengis.net/kml/2.2"><Document><name>GCP layout</name>
<Placemark><name>Boundary</name><Style><LineStyle><color>ffffaa00</color><width>2</width></LineStyle><PolyStyle><fill>0</fill></PolyStyle></Style><Polygon><outerBoundaryIs><LinearRing><coordinates>{bnd}</coordinates></LinearRing></outerBoundaryIs></Polygon></Placemark>
{''.join(pm(r) for r in rows)}</Document></kml>"""
open("gcp_points.kml", "w", encoding="utf-8").write(kml)

# PNG
fig, ax = plt.subplots(figsize=(8, 8))
px, py = poly.exterior.xy; ax.plot(px, py, "-", color="#0a7", lw=2)
for r in rows:
    c = "red" if r["type"] == "GCP" else "gold"
    m = "s" if r["type"] == "GCP" else "^"
    ax.scatter(r["E"], r["N"], c=c, marker=m, s=70, edgecolor="k", zorder=3)
    ax.annotate(r["id"][-2:] if r["type"] == "GCP" else "C" + r["id"][-2:], (r["E"], r["N"]), xytext=(4, 4), textcoords="offset points", fontsize=8)
ax.set_aspect("equal"); ax.grid(alpha=.3)
ax.set_xlabel("E (UTM 39N, m)"); ax.set_ylabel("N (m)")
ax.set_title(f"GCP (red) / Check (yellow) - {poly.area/1e4:.0f} ha")
fig.savefig("gcp_layout.png", dpi=130, bbox_inches="tight")
print(len(gcp), len(chk))
