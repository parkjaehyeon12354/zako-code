#!/bin/bash
# usage: asr.sh input_audio_or_video out.json
IN=$1; OUT=$2; T=$(mktemp -d)
ffmpeg -nostdin -hide_banner -loglevel error -y -i "$IN" -vn -ac 1 -ar 24000 -b:a 64k $T/a.mp3
python3 - "$T/a.mp3" > $T/req.json <<'PY'
import sys,base64,json
b=base64.b64encode(open(sys.argv[1],'rb').read()).decode()
print(json.dumps({"contents":[{"role":"user","parts":[{"inlineData":{"mimeType":"audio/mp3","data":b}},{"text":"이 한국어 음성을 들리는 그대로 받아 적어 주세요. 문장마다 한 줄씩, 다른 설명 없이 받아쓰기만 출력하세요."}]}],"generationConfig":{"temperature":0}}))
PY
TOK=$(env -u CLOUDSDK_AUTH_ACCESS_TOKEN gcloud auth print-access-token 2>/dev/null)
curl -sS -o "$OUT" -w "asr http=%{http_code}\n" -X POST "https://aiplatform.googleapis.com/v1/projects/composed-venture-6457f/locations/global/publishers/google/models/gemini-2.5-flash:generateContent" -H "Authorization: Bearer $TOK" -H "Content-Type: application/json" --data-binary @$T/req.json --max-time 300
python3 -c "import json,sys;d=json.load(open(sys.argv[1]));print(''.join(p.get('text','') for p in d['candidates'][0]['content']['parts']))" "$OUT"
rm -rf $T
