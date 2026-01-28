# 🚨 緊急修復：Streamlit Cloud 部署問題

## 問題診斷

從錯誤訊息看：
```
File "/mount/src/wftmufhir/ich_bp_agent/ui/app.py", line 336, in show_patient_dashboard
    if connect_direct_fhir(fhir_url):
```

**問題根源**：
- Streamlit Cloud 上的代碼版本與 GitHub 不一致
- 行號對不上（本地 line 336 在登入頁面，不在 show_patient_dashboard）
- 可能是部署時出現緩存或同步問題

## ⚡ 立即修復步驟

### 步驟 1: 強制重新部署 Streamlit Cloud

1. **前往** https://share.streamlit.io/
2. **登入**你的 GitHub 帳號（zeroR10B21022）
3. **找到** WFtmuFHIR 應用
4. **點擊**應用進入管理頁面
5. **點擊**右上角的「⋮」（三個點）選單
6. **選擇** 「Reboot app」
7. **等待** 2-3 分鐘讓應用重新部署

### 步驟 2: 清除 Streamlit Cloud 緩存

如果 Reboot 後還是有問題：

1. 在應用管理頁面
2. 點擊「Settings」
3. 滾動到最下方
4. 點擊「Clear cache」
5. 再次點擊「Reboot app」

### 步驟 3: 驗證部署成功

重新部署後：

1. 前往應用網址
2. 選擇「Demo 模式 (測試)」
3. 點擊「進入 Demo 模式」
4. 應該能看到「王大明」的資料
5. 嘗試「記錄血壓」- 應該不會出錯
6. **向下滾動**查看「📱 匯入智慧手錶資料」

## 🔍 檢查清單

- [ ] Streamlit Cloud 應用已 Reboot
- [ ] 等待 2-3 分鐘部署完成
- [ ] Demo 模式能正常進入
- [ ] 記錄血壓沒有錯誤
- [ ] 能看到智慧手錶匯入功能

## 🎯 如果還是不行

### 方案 A: 使用本地版本

```bash
cd "c:\Users\Brian\Desktop\claude test\ich_bp_agent_github"
streamlit run streamlit_app.py
```

本地版本應該沒問題，可以正常使用和測試。

### 方案 B: 檢查 Streamlit Cloud 日誌

1. 在應用管理頁面
2. 點擊「Logs」標籤
3. 查看最新的錯誤訊息
4. 截圖完整的錯誤 traceback
5. 發給我看

### 方案 C: 完全重新部署

如果上述方法都不行：

1. 在 Streamlit Cloud 中**刪除**現有應用
2. **重新創建**新應用：
   - Repository: `zeroR10B21022/WFtmuFHIR`
   - Branch: `traffic-light-system`
   - Main file: `streamlit_app.py`
3. 添加 Secrets（見下方）
4. 部署

## 🔐 Streamlit Cloud Secrets 配置

如果重新部署，記得添加 Secrets：

```toml
[direct_fhir]
FHIR_BASE_URL = "https://twcore.hapi.fhir.tw/fhir"

[smart]
SMART_FHIR_BASE_URL = "https://thas.mohw.gov.tw/v/r4/sim/WzIslilslilslkFVVE8iLDAsMCwwLCIiLCIiLCIiLCIiLCIiLCIiLCIiLCIiLDAsMSwill0/fhir"
SMART_CLIENT_ID = "demo_client"
SMART_REDIRECT_URI = "https://wftmufhir.streamlit.app/"
```

## 💡 為什麼會發生這個問題？

Streamlit Cloud 有時會：
1. **緩存舊版本代碼**
2. **部署時中斷**導致代碼不完整
3. **依賴包版本衝突**

Reboot app 會：
- ✅ 重新從 GitHub 拉取最新代碼
- ✅ 重新安裝所有依賴
- ✅ 清除運行時緩存

## 📞 還是有問題？

請提供：
1. Streamlit Cloud 日誌截圖（完整的 traceback）
2. 你執行的步驟
3. 錯誤發生在哪個操作時

---

**建立時間**: 2025-01-28
**狀態**: 等待 Streamlit Cloud 重新部署
