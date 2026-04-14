# scrap-image2.0

本專案是本地使用的商品圖片抓取工具，分成兩個部分：

- `extension`
  在支援網站的商品頁收集圖片網址，並把任務送到本地 service。
- `local service`
  接收任務、下載圖片、做裁白邊與切割，最後把處理結果輸出到指定資料夾。

目前已測試的網站：

- `en.love-minuet.com`
- `smartstore.naver.com`
- `maybe-baby.co.kr`
- `www.veryyou.co.kr`

## 使用方式

1. 安裝 Python 3.10+
2. 在專案根目錄安裝依賴：

```powershell
pip install -r requirements.txt
```

3. 啟動 local service：

```powershell
.\run_local_service.cmd
```

也可以直接執行：

```powershell
.\run_local_service.ps1
```

這兩個腳本都會以「腳本所在資料夾」當作專案根目錄，不會綁定固定磁碟代號。

4. 在 Chrome 的 `chrome://extensions/` 載入：

```text
src/extension
```

5. 打開支援網站商品頁，使用 extension 的右鍵功能送出任務。

## config.json

執行設定都放在專案根目錄的 `config.json`。

最重要的欄位：

- `port`
  Local service 的埠號，預設 `8765`
- `final_output_root`
  最終輸出資料夾
- `tmp_output_root`
  暫存工作資料夾
- `is_delete_tmp_output`
  任務完成後是否自動刪除對應的 `tmp_output/<folder_name>/`
- `clean_work_dirs_on_rerun`
  同商品重跑時，是否先清掉舊資料夾內容

範例：

```json
{
  "port": 8765,
  "tmp_output_root": "tmp_output",
  "final_output_root": "output",
  "is_delete_tmp_output": true
}
```

說明：

- `final_output_root` 可以改成任何你要交付結果的資料夾
- 如果設定相對路徑，會以本專案資料夾為基準
- `is_delete_tmp_output: true` 時，任務完成後會自動刪掉暫存資料夾
- 如果你要 debug，可暫時改成 `false`

## 輸出結果

正常使用時，最終產物會輸出到：

```text
<final_output_root>\<網站名-資訊名>\
```

例如：

- `output\love-minuet-...`
- `output\naver-...`
- `output\maybe-baby-...`
- `output\veryyou-...`

資料夾內會包含：

- 處理後的圖片
- `manifest.json`

## 專案結構

```text
scrap-image2.0/
  src/
    extension/
    local_service/
  resource/
  docs/
  SPEC/
  config.json
  requirements.txt
  run_local_service.cmd
  run_local_service.ps1
```

補充：

- `tmp_output/` 是執行中的暫存資料夾
- `output/` 是預設最終輸出資料夾
- `test_output/` 是開發測試用，不是一般使用者流程的一部分

## 目前功能

- 支援 extension 送任務到本地 service
- 支援下載商品圖片
- 支援白邊裁切
- 支援長圖切割
- 支援部分站點的 merge-then-split 規則
- 支援用 config 控制輸出路徑與暫存刪除

## 備註

- `veryyou` 目前有部分站點專用切割規則
- 動態 WebP / GIF 這類不適合的圖片會跳過
- 若要保留中間暫存結果，請把 `is_delete_tmp_output` 改成 `false`
