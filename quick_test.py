"""
Quick diagnostic script for smartwatch import issues
"""
import sys
sys.path.insert(0, '.')

print("=" * 60)
print("血壓管理系統 - 快速診斷")
print("=" * 60)
print()

# Test 1: Check BPReading
print("測試 1: BPReading 結構")
print("-" * 60)
try:
    from ich_bp_agent.analyzers.stability_analyzer import BPReading
    from datetime import datetime
    from dataclasses import fields

    # Check if source field exists
    field_names = [f.name for f in fields(BPReading)]
    print(f"BPReading 欄位: {', '.join(field_names)}")

    if 'source' in field_names:
        print("✅ source 欄位存在")

        # Try creating with default
        reading = BPReading(
            timestamp=datetime.now(),
            systolic=120,
            diastolic=80,
            patient_id="test"
        )
        print(f"✅ 預設 source 值: '{reading.source}'")
    else:
        print("❌ source 欄位不存在")

except Exception as e:
    print(f"❌ 錯誤: {e}")
    import traceback
    traceback.print_exc()
print()

# Test 2: Check smartwatch_import module
print("測試 2: smartwatch_import 模塊")
print("-" * 60)
try:
    from ich_bp_agent.utils.smartwatch_import import (
        parse_smartwatch_json,
        convert_to_bp_readings,
        merge_readings,
        import_smartwatch_file
    )
    print("✅ 所有函數導入成功")
    print("  - parse_smartwatch_json")
    print("  - convert_to_bp_readings")
    print("  - merge_readings")
    print("  - import_smartwatch_file")
except Exception as e:
    print(f"❌ 錯誤: {e}")
    import traceback
    traceback.print_exc()
print()

# Test 3: Test with sample data
print("測試 3: 範例資料匯入")
print("-" * 60)
try:
    import json
    from ich_bp_agent.utils.smartwatch_import import import_smartwatch_file

    # Check if sample file exists
    import os
    sample_file = "sample_smartwatch_data.json"
    if os.path.exists(sample_file):
        print(f"✅ 找到範例檔案: {sample_file}")

        with open(sample_file, 'r', encoding='utf-8') as f:
            file_content = f.read()
            data = json.loads(file_content)

        print(f"  - 血壓記錄: {len(data.get('bp', []))} 筆")
        print(f"  - 心率記錄: {len(data.get('hb', []))} 筆")
        print(f"  - 血氧記錄: {len(data.get('spo2', []))} 筆")

        # Try import
        merged_readings, stats = import_smartwatch_file(
            file_content,
            [],  # Empty existing readings
            "test_patient"
        )

        print(f"✅ 匯入成功:")
        print(f"  - 總記錄: {stats['total_records']}")
        print(f"  - 新增: {stats['new_records_added']}")
        print(f"  - 無效: {stats['invalid_records']}")

    else:
        print(f"⚠️ 範例檔案不存在: {sample_file}")

except Exception as e:
    print(f"❌ 錯誤: {e}")
    import traceback
    traceback.print_exc()
print()

# Test 4: Check app.py imports
print("測試 4: app.py 導入")
print("-" * 60)
try:
    from ich_bp_agent.ui import app
    print("✅ app.py 導入成功")

    # Check if main function exists
    if hasattr(app, 'main'):
        print("✅ main() 函數存在")
    else:
        print("❌ main() 函數不存在")

except Exception as e:
    print(f"❌ 錯誤: {e}")
    import traceback
    traceback.print_exc()
print()

print("=" * 60)
print("診斷完成")
print("=" * 60)
print()
print("如果所有測試都通過，問題可能在於:")
print("1. Streamlit 快取 - 嘗試重新啟動")
print("2. 瀏覽器快取 - 嘗試 Ctrl+F5")
print("3. Streamlit Cloud 版本 - 嘗試 Reboot app")
print()
print("如果有測試失敗，請將完整輸出發送給開發者。")
