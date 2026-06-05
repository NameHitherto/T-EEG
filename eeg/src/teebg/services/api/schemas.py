from typing import Any

from pydantic import BaseModel, Field


class MatVisualizationRequest(BaseModel):
    file_path: str = Field(..., min_length=1)


class MatVariable(BaseModel):
    name: str
    shape: list[int]
    dtype: str
    data: Any


class MatVisualizationResponse(BaseModel):
    filePath: str
    variables: list[MatVariable]
