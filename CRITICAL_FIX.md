# 🚨 緊急修復：清除緩存與 Session State

## 問題診斷

錯誤持續發生在：
```
File "/mount/src/wftmufhir/ich_bp_agent/ui/app.py", line 460
    latest_bp = max(bp_readings, key=lambda x: x.timestamp)
```

雖然代碼已經修復，但 **Streamlit Cloud 可能有舊的 session state 或緩存資料**，導致 BPReading 物件結構不一致。

## ⚡ 解決方案

### 步驟 1: 完全清除 Streamlit Cloud 緩存

1. 前往 https://share.streamlit.io/
2. 找到 WFtmuFHIR 應用
3. 點擊應用進入管理頁面
4. **點擊「Settings」標籤**
5. **滾動到最下方**
6. **點擊「Clear cache」按鈕**
7. 等待確認訊息
8. **再次點擊「Reboot app」**

### 步驟 2: 清除瀏覽器緩存

1. **按 Ctrl + Shift + Delete** 打開清除瀏覽器資料
2. 選擇「快取的圖片和檔案」
3. 時間範圍選「全部」
4. 點擊「清除資料」

### 步驟 3: 強制重新載入

1. 關閉所有 Streamlit 應用分頁
2. **按 Ctrl + Shift + R** 強制重新載入頁面
3. 或者使用無痕模式（Ctrl + Shift + N）開啟應用

### 步驟 4: 重新測試

1. 前往 https://wftmufhir.streamlit.app/
2. **選擇「Demo 模式 (測試)」**
3. **點擊「進入 Demo 模式」**
4. 應該能看到王大明的資料
5. **嘗試記錄血壓**

## 🔍 如果還是失敗

### 方案 A: 檢查 GitHub 是否同步

確認最新代碼已推送：

1. 前往 https://github.com/zeroR10B21022/WFtmuFHIR/tree/traffic-light-system
2. 查看最新 commit：應該是 "Fix BPReading source parameter issue"
3. 點擊 `ich_bp_agent/ui/app.py`
4. 檢查 line 560-566 是否有 `source="manual"`：

```python
new_reading = BPReading(
    timestamp=datetime.combine(date.today(), bp_time),
    systolic=systolic,
    diastolic=diastolic,
    patient_id=patient.patient_id,
    source="manual"  # <- 應該有這行
)
```

### 方案 B: 使用本地版本

如果 Streamlit Cloud 還是有問題，使用本地版本：

```bash
cd "c:\Users\Brian\Desktop\claude test\ich_bp_agent_github"

# 確認最新代碼
git pull origin traffic-light-system

# 啟動應用
streamlit run streamlit_app.py
```

本地版本應該完全正常。

### 方案 C: 完全重新部署

如果上述方法都不行，刪除並重新部署應用：

1. 在 Streamlit Cloud 中**刪除**現有應用
2. 等待 1 分鐘
3. **重新創建**新應用：
   - Repository: `zeroR10B21022/WFtmuFHIR`
   - Branch: `traffic-light-system`
   - Main file: `streamlit_app.py`
4. **添加 Secrets**：

```toml
[direct_fhir]
FHIR_BASE_URL = "https://twcore.hapi.fhir.tw/fhir"

[smart]
SMART_FHIR_BASE_URL = "https://thas.mohw.gov.tw/v/r4/sim/WzIslilslilslkFVVE8iLDAsMCwwLCIiLCIiLCIiLCIiLCIiLCIiLCIiLCIiLDAsMSwill0/fhir"
SMART_CLIENT_ID = "demo_client"
SMART_REDIRECT_URI = "https://wftmufhir.streamlit.app/"
```

5. 點擊「Deploy」

## 🐛 技術細節

這個問題的根源是：

1. **舊的 BPReading 物件**（沒有 source 欄位）可能存在 Streamlit session state 中
2. **新的 BPReading 定義**（有 source 欄位）與舊物件不兼容
3. Python dataclass 在這種情況下可能無法正確處理

**解決方法**：清除所有緩存和 session state，強制重新創建所有物件。

## 📊 預期結果

成功後應該能：

- ✅ 進入 Demo 模式
- ✅ 看到血壓資料和趨勢圖
- ✅ **記錄新的血壓（不再出錯）**
- ✅ 向下滾動看到「📱 匯入智慧手錶資料」
- ✅ 成功匯入 JSON 檔案

## 📞 還是不行？

請提供：

1. Streamlit Cloud 的完整錯誤日誌（Logs 標籤）
2. 你完成了哪些步驟
3. 使用本地版本是否正常

如果本地版本正常但 Streamlit Cloud 不行，那就是部署環境的問題，我們可以考慮其他解決方案。

---

**建立時間**: 2025-01-28
**Commit**: 2045401 - Fix BPReading source parameter issue
**狀態**: 等待清除緩存並重新測試
