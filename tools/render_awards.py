"""Render original arcade award movies: python tools/render_awards.py [NAME ...]."""
import math
import random
import sys
from functools import lru_cache
from pathlib import Path
import av
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from award_catalog import AWARD_THEMES
OUTPUT = ROOT / 'media' / 'awards'
W, H, FPS, SECONDS = 960, 540, 24, 3.6

@lru_cache(maxsize=32)
def font(size):
    for path in ('/System/Library/Fonts/Supplemental/Arial Bold.ttf',
                 'C:/Windows/Fonts/arialbd.ttf',
                 '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'):
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default(size=size)

def cube(d, x, y, size, accent, alpha, angle):
    pts = [(x+math.cos(angle+i*math.pi/2)*size, y+math.sin(angle+i*math.pi/2)*size) for i in range(4)]
    d.polygon(pts, fill=(*accent, alpha), outline=(255,255,255,alpha))
    dx, dy = size*.6, -size*.7
    d.polygon([pts[0], pts[1], (pts[1][0]+dx,pts[1][1]+dy), (pts[0][0]+dx,pts[0][1]+dy)],
              fill=(*accent, max(0,alpha//2)))

def scene(d, theme, accent, t, seed, count=9):
    cx, cy = W/2, H/2
    if theme in ('grid', 'cubes', 'tower', 'maximum', 'checkout'):
        for col in range(15):
            for row in range(7):
                x, y = col*70-30, row*88-35
                pulse = .5+.5*math.sin(col*.8+row*.7-t*3)
                alpha = int(12+35*pulse)
                if theme in ('tower', 'maximum'):
                    alpha = int(alpha*(.5+row*.2))
                d.rectangle((x, y, x+65, y+82), fill=(*accent,alpha), outline=(*accent,50))
        if theme == 'grid':
            scan = (t*170) % H
            d.rectangle((0,scan-15,W,scan+15), fill=(*accent,80))
            d.line((0,scan,W,scan),fill=(*accent,220),width=2)
        elif theme == 'checkout':
            for j in range(4):
                x = ((t*280+j*270) % (W+400))-200
                d.polygon([(x,0),(x+80,0),(x-180,H),(x-260,H)],fill=(*accent,80))
        else:
            for j,(x,y,rate,size) in enumerate(seed[:28]):
                yy = (y+t*rate*.8) % (H+100)-50
                cube(d, x, yy, size*9+4, accent, 90, t*.8+j)
    elif theme in ('bull', 'crown'):
        for j in range(5):
            radius = 70+j*42+9*math.sin(t*3+j)
            box = (cx-radius,cy-radius,cx+radius,cy+radius)
            d.arc(box, start=t*50+j*60, end=t*50+j*60+290, fill=(*accent,90),width=5 if j%2 else 2)
        for impact in (.25,.65,1.05):
            age=t-impact
            if 0 <= age < .9:
                radius = 10+age*340
                d.ellipse((cx-radius,cy-radius,cx+radius,cy+radius),outline=(*accent,int(240*(1-age/.9))),width=5)
        if theme == 'crown':
            d.polygon([(cx-58,cy-120),(cx-70,cy-170),(cx-30,cy-148),(cx,cy-188),
                       (cx+30,cy-148),(cx+70,cy-170),(cx+58,cy-120)],fill=(*accent,210))
    elif theme == 'lanes':
        for j in range(3):
            x = W*(j+1)/4
            d.polygon([(x-90,0),(x+30,0),(x+150,H),(x+30,H)],fill=(*accent,35+j*10))
            d.line((x,0,x+120,H),fill=(*accent,100),width=3)
            age = max(0, t-(.25+j*.35))
            y = min(H*.74, -100+age*650)
            d.ellipse((x+40-15,y-15,x+40+15,y+15),fill=(*accent,230))
            d.line((x+40,y-150,x+40,y),fill=(*accent,130),width=3)
    elif theme == 'tunnel':
        for j in range(11):
            depth = ((j/11+t*.19) % 1)**2
            rx,ry = 30+depth*W*.8, 20+depth*H*.8
            alpha=int(30+depth*170)
            d.rectangle((cx-rx,cy-ry,cx+rx,cy+ry),outline=(*accent,alpha),width=2+int(depth*5))
        for j in range(18):
            a=j*math.tau/18+t*.1
            radius=70+((t*190+j*65)%500)
            x,y=cx+math.cos(a)*radius,cy+math.sin(a)*radius*.65
            cube(d,x,y,8+(j%3)*5,accent,130,t+j)
    elif theme == 'horse':
        # A geometric, original galloping horse silhouette, with speed trails.
        shift = math.sin(t*3)*15
        x,y = cx-60+shift,cy-105
        pts=[(-80,10),(-32,-12),(15,-5),(38,-38),(35,-72),(65,-93),(88,-85),
             (98,-47),(70,-35),(58,5),(60,28),(30,50),(-45,48),(-78,35)]
        d.polygon([(x+a*1.5,y+b*1.5) for a,b in pts],fill=(*accent,160))
        for j in range(4):
            swing=math.sin(t*9+j*1.7)*28
            hx=x-65+j*38
            d.line((hx,y+52,hx+swing,y+102,hx+swing+25,y+125),fill=(*accent,190),width=10)
        for j in range(14):
            yy=60+j*30
            xx=(t*500+j*70) % (W+250)-250
            d.line((xx,yy,xx+120,yy),fill=(*accent,90),width=2)
    elif theme == 'count':
        for j in range(9):
            x,y=cx+(j%3-1)*84,cy+(j//3-1)*84
            lit = j < min(count,int(t*4))
            d.rectangle((x-34,y-34,x+34,y+34),fill=(*accent,60 if lit else 10),outline=(*accent,140 if lit else 35),width=2)
        radius=220
        d.arc((cx-radius,cy-radius,cx+radius,cy+radius),start=-90,end=-90+min(360,t/1.2*360),fill=(*accent,100),width=6)

def render(name, definition):
    filename, accent, theme, title, subtitle = definition
    rng=random.Random(19)
    particles=[(rng.random()*W,rng.random()*H,rng.uniform(20,100),rng.uniform(1,3)) for _ in range(55)]
    background=Image.new('RGB',(W,H))
    pixels=background.load()
    for y in range(H):
        for x in range(W):
            g=max(0,1-math.hypot((x-W/2)/(W*.7),(y-H/2)/(H*.8)))**2
            pixels[x,y]=(int(6+accent[0]*g*.16),int(8+accent[1]*g*.16),int(18+accent[2]*g*.16))
    OUTPUT.mkdir(parents=True,exist_ok=True)
    with av.open(str(OUTPUT/f'{filename}.mp4'),'w') as container:
        stream=container.add_stream('libx264',rate=FPS)
        stream.width,stream.height,stream.pix_fmt=W,H,'yuv420p'
        stream.options={'crf':'21','preset':'fast'}
        for index in range(round(SECONDS*FPS)):
            t=index/FPS
            layer=Image.new('RGBA',(W,H))
            d=ImageDraw.Draw(layer)
            scene(d,theme,accent,t,particles,int(name[0]) if theme=='count' else 9)
            for x,y,speed,radius in particles:
                px=(x+t*speed)%W
                d.line((px-16,y,px,y),fill=(*accent,70),width=max(1,int(radius)))
            appear=max(0,min(1,(t-.75)/.4))
            fade=min(1,(SECONDS-t)/.3)
            alpha=int(255*appear*fade)
            d.text((48,30),'D / M    /    AWARD',font=font(14),fill=(*accent,200))
            d.text((W-48,H-36),'DARTS MASTER',anchor='ra',font=font(12),fill=(180,192,208,220))
            if theme in ('count','maximum'):
                hero=title.split()[0] if theme=='count' else '180'
                d.text((W/2,H/2-15+(1-appear)*30),hero,anchor='mm',font=font(180 if theme=='count' else 160),
                       fill=(255,255,255,alpha),stroke_width=2)
                d.text((W/2,H/2+92),title,anchor='mm',font=font(25),fill=(*accent,alpha))
                sub_y=H/2+135
            else:
                size=86 if len(title)<12 else 62 if len(title)<17 else 48
                offset=(1-appear)*36
                d.text((W/2,H/2+offset),title,anchor='mm',font=font(size),fill=(255,255,255,alpha),stroke_width=1)
                sub_y=H/2+63
            if appear:
                half=90+240*appear
                d.line((W/2-half,sub_y-25,W/2+half,sub_y-25),fill=(*accent,alpha),width=3)
                d.text((W/2,sub_y),subtitle,anchor='mm',font=font(16),fill=(*accent,alpha))
            if .92 < t < 1.12:
                flash=int(55*(1-abs(t-1.02)/.1))
                d.rectangle((0,0,W,H),fill=(255,255,255,max(0,flash)))
            glow=layer.filter(ImageFilter.GaussianBlur(8))
            image=Image.alpha_composite(background.convert('RGBA'),glow)
            image=Image.alpha_composite(image,layer).convert('RGB')
            for packet in stream.encode(av.VideoFrame.from_image(image)):
                container.mux(packet)
        for packet in stream.encode(): container.mux(packet)
    print(name,flush=True)

if __name__=='__main__':
    chosen=sys.argv[1:] or list(AWARD_THEMES)
    for name in chosen:
        render(name,AWARD_THEMES[name])
