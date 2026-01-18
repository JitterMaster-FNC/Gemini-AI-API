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

# --- APIキーの設定（GitHubに漏洩させない設定） ---
# 第2引数の空文字部分は、ローカルテスト時のみ自分のキーを一時的に貼ってもOKですが、
# GitHubに上げる前には必ず空にするか、このままにしてください。
key1 = os.getenv("GEMINI_API_KEY_1", "")
key2 = os.getenv("GEMINI_API_KEY_2", "")

# 有効なキーだけをリスト化
API_KEYS = [k for k in [key1, key2] if k]

# 万が一キーが設定されていない場合の安全策
if not API_KEYS:
    print("WARNING: No API keys found in Environment Variables!")
    # ローカルテスト用に一時的にここに書く場合は、Push前に消してください
    # API_KEYS = ["YOUR_TEST_KEY_HERE"]

key_cycle = itertools.cycle(API_KEYS)

def get_next_client():
    if not API_KEYS:
        raise Exception("APIキーが設定されていません。RenderのEnvironment設定を確認してください。")
    next_key = next(key_cycle)
    print(f"DEBUG: Using Key starting with: {next_key[:8]}...", flush=True)
    return genai.Client(api_key=next_key)

def generate_with_retry(client, contents):
    """
    1.5 Flash（1500回枠）を優先し、エラーがあれば次を試すロジック
    """
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
            print(f"DEBUG: Model {model_name} failed. Reason: {str(e)[:50]}...", flush=True)
            continue
            
    raise last_error

@app.post("/chat")
async def chat(message: str = Form(""), file: Optional[UploadFile] = File(None)):
    print(f"--- New Chat Request Received ---", flush=True)
    try:
        client = get_next_client()
        parts = ["日本語で回答してください。マークダウン形式（表や太字）を適切に使ってください。"]
        
        if message:
            parts.append(f"質問: {message}")
        
        if file:
            file_data = await file.read()
            parts.append(types.Part.from_bytes(
                data=file_data,
                mime_type=file.content_type
            ))

        reply_text = generate_with_retry(client, parts)
        return {"reply": reply_text}
    
    except Exception as e:
        error_detail = str(e)
        print(f"!!! CRITICAL ERROR: {error_detail} !!!", flush=True)
        return {"error": f"API Error: {error_detail[:50]}"}

@app.post("/generate_title")
async def generate_title(request: dict):
    # タイトル生成（簡略版）
    return {"title": "チャット履歴"}

@app.get("/")
def read_root():
    return {"status": "Gemini AI Backend is running securely"}