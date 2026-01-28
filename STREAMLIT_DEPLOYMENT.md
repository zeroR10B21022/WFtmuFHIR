# Streamlit Cloud 部署指南

## 📦 已完成推送到 GitHub

✅ 智慧手錶匯入功能已成功推送到 GitHub
- Repository: https://github.com/zeroR10B21022/WFtmuFHIR
- Branch: `traffic-light-system`
- Commit: Add smartwatch data import functionality

## 🚀 部署到 Streamlit Cloud

### 方式一：從現有應用更新 (如果已部署)

如果您已經有部署在 Streamlit Cloud：

1. **自動更新**
   - Streamlit Cloud 會自動偵測 GitHub 更新
   - 稍等 1-2 分鐘，應用會自動重新部署
   - 前往 https://wftmufhir.streamlit.app/ 查看

2. **手動重新啟動** (如果沒有自動更新)
   - 前往 https://share.streamlit.io/
   - 登入您的帳號
   - 找到 WFtmuFHIR 應用
   - 點擊右上角「⋮」選單
   - 選擇「Reboot app」

### 方式二：全新部署

如果還沒有部署過：

#### 步驟 1: 登入 Streamlit Cloud

1. 前往 https://share.streamlit.io/
2. 使用 GitHub 帳號登入 (zeroR10B21022)

#### 步驟 2: 建立新應用

1. 點擊「New app」按鈕
2. 填寫應用資訊：
   - **Repository**: `zeroR10B21022/WFtmuFHIR`
   - **Branch**: `traffic-light-system`
   - **Main file path**: `streamlit_app.py`
   - **App URL** (optional): 自訂網址或使用預設

#### 步驟 3: 設定環境變數 (Secrets)

點擊「Advanced settings」→「Secrets」，添加以下內容：

```toml
# Taiwan HAPI FHIR Server (Direct Access - No OAuth)
[direct_fhir]
FHIR_BASE_URL = "https://twcore.hapi.fhir.tw/fhir"

# Taiwan MOHW SMART Sandbox (OAuth - 需要 client_id)
[smart]
SMART_FHIR_BASE_URL = "https://thas.mohw.gov.tw/v/r4/sim/WzIslilslilslkFVVE8iLDAsMCwwLCIiLCIiLCIiLCIiLCIiLCIiLCIiLCIiLDAsMSwill0/fhir"
SMART_CLIENT_ID = "demo_client"
SMART_REDIRECT_URI = "https://wftmufhir.streamlit.app/"

# Application Settings
[app]
APP_TITLE = "ICH 血壓紅黃綠燈系統"
DEBUG_MODE = "false"
```

#### 步驟 4: 部署

1. 點擊「Deploy!」按鈕
2. 等待 2-5 分鐘完成建置
3. 應用會自動開啟

## 📱 測試智慧手錶匯入功能

部署完成後，測試新功能：

1. 前往您的 Streamlit Cloud 網址
2. 選擇登入方式：
   - **推薦**: 「直接連接 FHIR 伺服器 (Taiwan HAPI)」
   - 或使用「Demo 模式」
3. 進入主頁面
4. 滾動到「📱 匯入智慧手錶資料」區塊
5. 上傳 `sample_smartwatch_data.json` 檔案測試
6. 查看匯入統計和儀表板更新

## 🔍 查看部署日誌

如果部署遇到問題：

1. 在 Streamlit Cloud 應用頁面
2. 點擊右下角「Manage app」
3. 查看「Logs」標籤
4. 檢查錯誤訊息

## 常見問題

### Q: 部署失敗，顯示 ModuleNotFoundError

**解決方法**:
- 確認 `requirements.txt` 包含所有依賴
- 目前配置應該沒問題，已包含：
  - streamlit
  - plotly
  - httpx
  - pydantic
  - 等等

### Q: 智慧手錶匯入按鈕找不到

**解決方法**:
- 確認已登入（選擇任一登入方式）
- 確認在主頁面（不是登入頁）
- 滾動到「輸入血壓」區塊下方

### Q: 匯入資料後看不到

**解決方法**:
- 檢查匯入統計是否顯示成功
- 重新整理頁面
- 查看歷史紀錄確認資料

### Q: FHIR 連接失敗

**解決方法**:
- Taiwan HAPI 伺服器可能暫時維護
- 改用「Demo 模式」測試
- 智慧手錶匯入功能在所有模式都可用

## 🎯 應用網址

- **預期網址**: https://wftmufhir.streamlit.app/
- **GitHub**: https://github.com/zeroR10B21022/WFtmuFHIR
- **Branch**: traffic-light-system

## 📊 功能清單

已部署的功能：

- ✅ 血壓紅黃綠燈分類
- ✅ 即時血壓趨勢圖表
- ✅ 穩定度評分計算
- ✅ 調藥建議 (REDUCE/MAINTAIN/VISIT)
- ✅ FHIR 整合 (Taiwan HAPI)
- ✅ **智慧手錶資料匯入** (NEW!)
  - JSON 格式支援
  - 自動去重
  - 批次匯入
  - 詳細統計

## 🔄 更新應用

當您推送新程式碼到 GitHub：

1. **自動更新** (預設):
   ```bash
   git add .
   git commit -m "Update message"
   git push origin traffic-light-system
   ```

2. Streamlit Cloud 會在 1-2 分鐘內自動重新部署

3. 如果需要手動觸發：
   - 前往 Streamlit Cloud
   - 點擊「Reboot app」

## 📞 技術支援

遇到問題？

1. 檢查 [SMARTWATCH_IMPORT.md](SMARTWATCH_IMPORT.md) - 匯入功能說明
2. 查看 Streamlit Cloud 日誌
3. 檢查 GitHub Actions (如果有設定)
4. Email: 114346@w.tmu.edu.tw

---

**最後更新**: 2025-01-28
**Commit**: 0f7f21c - Add smartwatch data import functionality
