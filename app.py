import streamlit as st
from google import genai

# タイトル
st.title("My Personal Gemini AI")

# サイドバーにAPIキーを入力（またはコードに直接書く）
KEY = "AIzaSyAxSJE5c-aB3i0TkvgBa8ja432Bw1oo5tQ"

# Geminiの準備
client = genai.Client(api_key=KEY)

# チャット履歴を保存する仕組み
if "messages" not in st.session_state:
    st.session_state.messages = []

# 過去のメッセージを表示
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ユーザーの入力
if prompt := st.chat_input("メッセージを入力してね"):
    # ユーザーのメッセージを表示
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Geminiからの返答を取得
    try:
        response = client.models.generate_content(
            model="models/gemini-flash-latest",
            contents=prompt
        )
        answer = response.text
        
        # AIの返答を表示
        with st.chat_message("assistant"):
            st.markdown(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})
    except Exception as e:
        st.error(f"エラーが発生しました: {e}")