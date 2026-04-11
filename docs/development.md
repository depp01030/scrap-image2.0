# Development

## Local Service

Install dependencies:

```bash
pip install -r requirements.txt
```

Run local service from repo root:

```bash
uvicorn app.main:app --app-dir src/local_service --reload --host 127.0.0.1 --port 8765
```

Health check:

```bash
http://127.0.0.1:8765/health
```

## Chrome Extension

Load unpacked extension from:

```text
src/extension
```

The extension is currently wired to:

```text
http://127.0.0.1:8765
```

## Output Layout

- Temporary work files:

```text
tmp_output/<folder_name>/
```

- Final deliverables:

```text
output/<folder_name>/
```

Both roots are controlled by `config.json`.

## Metadata Replay

Replay the four saved site payloads without using the browser extension:

```bash
C:\Users\User\.pyenv\pyenv-win\versions\3.10.11\python.exe tests/local_service/replay_site_metadata.py
```

The replay script will:

- export fixtures to `tests/fixtures/site_metadata/`
- write temporary replay files to `test_output/metadata_replay/tmp/`
- write final replay results to `test_output/metadata_replay/final/`

## Processing Replay

Rerun only the image-processing step from the saved `tmp_output/*/raw/` folders:

```bash
C:\Users\User\.pyenv\pyenv-win\versions\3.10.11\python.exe tests/local_service/reprocess_saved_downloads.py
```

The processing replay will:

- reuse the latest saved `metadata.json` for each of the four target sites
- skip image downloading entirely
- write processed comparison outputs to `test_output/processing_replay/final/`
