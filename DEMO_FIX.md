# Demo 模式問題修復

## 問題診斷

根據您的截圖和描述，發現兩個問題：

1. **按「記錄血壓」按鈕出現錯誤**
   - 錯誤位置：app.py line 336 (connect_direct_fhir)
   - 可能原因：代碼縮排或條件判斷問題

2. **看不到匯入智慧手錶資料的功能**
   - 原因：錯誤阻止了後續 UI 渲染

## 快速修復步驟

### 方法 1: 使用本地版本測試（推薦）

1. **打開本地終端**
   ```bash
   cd "c:\Users\Brian\Desktop\claude test\ich_bp_agent_github"
   ```

2. **運行測試腳本**
   ```bash
   python test_smartwatch_import.py
   ```
   這會測試匯入功能是否正常。

3. **啟動本地 Streamlit**
   ```bash
   streamlit run streamlit_app.py
   ```

4. **測試步驟**：
   - 選擇「Demo 模式 (測試)」
   - 點擊「進入 Demo 模式」
   - 應該能看到王大明的資料
   - 滾動頁面查看是否有「📱 匯入智慧手錶資料」區塊

### 方法 2: 檢查 Streamlit Cloud 日誌

如果您在 Streamlit Cloud 上遇到問題：

1. 前往 https://share.streamlit.io/
2. 找到您的應用
3. 點擊「Manage app」
4. 查看「Logs」標籤
5. 截圖錯誤訊息發給我

### 方法 3: 重新部署

如果 Streamlit Cloud 版本有問題：

1. 前往 https://share.streamlit.io/
2. 找到您的應用
3. 點擊右上角「⋮」選單
4. 選擇「Reboot app」

## 檢查清單

### Demo 模式測試

- [ ] 能成功進入 Demo 模式
- [ ] 能看到「王大明」的患者資訊
- [ ] 能看到血壓趨勢圖
- [ ] 能看到「輸入血壓」表單
- [ ] 能成功記錄血壓
- [ ] **能看到「📱 匯入智慧手錶資料」區塊**

### 匯入功能測試

- [ ] 能看到檔案上傳器
- [ ] 能選擇 JSON 檔案
- [ ] 能成功匯入資料
- [ ] 能看到匯入統計
- [ ] 儀表板有更新

## 預期畫面

在「輸入血壓」表單下方，應該看到：

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📱 匯入智慧手錶資料

上傳 JSON 檔案
[選擇檔案] 尚未選擇檔案

💡 支援包含血壓、心率、血氧等資料的 JSON 格式檔案
```

## 如果還是看不到匯入功能

可能的原因：

1. **頁面未完全載入**
   - 解決：重新整理頁面（F5）

2. **瀏覽器快取問題**
   - 解決：Ctrl + F5 強制重新載入

3. **代碼版本問題**
   - 解決：確認 git pull 最新代碼

4. **Streamlit Cloud 未更新**
   - 解決：Reboot app

## 需要更多協助？

請提供以下資訊：

1. 您是在本地運行還是 Streamlit Cloud？
2. 完整的錯誤訊息截圖（包含 Traceback）
3. Streamlit Cloud 日誌（如果適用）
4. 您選擇的登入方式（Demo/Direct FHIR/SMART）

---

**建立時間**: 2025-01-28
**相關文件**: SMARTWATCH_IMPORT.md, STREAMLIT_DEPLOYMENT.md
