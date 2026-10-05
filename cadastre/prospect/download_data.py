"""Download the inputs used by match_screenshot.py / spectral_indices.py.

Sentinel-2 L2A COGs (AWS open data, no login) and Copernicus DEM GLO-30.
Outputs: s2/big.npz (24x24 km window, UTM 40N, origin E 517506 N 3731389), dem.npy, dem_tr.txt.
The scripts also expect the two cadastre screenshots at ../screenshots/ (run all scripts from cadastre/prospect/).
"""
import os, numpy as np, rasterio
from rasterio.windows import from_bounds
os.environ["AWS_NO_SIGN_REQUEST"] = "YES"
os.makedirs("s2", exist_ok=True)
S2 = "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/40/S/EC/2024/8/S2A_40SEC_20240815_0_L2A/"
cx, cy, h = 529506, 3719389, 12000
out = {}
for b in ["B02", "B03", "B04", "B08", "B11", "B12", "B8A", "SCL"]:
    with rasterio.open(S2 + b + ".tif") as s:
        out[b] = s.read(1, window=from_bounds(cx - h, cy - h, cx + h, cy + h, s.transform))
np.savez("s2/big.npz", **out)
DEM = "https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_N33_00_E057_00_DEM/Copernicus_DSM_COG_10_N33_00_E057_00_DEM.tif"
with rasterio.open(DEM) as s:
    w = from_bounds(57.27, 33.575, 57.37, 33.655, s.transform)
    np.save("dem.npy", s.read(1, window=w)); open("dem_tr.txt", "w").write(repr(tuple(s.window_transform(w))[:6]))
