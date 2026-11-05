#!/bin/bash
# usage: gen.sh N  -> resp_N.json
cd "$(dirname "$0")"
URL=https://aiplatform.googleapis.com/v1/projects/composed-venture-6457f/locations/global/publishers/google/models/gemini-3.8-flash-tts:generateContent
TOK=$(env -u CLOUDSDK_AUTH_ACCESS_TOKEN gcloud auth print-access-token 2>/dev/null)
curl -sS -o resp_$1.json -w "take$1 http=%{http_code}\n" -X POST "$URL" \
  -H "Authorization: Bearer $TOK" -H "Content-Type: application/json; charset=utf-8" \
  --data-binary @req.json --max-time 300
