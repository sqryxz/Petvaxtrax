# PetVaxHK - 本地優先的香港寵物疫苗追蹤器

![PetVaxHK](https://img.shields.io/badge/Version-0.1.0-blue)
![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-green)

PetVaxHK 是一款專為香港寵物主人設計的本地優先（local-first）疫苗追蹤應用程式。支援貓狗，緊守香港漁農自然護理署（AFCD）的規定。

## 目錄

- [功能特點](#功能特點)
- [安裝](#安裝)
- [快速開始](#快速開始)
- [命令行介面](#命令行介面)
  - [寵物管理](#寵物管理)
  - [疫苗記錄](#疫苗記錄)
  - [提醒功能](#提醒功能)
  - [合規檢查](#合規檢查)
  - [數據匯出](#數據匯出)
- [網頁應用](#網頁應用)
- [香港疫苗規定](#香港疫苗規定)
- [常見問題](#常見問題)

---

## 功能特點

### 🐕 寵物管理
- 新增、編輯、刪除寵物資料
- 支援狗隻及貓隻
- 記錄晶片編號、出生日期、品種、主人資料

### 💉 疫苗追蹤
- 自動計算到期日
- 支援多種疫苗類型：
  - **狗隻**：狂犬病（Rabies）、DHPP（狗瘟熱、肝炎、流感、副流感）
  - **貓隻**：狂犬病（Rabies）、FVRCP（貓病毒性鼻氣管炎、杯狀病毒、貓瘟）
- 記錄疫苗名稱、注射日期、到期日、診所

### 🔔 智能提醒
- 逾期提醒
- 到期臨近提醒（30天內）
- 自動生成提醒

### ✅ 合規檢查
- 檢查是否符合 AFCD 規定
- 狗隻牌照續期提醒
- 進口動物檢疫要求

### 📤 數據匯出
- JSON 格式匯出
- CSV 格式匯出
- 完整數據備份

### 🌐 網頁介面
- 直觀的 Web UI
- 響應式設計，支援手機及桌面

---

## 安裝

### 前置要求

- Python 3.10 或更高版本
- SQLite3

### 步驟

```bash
# 1. 複製專案
git clone <repository-url>
cd petvax

# 2. 建立虛擬環境（可選但推薦）
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate     # Windows

# 3. 安裝依賴
pip install -e ".[web]"

# 4. 初始化數據庫（首次使用）
python3 -m app.cli pet list
```

---

## 快速開始

### 基本流程

```bash
# 1. 新增一隻狗
python3 -m app.cli pet add

# 2. 新增疫苗記錄
python3 -m app.cli vaccine add

# 3. 檢查合規狀態
python3 -m app.cli compliance

# 4. 生成提醒
python3 -m app.cli reminder generate

# 5. 查看提醒
python3 -m app.cli reminder show
```

---

## 命令行介面

### 寵物管理

#### 列出所有寵物
```bash
python3 -m app.cli pet list
```

#### 新增寵物
```bash
python3 -m app.cli pet add
```
互動式輸入：
- 名字
- 物種（狗/貓）
- 品種
- 出生日期（YYYY-MM-DD）
- 晶片編號（可選）
- 主人姓名
- 聯絡電話

#### 編輯寵物
```bash
python3 -m app.cli pet edit <寵物ID>
```

#### 刪除寵物
```bash
python3 -m app.cli pet delete <寵物ID>
```
系統會要求確認刪除。

---

### 疫苗記錄

#### 列出所有疫苗記錄
```bash
python3 -m app.cli vaccine list
```

#### 新增疫苗記錄
```bash
python3 -m app.cli vaccine add
```
互動式輸入：
- 寵物選擇
- 疫苗類型
- 注射日期
- 診所（可從目錄選擇或輸入新診所）
- 備註（可選）

系統會自動計算下次到期日。

#### 編輯疫苗記錄
```bash
python3 -m app.cli vaccine edit <疫苗ID>
```

#### 刪除疫苗記錄
```bash
python3 -m app.cli vaccine delete <疫苗ID>
```

---

### 提醒功能

#### 查看即將到期的提醒
```bash
python3 -m app.cli reminder show
```

#### 列出所有提醒
```bash
python3 -m app.cli reminder list
```

#### 生成新提醒
```bash
python3 -m app.cli reminder generate
```
根據疫苗記錄自動生成到期提醒。

#### 標記提醒為已處理
```bash
python3 -m app.cli reminder mark <提醒ID>
```

#### 取消提醒
```bash
python3 -m app.cli reminder cancel <提醒ID>
```

#### 刪除提醒
```bash
python3 -m app.cli reminder delete <提醒ID>
```

---

### 合規檢查

#### 基本合規檢查
```bash
python3 -m app.cli compliance
```

#### 詳細報告
```bash
python3 -m app.cli compliance --detailed
```

#### 檢查特定寵物
```bash
python3 -m app.cli compliance --pet <寵物ID>
```

---

### 數據匯出

#### 匯出為 JSON
```bash
python3 -m app.cli export --format json --output my_pets.json
```

#### 匯出為 CSV
```bash
python3 -m app.cli export --format csv --output my_pets.csv
```

---

## 網頁應用

啟動網頁介面：

```bash
python3 run_web.py
```

然後在瀏覽器打開：http://localhost:5000

### 網頁功能

- **儀表板**：總覽所有寵物及提醒
- **寵物管理**：新增、編輯、刪除寵物
- **疫苗管理**：新增、編輯、刪除疫苗記錄
- **提醒儀表板**：查看逾期及即將到期提醒
- **診所目錄**：儲存常用的獸醫診所
- **合規儀表板**：檢視合規狀態
- **設定**：語言、時區、日期格式
- **關於**：應用程式資訊

---

## 香港疫苗規定

### 狗隻

#### 本地居民狗隻
| 疫苗 | 首次注射 | 續期 |
|------|----------|------|
| 狂犬病 | 3個月大後 | 每年 |
| DHPP | 6-8週大起 | 每年 |

#### 牌照續期
- 狗隻牌照必須每年續期
- 牌照續期前需完成狂犬病疫苗注射

#### 進口要求
- 來自 Group I 國家：毋需檢疫
- 來自 Group II 國家：120天檢疫
- 來自 Group III 國家：180天檢疫
- 必須在抵港前120天內注射狂犬病疫苗

### 貓隻

#### 建議疫苗
| 疫苗 | 首次注射 | 續期 |
|------|----------|------|
| 狂犬病 | 3個月大後 | 每年 |
| FVRCP | 6-8週大起 | 每年 |

#### 進口要求
- 來自 Group I 國家：毋需檢疫
- 來自 Group II/III 國家：需要檢疫
- 必須在抵港前120天內注射狂犬病疫苗

---

## 常見問題

### Q: 數據儲存在哪裡？
A: 數據預設儲存在 `outputs/pets.db`（SQLite 資料庫）。

### Q: 如何備份數據？
A: 使用匯出功能：
```bash
python3 -m app.cli export --format json --output backup.json
```

### Q: 忘記下次疫苗到期日怎麼辦？
A: 使用 `reminder show` 查看即將到期的提醒。

### Q: 可以同時追蹤狗隻和貓咪嗎？
A: 可以，系統支援狗隻和貓咪。

### Q: 網頁版和命令行版數據同步嗎？
A: 是的，兩者共享同一個資料庫。

---

## 技術細節

- **資料庫**：SQLite3
- **CLI 框架**：argparse
- **網頁框架**：Flask + SQLAlchemy
- **測試框架**：pytest

### 執行測試

```bash
# 執行所有測試
pytest

# 執行特定測試
pytest app/tests/test_cli.py

# 顯示覆蓋率
pytest --cov=app
```

---

## 授權

MIT License

---

## 聯絡

如有问题，请提交 Issue。
