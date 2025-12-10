"""
檔案標準 (Standard):
本檔案負責音訊錄製、播放，以及語音克隆 API 整合。
區分 System Voice (官方導引音) 和 Persona Voice (數位分身音)。
輸入：文字（TTS）、音訊檔案（播放）、錄音控制
輸出：音訊檔案、播放控制

執行方式 (Execution):
- 被 main.py 呼叫進行錄音、播放、TTS 生成
- 獨立測試：python -m modules.audio (會測試錄音和播放功能)

相依性 (Dependencies):
- sounddevice: 音訊錄製與播放
- soundfile: 音訊檔案處理
- requests: HTTP API 呼叫
- asyncio: 非同步處理
- os: 檔案系統操作
- config: 系統配置（API 設定）
"""

import asyncio
import sounddevice as sd
import soundfile as sf
import numpy as np
import requests
import os
import tempfile
from typing import Optional, Callable
import config

class Audio:
    """音訊處理類別"""
    
    def __init__(self):
        """初始化音訊系統"""
        self.sample_rate = config.Config.AUDIO_SAMPLE_RATE
        self.channels = config.Config.AUDIO_CHANNELS
        self.is_recording = False
        self.recording_data = []
        self.recording_stream = None
        
        # 確保系統音效目錄存在
        os.makedirs(config.Config.ASSETS_SYSTEM_PATH, exist_ok=True)
    
    async def record_audio(self, duration: float = None) -> Optional[str]:
        """
        錄製音訊
        
        Args:
            duration: 錄音時長（秒），None 表示手動控制
        
        Returns:
            錄音檔案路徑，失敗返回 None
        """
        if self.is_recording:
            return None
        
        self.is_recording = True
        self.recording_data = []
        temp_path = None
        
        try:
            # 建立臨時檔案
            temp_file = tempfile.NamedTemporaryFile(
                suffix='.wav',
                delete=False
            )
            temp_path = temp_file.name
            temp_file.close()
            
            def callback(indata, frames, time, status):
                """錄音回呼函式"""
                if status:
                    print(f"錄音狀態: {status}")
                if self.is_recording:  # 只在錄音中時才收集資料
                    self.recording_data.append(indata.copy())
            
            # 開始錄音
            stream = sd.InputStream(
                device=config.Config.AUDIO_INPUT_CARD,
                channels=self.channels,
                samplerate=self.sample_rate,
                callback=callback,
                dtype='float32'
            )
            
            with stream:
                if duration:
                    await asyncio.sleep(duration)
                else:
                    # 手動控制：等待 is_recording 變為 False
                    while self.is_recording:
                        await asyncio.sleep(0.1)
            
            # 儲存錄音
            if self.recording_data:
                audio_data = np.concatenate(self.recording_data, axis=0)
                # 確保是單聲道
                if len(audio_data.shape) > 1:
                    audio_data = audio_data[:, 0]
                sf.write(temp_path, audio_data, self.sample_rate)
                return temp_path
            else:
                # 沒有錄到資料，刪除臨時檔案
                if temp_path and os.path.exists(temp_path):
                    os.unlink(temp_path)
                return None
            
        except Exception as e:
            print(f"錄音錯誤: {e}")
            # 發生錯誤時清理臨時檔案
            if temp_path and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except:
                    pass
            return None
        finally:
            self.is_recording = False
            self.recording_data = []
    
    def stop_recording(self):
        """停止錄音"""
        self.is_recording = False
    
    async def play_audio(self, file_path: str):
        """
        播放音訊檔案
        
        Args:
            file_path: 音訊檔案路徑
        """
        try:
            if not os.path.exists(file_path):
                print(f"音訊檔案不存在: {file_path}")
                return
            
            # 讀取音訊檔案
            data, sr = sf.read(file_path)
            
            # 播放
            sd.play(data, sr)
            sd.wait()  # 等待播放完成
            
        except Exception as e:
            print(f"播放錯誤: {e}")
    
    async def play_system_sound(self, filename: str):
        """
        播放系統音效
        
        Args:
            filename: 音效檔名（在 assets/system/ 目錄下）
        """
        file_path = os.path.join(config.Config.ASSETS_SYSTEM_PATH, filename)
        if os.path.exists(file_path):
            await self.play_audio(file_path)
        else:
            print(f"系統音效不存在: {file_path}")
    
    async def upload_audio(self, audio_path: str) -> Optional[str]:
        """
        上傳音訊檔案到語音克隆服務
        
        Args:
            audio_path: 音訊檔案路徑
        
        Returns:
            音訊 URL，失敗返回 None
        """
        try:
            with open(audio_path, 'rb') as f:
                files = {'file': f}
                data = {'api_key': config.Config.VOICE_CLONE_API_KEY}
                
                response = requests.post(
                    config.Config.VOICE_CLONE_UPLOAD_URL,
                    files=files,
                    data=data,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        return result.get('audio_url')
                    else:
                        print(f"上傳失敗: {result}")
                else:
                    print(f"上傳錯誤: HTTP {response.status_code}")
                    
        except Exception as e:
            print(f"上傳音訊錯誤: {e}")
        
        return None
    
    async def clone_voice_sync(self, 
                              text: str, 
                              audio_url: str,
                              voice_type: str = 'system',
                              speed_ratio: float = 1.0,
                              pitch_ratio: float = 1.0,
                              volume_ratio: float = 1.0) -> Optional[str]:
        """
        同步語音克隆（生成語音）
        
        Args:
            text: 要合成的文字
            audio_url: 參考音訊 URL
            voice_type: 'system' 或 'persona'
            speed_ratio: 語速比例
            pitch_ratio: 音調比例
            volume_ratio: 音量比例
        
        Returns:
            生成的音訊 URL，失敗返回 None
        """
        try:
            # 選擇語音 ID
            voice_id = (config.Config.SYSTEM_VOICE_ID if voice_type == 'system' 
                       else config.Config.PERSONA_VOICE_ID)
            
            if not voice_id:
                # 如果沒有設定語音 ID，使用上傳的 audio_url
                voice_id = audio_url
            
            # 準備請求參數
            data = {
                'audio_url': voice_id if voice_id.startswith('http') else audio_url,
                'text': text,
                'api_key': config.Config.VOICE_CLONE_API_KEY,
                'type': 2,  # 返回 URL
                'speed_ratio': speed_ratio,
                'pitch_ratio': pitch_ratio,
                'volume_ratio': volume_ratio
            }
            
            response = requests.post(
                config.Config.VOICE_CLONE_SYNC_URL,
                data=data,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success') or 'audio_url' in result:
                    return result.get('audio_url') or result.get('url')
                else:
                    print(f"語音克隆失敗: {result}")
            else:
                print(f"語音克隆錯誤: HTTP {response.status_code}")
                print(f"回應: {response.text}")
                
        except Exception as e:
            print(f"語音克隆錯誤: {e}")
        
        return None
    
    async def text_to_speech(self, 
                            text: str, 
                            voice_type: str = 'system',
                            play: bool = True) -> Optional[str]:
        """
        文字轉語音（整合上傳和克隆）
        
        Args:
            text: 要合成的文字
            voice_type: 'system' 或 'persona'
            play: 是否立即播放
        
        Returns:
            生成的音訊 URL，失敗返回 None
        """
        # 如果使用預設語音 ID，直接呼叫克隆 API
        voice_id = (config.Config.SYSTEM_VOICE_ID if voice_type == 'system' 
                   else config.Config.PERSONA_VOICE_ID)
        
        if voice_id and not voice_id.startswith('http'):
            # 如果有設定的語音 ID，直接使用
            audio_url = voice_id
        else:
            # 否則需要先上傳參考音訊（這裡簡化處理，實際應該有預設的參考音訊）
            print("警告: 未設定語音 ID，需要先上傳參考音訊")
            return None
        
        # 呼叫語音克隆
        audio_url = await self.clone_voice_sync(text, audio_url, voice_type)
        
        if audio_url and play:
            # 下載並播放
            await self._download_and_play(audio_url)
        
        return audio_url
    
    async def _download_and_play(self, url: str):
        """下載音訊並播放"""
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                # 儲存到臨時檔案
                temp_file = tempfile.NamedTemporaryFile(
                    suffix='.wav',
                    delete=False
                )
                temp_path = temp_file.name
                temp_file.write(response.content)
                temp_file.close()
                
                # 播放
                await self.play_audio(temp_path)
                
                # 清理臨時檔案
                os.unlink(temp_path)
        except Exception as e:
            print(f"下載播放錯誤: {e}")

if __name__ == '__main__':
    # 測試音訊功能
    print("音訊功能測試")
    
    async def test():
        audio = Audio()
        
        # 測試 1: 錄音（3 秒）
        print("測試 1: 錄音 3 秒...")
        recording_path = await audio.record_audio(duration=3.0)
        if recording_path:
            print(f"錄音完成: {recording_path}")
            
            # 測試 2: 播放錄音
            print("測試 2: 播放錄音...")
            await audio.play_audio(recording_path)
            
            # 清理
            if os.path.exists(recording_path):
                os.unlink(recording_path)
        else:
            print("錄音失敗")
        
        # 測試 3: 播放系統音效（如果存在）
        print("測試 3: 播放系統音效...")
        await audio.play_system_sound("thinking_filler.wav")
    
    asyncio.run(test())

