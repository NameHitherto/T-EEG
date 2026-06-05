from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from teebg.services.api.schemas import (
    MatVisualizationRequest,
    MatVisualizationResponse,
)
from teebg.services.mat_visualization import (
    MatVisualizationError,
    load_mat_visualization,
)

app = FastAPI(title="T-EEG API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/visualization/mat", response_model=MatVisualizationResponse)
def visualize_mat(request: MatVisualizationRequest) -> MatVisualizationResponse:
    try:
        return load_mat_visualization(request.file_path)
    except MatVisualizationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
