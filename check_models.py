import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ 錯誤: 找不到 GEMINI_API_KEY，請檢查 .env 檔案")
else:
    genai.configure(api_key=api_key)
    print("=== 可用的 Gemini 模型列表 ===")
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"- {m.name}")
    except Exception as e:
        print(f"連線錯誤: {e}")