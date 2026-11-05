import subprocess,re,json,wave,numpy as np,sys
lines=[l.strip() for l in open('script_tts.txt',encoding='utf-8') if l.strip()]
syl=[sum(1 for c in l if '가'<=c<='힣') for l in lines]
def sil(f):
    o=subprocess.run(['ffmpeg','-hide_banner','-i',f,'-af','silencedetect=n=-40dB:d=0.2','-f','null','-'],capture_output=True,text=True).stderr
    s=[float(x) for x in re.findall(r'silence_start: ([\d.]+)',o)]
    e=[float(x) for x in re.findall(r'silence_end: ([\d.]+)',o)]
    return list(zip(s,e))
def load(f):
    w=wave.open(f);x=np.frombuffer(w.readframes(w.getnframes()),np.int16).astype(float)/32768;return x,w.getframerate()
def f0(x,sr):
    fl=int(0.04*sr);hop=int(0.01*sr);out=[]
    lo,hi=int(sr/400),int(sr/90)
    for i in range(0,len(x)-fl,hop):
        fr=x[i:i+fl]
        if np.sqrt(np.mean(fr**2))<0.02: continue
        fr=fr-fr.mean();ac=np.correlate(fr,fr,'full')[fl-1:]
        if ac[0]<=0: continue
        k=lo+np.argmax(ac[lo:hi]);
        if ac[k]/ac[0]>0.5: out.append(sr/k)
    return np.median(out) if out else float('nan')
res={}
for t in range(1,7):
    f=f'take{t}.wav';x,sr=load(f);dur=len(x)/sr
    S=sil(f)
    lead=S[0][1] if S and S[0][0]<0.01 else 0
    tail_s=S[-1][0] if S and S[-1][1]>dur-0.05 else dur
    inner=[(a,b) for a,b in S if a>0.01 and b<dur-0.05]
    inner_sorted=sorted(inner,key=lambda p:p[1]-p[0],reverse=True)
    if len(inner)<17: print('take',t,'only',len(inner),'gaps');continue
    bnd=sorted(inner_sorted[:17]);rest=inner_sorted[17:]
    min_b=min(b-a for a,b in bnd); max_r=max([b-a for a,b in rest],default=0)
    segs=[];st=lead
    for a,b in bnd: segs.append((st,a)); st=b
    segs.append((st,tail_s))
    lens=[b-a for a,b in segs]
    corr=np.corrcoef(lens,syl)[0,1]
    rate=[l/s for l,s in zip(lens,syl)]
    f0s=[f0(x[int(a*sr):int(b*sr)],sr) for a,b in segs]
    # tail energy check: rms of last 50ms of speech
    endrms=20*np.log10(np.sqrt(np.mean(x[int((tail_s-0.05)*sr):int(tail_s*sr)]**2))+1e-9)
    res[t]=dict(dur=dur,n_inner=len(inner),min_boundary=min_b,max_other=max_r,corr=corr,
      rate_minmax=(min(rate),max(rate)),f0=f0s,f0_range=max(f0s)-min(f0s),tail=dur-tail_s,endrms=endrms,segs=segs,speech=sum(lens))
    print(f"take{t} dur={dur:.2f} speech={sum(lens):.2f} gaps={len(inner)} minBoundary={min_b:.3f} maxOtherPause={max_r:.3f} corr={corr:.3f} s/syl={min(rate):.3f}-{max(rate):.3f} F0range={max(f0s)-min(f0s):.1f}Hz ({min(f0s):.0f}-{max(f0s):.0f}) tailSil={dur-tail_s:.2f}s last50ms={endrms:.1f}dB")
json.dump({k:{kk:(vv if not isinstance(vv,np.floating) else float(vv)) for kk,vv in v.items()} for k,v in res.items()},open('analysis.json','w'),default=float,indent=1)
