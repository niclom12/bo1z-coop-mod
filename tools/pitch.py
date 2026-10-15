import sys,subprocess,numpy as np
# median f0 via autocorrelation on voiced frames; usage: pitch.py file [fmin fmax]
f=sys.argv[1]; fmin=float(sys.argv[2]) if len(sys.argv)>2 else 70; fmax=float(sys.argv[3]) if len(sys.argv)>3 else 500
sr=16000
x=np.frombuffer(subprocess.run(["ffmpeg","-v","error","-i",f,"-ar",str(sr),"-ac","1","-f","s16le","-"],capture_output=True).stdout,dtype=np.int16).astype(float)/32768
N=int(.04*sr);H=int(.01*sr);fs=[]
thr=0.25*np.sqrt(np.mean(x**2))
for i in range(0,len(x)-N,H):
    s=x[i:i+N]; s=s-s.mean()
    if np.sqrt(np.mean(s**2))<thr: continue
    w=s*np.hanning(N); a=np.correlate(w,w,'full')[N-1:]; a/=a[0]+1e-12
    lo,hi=int(sr/fmax),int(sr/fmin); k=lo+np.argmax(a[lo:hi])
    if a[k]>0.5:
        # parabolic interpolation
        if 0<k<len(a)-1:
            d=a[k-1]-2*a[k]+a[k+1]; k=k+(0.5*(a[k-1]-a[k+1])/d if d else 0)
        fs.append(sr/k)
fs=np.array(fs)
print(f"{f}: voiced={len(fs)} median={np.median(fs):.0f}Hz p10={np.percentile(fs,10):.0f} p90={np.percentile(fs,90):.0f}" if len(fs) else f"{f}: no voiced frames")
