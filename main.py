"""
檔案標準 (Standard):
本檔案是系統的主程式入口，實作 Asyncio 非同步狀態機。
管理四種模式：MODE_DAILY (每日訪談)、MODE_CHAT (聊天)、MODE_DIARY (日記)、MODE_REMINDER (提醒)。
協調所有模組（硬體、顯示、音訊、AI、資料庫）的運作。

執行方式 (Execution):
- 主程式：python main.py
- 需要先設定 .env 檔案中的 API 金鑰
- 需要確保硬體正確連接

相依性 (Dependencies):
- asyncio: 非同步架構
- config: 系統配置
- modules.hardware: 硬體控制
- modules.display: OLED 顯示
- modules.audio: 音訊處理
- modules.ai: AI 處理
- modules.database: 資料庫
"""

import asyncio
import sys
from datetime import datetime, timedelta
from typing import Optional
import config
from modules.hardware import Hardware
from modules.display import Display
from modules.audio import Audio
from modules.ai import AI
from modules.database import Database

class EchoMemo:
    """主系統類別（狀態機）"""
    
    def __init__(self):
        """初始化系統"""
        # 驗證配置
        errors = config.Config.validate()
        if errors:
            print("配置錯誤:")
            for error in errors:
                print(f"  - {error}")
            print("\n請檢查 .env 檔案設定")
            sys.exit(1)
        
        # 初始化模組
        self.hw = Hardware()
        self.display = Display()
        self.audio = Audio()
        self.ai = AI()
        self.db = Database()
        
        # 狀態機變數
        self.current_mode = config.Config.MODE_DAILY
        self.modes = [
            config.Config.MODE_DAILY,
            config.Config.MODE_CHAT,
            config.Config.MODE_DIARY,
            config.Config.MODE_REMINDER
        ]
        self.mode_index = 0
        
        # 錄音狀態
        self.is_recording = False
        self.recording_task: Optional[asyncio.Task] = None
        
        # 提醒模式
        self.reminder_task: Optional[asyncio.Task] = None
        self.reminder_active = False
        
        # 日記模式
        self.diary_date_index = 0
        self.diary_dates = []
        
        # 設定硬體事件回呼
        self._setup_hardware_callbacks()
    
    def _setup_hardware_callbacks(self):
        """設定硬體事件回呼"""
        # 旋轉編碼器旋轉：切換模式
        self.hw.on_rotary_rotate = self._on_mode_change
        
        # 編碼器按鈕：確認選擇
        self.hw.on_rotary_press = self._on_mode_confirm
        
        # 錄音按鈕：開始/停止錄音
        self.hw.on_record_press = self._on_record_start
        self.hw.on_record_release = self._on_record_stop
    
    async def _on_mode_change(self, delta: int):
        """處理模式切換"""
        if self.current_mode == config.Config.MODE_DIARY:
            # 日記模式：切換日期
            await self._change_diary_date(delta)
        else:
            # 其他模式：切換模式
            self.mode_index = (self.mode_index + delta) % len(self.modes)
            new_mode = self.modes[self.mode_index]
            self.display.show_mode(new_mode, "按鈕確認")
    
    async def _on_mode_confirm(self):
        """確認模式選擇"""
        self.current_mode = self.modes[self.mode_index]
        self.display.show_mode(self.current_mode, "已選擇")
        await asyncio.sleep(1)
        await self._enter_mode(self.current_mode)
    
    async def _on_record_start(self):
        """開始錄音"""
        if not self.is_recording:
            self.is_recording = True
            self.last_recording_path = None
            self.display.show_text("錄音中...", 0, 0)
            self.recording_task = asyncio.create_task(
                self._record_audio_wrapper()
            )
    
    async def _record_audio_wrapper(self):
        """錄音包裝函式，保存錄音檔案路徑"""
        self.last_recording_path = await self.audio.record_audio()
    
    async def _on_record_stop(self):
        """停止錄音"""
        if self.is_recording:
            self.is_recording = False
            self.audio.stop_recording()
            if self.recording_task:
                await self.recording_task
                self.recording_task = None
            
            # 根據模式處理錄音
            await self._process_recording()
    
    async def _enter_mode(self, mode: str):
        """進入模式"""
        if mode == config.Config.MODE_DAILY:
            await self._mode_daily_entry()
        elif mode == config.Config.MODE_CHAT:
            await self._mode_chat_entry()
        elif mode == config.Config.MODE_DIARY:
            await self._mode_diary_entry()
        elif mode == config.Config.MODE_REMINDER:
            await self._mode_reminder_entry()
    
    async def _mode_daily_entry(self):
        """每日訪談模式：進入"""
        self.display.show_text("構思問題...", 0, 0)
        
        # 播放思考音效
        await self.audio.play_system_sound("thinking_filler.wav")
        
        # 生成問題
        question = await self.ai.generate_daily_question()
        if question:
            self.display.show_multiline(["每日訪談", question])
            
            # 使用系統音生成語音
            audio_url = await self.audio.text_to_speech(
                question,
                voice_type='system',
                play=True
            )
        else:
            self.display.show_text("生成問題失敗", 0, 0)
    
    async def _mode_daily_loop(self):
        """每日訪談模式：循環"""
        # 等待錄音（已在硬體回呼中處理）
        pass
    
    async def _process_recording(self):
        """處理錄音結果"""
        if not self.last_recording_path:
            self.display.show_text("錄音失敗", 0, 0)
            await asyncio.sleep(1)
            return
        
        self.display.show_text("處理中...", 0, 0)
        
        # 根據模式處理錄音
        if self.current_mode == config.Config.MODE_DAILY:
            await self._process_daily_recording()
        elif self.current_mode == config.Config.MODE_CHAT:
            await self._process_chat_recording()
    
    async def _process_daily_recording(self):
        """處理每日訪談錄音"""
        # 語音轉文字
        text = await self.ai.speech_to_text(self.last_recording_path)
        
        if text:
            # 儲存到資料庫
            memory_id = self.db.add_memory(
                content=text,
                mode=config.Config.MODE_DAILY
            )
            self.display.show_multiline(["已記錄", f"ID: {memory_id}"])
            
            # 播放確認音效
            await self.audio.play_system_sound("thinking_filler.wav")
        else:
            self.display.show_text("無法識別", 0, 0)
        
        await asyncio.sleep(2)
        
        # 清理錄音檔案
        if self.last_recording_path:
            import os
            try:
                os.unlink(self.last_recording_path)
            except:
                pass
        self.last_recording_path = None
    
    async def _process_chat_recording(self):
        """處理聊天錄音"""
        # 語音轉文字
        text = await self.ai.speech_to_text(self.last_recording_path)
        
        if text:
            # 儲存使用者輸入
            self.db.add_memory(
                content=f"使用者: {text}",
                mode=config.Config.MODE_CHAT
            )
            
            # 使用 RAG 生成回應
            self.display.show_text("思考中...", 0, 0)
            response = await self.ai.chat_with_rag(text)
            
            if response:
                # 儲存 AI 回應
                self.db.add_memory(
                    content=f"AI: {response}",
                    mode=config.Config.MODE_CHAT
                )
                
                # 使用分身音播放回應
                self.display.show_multiline(["回應", response[:20] + "..."])
                await self.audio.text_to_speech(
                    response,
                    voice_type='persona',
                    play=True
                )
            else:
                self.display.show_text("生成失敗", 0, 0)
        else:
            self.display.show_text("無法識別", 0, 0)
        
        await asyncio.sleep(1)
        
        # 清理錄音檔案
        if self.last_recording_path:
            import os
            try:
                os.unlink(self.last_recording_path)
            except:
                pass
        self.last_recording_path = None
    
    async def _mode_chat_entry(self):
        """聊天模式：進入"""
        self.display.show_multiline(["聊天模式", "等待錄音..."])
    
    async def _mode_chat_loop(self):
        """聊天模式：循環"""
        # 等待錄音（已在硬體回呼中處理）
        pass
    
    async def _mode_diary_entry(self):
        """日記模式：進入"""
        # 載入可用日期
        self._load_diary_dates()
        self.diary_date_index = 0
        await self._update_diary_display()
    
    async def _mode_diary_loop(self):
        """日記模式：循環"""
        # 等待編碼器旋轉或按鈕按下（已在硬體回呼中處理）
        pass
    
    async def _change_diary_date(self, delta: int):
        """切換日記日期"""
        if self.diary_dates:
            self.diary_date_index = (
                self.diary_date_index + delta
            ) % len(self.diary_dates)
            await self._update_diary_display()
    
    async def _update_diary_display(self):
        """更新日記顯示"""
        if self.diary_dates:
            date = self.diary_dates[self.diary_date_index]
            memories = self.db.get_memory_by_date(date)
            count = len(memories)
            self.display.show_multiline([
                "日記回顧",
                date,
                f"{count} 條記錄"
            ])
    
    async def _mode_reminder_entry(self):
        """提醒模式：進入"""
        self.display.show_multiline(["提醒模式", "按鈕啟動"])
    
    async def _mode_reminder_loop(self):
        """提醒模式：循環"""
        # 等待按鈕（已在硬體回呼中處理）
        pass
    
    def _load_diary_dates(self):
        """載入日記可用日期"""
        # 取得最近 30 天的記憶
        memories = self.db.get_memories(limit=100)
        dates = set()
        for mem in memories:
            if mem.get('timestamp'):
                date = mem['timestamp'][:10]  # YYYY-MM-DD
                dates.add(date)
        self.diary_dates = sorted(list(dates), reverse=True)
    
    async def run(self):
        """主運行循環"""
        try:
            # 設定硬體事件循環（用於處理執行緒安全的事件）
            self.hw.set_event_loop(asyncio.get_event_loop())
            
            # 初始化顯示
            self.display.show_text("EchoMemo", 0, 0)
            await asyncio.sleep(1)
            
            # 進入初始模式
            await self._enter_mode(self.current_mode)
            
            # 主循環
            while True:
                # 處理硬體事件佇列（執行緒安全）
                await self.hw.process_events()
                
                await asyncio.sleep(0.05)  # 減少延遲以提高響應性
                
                # 根據當前模式執行循環邏輯
                if self.current_mode == config.Config.MODE_DAILY:
                    await self._mode_daily_loop()
                elif self.current_mode == config.Config.MODE_CHAT:
                    await self._mode_chat_loop()
                elif self.current_mode == config.Config.MODE_DIARY:
                    await self._mode_diary_loop()
                elif self.current_mode == config.Config.MODE_REMINDER:
                    await self._mode_reminder_loop()
        
        except KeyboardInterrupt:
            print("\n系統關閉中...")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """清理資源"""
        self.display.clear()
        self.hw.cleanup()

async def main():
    """主函式"""
    system = EchoMemo()
    await system.run()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n程式結束")

