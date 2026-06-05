# T-EEG Python Core

Run the API service:

```powershell
uv run uvicorn teebg.services.api.app:app --reload
```

Run checks:

```powershell
uv run ruff check .
uv run pytest
```
