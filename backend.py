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

# Windowsターミナルの日本語表示エラーを強制回避
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

app = FastAPI()

# CORS設定（公開後、必要に応じて origins を制限します）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- APIキーの設定 ---
# GitHubに上げた際、キーを盗まれないよう os.getenv を使用します。
# 第2引数に現在のキーを書いておくことで、自分のPCではそのまま動きます。
API_KEYS = [
    os.getenv("GEMINI_API_KEY_1", "AIzaSyAxSJE5c-aB3i0TkvgBa8ja432Bw1oo5tQ"),
    os.getenv("GEMINI_API_KEY_2", "AIzaSyCDjrjx0-z5Zsv0JLOV9Xr-HMTimBqTrNo")
]

key_cycle = itertools.cycle(API_KEYS)

def get_next_client():
    """リクエストごとに次のAPIキーを使用してクライアントを作成"""
    next_key = next(key_cycle)
    return genai.Client(api_key=next_key)

class ChatRequest(BaseModel):
    message: str

def generate_with_retry(client, contents):
    """
    お使いの環境で確実に存在するモデルを順番に試し、
    404エラーや20回制限(429)を自動で回避します。
    """
    # 優先順：1.5-flash (1,500回枠) -> 2.0-flash -> latest
    candidates = ["gemini-1.5-flash", "gemini-2.0-flash", "gemini-flash-latest"]
    
    last_error = None
    for model_name in candidates:
        try:
            print(f"Trying model: {model_name}")
            response = client.models.generate_content(
                model=model_name,
                contents=contents
            )
            return response.text
        except Exception as e:
            last_error = e
            error_str = str(e)
            print(f"Skipped {model_name}: {error_str[:50]}...")
            continue
            
    raise last_error

@app.post("/chat")
async def chat(message: str = Form(""), file: Optional[UploadFile] = File(None)):
    try:
        client = get_next_client()
        
        # システム指示文
        parts = ["詳細に日本語で回答してください。マークダウン形式（表や太字など）を適切に使用してください。"]
        
        if message:
            parts.append(f"質問: {message}")
        
        if file:
            file_data = await file.read()
            # 最新SDK専用の形式で画像を添付（18個のバリデーションエラーを回避）
            parts.append(types.Part.from_bytes(
                data=file_data,
                mime_type=file.content_type
            ))

        # モデルを自動選択して生成
        reply_text = generate_with_retry(client, parts)
        return {"reply": reply_text}
    
    except Exception as e:
        print(f"Final Error: {e}")
        return {"error": "現在サーバーが混み合っているか、制限に達しています。1分後に再度お試しください。"}

@app.post("/generate_title")
async def generate_title(request: ChatRequest):
    """チャット履歴用の短いタイトルを自動生成"""
    try:
        client = get_next_client()
        # タイトル生成は gemini-1.5-flash を優先試行
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=f"以下の内容を要約し、非常に短いタイトル（名詞のみ、最大10文字）を1つ生成してください：\n{request.message}"
        )
        return {"title": response.text.strip()}
    except:
        # 失敗した場合は暫定のタイトルを返す
        return {"title": "チャット履歴"}

@app.get("/")
def read_root():
    """サーバーの生存確認用"""
    return {"status": "Gemini AI Backend is running"}