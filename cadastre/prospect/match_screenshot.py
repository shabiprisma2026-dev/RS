import numpy as np, cv2, sys
from PIL import Image
s=np.load("s2/big.npz")
X0,Y0=517506,3731389
g=((s["B02"].astype(float)+s["B03"]+s["B04"])/3).astype(np.float32)
def prep(img): # high-pass to match texture not albedo
    img=img.astype(np.float32); return img-cv2.GaussianBlur(img,(0,0),8)
gI=prep(g)
res_all=[]
for fn,anchor,top,bot in [("../images/2.webp",(612.5,511),70,885),("../images/1.webp",None,125,940)]:
    im=np.array(Image.open(fn).convert("RGB")).astype(float)
    mapa=im[top:bot,0:1835]; R,G,B=[mapa[...,i] for i in range(3)]
    sat=(np.abs(R-G)<22)&(np.abs(G-B)<28)&(R>70)&(R<235)
    sat=cv2.erode(sat.astype(np.uint8),np.ones((9,9),np.uint8))>0
    gray=mapa.mean(axis=2)
    best=[]
    for sc in np.arange(3.0,7.01,0.1):
        f=sc/10
        gs=cv2.resize(gray,None,fx=f,fy=f,interpolation=cv2.INTER_AREA)
        ms=cv2.resize(sat.astype(np.uint8),None,fx=f,fy=f,interpolation=cv2.INTER_NEAREST).astype(np.float32)
        T=prep(gs)
        r=cv2.matchTemplate(gI,T,cv2.TM_CCOEFF_NORMED,mask=ms)
        r=np.nan_to_num(r,nan=-1,posinf=-1,neginf=-1)
        i=np.unravel_index(r.argmax(),r.shape); best.append((float(r.max()),round(sc,2),i))
    best.sort(reverse=True); print(fn,best[:4])
    mx,sc,(row,col)=best[0]
    np.save(fn.split("/")[-1]+".fit.npy",np.array([sc,row,col,top]))
