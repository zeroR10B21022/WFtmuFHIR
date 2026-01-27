# ICH 血壓管理 SMART on FHIR 應用程式 - 專案狀態

## 專案概述

這是一個用於腦出血 (ICH) 患者血壓管理的 SMART on FHIR 應用程式，使用 Python + Streamlit 開發。

## 目前進度

### 已完成 ✅

1. **核心模組開發完成**
   - `models/` - 資料模型 (Patient, Medication, Stability)
   - `analyzers/` - 穩定度分析器、調藥建議引擎
   - `safety/` - 安全護欄機制
   - `auth/` - SMART on FHIR OAuth 客戶端
   - `ui/` - Streamlit 介面

2. **穩定度評分演算法**
   - 目標達成率 (40分)
   - 變異係數 CV (30分)
   - 低血壓安全 (20分)
   - 趨勢穩定 (10分)

3. **支援藥物**
   - Norvasc (Amlodipine): 2.5mg, 5mg, 10mg
   - Exforge (Valsartan/Amlodipine): 80/5mg, 160/5mg, 160/10mg

4. **測試通過**
   - `tests/test_stability_analyzer.py` - 7 個測試全部通過

5. **部署準備**
   - 已準備好 Streamlit Cloud 部署結構
   - 包含 requirements.txt, .streamlit/config.toml

### 待完成 🔲

1. **上傳到 GitHub** - 將此資料夾上傳到 GitHub Repository
2. **部署到 Streamlit Cloud** - 在 share.streamlit.io 部署
3. **衛服部 SMART Sandbox 註冊** - 取得 Client ID
4. **整合測試** - 與真實 FHIR 伺服器測試

## 重要檔案位置

| 檔案 | 說明 |
|------|------|
| `ich_bp_agent/ui/app.py` | Streamlit 主程式 (部署時指向這個) |
| `ich_bp_agent/analyzers/stability_analyzer.py` | 穩定度計算核心邏輯 |
| `ich_bp_agent/analyzers/medication_advisor.py` | 調藥建議引擎 |
| `ich_bp_agent/safety/guardrails.py` | 安全護欄 |
| `ich_bp_agent/config.py` | 設定參數 |
| `requirements.txt` | Python 依賴套件 |

## 本地執行方式

```bash
# 安裝依賴
pip install -r requirements.txt

# 啟動應用程式
streamlit run ich_bp_agent/ui/app.py
```

瀏覽器開啟 http://localhost:8501

## 部署到 Streamlit Cloud

1. 上傳到 GitHub
2. 前往 https://share.streamlit.io/
3. New app → 選擇 repo → Main file: `ich_bp_agent/ui/app.py`
4. Deploy

## 已知問題與修復

1. **時區問題** - `stability_analyzer.py:82` 已修復 offset-naive/aware datetime 比較問題
2. **模組匯入** - `models/__init__.py` 已加入 `TrendDirection`, `SafetyLevel` 匯出

## 技術棧

- Python 3.9+
- Streamlit 1.29+
- Plotly (圖表)
- Pydantic (資料驗證)
- FHIR R4 標準

## 聯絡

如有問題，請參考 README.md 或詢問 Claude Code。
