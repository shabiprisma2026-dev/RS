import numpy as np, cv2
from PIL import Image
from shapely.geometry import LineString, Point
s=np.load("s2/big.npz"); X0,Y0=517506,3731389
f=lambda b: s[b].astype(np.float32)/10000
up=lambda a: cv2.resize(a,(2400,2400),interpolation=cv2.INTER_NEAREST)
B2,B3,B4,B8=f("B02"),f("B03"),f("B04"),f("B08")
B11,B12,B8A=up(f("B11")),up(f("B12")),up(f("B8A"))
scl=up(s["SCL"].astype(np.float32))
eps=1e-4
idx={
 "ferric_B4/B2":B4/(B2+eps),
 "gossan_B11/B4":B11/(B4+eps),
 "ferrous_(B12/B8A+B3/B4)":B12/(B8A+eps)+B3/(B4+eps),
 "OH_clay_B11/B12":B11/(B12+eps),
 "NDVI":(B8-B4)/(B8+B4+eps),
 "albedo":(B2+B3+B4)/3,
}
# refined centreline (mean of both screenshot fits)
cl=LineString([(529321,3719337),(529697,3719595),(529852,3719923)])
strip=cl.buffer(21,cap_style=2,join_style=2)
yy,xx=np.mgrid[0:2400,0:2400]; E=X0+10*xx+5; N=Y0-10*yy-5
def mask(geom):
    from shapely import contains_xy
    return contains_xy(geom,E,N)
m_strip=mask(strip); m_b500=mask(cl.buffer(500))&~m_strip
from shapely.geometry import box
loc=box(529506-4000,3719389-4000,529506+4000,3719389+4000)
m_loc=mask(loc)
valid=(scl!=8)&(scl!=9)&(scl!=3)
print("pixels strip",m_strip.sum(),"buf",m_b500.sum())
rows=[]
for k,v in idx.items():
    ref=v[m_loc&valid]
    def pr(m):
        vals=v[m&valid]; med=np.median(vals)
        return med,(ref<med).mean()*100, (vals>np.percentile(ref,95)).mean()*100
    a=pr(m_strip); b=pr(m_b500)
    rows.append((k,a,b)); print(f"{k:28s} strip med {a[0]:.3f} pct {a[1]:5.1f} >p95 {a[2]:5.1f}% | buf500 med {b[0]:.3f} pct {b[1]:5.1f} >p95 {b[2]:5.1f}%")
np.savez("idx.npz",**{k.split('_')[0]:v for k,v in idx.items()})
# maps
def st(a,lo=2,hi=98):
    p1,p2=np.percentile(a[m_loc],[lo,hi]); return np.clip((a-p1)/(p2-p1)*255,0,255).astype(np.uint8)
r0,c0=int((Y0-3719600)/10),int((529600-X0)/10); H=200
sl=(slice(r0-H,r0+H),slice(c0-H,c0+H))
outline=np.zeros((2400,2400),np.uint8)
pts=np.array([[(x-X0)/10,(Y0-y)/10] for x,y in strip.exterior.coords],np.int32)
cv2.polylines(outline,[pts],True,255,1)
def save(img,name):
    img=img.copy()
    if img.ndim==2: img=np.dstack([img]*3)
    img[outline>0]=(255,255,0)
    Image.fromarray(img[sl]).resize((800,800),Image.NEAREST).save(name)
save(np.dstack([st(B4),st(B3),st(B2)]),"m_truecolor.png")
save(np.dstack([st(B12),st(B11),st(B2)]),"m_swir_12_11_2.png")
save(np.dstack([st(idx["gossan_B11/B4"]),st(idx["OH_clay_B11/B12"]),st(idx["ferric_B4/B2"])]),"m_ratio_RGB.png")
for k in ["ferric_B4/B2","OH_clay_B11/B12","ferrous_(B12/B8A+B3/B4)"]:
    v=st(idx[k]); col=cv2.applyColorMap(v,cv2.COLORMAP_JET)[...,::-1]; save(col,"m_"+k.split('_')[0]+".png")
