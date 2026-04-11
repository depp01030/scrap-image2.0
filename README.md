# scrap-image2.0

Chrome extension + local service project for scraping product detail images from supported shopping sites, then running local image processing on the downloaded files.

Current MVP focus:

- collect product detail image URLs from supported sites
- send a job from the Chrome extension to the local service
- download source images into a temporary workspace
- trim white borders and split long stacked images into smaller outputs
- publish processed results into a final output folder

Not finished yet:

- merge multiple source images before splitting
- second-pass processing for stitched long images

## Supported Sites

Current first-pass support has been tested on these four site families:

- `en.love-minuet.com`
- `smartstore.naver.com`
- `maybe-baby.co.kr`
- `www.veryyou.co.kr`

## How It Works

There are two main parts in the repo:

- Chrome extension
  Handles page-side extraction, removes right-click blocking, and sends the product job to the local service.
- Local service
  Receives the job, downloads images, processes them, and writes final outputs to disk.

Main flow:

1. Open a supported product page.
2. Use the extension context menu to send the product job.
3. Local service downloads source images into `tmp_output/`.
4. Local service runs crop / split processing on the downloaded files.
5. Final processed files are published to `output/`.

## Project Structure

```text
scrap-image2.0/
├─ src/
│  ├─ extension/
│  │  ├─ background/
│  │  ├─ content/
│  │  ├─ popup/
│  │  ├─ site_handlers/
│  │  └─ utils/
│  └─ local_service/
│     └─ app/
│        ├─ api/
│        ├─ core/
│        ├─ schemas/
│        ├─ services/
│        └─ utils/
├─ SPEC/
├─ docs/
├─ resource/
├─ tests/
│  ├─ fixtures/
│  └─ local_service/
├─ tmp_output/
├─ output/
└─ test_output/
```

Folder roles:

- `src/extension/`
  Chrome extension source.
- `src/local_service/`
  FastAPI local service source.
- `SPEC/`
  Product requirements, architecture notes, and implementation planning.
- `docs/`
  Development and operation notes.
- `resource/`
  Reference URLs and manual research notes.
- `tests/fixtures/`
  Saved test payloads such as extracted metadata fixtures.
- `tmp_output/`
  Temporary working area for downloaded raw files and intermediate processing.
- `output/`
  Final published results from the normal app flow.
- `test_output/`
  Isolated replay / comparison outputs used for development validation.

## Output Layout

Normal app flow writes to two roots:

- temporary work root: `tmp_output/<folder_name>/`
- final result root: `output/<folder_name>/`

Inside `tmp_output/<folder_name>/`:

- `raw/`
  Downloaded source images.
- `processed/`
  Processed images after crop / split.
- `stitched/`
  Reserved for future image merge output.
- `split/`
  Reserved for future split pipeline output.
- `logs/`
  Reserved for per-job logs.
- `metadata.json`
  Full job metadata and processing result summary.

Inside `output/<folder_name>/`:

- processed image files
- `manifest.json`

Folder naming is currently:

- `網站名-資訊名`

Examples:

- `love-minuet-...`
- `naver-...`
- `maybe-baby-...`
- `veryyou-...`

## Configuration

Runtime settings are controlled by [config.json](D:\VibeCode\scrap-image2.0\config.json).

Important keys:

- `port`
  Local service port. Current default is `8765`.
- `tmp_output_root`
  Temporary working root.
- `final_output_root`
  Final published output root.
- `trim_threshold`
  White-border trimming threshold.
- `split_row_threshold`
  Blank-row detection threshold.
- `min_split_gap_rows`
  Minimum blank gap height used for split decisions.
- `min_segment_height`
  Minimum output segment height.
- `max_split_parts`
  Maximum top-level split parts used by the current heuristic.

## Install

Use Python `3.10.11` in this project.

```bash
pip install -r requirements.txt
```

Current Python dependencies:

- `fastapi`
- `uvicorn`
- `httpx`
- `pillow`
- `opencv-python-headless`
- `pydantic`
- `pytest`

## Run Local Service

From repo root:

```bash
C:\Users\User\.pyenv\pyenv-win\versions\3.10.11\python.exe -m uvicorn app.main:app --app-dir src/local_service --host 127.0.0.1 --port 8765
```

Health check:

```text
http://127.0.0.1:8765/health
```

## Load Chrome Extension

Load unpacked extension from:

```text
src/extension
```

The extension currently talks to:

```text
http://127.0.0.1:8765
```

## Development Test Flows

### 1. Full flow with extension

Use the extension on a supported product page, then inspect:

- `tmp_output/<folder_name>/`
- `output/<folder_name>/`

### 2. Replay saved metadata

This reruns the end-to-end local service path from saved metadata fixtures and writes to:

- `test_output/metadata_replay/`

Command:

```bash
C:\Users\User\.pyenv\pyenv-win\versions\3.10.11\python.exe tests/local_service/replay_site_metadata.py
```

### 3. Reprocess saved downloads only

This is the current best validation path when you want to test only the image-processing stage.

It:

- reads the latest saved `metadata.json` for each supported site from `tmp_output/`
- reuses the existing `raw/` downloaded images
- skips extension and downloading entirely
- reruns only crop / split processing
- writes comparison results to `test_output/processing_replay/`

Command:

```bash
C:\Users\User\.pyenv\pyenv-win\versions\3.10.11\python.exe tests/local_service/reprocess_saved_downloads.py
```

Check these outputs:

- [processing replay final](D:\VibeCode\scrap-image2.0\test_output\processing_replay\final)
- [processing replay report](D:\VibeCode\scrap-image2.0\test_output\processing_replay\report.json)

## Current Limitations

- merge-then-split workflow is not implemented yet
- some extracted product names still suffer from encoding issues in older saved metadata
- split heuristics are still rule-based and need more site-specific tuning
- some animated images such as animated WebP are skipped during processing

## Key Files

- [config.json](D:\VibeCode\scrap-image2.0\config.json)
- [step.md](D:\VibeCode\scrap-image2.0\step.md)
- [development.md](D:\VibeCode\scrap-image2.0\docs\development.md)
- [page-scanner.js](D:\VibeCode\scrap-image2.0\src\extension\content\page-scanner.js)
- [service-worker.js](D:\VibeCode\scrap-image2.0\src\extension\background\service-worker.js)
- [main.py](D:\VibeCode\scrap-image2.0\src\local_service\app\main.py)
- [job_service.py](D:\VibeCode\scrap-image2.0\src\local_service\app\services\job_service.py)
- [crop_service.py](D:\VibeCode\scrap-image2.0\src\local_service\app\services\crop_service.py)
