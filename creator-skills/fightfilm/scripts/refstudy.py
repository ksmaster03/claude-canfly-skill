# แกะคลิปต้นแบบ: จังหวะตัดภาพ + โครงเสียง ออกมาเป็นตัวเลขและภาพให้ดู
# ใช้: python refstudy.py <clip.mp4 หรือ URL> [โฟลเดอร์ผลลัพธ์]
# ได้: sheet_*.jpg (ภาพย่อ 4 ภาพ/วิ), spec.png (สเปกโตรแกรม), report.txt
import sys,os,io,subprocess,glob,numpy as np
from scipy.signal import butter,sosfiltfilt,find_peaks,stft
src=sys.argv[1];out=sys.argv[2] if len(sys.argv)>2 else "refstudy";os.makedirs(out,exist_ok=True)
run=lambda a:subprocess.run(a,capture_output=True,text=True,encoding="utf-8",errors="replace")
if src.startswith("http"):
    run(["yt-dlp","-o",os.path.join(out,"ref.%(ext)s"),"--merge-output-format","mp4",src]);src=os.path.join(out,"ref.mp4")
R=[];P=lambda *a:R.append(" ".join(str(x) for x in a))
pr=run(["ffprobe","-v","error","-show_entries","format=duration:stream=codec_type,width,height,r_frame_rate","-of","default=nw=1",src]).stdout
dur=float([l for l in pr.splitlines() if l.startswith("duration=")][0].split("=")[1]);P("== ไฟล์ ==");P(pr.strip())

# ---------- ภาพ ----------
run(["ffmpeg","-v","error","-y","-i",src,"-vf","fps=4,scale=270:-1,tile=10x6","-q:v","3",os.path.join(out,"sheet_%02d.jpg")])
sc=run(["ffmpeg","-v","error","-i",src,"-vf","select='gt(scene,0.25)',metadata=print:file=-","-an","-f","null","-"]).stdout
cuts=[float(l.split("pts_time:")[1]) for l in sc.splitlines() if "pts_time:" in l]
cuts=[c for i,c in enumerate(cuts) if i==0 or c-cuts[i-1]>0.1]          # รวมเฟรมแฟลชที่ติดกัน
P("\n== ภาพ ==");P("จุดตัด",len(cuts),"จุด:"," ".join(f"{c:.2f}" for c in cuts))
if len(cuts)>1:
    g=np.diff([0]+cuts+[dur]);P(f"ความยาวช็อต: กลาง {np.median(g):.2f} วิ · สั้นสุด {g.min():.2f} · ยาวสุด {g.max():.2f} · เฉลี่ย {dur/len(g):.2f}")
    P("ช็อตสั้นกว่า 0.35 วิ (ช่วงรัว):"," ".join(f"{c:.2f}" for c,d in zip([0]+cuts,g) if d<0.35) or "-")

# ---------- เสียง ----------
sr=22050
x=np.frombuffer(subprocess.run(["ffmpeg","-v","error","-i",src,"-ac","1","-ar",str(sr),"-f","s16le","-"],capture_output=True).stdout,np.int16).astype(float)/32768
run(["ffmpeg","-v","error","-y","-i",src,"-lavfi","showspectrumpic=s=1800x700:legend=1:scale=log:fscale=log",os.path.join(out,"spec.png")])
lu=run(["ffmpeg","-hide_banner","-nostats","-i",src,"-af","ebur128=peak=true","-f","null","-"]).stderr
P("\n== เสียง ==");P(" ".join(l.strip() for l in lu.splitlines()[-25:] if l.strip().startswith(("I:","LRA:","Peak:"))))
# หัวเสียงย่านต่ำ (kick/sub) = โครงจังหวะ
lo=sosfiltfilt(butter(4,120,'low',fs=sr,output='sos'),x);hop=110
env=np.sqrt(np.convolve(lo**2,np.ones(hop)/hop,'same'))[::hop];d=np.maximum(0,np.diff(env,prepend=env[0]))
pk,_=find_peaks(d,height=d.max()*0.12,distance=int(0.2*sr/hop));kt=pk*hop/sr
P("หัวเสียงเบส",len(kt),"จุด:"," ".join(f"{t:.2f}" for t in kt))
if len(kt)>3:
    iv=np.diff(kt);iv=iv[(iv>0.3)&(iv<1.1)]
    if len(iv):
        h,e=np.histogram(iv,bins=np.arange(0.3,1.12,0.02));b=e[h.argmax()]+0.01;P(f"ช่วงห่างที่พบบ่อยสุด {b:.2f} วิ = {60/b:.0f} BPM (ลองเทียบ {30/b:.0f} และ {120/b:.0f} ด้วย)")
# หัวเสียงทุกย่าน (spectral flux) ใช้เทียบกับจุดตัดภาพ
fa,ta,Za=stft(x,sr,nperseg=1024,noverlap=1024-256);Ma=np.log1p(40*np.abs(Za));fl=np.maximum(0,np.diff(Ma,axis=1,prepend=Ma[:,:1])).sum(0)
ok,_=find_peaks(fl,height=fl.max()*0.18,distance=int(0.08*sr/256));ot=ta[ok]
P("หัวเสียงทุกย่าน",len(ot),"จุด:"," ".join(f"{t:.2f}" for t in ot))
if cuts and len(ot):
    off=[1000*(ot[np.argmin(abs(ot-c))]-c) for c in cuts];on=sum(abs(o)<70 for o in off)
    P(f"จุดตัดที่มีหัวเสียงภายใน ±70 ms: {on}/{len(cuts)} · ค่ากลางของระยะ {np.median([o for o in off if abs(o)<70] or [0]):+.0f} ms (บวก = เสียงมาหลังภาพ)")
    P("จุดตัดที่ไม่มีเสียงรับ:"," ".join(f"{c:.2f}" for c,o in zip(cuts,off) if abs(o)>=70) or "-")
    P(f"หัวเสียงที่ไม่ตรงจุดตัด (เสียงรับการเคลื่อนไหวในช็อต): {sum(min(abs(np.array(cuts)-o))>=0.07 for o in ot)}/{len(ot)}")
# riser = เส้นความถี่เด่นที่ไต่ขึ้นต่อเนื่อง
f,t,Z=stft(x,sr,nperseg=4096,noverlap=4096-512);M=np.abs(Z);m=(f>250)&(f<8000);pf=f[m][M[m].argmax(0)];lv=M[m].max(0);act=lv>lv.max()*0.08
i=0;ris=[]
while i<len(t)-4:
    j=i
    while j+1<len(t) and act[j+1] and pf[j+1]>=pf[j]*0.97:j+=1
    if t[j]-t[i]>0.6 and pf[j]>pf[i]*2:ris.append((t[i],t[j],pf[i],pf[j]))
    i=j+1
P("riser (ความถี่ไต่ขึ้น):"," | ".join(f"{a:.2f}→{b:.2f} วิ {p:.0f}→{q:.0f} Hz ({np.log2(q/p):.1f} อ็อกเทฟ)" for a,b,p,q in ris) or "-")
# ช่วงเงียบก่อนเสียงใหญ่ (ช่องว่างก่อน drop)
r=np.sqrt(np.convolve(x**2,np.ones(441)/441,'same'))[::441];rt=np.arange(len(r))*441/sr;q=r<10**(-40/20)
ed=np.flatnonzero(np.diff(np.r_[0,q.astype(int),0]));gaps=[(rt[a],rt[min(b,len(rt)-1)]) for a,b in zip(ed[::2],ed[1::2]) if (b-a)*441/sr>0.08]
P("ช่วงเงียบ (< -40 dB เกิน 0.08 วิ):"," ".join(f"{a:.2f}+{b-a:.2f}" for a,b in gaps) or "-")
P("ระดับเสียงทุก 0.5 วิ (dB):"," ".join(f"{20*np.log10(np.sqrt((x[int(i*sr/2):int((i+1)*sr/2)]**2).mean())+1e-9):.0f}" for i in range(int(dur*2))))
io.open(os.path.join(out,"report.txt"),"w",encoding="utf-8").write("\n".join(R));sys.stdout.reconfigure(encoding="utf-8");print("\n".join(R))
