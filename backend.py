import os
import sys
import io
import itertools
import json
from typing import Optional
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai
from google.genai import types

# Windowsターミナルの日本語表示エラー回避
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- APIキーの設定（RenderのEnvironment Variablesから読み込み） ---
API_KEYS = [
    os.getenv("GEMINI_API_KEY_1", "AIzaSyAxSJE5c-aB3i0TkvgBa8ja432Bw1oo5tQ"),
    os.getenv("GEMINI_API_KEY_2", "AIzaSyCDjrjx0-z5Zsv0JLOV9Xr-HMTimBqTrNo")
]
key_cycle = itertools.cycle([k for k in API_KEYS if k])

def get_next_client():
    next_key = next(key_cycle)
    return genai.Client(api_key=next_key)

def generate_with_retry(client, contents):
    """
    1.5-flashを優先し、エラーがあれば他のモデルを試行する
    """
    candidates = ["gemini-1.5-flash", "gemini-2.0-flash", "gemini-flash-latest"]
    last_error = None
    for model_name in candidates:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=contents
            )
            return response.text
        except Exception as e:
            last_error = e
            continue
    raise last_error

@app.post("/chat")
async def chat(
    message: str = Form(""), 
    history: str = Form("[]"), 
    file: Optional[UploadFile] = File(None)
):
    try:
        client = get_next_client()
        
        # 1. 指示文（システムプロンプト）
        parts = ["あなたは親切なAIアシスタントです。これまでの会話の流れを踏まえて、詳細に日本語で回答してください。"]
        
        # 2. 記憶（履歴）の追加
        # Reactから届いたJSON形式の履歴を解析して、会話の流れを作る
        past_messages = json.loads(history)
        for msg in past_messages:
            role_label = "ユーザー" if msg['role'] == 'user' else "AI"
            parts.append(f"{role_label}: {msg['text']}")
        
        # 3. 今回の質問を追加
        if message:
            parts.append(f"ユーザーの最新の質問: {message}")
        
        # 4. ファイル（画像）があれば追加
        if file:
            file_data = await file.read()
            parts.append(types.Part.from_bytes(
                data=file_data,
                mime_type=file.content_type
            ))

        # AIに送信して回答を得る
        reply_text = generate_with_retry(client, parts)
        return {"reply": reply_text}
    
    except Exception as e:
        print(f"Chat Error: {e}")
        return {"error": str(e)}

@app.post("/generate_title")
async def generate_title(message: str = Form("")):
    """チャット履歴用の短いタイトルを自動生成"""
    try:
        client = get_next_client()
        prompt = f"以下の内容を10文字以内の名詞で要約してタイトルを作ってください。余計な言葉は不要です：\n{message}"
        response = client.models.generate_content(model="gemini-1.5-flash", contents=prompt)
        return {"title": response.text.strip()}
    except:
        return {"title": "新しいチャット"}

@app.get("/")
def read_root():
    return {"status": "Gemini AI Backend is running with Memory Support"}