import json,base64,sys,struct
for i in range(1,7):
    d=json.load(open(f'resp_{i}.json'))
    p=d['candidates'][0]['content']['parts'][0]['inlineData']
    raw=base64.b64decode(p['data'])
    if raw[:4]!=b'RIFF':
        sr=24000
        hdr=b'RIFF'+struct.pack('<I',36+len(raw))+b'WAVEfmt '+struct.pack('<IHHIIHH',16,1,1,sr,sr*2,2,16)+b'data'+struct.pack('<I',len(raw))
        raw=hdr+raw
    open(f'take{i}.wav','wb').write(raw)
    print(i,p['mimeType'],len(raw))
