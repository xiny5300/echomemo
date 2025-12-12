"""
檔案標準 (Standard):
本檔案封裝 Google Gemini 1.5 Flash 的所有 AI 功能，包括：
1. STT (語音轉文字): 使用 Gemini 的多模態能力進行語音識別
2. LLM (對話生成): 使用 Gemini 進行對話生成，支援不同人格模式
3. RAG (檢索增強生成): 結合資料庫搜尋與 Gemini 生成

輸入：音訊檔案（STT）、文字（LLM）、上下文（RAG）
輸出：文字轉錄、對話回應、問題生成

執行方式 (Execution):
- 被 main.py 呼叫進行 AI 處理
- 獨立測試：python -m modules.ai (會測試 STT 和 LLM 功能)

相依性 (Dependencies):
- google-generativeai: Google Gemini API
- asyncio: 非同步處理
- config: 系統配置（API 金鑰）
- database: 資料庫模組（RAG 功能）
"""

import google.generativeai as genai
import asyncio
from typing import Optional, List, Dict
import config
from modules.database import Database

class AI:
    """AI 處理類別（封裝 Gemini）"""
    
    def __init__(self):
        """初始化 Gemini API"""
        genai.configure(api_key=config.Config.GEMINI_KEY)
        self.model = genai.GenerativeModel("models/gemini-2.0-flash")
        self.db = Database()
        
        # 不同模式的 System Prompt
        self.system_prompts = {
            'system': """你是一個友善的 AI 助手，負責引導使用者進行每日訪談。
你的任務是提出開放性的問題，幫助使用者記錄他們的想法和感受。
問題應該簡短、親切，並且能夠引發深入的思考。""",
            
            'persona': """你是一個數位分身，模仿使用者的說話風格和語氣。
你應該根據使用者的記憶和過往對話，以使用者的方式回應。
你的回應應該自然、親切，就像使用者本人在說話一樣。""",
            
            'daily': """你是一個每日訪談助手，負責提出有意義的問題。
問題應該：
1. 簡短明確（不超過 50 字）
2. 開放性（沒有標準答案）
3. 引發思考（幫助使用者反思）
4. 親切友善（像朋友聊天）
請只輸出問題，不要其他說明。"""
        }
    
    async def speech_to_text(self, audio_path: str) -> Optional[str]:
        """
        語音轉文字（使用 Gemini 多模態能力）
        
        Args:
            audio_path: 音訊檔案路徑
        
        Returns:
            轉錄的文字，失敗返回 None
        """
        try:
            # 上傳音訊檔案到 Gemini
            audio_file = genai.upload_file(audio_path)
            
            # 等待檔案處理完成
            while audio_file.state.name == "PROCESSING":
                await asyncio.sleep(1)
                audio_file = genai.get_file(audio_file.name)
            
            if audio_file.state.name == "FAILED":
                print("音訊檔案處理失敗")
                return None
            
            # 使用 Gemini 進行語音識別
            prompt = "請逐字聽寫這段錄音的內容。如果錄音中有說話，請完整轉錄所有文字。如果沒有說話或只有噪音，請回覆「無語音內容」。"
            
            response = self.model.generate_content([
                prompt,
                audio_file
            ])
            
            text = response.text.strip()
            
            # 清理上傳的檔案
            genai.delete_file(audio_file.name)
            
            # 處理特殊回應
            if "無語音內容" in text or len(text) < 2:
                return None
            
            return text
            
        except Exception as e:
            print(f"語音轉文字錯誤: {e}")
            return None
    
    async def generate_response(self, 
                               user_input: str, 
                               mode: str = 'persona',
                               context: List[Dict] = None) -> Optional[str]:
        """
        生成對話回應
        
        Args:
            user_input: 使用者輸入
            mode: 模式（'system', 'persona', 'daily'）
            context: 上下文記憶列表
        
        Returns:
            AI 回應文字
        """
        try:
            # 取得 System Prompt
            system_prompt = self.system_prompts.get(mode, self.system_prompts['persona'])
            
            # 建立對話歷史
            chat = self.model.start_chat(history=[])
            
            # 如果有上下文，加入提示
            if context and mode == 'persona':
                context_text = "\n".join([
                    f"- {mem['content']}" for mem in context[:5]
                ])
                full_prompt = f"""{system_prompt}

以下是使用者的過往記憶，請參考這些內容來回應：
{context_text}

使用者說：{user_input}

請以使用者的語氣和風格回應："""
            else:
                full_prompt = f"""{system_prompt}

使用者輸入：{user_input}

請回應："""
            
            # 生成回應
            response = chat.send_message(full_prompt)
            return response.text.strip()
            
        except Exception as e:
            print(f"生成回應錯誤: {e}")
            return None
    
    async def generate_daily_question(self) -> Optional[str]:
        """
        生成每日訪談問題
        
        Returns:
            問題文字
        """
        try:
            # 取得最近幾天的記憶作為上下文
            recent_memories = self.db.get_recent_memories(days=7, limit=5)
            
            context_text = ""
            if recent_memories:
                context_text = "\n".join([
                    f"- {mem['content']}" for mem in recent_memories
                ])
                prompt = f"""根據使用者最近的記憶，提出一個新的、有意義的問題：

最近記憶：
{context_text}

請提出一個能夠幫助使用者進一步思考或分享的問題："""
            else:
                prompt = "請提出一個友善的、開放性的問題，幫助使用者開始今天的記錄："
            
            response = self.model.generate_content(prompt)
            question = response.text.strip()
            
            # 清理問題（移除引號等）
            question = question.strip('"').strip("'").strip()
            
            return question
            
        except Exception as e:
            print(f"生成問題錯誤: {e}")
            return None
    
    async def chat_with_rag(self, user_input: str) -> Optional[str]:
        """
        使用 RAG (檢索增強生成) 進行對話
        
        Args:
            user_input: 使用者輸入
        
        Returns:
            AI 回應
        """
        # 從使用者輸入中提取關鍵字進行搜尋
        keywords = self._extract_keywords(user_input)
        
        # 搜尋相關記憶
        context = []
        for keyword in keywords[:3]:  # 最多使用 3 個關鍵字
            results = self.db.search_memories(keyword, limit=3)
            context.extend(results)
        
        # 去重
        seen_ids = set()
        unique_context = []
        for mem in context:
            if mem['id'] not in seen_ids:
                seen_ids.add(mem['id'])
                unique_context.append(mem)
        
        # 如果沒有找到相關記憶，使用最近的記憶
        if not unique_context:
            unique_context = self.db.get_recent_memories(days=7, limit=5)
        
        # 生成回應
        return await self.generate_response(
            user_input,
            mode='persona',
            context=unique_context
        )
    
    def _extract_keywords(self, text: str) -> List[str]:
        """
        從文字中提取關鍵字（簡單實作）
        
        Args:
            text: 輸入文字
        
        Returns:
            關鍵字列表
        """
        # 簡單的關鍵字提取（移除常見停用詞）
        stop_words = {'的', '了', '是', '在', '有', '和', '就', '不', '人', '都', '一', '一個', '上', '也', '很', '到', '說', '要', '去', '你', '會', '著', '沒有', '看', '好', '自己', '這'}
        words = text.split()
        keywords = [w for w in words if len(w) > 1 and w not in stop_words]
        return keywords[:5]  # 最多返回 5 個關鍵字

if __name__ == '__main__':
    # 測試 AI 功能
    print("AI 功能測試")
    
    async def test():
        ai = AI()
        
        # 測試 1: 生成問題
        print("測試 1: 生成每日問題...")
        question = await ai.generate_daily_question()
        if question:
            print(f"問題: {question}")
        else:
            print("生成問題失敗")
        
        # 測試 2: 生成回應
        print("\n測試 2: 生成對話回應...")
        response = await ai.generate_response("我今天心情很好", mode='persona')
        if response:
            print(f"回應: {response}")
        else:
            print("生成回應失敗")
        
        # 測試 3: RAG 對話
        print("\n測試 3: RAG 對話...")
        rag_response = await ai.chat_with_rag("告訴我關於天氣的事情")
        if rag_response:
            print(f"RAG 回應: {rag_response}")
        else:
            print("RAG 對話失敗")
    
    asyncio.run(test())

