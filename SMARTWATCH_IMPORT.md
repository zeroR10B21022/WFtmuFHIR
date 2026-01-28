# 智慧手錶資料匯入功能

## 新增功能 (2025-01-28)

現在可以從智慧手錶 JSON 檔案批次匯入血壓資料！

## 使用方法

### 1. 啟動應用程式

```bash
cd ich_bp_agent_github
streamlit run streamlit_app.py
```

或使用快捷批次檔：

```bash
start_ich_app.bat
```

### 2. 登入並選擇患者

- 選擇登入方式（SMART on FHIR 或 Direct FHIR 或 Demo 模式）
- 選擇或建立患者

### 3. 匯入智慧手錶資料

在主頁面中：

1. 滾動到「📝 輸入血壓」區塊下方
2. 找到「📱 匯入智慧手錶資料」區塊
3. 點擊「上傳 JSON 檔案」按鈕
4. 選擇您的 JSON 檔案（例如: `records.json`）
5. 系統會自動處理並顯示匯入統計

### 4. 查看結果

- 儀表板會自動更新
- 血壓趨勢圖會包含新匯入的資料
- 歷史紀錄會顯示所有資料（包含來源標記）

## 支援的資料格式

### JSON 結構

```json
{
  "bp": [
    {
      "time": "2024-10-16 10:15:00",
      "sys": 130,
      "dia": 92
    },
    {
      "time": "2024-10-16 10:30:00",
      "sys": 132,
      "dia": 92
    }
  ],
  "hb": [
    {
      "time": "2024-10-16 10:04:00",
      "heartrate": 95
    }
  ],
  "spo2": [
    {
      "time": "2024-10-16 10:11:00",
      "spo2": 86
    }
  ]
}
```

### 必需欄位

- `bp`: 血壓資料陣列（**必需**）
  - `time`: 測量時間（格式: "YYYY-MM-DD HH:MM:SS"）
  - `sys`: 收縮壓（mmHg）
  - `dia`: 舒張壓（mmHg）

### 選用欄位

- `hb`: 心率資料（目前不會匯入，僅用於統計顯示）
- `spo2`: 血氧資料（目前不會匯入，僅用於統計顯示）
- `bia`: 身體成分分析（保留供未來使用）

## 功能特點

### ✅ 自動去重
- 系統會根據測量時間自動識別重複記錄
- 重複記錄不會被匯入
- 顯示跳過的重複記錄數量

### ✅ 資料驗證
- 收縮壓範圍: 60-250 mmHg
- 舒張壓範圍: 40-150 mmHg
- 時間格式驗證
- 無效記錄自動跳過

### ✅ 來源標記
- 匯入的資料標記為 `smartwatch`
- 手動輸入標記為 `manual`
- FHIR 資料標記為 `fhir`

### ✅ 批次處理
- 一次可匯入數十甚至數百筆記錄
- 高效的資料合併演算法
- 自動排序（最新記錄在前）

## 技術實作

### 新增模組

#### `ich_bp_agent/utils/smartwatch_import.py`

核心功能模組，包含：

- `parse_smartwatch_json()`: JSON 解析與驗證
- `convert_to_bp_readings()`: 格式轉換
- `merge_readings()`: 資料合併與去重
- `import_smartwatch_file()`: 完整匯入流程

#### `ich_bp_agent/ui/app.py`

UI 整合：

- Streamlit 檔案上傳器
- 匯入統計顯示
- 錯誤處理與使用者回饋

#### `ich_bp_agent/analyzers/stability_analyzer.py`

資料模型更新：

- `BPReading.source` 欄位新增
- 支援標記資料來源

## 範例資料

專案包含範例資料檔案：

- 位置: `DATA/records.json`
- 包含: 2024-10-16 一整天的血壓、心率、血氧資料
- 可用於測試匯入功能

## 故障排除

### 匯入失敗

**可能原因**:
1. JSON 格式錯誤
2. 缺少必需欄位
3. 資料格式不正確
4. 檔案編碼問題

**解決方法**:
1. 使用 JSON 驗證工具檢查格式
2. 確認包含 `bp` 陣列
3. 檢查時間格式和數值範圍
4. 確保檔案使用 UTF-8 編碼

### 部分記錄未匯入

**可能原因**:
1. 記錄重複（時間戳相同）
2. 資料無效（超出合理範圍）
3. 時間格式錯誤

**解決方法**:
- 查看匯入統計中的「無效記錄」數量
- 檢查被跳過的記錄
- 修正資料後重新匯入

### 匯入後看不到資料

**可能原因**:
1. 瀏覽器快取問題
2. 時間範圍篩選
3. 頁面未重新整理

**解決方法**:
1. 重新整理頁面（F5）
2. 檢查時間範圍設定
3. 查看歷史紀錄確認資料已匯入

## 未來計劃

- [ ] 支援 CSV 格式直接匯入
- [ ] 支援心率資料匯入與顯示
- [ ] 支援血氧資料匯入與分析
- [ ] 匯入資料的編輯與刪除功能
- [ ] 匯出功能（將現有資料匯出為 JSON）
- [ ] 多檔案批次匯入
- [ ] 自動偵測智慧手錶品牌與格式

## API 使用範例

如果要在自己的程式中使用匯入功能：

```python
from ich_bp_agent.utils.smartwatch_import import import_smartwatch_file
from ich_bp_agent.analyzers.stability_analyzer import BPReading

# 讀取 JSON 檔案
with open('records.json', 'r', encoding='utf-8') as f:
    file_content = f.read()

# 匯入資料
existing_readings = []  # 現有的 BPReading 物件列表
patient_id = "patient123"

merged_readings, stats = import_smartwatch_file(
    file_content,
    existing_readings,
    patient_id
)

# 查看統計
print(f"成功匯入 {stats['new_records_added']} 筆記錄")
print(f"跳過 {stats['duplicates_skipped']} 筆重複記錄")
print(f"無效記錄: {stats['invalid_records']} 筆")

# 使用合併後的資料
for reading in merged_readings:
    print(f"{reading.timestamp}: {reading.systolic}/{reading.diastolic} ({reading.source})")
```

## 相關文件

- [IMPORT_GUIDE.md](../BP-Traffic-Light-HTML/IMPORT_GUIDE.md) - HTML 版本匯入指南
- [README.md](README.md) - 主要專案說明
- [FIXED_LAUNCH_ISSUE.md](FIXED_LAUNCH_ISSUE.md) - OAuth 修復文件

## 技術支援

如有問題或建議，請聯繫：

- Email: 114346@w.tmu.edu.tw
- GitHub Issues: https://github.com/zeroR10B21022/WFtmuFHIR/issues

---

**版本**: 1.0.0
**最後更新**: 2025-01-28
**作者**: 萬芳醫院腦神經外科 鄔雨銘醫師
