# ICH 血壓管理 SMART on FHIR 應用程式

腦出血 (Intracerebral Hemorrhage, ICH) 患者的血壓藥物調整管理系統

## 功能概述

本應用程式專為 ICH 後血壓管理設計，提供：

- **血壓監測儀表板** - 即時顯示血壓趨勢與統計
- **穩定度評分系統** - 0-100 分的客觀評估指標
- **調藥建議引擎** - 基於臨床證據的減量/維持/回診建議
- **安全護欄機制** - 防止危險的藥物調整
- **SMART on FHIR 整合** - 符合醫療資訊標準

## 快速開始

### 1. 安裝依賴套件

```bash
cd ich_bp_agent
pip install -r requirements.txt
```

### 2. 啟動應用程式

```bash
# 方法一：使用啟動腳本
python ../run_ich_app.py

# 方法二：直接啟動 Streamlit
streamlit run ui/app.py
```

### 3. 開啟瀏覽器

應用程式會在 http://localhost:8501 啟動

## 使用說明

### Demo 模式

1. 在登入頁面選擇「Demo 模式」
2. 系統會載入模擬的 ICH 患者資料
3. 可以體驗完整功能，包括：
   - 血壓趨勢圖
   - 穩定度分數儀表
   - 調藥建議卡片
   - 血壓輸入表單

### SMART on FHIR 模式

1. 需要先在衛服部 SMART Sandbox 註冊應用程式
2. 設定環境變數（見下方設定說明）
3. 選擇「SMART on FHIR 登入」進行 OAuth 認證

## 支援藥物

| 藥物名稱 | 成分 | 類型 | 可用劑量 |
|----------|------|------|----------|
| Norvasc (脈優) | Amlodipine | CCB | 2.5mg, 5mg, 10mg |
| Exforge (易安穩) | Valsartan + Amlodipine | ARB+CCB | 80/5mg, 160/5mg, 160/10mg |

### 減量順序

- **Norvasc**: 10mg → 5mg → 2.5mg
- **Exforge**: 160/10mg → 160/5mg → 80/5mg

## 穩定度分數演算法

總分 100 分，由四個面向組成：

| 項目 | 權重 | 說明 |
|------|------|------|
| 目標達成率 | 40 分 | 14 天內血壓在目標範圍的比例 |
| 變異係數 (CV) | 30 分 | CV < 10% 滿分，CV > 20% 零分 |
| 低血壓安全 | 20 分 | 每次低血壓事件扣分 |
| 趨勢穩定 | 10 分 | 血壓趨勢穩定或改善得分 |

### 分數解讀

| 分數範圍 | 分類 | 建議行動 |
|----------|------|----------|
| ≥ 80 | 優良 | 可考慮減量 |
| 60-79 | 良好 | 建議維持 |
| 40-59 | 普通 | 建議回診評估 |
| < 40 | 需注意 | 需緊急評估 |

## 減量資格條件

必須同時滿足以下所有條件：

1. 穩定度分數 ≥ 80
2. 連續達標天數 ≥ 14 天
3. 過去 7 天無低血壓事件
4. 變異係數 < 15%
5. ICH 階段為「穩定期」（發病 > 12 週）

## 安全護欄規則

| 情境 | 動作 | 說明 |
|------|------|------|
| 急性期 (< 2 週) | 阻擋 | 禁止任何減量建議 |
| 亞急性期 (2-12 週) | 警告 | 減量需特別謹慎 |
| 7 天內有低血壓 | 阻擋 | 需醫師確認後才能減量 |
| SBP > 180 或 DBP > 120 | 緊急警報 | 高血壓危象 |
| SBP < 80 | 緊急警報 | 嚴重低血壓 |

## 環境設定

建立 `.env` 檔案：

```env
# SMART on FHIR 設定
SMART_CLIENT_ID=your_client_id
SMART_FHIR_BASE_URL=https://fhir.mohw.gov.tw/fhir/R4

# 應用程式設定
APP_SECRET_KEY=your_secret_key
APP_REDIRECT_URI=http://localhost:8501/callback
```

## 專案結構

```
ich_bp_agent/
├── __init__.py              # 模組入口
├── config.py                # 設定檔
├── requirements.txt         # 依賴套件
├── README.md               # 本文件
│
├── models/                  # 資料模型
│   ├── patient.py          # ICH 患者模型
│   ├── medication.py       # 藥物模型
│   └── stability.py        # 穩定度評分模型
│
├── auth/                    # 認證模組
│   └── smart_client.py     # SMART on FHIR OAuth 客戶端
│
├── analyzers/               # 分析引擎
│   ├── stability_analyzer.py   # 穩定度計算
│   └── medication_advisor.py   # 調藥建議
│
├── safety/                  # 安全機制
│   └── guardrails.py       # 安全護欄
│
├── agents/                  # 代理程式
│   └── ich_agent.py        # 主要協調器
│
├── ui/                      # 使用者介面
│   ├── app.py              # Streamlit 主程式
│   └── components/         # UI 元件
│       ├── bp_chart.py     # 血壓趨勢圖
│       ├── stability_gauge.py  # 穩定度儀表
│       └── recommendation_card.py  # 建議卡片
│
├── data/samples/            # 範例資料
│   ├── ich_patient_bundle.json  # 患者 FHIR Bundle
│   └── bp_observations.json     # 血壓觀察值
│
└── tests/                   # 測試
    └── test_stability_analyzer.py
```

## 執行測試

```bash
# 執行穩定度分析器測試
python -m ich_bp_agent.tests.test_stability_analyzer

# 或直接執行
python ich_bp_agent/tests/test_stability_analyzer.py
```

## 技術規格

### FHIR 資源類型

- `Patient` - 患者基本資料
- `Observation` - 血壓測量值 (LOINC: 85354-9)
- `Condition` - ICH 診斷 (ICD-10: I61.x)
- `MedicationRequest` - 藥物處方

### LOINC 代碼

| 代碼 | 說明 |
|------|------|
| 85354-9 | Blood pressure panel |
| 8480-6 | Systolic blood pressure |
| 8462-4 | Diastolic blood pressure |

### ICH 階段定義

| 階段 | 時間範圍 | 說明 |
|------|----------|------|
| ACUTE | 0-14 天 | 急性期，禁止減量 |
| SUBACUTE | 14-84 天 | 亞急性期，減量需謹慎 |
| STABLE | > 84 天 | 穩定期，可考慮減量 |

## 注意事項

1. **本系統僅供參考** - 所有調藥建議需經醫師確認
2. **需要充足資料** - 建議至少 14 天、每日兩次的血壓記錄
3. **定期回診** - 即使血壓穩定，仍建議定期回診評估
4. **緊急狀況** - 若出現緊急警報，請立即就醫

## 授權與免責聲明

本軟體僅供研究與教育用途。在臨床使用前，請確保符合當地法規要求，並經過適當的臨床驗證。

所有醫療決策應由具有執照的醫療專業人員做出。本軟體的建議不能取代專業醫療意見。

## 聯絡資訊

如有問題或建議，請聯繫開發團隊。

---

*最後更新：2026-01-27*
