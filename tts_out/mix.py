import json,subprocess,wave,numpy as np
SR=48000;DUCK=-8.0;ATT=0.3;REL=0.5
P=json.load(open('placement.json'))
mus=np.frombuffer(subprocess.run(['ffmpeg','-nostdin','-v','error','-i','src73.mp4','-vn','-ac','2','-ar',str(SR),'-f','f32le','-'],capture_output=True,check=True).stdout,np.float32).reshape(-1,2).astype(float)
w=wave.open('narration_48k.wav');v=np.frombuffer(w.readframes(w.getnframes()),np.int16).astype(float)/32768
N=int(73.0*SR);mus=np.pad(mus,((0,max(0,N-len(mus))),(0,0)))[:N];v=np.pad(v,(0,max(0,N-len(v))))[:N]
t=np.arange(N)/SR;g=np.zeros(N)
for r in P:
    on,en=r['onset'],r['end']
    c=np.zeros(N)
    c=np.where((t>=on)&(t<=en),DUCK,c)
    m=(t>on-ATT)&(t<on);c[m]=DUCK*(t[m]-(on-ATT))/ATT
    m=(t>en)&(t<en+REL);c[m]=DUCK*(1-(t[m]-en)/REL)
    g=np.minimum(g,c)
mix=mus*(10**(g/20))[:,None]+v[:,None]
pk=np.abs(mix).max();print('pre-encode peak',round(pk,4))
if pk>0.88: mix*=0.88/pk;print('scaled to 0.88')
open('mix_48k.f32','wb').write(mix.astype(np.float32).tobytes())
