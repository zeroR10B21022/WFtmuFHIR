# ICH 血壓管理 APP - 快速入門指南

## 第一次使用？從這裡開始！

### 步驟 1：開啟命令列

按 `Win + R`，輸入 `cmd`，按 Enter

### 步驟 2：進入專案目錄

```cmd
cd "C:\Users\Brian\Desktop\claude test"
```

### 步驟 3：安裝依賴套件（只需執行一次）

```cmd
py -m pip install -r ich_bp_agent/requirements.txt
```

### 步驟 4：啟動應用程式

```cmd
py -m streamlit run ich_bp_agent/ui/app.py
```

### 步驟 5：使用應用程式

1. 瀏覽器會自動開啟 http://localhost:8501
2. 在登入頁面選擇「Demo 模式」
3. 開始使用！

---

## 之後每次使用

只需要執行步驟 2 和步驟 4：

```cmd
cd "C:\Users\Brian\Desktop\claude test"
py -m streamlit run ich_bp_agent/ui/app.py
```

---

## 常見問題

### Q: 出現 "No module named 'xxx'" 錯誤？

重新執行步驟 3 安裝套件：
```cmd
py -m pip install -r ich_bp_agent/requirements.txt
```

### Q: 瀏覽器沒有自動開啟？

手動開啟瀏覯器，輸入網址：http://localhost:8501

### Q: 要停止應用程式？

在命令列按 `Ctrl + C`

### Q: 忘記專案路徑？

專案位於：`C:\Users\Brian\Desktop\claude test\ich_bp_agent`

---

## 檔案說明

```
ich_bp_agent/
├── ui/app.py          ← 主程式（啟動這個）
├── requirements.txt   ← 依賴套件清單
├── README.md          ← 完整說明文件
└── QUICKSTART.md      ← 本文件
```
