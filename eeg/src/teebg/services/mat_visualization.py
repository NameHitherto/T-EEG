from pathlib import Path
from typing import Any

import numpy as np
from scipy.io import loadmat

from teebg.services.api.schemas import MatVariable, MatVisualizationResponse

MAT_METADATA_KEYS = {"__header__", "__version__", "__globals__"}


class MatVisualizationError(ValueError):
    pass


def load_mat_visualization(file_path: str) -> MatVisualizationResponse:
    path = Path(file_path).expanduser()

    if path.suffix.lower() != ".mat":
        raise MatVisualizationError("Only .mat files are supported.")
    if not path.exists():
        raise MatVisualizationError("MAT file does not exist.")
    if not path.is_file():
        raise MatVisualizationError("MAT path must point to a file.")

    try:
        mat_data = loadmat(path)
    except NotImplementedError as exc:
        raise MatVisualizationError(
            "MATLAB v7.3/HDF5 .mat files are not supported in this version."
        ) from exc
    except Exception as exc:
        raise MatVisualizationError(f"Unable to read MAT file: {exc}") from exc

    variables = [
        MatVariable(
            name=name,
            shape=list(value.shape),
            dtype=str(value.dtype),
            data=_to_json_data(value),
        )
        for name, value in mat_data.items()
        if _is_numeric_mat_variable(name, value)
    ]

    return MatVisualizationResponse(filePath=str(path.resolve()), variables=variables)


def _is_numeric_mat_variable(name: str, value: Any) -> bool:
    return (
        name not in MAT_METADATA_KEYS
        and isinstance(value, np.ndarray)
        and np.issubdtype(value.dtype, np.number)
    )


def _to_json_data(value: np.ndarray) -> Any:
    if value.ndim == 0:
        return value.item()
    return value.tolist()
