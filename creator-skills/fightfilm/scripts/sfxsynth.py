# เสียงประกอบโมชันกราฟิกแบบสังเคราะห์ล้วน (ไม่ต้องมีไฟล์ sample) + ตัววางเสียงตามเวลา
# ใช้:  python sfxsynth.py demo out.wav                 เล่นทุกเสียงเรียงกันไว้ฟังเทียบ
#       python sfxsynth.py mix events.json out.wav [ยาวกี่วิ]
# events.json = [{"t":1.40,"k":"kick"},{"t":10.05,"k":"riser","dur":2.1,"gap":0.4},{"t":12.59,"k":"boom","g":1.0}, ...]
#   t = เวลาที่ "หัวเสียง" ต้องตรงกับภาพ (riser: t คือเวลาเริ่ม · whoosh: t คือจุดพีค)
# ตัวเลขตั้งต้นวัดจากคลิปต้นแบบ (ดู references/motion-graphics.md) · ฉากต่อสู้ยังใช้ sample จริงตาม sfx4.py
import sys,json,io,wave,numpy as np
from scipy.signal import butter,sosfilt
SR=48000
def T(d):return np.arange(int(d*SR))/SR
def env(n,a=0.002,r=0.1,curve=4.0):                      # attack เส้นตรง + release แบบ exp
    t=np.arange(n)/SR;return np.minimum(1,t/max(a,1e-4))*np.exp(-curve*np.maximum(0,t-a)/max(r,1e-4))
def sweep(f0,f1,d,k=6.0):                                # ความถี่ไหลแบบ exp จาก f0 ไป f1
    t=T(d);f=f1+(f0-f1)*np.exp(-k*t/d);return np.sin(2*np.pi*np.cumsum(f)/SR)
def noise(d,seed=1):return np.random.default_rng(seed).uniform(-1,1,int(d*SR))
def bp(x,lo,hi):return sosfilt(butter(2,[lo,hi],'band',fs=SR,output='sos'),x)
def lp(x,f):return sosfilt(butter(2,f,'low',fs=SR,output='sos'),x)
def hp(x,f):return sosfilt(butter(2,f,'high',fs=SR,output='sos'),x)
def fade(x,a=0.003,r=0.01):
    n=len(x);e=np.ones(n);i=min(n,int(a*SR));j=min(n,int(r*SR));e[:i]=np.linspace(0,1,i);e[n-j:]*=np.linspace(1,0,j);return x*e
sat=lambda x,d=1.6:np.tanh(x*d)/np.tanh(d)

def kick(d=0.30,f0=150,f1=45):                           # หัวเสียงรับจุดตัด: ซับไหลลง + คลิกสั้น
    x=sweep(f0,f1,d,9)*env(int(d*SR),0.002,d*0.45);c=hp(noise(0.012,2),2500)*env(int(0.012*SR),0.0005,0.004)
    x[:len(c)]+=0.5*c;return fade(sat(x))
def tick(d=0.04,f=3200):                                 # ติ๊กรับคำที่เด้งขึ้นทีละคำ
    return fade(bp(noise(d,3),f*0.7,f*1.4)*env(int(d*SR),0.0005,0.012)*1.8,0.0005,0.004)
def pop(d=0.09,f0=520,f1=900):                           # ป๊อปรับวัตถุ/สติกเกอร์เด้ง
    return fade(sweep(f0,f1,d,10)*env(int(d*SR),0.002,0.035))
def blip(d=0.11,f=1100,h=(1,1.5)):                       # เสียง UI (สวิตช์ ปุ่ม ตัวพิมพ์) โทนบริสุทธิ์
    t=T(d);return fade(sum(np.sin(2*np.pi*f*k*t) for k in h)/len(h)*env(len(t),0.002,0.05))
def whoosh(d=0.35,lo=300,hi=5000,peak=0.6):              # noise ผ่านตัวกรองที่กวาด · พีคตรงตำแหน่ง peak ของความยาว
    n=int(d*SR);x=noise(d,4);t=np.arange(n)/n;e=np.where(t<peak,(t/peak)**2,((1-t)/(1-peak))**1.5)
    out=np.zeros(n);seg=8;L=n//seg
    for i in range(seg):                                 # กวาดความถี่กลางเป็นช่วงๆ แล้วต่อด้วย crossfade
        fc=lo*(hi/lo)**(1-abs((i+0.5)/seg-peak)/max(peak,1-peak));a=max(0,i*L-L//2);b=min(n,(i+1)*L+L//2)
        w=np.hanning(b-a);out[a:b]+=bp(x[a:b],fc*0.6,min(fc*1.6,SR*0.45))*w
    return fade(out*e*1.6,0.01,0.02)
def riser(d=2.1,f0=310,f1=2900,gap=0.0):                 # ไต่ขึ้นแบบ exp ราว 3 อ็อกเทฟ + noise ที่เปิดกว้างขึ้น · gap = ความเงียบต่อท้าย
    n=int(d*SR);t=np.arange(n)/n;f=f0*(f1/f0)**t;ph=2*np.pi*np.cumsum(f)/SR
    tone=(np.sin(ph)+0.5*np.sin(2*ph)+0.25*np.sin(3.01*ph))*(0.25+0.75*t)
    nz=hp(noise(d,5),600)*t**2*0.5;trem=1-0.25*(0.5+0.5*np.sin(2*np.pi*np.cumsum(4+12*t)/SR))
    return np.r_[fade(sat((tone*0.5+nz)*trem,1.2),0.03,0.012),np.zeros(int(gap*SR))]
def boom(d=1.5,f0=110,f1=34):                            # ลงหนัก: ซับยาว + เสียงแตกสั้นย่านกลาง + หาง noise ทุ้ม
    n=int(d*SR);x=sweep(f0,f1,d,5)*env(n,0.003,d*0.5,3);c=bp(noise(0.08,6),150,2500)*env(int(0.08*SR),0.001,0.03)
    x[:len(c)]+=0.7*c;x+=lp(noise(d,7),260)*env(n,0.004,d*0.35,3)*0.5;return fade(sat(x,2.2),0.002,0.08)
def glitch(d=0.18,seed=8):                               # แตกเป็นเม็ด: โทนสั้นๆ สุ่มความถี่ สลับเงียบ
    r=np.random.default_rng(seed);n=int(d*SR);x=np.zeros(n);L=int(0.012*SR)
    for a in range(0,n-L,L):
        if r.random()<0.7:x[a:a+L]=np.sign(np.sin(2*np.pi*r.choice([220,440,880,1760,3520])*np.arange(L)/SR))*0.5*np.hanning(L)
    return hp(x,180)
def shimmer(d=0.9,f=1320):                               # โลโก้/การ์ดปิดท้าย: คอร์ดเปิด ค่อยๆ จาง
    t=T(d);return fade(sum(np.sin(2*np.pi*f*k*t+i) for i,k in enumerate((0.5,0.75,1,1.5,2)))/5*env(len(t),0.01,d*0.5,3),0.01,0.1)
KIND=dict(kick=kick,tick=tick,pop=pop,blip=blip,whoosh=whoosh,riser=riser,boom=boom,glitch=glitch,shimmer=shimmer)
# ระดับตั้งต้น (เทียบ full scale) · คลิปต้นแบบ: พื้น -24 dB, จุดลงหนัก -5 dB ห่างกัน ~19 dB
GAIN=dict(kick=0.42,tick=0.16,pop=0.26,blip=0.2,whoosh=0.3,riser=0.34,boom=0.92,glitch=0.22,shimmer=0.3)

def mix(events,dur):
    out=np.zeros(int(dur*SR)+SR)
    for e in events:
        kw={k:v for k,v in e.items() if k not in('t','k','g')};x=KIND[e['k']](**kw)*GAIN[e['k']]*e.get('g',1.0)
        t=e['t']-(kw.get('d',0.35)*kw.get('peak',0.6) if e['k']=='whoosh' else 0)       # whoosh: ให้พีคตรง t
        a=max(0,int(t*SR));x=x[:len(out)-a];out[a:a+len(x)]+=x
    return out[:int(dur*SR)]
def save(p,x):
    x=np.clip(x,-0.98,0.98);w=wave.open(p,'wb');w.setnchannels(2);w.setsampwidth(2);w.setframerate(SR)
    w.writeframes((np.repeat(x[:,None],2,1)*32767).astype(np.int16).tobytes());w.close()
if __name__=='__main__':
    if sys.argv[1]=='demo':
        ev=[];t=0.3
        for k in KIND:ev.append(dict(t=t+(0.25 if k=='whoosh' else 0),k=k));t+=len(KIND[k]())/SR+0.5;print(f"{ev[-1]['t']:.2f} {k}")
        save(sys.argv[2],mix(ev,t))
    else:
        ev=json.load(io.open(sys.argv[2],encoding='utf-8'));dur=float(sys.argv[4]) if len(sys.argv)>4 else max(e['t'] for e in ev)+3
        save(sys.argv[3],mix(ev,dur));print(len(ev),'events',round(dur,2),'s')
