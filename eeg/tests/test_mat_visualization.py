import numpy as np
import pytest
from scipy.io import savemat

from teebg.services.mat_visualization import (
    MatVisualizationError,
    load_mat_visualization,
)


def test_load_mat_visualization_returns_numeric_variables(tmp_path):
    mat_path = tmp_path / "sample.mat"
    savemat(
        mat_path,
        {
            "eeg": np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]),
            "label": np.array(["skip"]),
        },
    )

    result = load_mat_visualization(str(mat_path))

    assert result.filePath == str(mat_path.resolve())
    assert len(result.variables) == 1
    assert result.variables[0].name == "eeg"
    assert result.variables[0].shape == [2, 3]
    assert result.variables[0].dtype == "float64"
    assert result.variables[0].data == [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]


def test_load_mat_visualization_rejects_missing_file(tmp_path):
    with pytest.raises(MatVisualizationError, match="does not exist"):
        load_mat_visualization(str(tmp_path / "missing.mat"))


def test_load_mat_visualization_rejects_non_mat_file(tmp_path):
    text_path = tmp_path / "sample.txt"
    text_path.write_text("not a mat file")

    with pytest.raises(MatVisualizationError, match="Only .mat"):
        load_mat_visualization(str(text_path))
