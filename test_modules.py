"""
測試腳本：用於測試各個模組的功能

執行方式：
python test_modules.py [module_name]

可選的模組名稱：
- config: 測試配置載入
- database: 測試資料庫功能
- display: 測試 OLED 顯示
- audio: 測試音訊功能
- ai: 測試 AI 功能
- all: 測試所有模組（不包含需要硬體的模組）
"""

import sys
import asyncio

def test_config():
    """測試配置模組"""
    print("=" * 50)
    print("測試配置模組")
    print("=" * 50)
    import config
    errors = config.Config.validate()
    if errors:
        print("配置錯誤:")
        for error in errors:
            print(f"  - {error}")
        return False
    else:
        print("配置驗證通過！")
        return True

def test_database():
    """測試資料庫模組"""
    print("=" * 50)
    print("測試資料庫模組")
    print("=" * 50)
    try:
        from modules.database import Database
        db = Database()
        
        # 測試新增
        id1 = db.add_memory("測試記憶 1", mode="test")
        print(f"✓ 新增記憶 ID: {id1}")
        
        # 測試查詢
        memories = db.get_memories(limit=5)
        print(f"✓ 查詢到 {len(memories)} 條記憶")
        
        # 測試搜尋
        results = db.search_memories("測試")
        print(f"✓ 搜尋到 {len(results)} 條相關記憶")
        
        return True
    except Exception as e:
        print(f"✗ 測試失敗: {e}")
        return False

def test_display():
    """測試顯示模組"""
    print("=" * 50)
    print("測試顯示模組（需要 OLED 硬體）")
    print("=" * 50)
    try:
        from modules.display import Display
        display = Display()
        
        print("顯示測試文字...")
        display.show_text("測試中...", 0, 0)
        import time
        time.sleep(2)
        
        display.show_centered("測試完成")
        time.sleep(2)
        
        display.clear()
        print("✓ 顯示測試完成")
        return True
    except Exception as e:
        print(f"✗ 測試失敗: {e}")
        print("  請確認 OLED 顯示器已正確連接")
        return False

async def test_audio():
    """測試音訊模組"""
    print("=" * 50)
    print("測試音訊模組（需要音訊硬體）")
    print("=" * 50)
    try:
        from modules.audio import Audio
        audio = Audio()
        
        print("測試錄音（3 秒）...")
        recording_path = await audio.record_audio(duration=3.0)
        
        if recording_path:
            print(f"✓ 錄音完成: {recording_path}")
            print("播放錄音...")
            await audio.play_audio(recording_path)
            print("✓ 播放完成")
            
            # 清理
            import os
            if os.path.exists(recording_path):
                os.unlink(recording_path)
        else:
            print("✗ 錄音失敗")
            return False
        
        return True
    except Exception as e:
        print(f"✗ 測試失敗: {e}")
        print("  請確認音訊硬體已正確連接")
        return False

async def test_ai():
    """測試 AI 模組"""
    print("=" * 50)
    print("測試 AI 模組（需要 API 金鑰）")
    print("=" * 50)
    try:
        from modules.ai import AI
        ai = AI()
        
        print("測試生成問題...")
        question = await ai.generate_daily_question()
        if question:
            print(f"✓ 生成問題: {question}")
        else:
            print("✗ 生成問題失敗")
            return False
        
        print("\n測試生成回應...")
        response = await ai.generate_response("你好", mode='persona')
        if response:
            print(f"✓ 生成回應: {response}")
        else:
            print("✗ 生成回應失敗")
            return False
        
        return True
    except Exception as e:
        print(f"✗ 測試失敗: {e}")
        print("  請確認 GEMINI_KEY 已正確設定")
        return False

async def test_all():
    """測試所有模組（不包含需要硬體的）"""
    print("=" * 50)
    print("測試所有模組")
    print("=" * 50)
    
    results = []
    
    # 測試配置
    results.append(("配置", test_config()))
    
    # 測試資料庫
    results.append(("資料庫", test_database()))
    
    # 測試 AI（需要 API 金鑰）
    try:
        results.append(("AI", await test_ai()))
    except:
        results.append(("AI", False))
    
    # 顯示結果
    print("\n" + "=" * 50)
    print("測試結果摘要")
    print("=" * 50)
    for name, result in results:
        status = "✓ 通過" if result else "✗ 失敗"
        print(f"{name}: {status}")
    
    all_passed = all(result for _, result in results)
    return all_passed

async def main():
    """主函式"""
    if len(sys.argv) > 1:
        module = sys.argv[1].lower()
        
        if module == "config":
            success = test_config()
        elif module == "database":
            success = test_database()
        elif module == "display":
            success = test_display()
        elif module == "audio":
            success = await test_audio()
        elif module == "ai":
            success = await test_ai()
        elif module == "all":
            success = await test_all()
        else:
            print(f"未知的模組: {module}")
            print("可用的模組: config, database, display, audio, ai, all")
            success = False
    else:
        print("請指定要測試的模組")
        print("用法: python test_modules.py [module_name]")
        print("可用的模組: config, database, display, audio, ai, all")
        success = False
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    asyncio.run(main())

