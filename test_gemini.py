from google import genai
import sys
import io

# 日本語表示エラー対策
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

KEY = "AIzaSyAxSJE5c-aB3i0TkvgBa8ja432Bw1oo5tQ"

def run_test():
    print("--- 接続テスト (モデル変更版) ---")
    client = genai.Client(api_key=KEY)
    
    # リストにあった別の安定版モデルを試す
    target_model = "models/gemini-flash-latest"
    
    try:
        print(f"モデル '{target_model}' を試しています...")
        
        response = client.models.generate_content(
            model=target_model,
            contents="Hello, please respond in Japanese."
        )
        
        print("\n成功しました！")
        print(response.text)
        
    except Exception as e:
        print("\nまだ制限がかかっています。")
        print("Google側の準備が整うまで少し時間がかかるようです。")
        print(f"エラー内容: {e}")

if __name__ == "__main__":
    run_test()