"""Deterministic local film: Pillow 12.3, NumPy 2.3, FFmpeg 8.0."""
from pathlib import Path
import math, subprocess, wave, json, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parent
W,H,FPS,DURATION = 1920,1080,24,42
WHITE=(231,233,229); MUTED=(141,151,159); GOLD=(204,173,121)
FONTS={}
def font(size,kind='cn'):
    key=(size,kind)
    if key not in FONTS:
        path={'cn':'/System/Library/Fonts/STHeiti Light.ttc','serif':'/System/Library/Fonts/Supplemental/Didot.ttc','en':'/System/Library/Fonts/HelveticaNeue.ttc'}[kind]
        FONTS[key]=ImageFont.truetype(path,size)
    return FONTS[key]
def ease(v):
    v=max(0,min(1,v)); return v*v*(3-2*v)
def text(d,xy,s,size=40,fill=WHITE,kind='cn',anchor='lt'):
    d.text(xy,s,font=font(size,kind),fill=fill,anchor=anchor)
def tracked(d,x,y,s,size=20,spacing=5,fill=MUTED):
    for ch in s:
        text(d,(x,y),ch,size,fill,'en'); x+=d.textlength(ch,font=font(size,'en'))+spacing

RNG=np.random.default_rng(108)
STARS=RNG.random((150,3))
yy,xx=np.mgrid[0:270,0:480]
vign=np.exp(-(((xx-300)/250)**2+((yy-140)/160)**2)*1.4)
base=np.stack([5+vign*8,8+vign*13,13+vign*20],axis=-1).astype(np.uint8)
BASE=Image.fromarray(base).resize((W,H),Image.Resampling.BICUBIC)
ANGLE=np.linspace(0,math.tau,230)

def ring(im,t,cx,cy,r=280,power=1,tilt=.8):
    """Projected metallic ribbons; different depths produce evolving light."""
    d=ImageDraw.Draw(im)
    for k in range(27):
        a=ANGLE
        minor=(k-13)*.006
        rr=r*(1+minor+.022*np.sin(a*3+t*.33+k*.08))
        x=rr*np.cos(a); y=rr*np.sin(a); z=r*.16*np.sin(a*2+t*.3+k*.05)
        spin=t*.14
        X=x*np.cos(spin)+z*np.sin(spin)
        Z=-x*np.sin(spin)+z*np.cos(spin)
        Y=y*np.cos(tilt)-Z*np.sin(tilt)
        Z=y*np.sin(tilt)+Z*np.cos(tilt)
        scale=1/(1+Z/1600)
        pts=np.stack([cx+X*scale,cy+Y*scale],axis=-1)
        for j in range(0,len(a)-1,3):
            light=(.34+.66*max(0,math.cos(a[j]-t*.45+k*.04))**7)*power
            cold=(k<14)
            col=tuple(int(q*light) for q in ((190,213,226) if cold else (223,181,116)))
            d.line([tuple(p) for p in pts[j:j+4]],fill=col,width=2)

SCENES=[(0,6),(6,13),(13,20),(20,27),(27,35),(35,42)]
def frame(t):
    idx=next(i for i,(a,b) in enumerate(SCENES) if a<=t<b)
    a,b=SCENES[idx]; u=t-a
    im=BASE.copy(); d=ImageDraw.Draw(im)
    for x,y,z in STARS:
        px=int(x*W+(t*2*z))%W; py=int(y*H)
        c=int(26+z*32); d.point((px,py),fill=(c,c,c+7))
    text(d,(105,62),'V / Q',23,GOLD,'en')
    tracked(d,180,67,'THE QUALITY SERIES',16,3)
    text(d,(1815,67),f'{idx+1:02d} / 06',18,MUTED,'en','rt')
    d.line((105,975,1815,975),fill=(41,49,55),width=1)
    d.line((105,975,105+1710*t/DURATION,975),fill=GOLD,width=2)
    tracked(d,105,1000,'VIDEO QUALITY LOOP',16,4)
    text(d,(1815,1000),f'00:{int(t):02d}  /  00:42',17,MUTED,'en','rt')
    reveal=ease(u/1.0)
    shift=int(30*(1-reveal))
    if idx==0:
        ring(im,t,1420,525,420,.9,1.02)
        d=ImageDraw.Draw(im)
        tracked(d,130,255,'A FILM ABOUT FINISHING',19,5,GOLD)
        text(d,(123,326+shift),'Every frame.',112,WHITE,'serif')
        text(d,(130,495+shift),'都值得再看一遍。',67)
        text(d,(134,630),'让高标准，进入每一次创作。',28,MUTED)
    elif idx==1:
        ring(im,t,1390,525,300,1,.58)
        d=ImageDraw.Draw(im)
        tracked(d,130,265,'INTRODUCING',19,6,GOLD)
        text(d,(125,335+shift),'VIDEO',118,WHITE,'en')
        text(d,(125,469+shift),'QUALITY LOOP',92,WHITE,'en')
        text(d,(133,626),'一个面向真实成片的质量闭环 Skill',33,MUTED)
        text(d,(133,725),'目标  /  检查  /  修复  /  复验',26,GOLD)
    elif idx==2:
        ring(im,t,1580,560,380,.28,1.15)
        d=ImageDraw.Draw(im)
        tracked(d,130,203,'01  /  DEFINE THE STANDARD',18,4,GOLD)
        text(d,(127,265+shift),'让“高级”，有据可查。',68)
        labels=['叙事与信息','字体与字幕','留白与构图','视觉层级','色彩与光影','运动连续性','剪辑与节奏','微动效细节','声音设计','画幅适配','原创与一致','导出完整性']
        for j,label in enumerate(labels):
            col=j%4; row=j//4; x=132+col*420; y=435+row*138
            on=ease((u-.8-j*.11)/.65)
            if on>0:
                text(d,(x,y),f'{j+1:02d}',18,tuple(int(c*on) for c in GOLD),'en')
                text(d,(x,y+38),label,32,tuple(int(c*on) for c in WHITE))
                d.line((x,y+93,x+325,y+93),fill=(47,55,61),width=1)
    elif idx==3:
        tracked(d,130,200,'02  /  INSPECT THE REAL FILM',18,4,GOLD)
        text(d,(127,265+shift),'回到成片，发现问题。',66)
        # Original inspection illustration, deliberately not a real app recording.
        d.rectangle((140,410,1140,870),outline=(64,75,85),width=1)
        ring(im,t,650,635,220,.8,.7)
        d=ImageDraw.Draw(im)
        scan=160+960*((u*.18)%1)
        d.line((scan,430,scan,850),fill=(174,205,219),width=2)
        text(d,(168,435),'REVIEW / FRAME STUDY',17,MUTED,'en')
        for j,(label,small) in enumerate([('定位到时间码','00:12.08  /  字幕阅读时间'),('只改真正的问题','层级 · 节奏 · 连续性'),('保留每次修复证据','问题 → 修改 → 复验')]):
            y=460+j*132
            text(d,(1230,y),label,31)
            text(d,(1230,y+52),small,22,MUTED)
        text(d,(165,900),'概念演示画面',16,MUTED)
    elif idx==4:
        ring(im,t,960,552,255,1,.3+.1*math.sin(t*.2))
        d=ImageDraw.Draw(im)
        tracked(d,130,190,'03  /  REFINE. RENDER. REPEAT.',18,4,GOLD)
        text(d,(960,288+shift),'把好作品，再推进一步。',62,WHITE,anchor='mt')
        labels=[('制作',960,405),('检查',1380,600),('修复',960,805),('复验',540,600)]
        for j,(label,x,y) in enumerate(labels):
            active=int((u*.6)%4)==j
            text(d,(x,y),label,36,GOLD if active else WHITE,anchor='mm')
        text(d,(960,565),'QUALITY',34,WHITE,'en','mm')
        tracked(d,862,612,'IN MOTION',15,4)
        text(d,(960,900),'逐项检查  ·  定点修复  ·  重新渲染',25,MUTED,anchor='mt')
    else:
        ring(im,t,960,530,405,.52,.8)
        # Dark panel isolates the lockup while allowing the ring to move around it.
        mask=Image.new('L',(W,H),0)
        ImageDraw.Draw(mask).rounded_rectangle((320,357,1600,725),radius=100,fill=225)
        mask=mask.filter(ImageFilter.GaussianBlur(80))
        overlay=Image.new('RGBA',(W,H),(5,9,15,0));overlay.putalpha(mask)
        im=Image.alpha_composite(im.convert('RGBA'),overlay).convert('RGB'); d=ImageDraw.Draw(im)
        tracked(d,718,279,'CRAFT IS A PROCESS',19,6,GOLD)
        text(d,(960,407+shift),'完成之后，再进一步。',76,WHITE,anchor='mt')
        text(d,(960,553),'VIDEO QUALITY LOOP',48,WHITE,'en','mt')
        text(d,(960,646),'从一句要求，到可检查的完成度。',29,MUTED,anchor='mt')
        text(d,(960,810),'$video-quality-loop',28,GOLD,'en','mt')
    # Short, smooth dip between chapters; no white flashes.
    fade=min(ease(u/.65),ease((b-t)/.55))
    if fade<1: im=Image.blend(Image.new('RGB',(W,H),(4,7,11)),im,fade)
    return im

NARRATION=[
 (0.9,'每一帧，都值得再看一遍。'),
 (6.5,'视频质量闭环。让高标准，进入每一次创作。'),
 (13.4,'从叙事到声音，从构图到节奏。让每一个维度，都有据可查。'),
 (20.4,'回到真实成片。定位问题，记录时间码，只改真正需要改变的地方。'),
 (27.6,'制作，检查，修复，复验。把好作品，再推进一步。'),
 (35.5,'完成之后，再进一步。视频质量闭环。')]
def audio():
    sr=48000; n=sr*DURATION; t=np.arange(n)/sr
    sound=np.zeros((n,2),np.float32)
    # Original slow evolving D-minor score. No sampled/licensed music.
    for j,(start,end,notes) in enumerate([(0,13,[73.416,110,146.832,174.614]),(13,27,[65.406,98,130.813,164.814]),(27,42,[73.416,110,146.832,220])]):
        env=np.minimum(np.clip((t-start)/3,0,1),np.clip((end+2-t)/3,0,1))
        for k,f in enumerate(notes):
            signal=(np.sin(2*np.pi*f*t+.3*np.sin(t*.4))+.22*np.sin(2*np.pi*f*2*t))*.023*env
            sound[:,0]+=signal*(.85+k*.03)
            sound[:,1]+=np.roll(signal,int(sr*.005*(k+1)))
    for beat in [0.4,6,13,20,27,35]:
        q=t-beat; env=np.where(q>=0,np.exp(-np.maximum(q,0)*3),0)
        hit=np.sin(2*np.pi*(43*q+18*(1-np.exp(-np.maximum(q,0)*8))))*env*.14
        sound+=hit[:,None]
    voice_log=[]
    for j,(start,words) in enumerate(NARRATION):
        af=ROOT/f'voice-{j}.aiff'; wf=ROOT/f'voice-{j}.wav'
        subprocess.run(['say','-v','Tingting (中文（中国大陆）)','-r','205','-o',str(af),words],check=True)
        subprocess.run(['ffmpeg','-v','error','-y','-i',str(af),'-ar',str(sr),'-ac','1',str(wf)],check=True)
        with wave.open(str(wf),'rb') as f:
            v=np.frombuffer(f.readframes(f.getnframes()),np.int16).astype(np.float32)/32768
        pos=int(start*sr); end=min(pos+len(v),n)
        sound[pos:end]*=.36
        sound[pos:end]+=v[:end-pos,None]*.74
        voice_log.append({'start':start,'end':start+len(v)/sr,'text':words})
    sound*=np.minimum(np.clip(t/1.5,0,1),np.clip((DURATION-t)/2,0,1))[:,None]
    peak=float(np.max(np.abs(sound)))
    sound*=.88/max(peak,.88)
    with wave.open(str(ROOT/'soundtrack.wav'),'wb') as f:
        f.setnchannels(2);f.setsampwidth(2);f.setframerate(sr);f.writeframes((sound*32767).astype(np.int16).tobytes())
    (ROOT/'narration.json').write_text(json.dumps(voice_log,ensure_ascii=False,indent=2))
    print('Audio ready',voice_log,flush=True)

def contact():
    sheet=Image.new('RGB',(1280,3*405),(7,10,15))
    for j,t in enumerate([3,9,16.5,23.5,31,38.5]):
        thumb=frame(t).resize((640,360),Image.Resampling.LANCZOS)
        x=(j%2)*640;y=(j//2)*405;sheet.paste(thumb,(x,y))
        ImageDraw.Draw(sheet).text((x+24,y+370),f'{t:04.1f}s',font=font(20,'en'),fill=GOLD)
    sheet.save(ROOT/'contact-sheet.jpg',quality=95)
    frame(38.5).save(ROOT/'poster.jpg',quality=96)

def render():
    audio();contact()
    out=ROOT/'video-quality-loop-cinematic.mp4'
    cmd=['ffmpeg','-hide_banner','-loglevel','warning','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-i',str(ROOT/'soundtrack.wav'),'-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-b:a','256k','-movflags','+faststart','-t',str(DURATION),str(out)]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    for i in range(FPS*DURATION):
        proc.stdin.write(frame(i/FPS).tobytes())
        if i%(FPS*3)==0:print(f'Render {i/FPS:.0f}/{DURATION}s',flush=True)
    proc.stdin.close()
    if proc.wait(): raise RuntimeError('FFmpeg render failed')
    print(out,flush=True)

if __name__=='__main__':
    if '--contact' in sys.argv:contact()
    else:render()
