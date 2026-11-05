import json,subprocess,wave,numpy as np
TAKE='6'
a=json.load(open('analysis.json'))[TAKE]
T=[(0.2,4.3),(4.6,9.7),(10.0,15.9),(16.2,19.7),(20.0,25.3),(25.6,29.7),(30.2,33.3),(33.6,37.3),(37.6,41.1),(41.4,44.7),(45.2,47.7),(48.0,51.2),(51.5,54.0),(54.3,58.7),(59.2,62.1),(62.4,65.8),(66.1,68.9),(69.2,71.7)]
lines=[l.strip() for l in open('script_tts.txt',encoding='utf-8') if l.strip()]
syl=[sum(1 for c in l if '가'<=c<='힣') for l in lines]
SR=48000;PRE,POST=0.03,0.12
def ff(args): subprocess.run(['ffmpeg','-nostdin','-hide_banner','-loglevel','error','-y']+args,check=True,stdin=subprocess.DEVNULL)
def rd(f):
    w=wave.open(f);return np.frombuffer(w.readframes(w.getnframes()),np.int16).astype(float)/32768
out=np.zeros(int(73.0*SR));rows=[]
for i,((s,e),(ts,lim)) in enumerate(zip(a['segs'],T),1):
    cs,ce=max(0,s-PRE),e+POST;cl=ce-cs
    ff(['-i',f'take{TAKE}.wav','-af',f'atrim={cs:.4f}:{ce:.4f},asetpts=N/SR/TB,afade=t=in:d=0.01,afade=t=out:st={cl-0.01:.4f}:d=0.01',f's{i:02d}.wav'])
    speech=e-s;onset=ts+0.05;avail=lim-onset
    tempo=1.0
    if speech>avail: tempo=min(1.15,speech/avail)
    tempo=round(tempo,4) if tempo>1 else 1.0
    af=f'aresample={SR}:resampler=soxr'+(f',atempo={tempo}' if tempo>1 else '')
    ff(['-i',f's{i:02d}.wav','-af',af,'-ac','1',f'p{i:02d}.wav'])
    y=rd(f'p{i:02d}.wav')
    pos=int((onset-PRE/tempo)*SR); out[pos:pos+len(y)]+=y
    sp_end=onset+speech/tempo
    rows.append(dict(n=i,syl=syl[i-1],src_start=round(s,3),src_len=round(speech,3),s_per_syl=round(speech/syl[i-1],3),onset=round(onset,3),tempo=tempo,out_len=round(speech/tempo,3),end=round(sp_end,3),limit=lim,over=round(max(0,sp_end-lim),3)))
# gap checks
for r,nx in zip(rows,rows[1:]): r['gap_next']=round(nx['onset']-r['end'],3)
# loudness: RMS of speaking frames -> -16 dBFS
fr=int(0.02*SR);blk=out[:len(out)//fr*fr].reshape(-1,fr);rms=np.sqrt((blk**2).mean(1))
act=blk[rms>10**(-40/20)];cur=20*np.log10(np.sqrt((act**2).mean()))
g=10**((-16-cur)/20);out*=g
print('speech rms before',round(cur,2),'gain dB',round(20*np.log10(g),2),'voice peak',round(np.abs(out).max(),3))
wave_out=wave.open('narration_48k.wav','wb');wave_out.setnchannels(1);wave_out.setsampwidth(2);wave_out.setframerate(SR)
wave_out.writeframes((np.clip(out,-1,1)*32767).astype(np.int16).tobytes());wave_out.close()
json.dump(rows,open('placement.json','w'),ensure_ascii=False,indent=1)
for r in rows: print(r)
