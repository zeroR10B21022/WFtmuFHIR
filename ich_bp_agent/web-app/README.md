# ICH 血壓管理 Web App - 部署指南

這是一個純前端的 SMART on FHIR 應用程式，可以部署到 GitHub Pages。

## 檔案結構

```
web-app/
├── docs/
│   ├── launch.html    # SMART OAuth2 授權啟動頁面
│   ├── index.html     # 主應用程式頁面
│   └── app.js         # JavaScript 邏輯
└── README.md          # 本文件
```

## 部署到 GitHub Pages

### Step 1: 建立 GitHub Repository

1. 登入 [GitHub](https://github.com)
2. 點選 **New Repository**
3. 輸入名稱，例如：`ich-bp-app`
4. 勾選 **Add a README file**
5. 點選 **Create repository**

### Step 2: 上傳檔案

1. 進入新建的 repository
2. 點選 **Add file** → **Upload files**
3. 將 `docs` 資料夾內的所有檔案拖曳上傳：
   - `launch.html`
   - `index.html`
   - `app.js`
4. 點選 **Commit changes**

### Step 3: 啟用 GitHub Pages

1. 進入 repository 的 **Settings**
2. 左側選單點選 **Pages**
3. 在 **Source** 區塊：
   - Branch: 選擇 `main`
   - Folder: 選擇 `/ (root)` 或 `/docs`
4. 點選 **Save**

### Step 4: 取得網址

等待幾分鐘後，您的應用程式會部署在：
```
https://[你的GitHub帳號].github.io/[repository名稱]/
```

例如：
```
https://username.github.io/ich-bp-app/
```

## 在衛服部 SMART Sandbox 註冊

### Step 1: 註冊應用程式

1. 前往衛服部 SMART on FHIR 開發者入口
2. 註冊新應用程式
3. 填寫以下資訊：

| 欄位 | 值 |
|------|-----|
| App Name | ICH 血壓管理 |
| Launch URL | `https://[你的網址]/launch.html` |
| Redirect URI | `https://[你的網址]/index.html` |
| Scopes | `launch openid fhirUser patient/Patient.read patient/Observation.read patient/Observation.write patient/Condition.read patient/MedicationRequest.read` |

### Step 2: 取得 Client ID

註冊完成後，您會收到一個 **Client ID**。

### Step 3: 更新 launch.html

編輯 `launch.html`，將 `clientId` 改成您取得的 Client ID：

```javascript
FHIR.oauth2.authorize({
    clientId: "你的Client_ID",  // <-- 改這裡
    scope: "launch openid fhirUser patient/Patient.read ...",
    redirectUri: "index.html"
});
```

## 測試應用程式

### 使用 SMART Health IT 公開沙盒測試

如果您還沒有衛服部的 Client ID，可以先用 SMART Health IT 的公開沙盒測試：

1. 前往 https://launch.smarthealthit.org/
2. 在 **Launch URL** 輸入您的 `launch.html` 網址
3. 選擇一個測試患者
4. 點選 **Launch**

### Demo 模式

如果無法連接 FHIR 伺服器，應用程式會自動進入 **Demo 模式**，使用模擬資料展示功能。

直接開啟 `index.html` 即可進入 Demo 模式：
```
https://[你的網址]/index.html
```

## 本地測試

如果要在本地測試，可以使用 Python 的簡易伺服器：

```bash
cd docs
python -m http.server 8000
```

然後開啟瀏覽器訪問：
- Demo 模式: http://localhost:8000/index.html
- SMART 啟動: http://localhost:8000/launch.html (需要 FHIR 伺服器)

## 功能說明

### 儀表板
- 顯示最新血壓、14天平均值
- 血壓趨勢圖表
- 穩定度評分 (0-100)
- 調藥建議

### 輸入血壓
- 手動輸入收縮壓/舒張壓
- 儲存到 FHIR 伺服器 (或本地 Demo 模式)

### 歷史紀錄
- 查看過去的血壓紀錄
- 標示達標/異常狀態

## 穩定度評分演算法

| 項目 | 分數 | 說明 |
|------|------|------|
| 目標達成率 | 40 分 | 血壓在目標範圍的比例 |
| 變異係數 (CV) | 30 分 | CV < 10% 滿分 |
| 低血壓安全 | 20 分 | 每次低血壓事件扣 5 分 |
| 趨勢穩定 | 10 分 | 穩定或改善得滿分 |

## 自訂設定

編輯 `app.js` 中的 `CONFIG` 物件來調整：

```javascript
const CONFIG = {
    targetSystolic: { min: 120, max: 140 },  // 目標收縮壓
    targetDiastolic: { min: 70, max: 90 },   // 目標舒張壓
    stabilityWindowDays: 14,                  // 分析天數
    // ... 其他設定
};
```

## 注意事項

1. 此應用程式僅供參考，調藥建議需經醫師確認
2. GitHub Pages 只支援 HTTPS，確保您的 FHIR 伺服器也支援 HTTPS
3. 瀏覽器需要允許第三方 Cookie (用於 OAuth)

## 技術規格

- 純前端 HTML/CSS/JavaScript
- 使用 [fhirclient.js](https://github.com/smart-on-fhir/client-js) 處理 SMART on FHIR
- 使用 [Chart.js](https://www.chartjs.org/) 繪製圖表
- 使用 [Bootstrap 5](https://getbootstrap.com/) 做 UI

## 聯絡

如有問題，請聯繫開發團隊。
