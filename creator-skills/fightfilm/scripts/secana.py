import sys,subprocess,numpy as np
from scipy.signal import stft,find_peaks,butter,sosfilt
f=sys.argv[1];sr=22050
x=np.frombuffer(subprocess.run(["ffmpeg","-v","error","-i",f,"-ac","1","-ar",str(sr),"-f","s16le","-"],capture_output=True).stdout,np.int16).astype(float)/32768
h=512;e=np.array([np.sum(x[i:i+h]**2) for i in range(0,len(x)-h,h)]);o=np.maximum(0,np.diff(np.log(e+1e-9)));fr=sr/h
seg=o[:int(90*fr)]-o[:int(90*fr)].mean();ac=np.correlate(seg,seg,'full')[len(seg)-1:];lags=np.arange(len(ac))/fr;m=(lags>0.33)&(lags<0.6);L=lags[m][np.argmax(ac[m])];print("BPM",round(60/L,1))
db=lambda s:20*np.log10(np.sqrt((s**2).mean())+1e-9);lo=sosfilt(butter(4,150,'low',fs=sr,output='sos'),x)
print("4s blocks full/bass:"," ".join(f"{t}:{db(x[int(t*sr):int((t+4)*sr)]):.0f}/{db(lo[int(t*sr):int((t+4)*sr)]):.0f}" for t in range(0,int(len(x)/sr)-3,4)))
hop=int(sr*L/2);fq,t,Z=stft(x,sr,nperseg=4096,noverlap=4096-hop);M=np.abs(Z);ed=np.geomspace(40,10000,33)
B=np.array([M[(fq>=ed[i])&(fq<ed[i+1])].mean(0) for i in range(32)]);F=np.log(B+1e-6);F=(F-F.mean(1,keepdims=True))/(F.std(1,keepdims=True)+1e-9)
Fs=np.array([np.convolve(r,np.ones(6)/6,'same') for r in F]);Fn=Fs/(np.linalg.norm(Fs,axis=0,keepdims=True)+1e-9);SSM=Fn.T@Fn
n=SSM.shape[0];K=16;s=np.r_[-np.ones(K),np.ones(K)];kern=np.outer(s,s);gg=np.exp(-((np.arange(2*K)-K+.5)/(K*.6))**2);kern*=np.outer(gg,gg)
nov=np.zeros(n)
for i in range(K,n-K):nov[i]=(SSM[i-K:i+K,i-K:i+K]*kern).sum()
nov=np.maximum(nov,0);nov/=nov.max();pk,_=find_peaks(nov,height=0.2,distance=int(5/(L/2)))
print("bounds:"," ".join(f"{t[p]:.1f}({nov[p]:.2f})" for p in pk))
# ช่วงเบาลง (breakdown)
E=np.array([db(x[int(t*sr):int((t+1)*sr)]) for t in range(int(len(x)/sr))]);med=np.median(E)
print("quiet secs (<median-4dB):",[i for i,v in enumerate(E) if v<med-4])
