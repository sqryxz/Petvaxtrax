# PetVaxHK 疑難排解 FAQ

## 目錄
1. [安裝問題](#1-安裝問題)
2. [資料庫問題](#2-資料庫問題)
3. [CLI 使用問題](#3-cli-使用問題)
4. [Web 應用問題](#4-web-應用問題)
5. [疫苗記錄問題](#5-疫苗記錄問題)
6. [合規性問題](#6-合規性問題)
7. [匯入/匯出問題](#7-匯入匯出問題)
8. [其他問題](#8-其他問題)

---

## 1. 安裝問題

### Q1.1: 安裝時出現 `ModuleNotFoundError: No module named 'petvax'`

**解決方案:**
```bash
# 方法 1: 使用 pip 安裝
cd petvax
pip install -e .

# 方法 2: 設定 PYTHONPATH
export PYTHONPATH=/path/to/petvax:$PYTHONPATH
```

### Q1.2: `sqlite3` 模組找不到

**解決方案:**
- Python 3 已內建 sqlite3，若出現錯誤，嘗試重新安裝 Python
- macOS: `brew install python3`
- Ubuntu/Debian: `sudo apt-get install python3-sqlite`

### Q1.3: 安裝依賴時出現權限錯誤

**解決方案:**
```bash
# 使用虛擬環境
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate     # Windows

pip install -r requirements.txt
```

### Q1.4: Flask 相關錯誤

**解決方案:**
```bash
pip install flask flask-sqlalchemy flask-cors
```

---

## 2. 資料庫問題

### Q2.1: 資料庫檔案不存在

**錯誤訊息:** `Error: Database file not found`

**解決方案:**
```bash
# 初始化新資料庫
python -m app.cli init

# 或指定資料庫路徑
python -m app.cli --db-path /custom/path/pets.db init
```

### Q2.2: 資料庫被鎖定

**錯誤訊息:** `Error: database is locked`

**解決方案:**
- 確保沒有其他程式正在存取資料庫
- Web 伺服器正在運行時，CLI 無法寫入同一個資料庫
- 關閉 Web 伺服器後再進行 CLI 操作

### Q2.3: 資料庫遷移失敗

**解決方案:**
```bash
# 備份現有資料庫
cp outputs/pets.db outputs/pets.db.backup

# 重新初始化
rm outputs/pets.db
python -m app.cli init

# 如有備份資料，可匯入
python -m app.cli import --file backup.json
```

### Q2.4: 如何修復損壞的資料庫

**解決方案:**
```bash
# 檢查 SQLite 資料庫完整性
sqlite3 outputs/pets.db "PRAGMA integrity_check;"

# 如有問題，匯出現有資料為 JSON
python -m app.cli export -f json -o recovery.json

# 重新建立資料庫
rm outputs/pets.db
python -m app.cli init

# 匯入資料
python -m app.cli import --file recovery.json
```

---

## 3. CLI 使用問題

### Q3.1: 指令無回應或卡住

**解決方案:**
- 按 `Ctrl+C` 中斷
- 檢查資料庫是否被其他程式鎖定
- 使用 `--help` 查看指令語法

### Q3.2: 寵物資料無法新增

**常見原因:**
- 必填欄位未填寫
- 物種選擇錯誤（僅支援 `dog` 或 `cat`）
- 日期格式錯誤

**正確格式:**
```bash
python -m app.cli pet add --name "旺財" --species dog --breed "柴犬" --dob 2020-05-15
```

### Q3.3: 疫苗記錄無法新增

**解決方案:**
- 確認寵物 ID 正確: `python -m app.cli pet list`
- 確認疫苗類型有效
- 確認日期格式為 YYYY-MM-DD

### Q3.4: 指令參數錯誤

**解決方案:**
```bash
# 查看正確語法
python -m app.cli <command> --help

# 例如
python -m app.cli pet add --help
python -m app.cli vaccine add --help
```

---

## 4. Web 應用問題

### Q4.1: Web 伺服器無法啟動

**錯誤訊息:** `Address already in use`

**解決方案:**
```bash
# 找出佔用端口的程式
lsof -i :5000  # Linux/macOS
netstat -ano | findstr :5000  # Windows

# 終止程序或使用不同端口
python run_web.py --port 5001
```

### Q4.2: 網頁顯示空白或樣式錯誤

**解決方案:**
- 清除瀏覽器快取 (Ctrl+Shift+R / Cmd+Shift+R)
- 確認 `app/static/css/style.css` 存在
- 檢查瀏覽器開發者工具的 Console 錯誤

### Q4.3: 無法登入或權限問題

**說明:** PetVaxHK 目前為單機應用，無需登入。所有操作均為本地存取。

### Q4.4: 資料同步問題

**說明:** Web 應用和 CLI 共享同一資料庫。確保:
- 關閉 Web 伺服器後再進行 CLI 大量操作
- 或使用不同的資料庫路徑

---

## 5. 疫苗記錄問題

### Q5.1: 疫苗到期日計算錯誤

**可能原因:**
- 輸入的疫苗日期不正確
- 寵物出生日期設定錯誤

**解決方案:**
```bash
# 檢查寵物資料
python -m app.cli pet detail <pet_id>

# 重新設定出生日期
python -m app.cli pet edit <pet_id> --dob 2020-01-01
```

### Q5.2: 狂犬病疫苗間隔計算

**說明:**
- 狂犬病疫苗有效期為 1 年
- 每次注射後需等待 30 天才能取得有效抗體
- 進口動物需在入境前 180 天內完成注射

### Q5.3: DHPP/DAPP 疫苗記錄

**說明:** 狗隻的 DHPP/DAPP 疫苗:
- 幼犬需在 8-12 週齡開始注射
- 每次注射間隔 2-4 週
- 每年需加強注射

### Q5.4: 疫苗種類選擇

**正確的疫苗代碼:**
- 狗: `DHPP`, `DAPP`, `Rabies`, `Bordetella`, `Leptospirosis`, `Canine Influenza`
- 貓: `FVRCP`, `Rabies`, `FeLV`, `FIV`, `Bordetella`

---

## 6. 合規性問題

### Q6.1: 寵物牌照過期

**說明:** 香港法例規定，所有狗隻必須在 5 個月大前領牌，並每年續牌。

**解決方案:**
```bash
# 查看合規狀態
python -m app.cli compliance --detailed

# 系統會顯示:
# - 牌照到期日
# - 疫苗到期日
# - 需要完成的項目
```

### Q6.2: 進口檢疫要求

**說明:** 根據動物來源國，分為:
- Group I (低風險): 無檢疫
- Group II (中風險): 180 天檢疫
- Group III (高風險): 180 天檢疫 + 血液檢測

### Q6.3: 合規報告解讀

**狀態說明:**
- ✅ Compliant: 完全合規
- ⚠️ Warning: 即將到期，需注意
- ❌ Non-compliant: 不合規，需立即處理

---

## 7. 匯入/匯出問題

### Q7.1: JSON 匯入格式錯誤

**解決方案:**
```bash
# 檢查 JSON 格式
python -c "import json; json.load(open('data.json'))"

# 參考範例格式
cat inputs/seeds/sample_data.json
```

### Q7.2: CSV 匯入問題

**解決方案:**
- 確認 CSV 編碼為 UTF-8
- 確認欄位名稱正確
- 檢查日期格式為 YYYY-MM-DD

### Q7.3: 大量資料匯入失敗

**解決方案:**
- 分批匯入較小的檔案
- 檢查資料庫剩餘空間
- 確認來源資料無重複 ID

---

## 8. 其他問題

### Q8.1: 語言設定

**說明:** 系統支援英文 (en) 和繁體中文 (zh)。

**設定方式:**
```bash
# CLI 設定
python -m app.cli config set language zh

# Web 應用: 進入 Settings 頁面修改
```

### Q8.2: 資料備份

**建議:**
```bash
# 定期匯出備份
python -m app.cli export -f json -o backup_$(date +%Y%m%d).json

# 或使用內建備份指令
python -m app.cli backup
```

### Q8.3: 效能優化

**建議:**
- 定期清理過期的提醒記錄
- 避免在同一資料庫同時執行 Web 和 CLI
- 資料庫檔案超過 100MB 時考慮歸檔

### Q8.4: 如何取得技術支援

1. 查閱本 FAQ
2. 檢視 `README.md` 和 `API.md`
3. 執行測試確保功能正常: `python -m pytest`
4. 查看日誌檔案: `logs/`

### Q8.5: 報告錯誤

**錯誤報告資訊:**
- 作業系統版本
- Python 版本 (`python --version`)
- 錯誤訊息截圖
- 重現步驟
- `logs/` 目錄中的相關日誌

---

## 快速診斷指令

```bash
# 檢查系統狀態
python -m app.cli status

# 執行所有測試
python -m pytest -v

# 檢查資料庫
sqlite3 outputs/pets.db ".tables"
sqlite3 outputs/pets.db "SELECT COUNT(*) FROM pets;"

# 查看最近錯誤
tail -n 50 logs/app.log
```

---

*PetVaxHK v1.0.0 - 香港寵物疫苗追蹤工具*
