# ICH 血壓管理 SMART on FHIR 應用程式

腦出血 (Intracerebral Hemorrhage, ICH) 患者的血壓藥物調整管理系統

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://streamlit.io/)

## 功能特色

- **血壓監測儀表板** - 即時顯示血壓趨勢與統計
- **穩定度評分系統** - 0-100 分的客觀評估指標
- **調藥建議引擎** - 基於臨床證據的減量/維持/回診建議
- **安全護欄機制** - 防止危險的藥物調整
- **SMART on FHIR 整合** - 符合醫療資訊標準

## 部署到 Streamlit Cloud

### Step 1: Fork 或上傳到 GitHub

確保你的 Repository 包含以下結構：

```
your-repo/
├── .gitignore
├── .streamlit/
│   └── config.toml
├── requirements.txt
├── README.md
└── ich_bp_agent/
    ├── __init__.py
    ├── config.py
    ├── models/
    ├── analyzers/
    ├── safety/
    ├── ui/
    │   ├── app.py          ← 主程式
    │   └── components/
    └── data/samples/
```

### Step 2: 部署到 Streamlit Cloud

1. 前往 [share.streamlit.io](https://share.streamlit.io/)
2. 用 GitHub 帳號登入
3. 點選 **New app**
4. 填入：
   - **Repository**: 選擇你的 repo
   - **Branch**: `main`
   - **Main file path**: `ich_bp_agent/ui/app.py`
5. 點選 **Deploy**

等待 2-3 分鐘，你的 App 就上線了！

## 本地執行

```bash
# 安裝依賴
pip install -r requirements.txt

# 啟動應用程式
streamlit run ich_bp_agent/ui/app.py
```

然後開啟瀏覽器訪問 http://localhost:8501

## 支援藥物

| 藥物名稱 | 成分 | 類型 | 可用劑量 |
|----------|------|------|----------|
| Norvasc (脈優) | Amlodipine | CCB | 2.5mg, 5mg, 10mg |
| Exforge (易安穩) | Valsartan + Amlodipine | ARB+CCB | 80/5mg, 160/5mg, 160/10mg |

## 穩定度評分

| 項目 | 權重 | 說明 |
|------|------|------|
| 目標達成率 | 40 分 | 14 天內血壓在目標範圍的比例 |
| 變異係數 (CV) | 30 分 | CV < 10% 滿分 |
| 低血壓安全 | 20 分 | 每次低血壓事件扣分 |
| 趨勢穩定 | 10 分 | 穩定或改善得滿分 |

### 分數解讀

| 分數 | 分類 | 建議 |
|------|------|------|
| ≥ 80 | 優良 | 可考慮減量 |
| 60-79 | 良好 | 建議維持 |
| 40-59 | 普通 | 建議回診 |
| < 40 | 需注意 | 需緊急評估 |

## SMART on FHIR 整合

### 衛服部 SMART Sandbox 設定

部署後，在衛服部註冊你的應用程式：

| 欄位 | 值 |
|------|-----|
| Launch URL | `https://你的app.streamlit.app/` |
| Redirect URI | `https://你的app.streamlit.app/` |
| Scopes | `launch openid fhirUser patient/Patient.read patient/Observation.read patient/Observation.write` |

## 安全注意事項

- 本系統僅供參考，調藥建議需經醫師確認
- 急性期 (< 2 週) 禁止減量建議
- 出現高血壓危象 (SBP > 180) 或嚴重低血壓 (SBP < 80) 會觸發緊急警報

## 技術規格

- Python 3.9+
- Streamlit 1.29+
- Plotly (圖表)
- Pydantic (資料驗證)

## 授權

本軟體僅供研究與教育用途。在臨床使用前，請確保符合當地法規要求。
