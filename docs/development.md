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
