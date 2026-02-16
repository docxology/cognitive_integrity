"""Regression models for scaling analysis.

Provides linear, quadratic, and log-linear curve fitting used to
characterise how CIF latency and detection rate scale with agent count.

Key target: quadratic fit R^2 = 0.994 for latency vs. agent count.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import numpy as np
from scipy.optimize import curve_fit

# ---------------------------------------------------------------------------
# Result container
# ---------------------------------------------------------------------------

@dataclass
class RegressionResult:
    """Structured result from a regression fit.

    Attributes:
        coefficients: Fitted parameter values.
        r_squared: Coefficient of determination (R^2).
        residuals: Residuals (y_true - y_pred) for each observation.
        model_name: Human-readable name of the fitted model.
        prediction_fn: Callable that maps x-values to predictions.
    """

    coefficients: np.ndarray
    r_squared: float
    residuals: np.ndarray
    model_name: str
    prediction_fn: Callable[[np.ndarray], np.ndarray] = field(repr=False)


# ---------------------------------------------------------------------------
# R-squared
# ---------------------------------------------------------------------------

def r_squared(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Coefficient of determination (R^2).

    ``R^2 = 1 - SS_res / SS_tot``

    Args:
        y_true: Observed values.
        y_pred: Predicted values.

    Returns:
        R^2 value (can be negative for a poor model).
    """
    y_true = np.asarray(y_true, dtype=np.float64)
    y_pred = np.asarray(y_pred, dtype=np.float64)

    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)

    if ss_tot == 0.0:
        return 1.0 if ss_res == 0.0 else 0.0

    return 1.0 - ss_res / ss_tot


# ---------------------------------------------------------------------------
# Prediction helper
# ---------------------------------------------------------------------------

def predict(model: RegressionResult, x: np.ndarray) -> np.ndarray:
    """Generate predictions from a fitted regression model.

    Args:
        model: A :class:`RegressionResult` with a *prediction_fn*.
        x: Input values.

    Returns:
        Predicted y values.
    """
    return model.prediction_fn(np.asarray(x, dtype=np.float64))


# ---------------------------------------------------------------------------
# Linear regression
# ---------------------------------------------------------------------------

def fit_linear(x: np.ndarray, y: np.ndarray) -> RegressionResult:
    """Simple linear regression: y = b0 + b1 * x.

    Uses ``numpy.polyfit`` with degree 1.

    Args:
        x: Independent variable values.
        y: Dependent variable values.

    Returns:
        :class:`RegressionResult` with 2 coefficients ``[b1, b0]``.
    """
    x_arr = np.asarray(x, dtype=np.float64)
    y_arr = np.asarray(y, dtype=np.float64)

    coeffs = np.polyfit(x_arr, y_arr, deg=1)  # [b1, b0]
    poly = np.poly1d(coeffs)

    y_pred = poly(x_arr)
    resid = y_arr - y_pred
    r2 = r_squared(y_arr, y_pred)

    return RegressionResult(
        coefficients=coeffs,
        r_squared=r2,
        residuals=resid,
        model_name="linear (y = b0 + b1*x)",
        prediction_fn=lambda xv: np.poly1d(coeffs)(np.asarray(xv, dtype=np.float64)),
    )


# ---------------------------------------------------------------------------
# Quadratic regression
# ---------------------------------------------------------------------------

def fit_quadratic(x: np.ndarray, y: np.ndarray) -> RegressionResult:
    """Quadratic regression: T = b0 + b1*n + b2*n^2.

    Uses ``numpy.polyfit`` with degree 2.  Target R^2 for latency
    scaling is 0.994.

    Args:
        x: Independent variable (e.g. agent count *n*).
        y: Dependent variable (e.g. latency *T*).

    Returns:
        :class:`RegressionResult` with 3 coefficients ``[b2, b1, b0]``.
    """
    x_arr = np.asarray(x, dtype=np.float64)
    y_arr = np.asarray(y, dtype=np.float64)

    coeffs = np.polyfit(x_arr, y_arr, deg=2)  # [b2, b1, b0]
    poly = np.poly1d(coeffs)

    y_pred = poly(x_arr)
    resid = y_arr - y_pred
    r2 = r_squared(y_arr, y_pred)

    return RegressionResult(
        coefficients=coeffs,
        r_squared=r2,
        residuals=resid,
        model_name="quadratic (y = b0 + b1*x + b2*x^2)",
        prediction_fn=lambda xv: np.poly1d(coeffs)(np.asarray(xv, dtype=np.float64)),
    )


# ---------------------------------------------------------------------------
# Log-linear regression
# ---------------------------------------------------------------------------

def _log_linear_model(x: np.ndarray, a: float, b: float) -> np.ndarray:
    """Internal model function: T = a + b * log(x)."""
    return a + b * np.log(x)


def fit_log_linear(x: np.ndarray, y: np.ndarray) -> RegressionResult:
    """Log-linear regression: T = a + b * log(n).

    Uses ``scipy.optimize.curve_fit`` with the natural logarithm.

    Args:
        x: Independent variable (must be > 0).
        y: Dependent variable.

    Returns:
        :class:`RegressionResult` with coefficients ``[a, b]``.

    Raises:
        ValueError: If any x value is <= 0.
    """
    x_arr = np.asarray(x, dtype=np.float64)
    y_arr = np.asarray(y, dtype=np.float64)

    if np.any(x_arr <= 0):
        raise ValueError("All x values must be positive for log-linear fit")

    popt, _ = curve_fit(_log_linear_model, x_arr, y_arr)
    coeffs = np.array(popt)

    y_pred = _log_linear_model(x_arr, *popt)
    resid = y_arr - y_pred
    r2 = r_squared(y_arr, y_pred)

    # Capture the coefficients in the closure to avoid late-binding issues
    a_fit, b_fit = float(popt[0]), float(popt[1])

    return RegressionResult(
        coefficients=coeffs,
        r_squared=r2,
        residuals=resid,
        model_name="log-linear (y = a + b*log(x))",
        prediction_fn=lambda xv: _log_linear_model(
            np.asarray(xv, dtype=np.float64), a_fit, b_fit
        ),
    )
