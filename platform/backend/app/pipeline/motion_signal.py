"""Stage 8: vector magnitude of the dynamic (gravity-removed) acceleration."""
import numpy as np


def vector_magnitude(dynamic_accel: np.ndarray) -> np.ndarray:
    return np.linalg.norm(dynamic_accel, axis=1)
