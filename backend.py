import os
import sys
import io
import itertools
from typing import Optional
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai
from google.genai import types

# Renderのログに即座に出力するための設定
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- APIキーの取得ロジック ---
# 環境変数が設定されていない場合、コード内の値をフォールバックとして使います
key1 = os.getenv("GEMINI_API_KEY_1", "AIzaSyAxSJE5c-aB3i0TkvgBa8ja432Bw1oo5tQ")
key2 = os.getenv("GEMINI_API_KEY_2", "AIzaSyCDjrjx0-z5Zsv0JLOV9Xr-HMTimBqTrNo")

API_KEYS = [k for k in [key1, key2] if k]
key_cycle = itertools.cycle(API_KEYS)

def get_next_client():
    next_key = next(key_cycle)
    # ログに使用するキーの断片を表示
    print(f"DEBUG: Using Key starting with: {next_key[:8]}...", flush=True)
    return genai.Client(api_key=next_key)

def generate_with_retry(client, contents):
    # あなたの環境で最も可能性が高いモデル名のリスト
    candidates = ["gemini-1.5-flash", "gemini-2.0-flash", "gemini-flash-latest"]
    
    last_error = None
    for model_name in candidates:
        try:
            print(f"DEBUG: Trying model: {model_name}", flush=True)
            response = client.models.generate_content(
                model=model_name,
                contents=contents
            )
            return response.text
        except Exception as e:
            last_error = e
            print(f"DEBUG: Model {model_name} failed. Error: {str(e)[:100]}", flush=True)
            continue
            
    raise last_error

@app.post("/chat")
async def chat(message: str = Form(""), file: Optional[UploadFile] = File(None)):
    print(f"--- New Chat Request Received ---", flush=True)
    try:
        client = get_next_client()
        parts = ["詳細に日本語で回答してください。"]
        if message:
            parts.append(f"質問: {message}")
        if file:
            file_data = await file.read()
            parts.append(types.Part.from_bytes(data=file_data, mime_type=file.content_type))

        reply_text = generate_with_retry(client, parts)
        return {"reply": reply_text}
    
    except Exception as e:
        # 【重要】ここが重要です。本当のエラーをログに出力します。
        error_detail = str(e)
        print(f"!!! CRITICAL ERROR: {error_detail} !!!", flush=True)
        return {"error": f"Internal API Error: {error_detail[:50]}"}

@app.post("/generate_title")
async def generate_title(request: dict):
    return {"title": "チャット履歴"}

@app.get("/")
def read_root():
    return {"status": "debug mode is active"}