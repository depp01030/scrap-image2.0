# 開發步驟

這份文件用來整理 `scrap-image2.0` 初版開發的執行步驟與 checklist，確認後即可開始實作。

## 規劃依據

- 主要參考文件：
  - `SPEC/SPEC.md`
  - `SPEC/requirements.md`
  - `SPEC/project_overview.md`
  - `SPEC/architecture.md`
  - `SPEC/implementation_plan.md`
- `SPEC.md` 內容可正常讀取，先前出現亂碼是讀取編碼不正確，不是檔案損壞。
- 初版目標以 MVP 為主，先完成可用、可測、可擴充的基本流程。

## 初版 MVP 範圍

- 建立本地運作的完整流程
- 建立 Chrome Extension，提供手動觸發
- 先支援 2 個網站 handler
- Extension 萃取圖片網址後，送到本地 FastAPI service
- Local service 下載圖片、整理資料夾、保存 metadata
- Local service 進行白邊裁切
- 保留後續擴充 stitching / splitting 的架構，但初版不先落地

## 初版目標網站

- `en.love-minuet.com`
- `smartstore.naver.com`
- `maybe-baby.co.kr`
- `www.veryyou.co.kr`

## 建議專案結構

```text
src/
  extension/
    manifest.json
    background/
    content/
    popup/
    site_handlers/
    utils/
  local_service/
    app/
      api/
      core/
      schemas/
      services/
      utils/
tests/
  local_service/
assets/
docs/
SPEC/
```

## 執行步驟與 Checklist

### Step 1. 建立專案骨架
- [x] 建立 `src/` 目錄結構
- [x] 建立 `tests/` 目錄結構
- [x] 建立 Python 專案初始化檔案
- [x] 建立基本開發文件與執行指令說明

完成標準：
- repo 有清楚的 extension / local service / tests 基本結構

### Step 2. 建立 local service 骨架
- [x] 建立 FastAPI 入口
- [x] 實作 `/health` endpoint
- [x] 實作 `/jobs` POST endpoint stub
- [x] 建立設定模組，包含 port、output root、retry 次數、白邊 threshold
- [x] 建立 logging 設定

完成標準：
- service 可以在本地啟動，`/health` 正常回傳

### Step 3. 定義 shared payload contract
- [x] 定義 request schema
- [x] 定義 response schema
- [x] 驗證必要欄位：`site_code`、`page_url`、`image_urls`、`metadata`
- [x] 回傳結構化成功與失敗訊息

完成標準：
- service 可以接收合法 payload，也能拒絕格式錯誤的 payload

### Step 4. 建立 job 與儲存流程
- [x] 設計 job ID 規則
- [x] 建立 job folder 結構
- [x] 儲存 metadata.json
- [x] 分離 `raw/`、`processed/`、`stitched/`、`split/`、`logs/`

完成標準：
- 每次成功請求都會建立一個可預期的 job 資料夾

### Step 5. 實作圖片下載流程
- [x] 建立 download service
- [x] 加入 retry 機制
- [x] 加入相同 URL 的去重處理
- [x] 將原始圖片存到 `raw/`
- [x] 對每張圖片記錄下載成功或失敗

完成標準：
- 提供圖片 URL 後，可以成功下載到 job 的 `raw/` 資料夾

### Step 6. 實作白邊裁切
- [ ] 先用 Pillow 實作 trim service
- [ ] 支援 near-white threshold 設定
- [ ] 保守裁切，避免裁掉主體
- [ ] 將結果存到 `processed/`
- [ ] 將裁切資訊寫入 metadata 或 logs

完成標準：
- 有白邊的圖片可以被正確裁切，且不明顯傷到內容

### Step 7. 建立 Chrome Extension 骨架
- [x] 建立 Manifest V3 結構
- [x] 建立 popup UI 與手動觸發按鈕
- [x] 建立 background service worker
- [x] 建立 content script / page scanner
- [x] 可以取得當前頁面的 URL 與 hostname

完成標準：
- extension 可在 Chrome 以 unpacked 模式載入，並可手動觸發

### Step 8. 建立第一個 site handler
- [x] 定義 base site handler interface
- [x] 建立第一個 concrete handler
- [x] 從商品頁萃取商品圖片 URL
- [x] 將萃取結果轉成 shared payload 格式
- [x] 過濾明顯重複圖或非內容圖

完成標準：
- 第一個目標網站可以完成頁面到 payload 的正確輸出

### Step 8-2. 建立第二個 site handler
- [x] 建立第二個 concrete handler
- [x] 處理第二個網站的圖片擷取邏輯
- [x] 將輸出統一轉成 shared payload 格式
- [x] 驗證兩個網站都能走同一條主流程

完成標準：
- 第二個目標網站可以在不改主流程的前提下完成擷取與送出

### Step 9. 串接 extension 與 local service
- [x] 建立 extension 的 localhost API client
- [x] 將 payload POST 到 local service
- [x] 處理成功與失敗回應
- [x] 在 popup 或 console 顯示 job 結果

完成標準：
- extension 可以成功觸發一個完整 job

### Step 10. 測試與驗證
- [ ] 加入 payload schema 驗證測試
- [ ] 加入白邊裁切測試
- [ ] 加入至少一個 `/jobs` service-level integration test
- [ ] 補上 extension 手動測試步驟

完成標準：
- MVP 有基本自動化測試與人工驗證方式

### Step 11. 文件整理
- [ ] 更新 `README.md`
- [ ] 補上安裝與執行方式
- [ ] 補上支援網站說明
- [ ] 補上輸出資料夾範例
- [ ] 記錄 MVP 已知限制

完成標準：
- 新加入的人只看 repo 文件就能理解如何啟動與測試

## 建議實作順序

1. Local service 骨架
2. Payload schema
3. Job / storage / downloader
4. 白邊裁切
5. Extension 骨架
6. 第一個 site handler
7. 第二個 site handler
8. Extension 與 service 串接
9. 測試與文件

## 開發前確認事項

- [x] 第一批正式支援網站：
  - `en.love-minuet.com`
  - `smartstore.naver.com`
  - `maybe-baby.co.kr`
  - `www.veryyou.co.kr`
- [x] Python 套件管理先使用 `requirements.txt`
- [x] Extension 與 local service 維持同一個 repo 管理
- [x] 初版不做 stitching / splitting，先保留擴充介面

## MVP 後續延伸項目

- [ ] 多網站 handler 擴充
- [ ] 圖片 stitching
- [ ] 圖片 splitting
- [ ] 更完整的 popup UI
- [ ] Job 歷史檢視
- [ ] 批次處理流程
