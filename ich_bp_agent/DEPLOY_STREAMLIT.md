# 部署 Streamlit App 到雲端

## 選項 1: Streamlit Community Cloud（推薦，免費）

### Step 1: 準備 GitHub Repository

1. 建立新的 GitHub Repository
2. 上傳以下檔案：

```
你的Repository/
├── ich_bp_agent/          # 整個 ich_bp_agent 資料夾
├── requirements.txt       # 依賴套件
└── .streamlit/
    └── config.toml        # Streamlit 設定
```

### Step 2: 建立 requirements.txt（根目錄）

```txt
streamlit>=1.29.0
plotly>=5.18.0
httpx>=0.24.0
authlib>=1.2.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
loguru>=0.7.0
python-dotenv>=1.0.0
python-dateutil>=2.8.0
```

### Step 3: 部署到 Streamlit Cloud

1. 前往 https://share.streamlit.io/
2. 用 GitHub 帳號登入
3. 點選 **New app**
4. 選擇你的 Repository
5. Main file path 填入: `ich_bp_agent/ui/app.py`
6. 點選 **Deploy**

等待幾分鐘，你的 App 就上線了！

網址格式: `https://你的app名稱.streamlit.app`

---

## 選項 2: Heroku

### Step 1: 建立必要檔案

**Procfile:**
```
web: streamlit run ich_bp_agent/ui/app.py --server.port $PORT --server.address 0.0.0.0
```

**setup.sh:**
```bash
mkdir -p ~/.streamlit/
echo "[server]
headless = true
port = $PORT
enableCORS = false
" > ~/.streamlit/config.toml
```

### Step 2: 部署
```bash
heroku create your-app-name
git push heroku main
```

---

## 選項 3: 自己的伺服器 (VPS/雲端主機)

```bash
# 安裝依賴
pip install -r requirements.txt

# 背景執行
nohup streamlit run ich_bp_agent/ui/app.py --server.port 80 --server.address 0.0.0.0 &
```

建議搭配 nginx 做反向代理和 HTTPS。

---

## SMART on FHIR 整合注意事項

### Redirect URI 設定

部署後，你需要在衛服部 SMART Sandbox 更新：

- **Redirect URI**: `https://你的app.streamlit.app/`

### 處理 OAuth Callback

Streamlit 會自動處理 URL 參數，在 `app.py` 中可以用：

```python
import streamlit as st

# 取得 OAuth callback 的 code
query_params = st.query_params
if "code" in query_params:
    auth_code = query_params["code"]
    # 用 auth_code 換取 access_token
```
