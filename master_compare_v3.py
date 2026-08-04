from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple
import re

import numpy as np
import pandas as pd

# -----------------------------------------------------------------------------
# Parameter schema
# -----------------------------------------------------------------------------
TECH_PARAMS = [
    "A", "A2", "B", "H", "H2", "E1", "E2",
    "C", "C0", "Mt", "Mt0", "ML", "ML0",
]
DIM_PARAMS = ["A", "A2", "B", "H", "H2", "E1", "E2"]
CAPACITY_PARAMS = ["C", "C0", "Mt", "Mt0", "ML", "ML0"]
SCORING_PARAMS = DIM_PARAMS + CAPACITY_PARAMS

# The legacy Ball Rail tool clearly supports H2 +/- 5 mm and C thresholds of
# 80 % or 100 %. C0 is excluded from mandatory checks to match legacy behaviour:
# the original ASP tool displayed C0 for information only and never filtered on it.
# C0 remains visible in the parameter comparison table and its ratio is reported.
DEFAULT_MANDATORY = ["B", "H2", "C"]

# Prototype model parameters. The old ASP files did not contain an exponential
# similarity function or a complete scale table. These values must therefore be
# treated as configurable prototype settings and calibrated before production.
PROTOTYPE_DIMENSION_SCALES_MM = {
    "A": 5.0,
    "A2": 5.0,
    "B": 5.0,
    "H": 5.0,
    "H2": 5.0,
    "E1": 5.0,
    "E2": 5.0,
}

# Configurable prototype weighting. The old ASP tool did not use group weights.
DEFAULT_WEIGHTS = {"dimensions": 0.55, "capacity": 0.45}


@dataclass
class CompareConfig:
    """Configuration for the technical comparison.

    b_rule:
        "legacy_max_plus" reproduces the traceable legacy Ball Rail condition
        B_candidate <= B_reference + b_tolerance_mm.
        "symmetric" uses |B_candidate - B_reference| <= b_tolerance_mm.

    mode:
        "strict" requires 100 % of the reference C/C0 value.
        "relaxed_80" requires 80 %.
    """

    mode: str = "relaxed_80"
    top_n: int = 10
    compare_all: bool = True

    # Traceable legacy default for Ball Rail: candidate B may be at most 5 mm
    # longer than the reference. The UI may expose a symmetric rule separately.
    b_rule: str = "legacy_max_plus"  # legacy_max_plus | symmetric

    # C0 is intentionally excluded from DEFAULT_MANDATORY. It is reported as a
    # ratio in the results but is not used as an eligibility gate, matching the
    # behaviour of the reviewed legacy ASP tool.
    b_tolerance_mm: float = 5.0

    # Traceable legacy Ball Rail option: H2 +/- 5 mm.
    h2_tolerance_mm: float = 5.0

    # New quality-control parameter; not present in the old ASP tool.
    min_coverage: float = 0.60

    # New scoring parameters; not present in the old ASP tool.
    weights: Optional[Dict[str, float]] = None
    dimension_scales_mm: Optional[Dict[str, float]] = None

    mandatory_params: Optional[List[str]] = None
    include_parameter_scores: bool = True


def _to_num(value) -> float:
    """Convert a cell value to float without treating missing data as zero."""
    if value is None or pd.isna(value):
        return np.nan
    if isinstance(value, (int, float, np.integer, np.floating)):
        return float(value)

    text = str(value).strip()
    if text.lower() in {"", "-", "nan", "none", "null"}:
        return np.nan

    # Ambiguous compound values are not silently reduced to the first number.
    if "/" in text:
        return np.nan

    text = text.replace("\u00a0", " ").replace("\u202f", " ").replace(" ", "")
    if "," in text and "." in text:
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    else:
        text = text.replace(",", ".")

    text = re.sub(r"[^0-9eE+.-]", "", text)
    try:
        return float(text)
    except ValueError:
        return np.nan


def _text(value) -> str:
    if value is None or pd.isna(value):
        return "-"
    value = str(value).strip()
    return value if value else "-"


def _model_id(row: pd.Series) -> str:
    one = _text(row.get("Model_Description_1"))
    two = _text(row.get("Model_Description_2"))
    return one if two == "-" else f"{one} | {two}"


def normalize_dynamic_to_100km(value, reference_distance_km) -> float:
    """Normalize a dynamic rating to a 100 km reference distance.

    Formula retained from the reviewed legacy Ball Rail/Roller Rail code:
        X_100 = X_R * (R / 100) ** (1/3)

    This helper is intentionally not called automatically. It should be applied
    during master-data preparation only when the source reference distance is
    known and the formula is valid for the relevant product/rating type.
    """
    value = _to_num(value)
    reference_distance_km = _to_num(reference_distance_km)
    if pd.isna(value) or pd.isna(reference_distance_km) or reference_distance_km <= 0:
        return np.nan
    return float(value * (reference_distance_km / 100.0) ** (1.0 / 3.0))


def load_master_dataset(workbook_path: Path | str) -> pd.DataFrame:
    path = Path(workbook_path)
    if not path.exists():
        raise FileNotFoundError(f"Master workbook not found: {path}")

    df = pd.read_excel(path)
    needed = {"Manufacturer", "Model_Description_1", "Model_Description_2"}
    missing = needed - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")

    out = df.copy()
    for col in TECH_PARAMS:
        out[col] = out[col].map(_to_num) if col in out else np.nan
    for col in ["Manufacturer", "Model_Description_1", "Model_Description_2"]:
        out[col] = out[col].map(_text)

    out["MODEL_ID"] = out.apply(_model_id, axis=1)
    keep = out[TECH_PARAMS].notna().any(axis=1) | out["MODEL_ID"].ne("-")
    return out[keep].reset_index(drop=True)


def _validate_config(cfg: CompareConfig) -> None:
    if cfg.mode not in {"strict", "relaxed_80"}:
        raise ValueError("mode must be 'strict' or 'relaxed_80'")
    if cfg.b_rule not in {"legacy_max_plus", "symmetric"}:
        raise ValueError("b_rule must be 'legacy_max_plus' or 'symmetric'")
    if cfg.top_n < 1:
        raise ValueError("top_n must be at least 1")
    if not 0.0 <= cfg.min_coverage <= 1.0:
        raise ValueError("min_coverage must be between 0 and 1")
    if cfg.b_tolerance_mm < 0 or cfg.h2_tolerance_mm < 0:
        raise ValueError("dimensional tolerances must be non-negative")

    weights = cfg.weights or DEFAULT_WEIGHTS
    if not weights or any(v < 0 for v in weights.values()) or sum(weights.values()) <= 0:
        raise ValueError("weights must be non-negative and sum to more than zero")

    scales = cfg.dimension_scales_mm or PROTOTYPE_DIMENSION_SCALES_MM
    missing_scales = set(DIM_PARAMS) - set(scales)
    if missing_scales:
        raise ValueError(f"Missing dimension scales: {sorted(missing_scales)}")
    if any(float(scales[p]) <= 0 for p in DIM_PARAMS):
        raise ValueError("all dimension scales must be greater than zero")


def _ratio(candidate, source) -> float:
    if pd.isna(candidate) or pd.isna(source) or float(source) == 0:
        return np.nan
    return float(candidate) / float(source)


def _dimension_similarity(source, candidate, scale_mm) -> float:
    if pd.isna(source) or pd.isna(candidate):
        return np.nan
    scale = float(scale_mm)
    if scale <= 0:
        raise ValueError("scale_mm must be greater than zero")
    return float(np.exp(-abs(float(candidate) - float(source)) / scale))


def _capacity_similarity(source, candidate) -> float:
    ratio = _ratio(candidate, source)
    if pd.isna(ratio):
        return np.nan
    return float(min(1.0, max(0.0, ratio)))


def _weighted_available_score(scores: Dict[str, float], weights: Dict[str, float]) -> float:
    available = [
        (float(scores[k]), float(weights[k]))
        for k in weights
        if k in scores and pd.notna(scores[k]) and float(weights[k]) > 0
    ]
    if not available:
        return np.nan
    return sum(score * weight for score, weight in available) / sum(weight for _, weight in available)


def _mean_available(values: Iterable[float]) -> float:
    vals = [float(v) for v in values if pd.notna(v)]
    return float(np.mean(vals)) if vals else np.nan


def _coverage(src: pd.Series, cand: pd.Series, params: List[str]) -> Tuple[float, List[str]]:
    available = 0
    missing: List[str] = []
    for param in params:
        if pd.notna(src.get(param)) and pd.notna(cand.get(param)):
            available += 1
        else:
            missing.append(param)
    return (available / len(params) if params else 0.0), missing


def _mandatory_checks(
    src: pd.Series, cand: pd.Series, cfg: CompareConfig
) -> Tuple[bool, Dict[str, str]]:
    threshold = 1.0 if cfg.mode == "strict" else 0.8
    mandatory = cfg.mandatory_params or DEFAULT_MANDATORY
    reasons: Dict[str, str] = {}

    for param in mandatory:
        source = src.get(param)
        candidate = cand.get(param)

        if pd.isna(source):
            reasons[param] = "NOT CHECKED: reference value missing"
            continue
        if pd.isna(candidate):
            reasons[param] = "FAIL: candidate value missing"
            return False, reasons

        if param == "B":
            if cfg.b_rule == "legacy_max_plus":
                limit = float(source) + cfg.b_tolerance_mm
                ok = float(candidate) <= limit
                reasons[param] = (
                    f"{'PASS' if ok else 'FAIL'}: candidate {float(candidate):.2f} mm; "
                    f"maximum {limit:.2f} mm (reference + {cfg.b_tolerance_mm:.2f} mm)"
                )
            else:
                difference = abs(float(candidate) - float(source))
                ok = difference <= cfg.b_tolerance_mm
                reasons[param] = (
                    f"{'PASS' if ok else 'FAIL'}: absolute difference {difference:.2f} mm; "
                    f"allowed {cfg.b_tolerance_mm:.2f} mm"
                )

        elif param == "H2":
            difference = abs(float(candidate) - float(source))
            ok = difference <= cfg.h2_tolerance_mm
            reasons[param] = (
                f"{'PASS' if ok else 'FAIL'}: absolute difference {difference:.2f} mm; "
                f"allowed {cfg.h2_tolerance_mm:.2f} mm"
            )

        else:
            ratio = _ratio(candidate, source)
            ok = pd.notna(ratio) and ratio >= threshold
            ratio_text = "not calculable" if pd.isna(ratio) else f"{ratio:.3f}"
            reasons[param] = (
                f"{'PASS' if ok else 'FAIL'}: ratio {ratio_text}; required {threshold:.2f}"
            )

        if not ok:
            return False, reasons

    return True, reasons


def _score(src: pd.Series, cand: pd.Series, cfg: CompareConfig):
    scales = cfg.dimension_scales_mm or PROTOTYPE_DIMENSION_SCALES_MM
    dim_by_param = {
        p: _dimension_similarity(src.get(p), cand.get(p), scales[p])
        for p in DIM_PARAMS
    }
    cap_by_param = {
        p: _capacity_similarity(src.get(p), cand.get(p))
        for p in CAPACITY_PARAMS
    }

    groups = {
        "dimensions": _mean_available(dim_by_param.values()),
        "capacity": _mean_available(cap_by_param.values()),
    }
    weights = cfg.weights or DEFAULT_WEIGHTS
    total = _weighted_available_score(groups, weights)
    return total, groups, {**dim_by_param, **cap_by_param}


def compare_master(
    master_df: pd.DataFrame,
    source_company: str,
    source_model_id: str,
    target_company: Optional[str],
    cfg: CompareConfig,
) -> pd.DataFrame:
    _validate_config(cfg)

    source_rows = master_df[
        (master_df["Manufacturer"].astype(str) == str(source_company))
        & (master_df["MODEL_ID"].astype(str) == str(source_model_id))
    ]
    if source_rows.empty:
        raise ValueError(f"Source model not found: {source_company} / {source_model_id}")
    src = source_rows.iloc[0]

    if cfg.compare_all or not target_company:
        candidates = master_df[master_df["Manufacturer"] != source_company]
    else:
        candidates = master_df[
            (master_df["Manufacturer"] == target_company)
            & (master_df["Manufacturer"] != source_company)
        ]

    rows = []
    for _, cand in candidates.iterrows():
        passed, checks = _mandatory_checks(src, cand, cfg)
        if not passed:
            continue

        coverage, missing = _coverage(src, cand, SCORING_PARAMS)
        if coverage < cfg.min_coverage:
            continue

        score, groups, per_param = _score(src, cand, cfg)
        if pd.isna(score):
            continue

        comparable_count = len(SCORING_PARAMS) - len(missing)
        row = {
            "Target_Company": cand.get("Manufacturer"),
            "Target_Model": cand.get("MODEL_ID"),
            "Similarity_Score": score,
            "Data_Coverage": coverage,
            "Comparable_Parameter_Count": comparable_count,
            "Total_Scoring_Parameter_Count": len(SCORING_PARAMS),
            "C_Ratio": _ratio(cand.get("C"), src.get("C")),
            "C0_Ratio": _ratio(cand.get("C0"), src.get("C0")),
            "Dimensions_Score": groups["dimensions"],
            "Capacity_Score": groups["capacity"],
            "Mandatory_Checks": " | ".join(f"{k}: {v}" for k, v in checks.items()),
            "Missing_Comparisons": ", ".join(missing) if missing else "None",
            "B_Rule": cfg.b_rule,
            "Comparison_Mode": cfg.mode,
        }

        if cfg.include_parameter_scores:
            for param, value in per_param.items():
                row[f"Score_{param}"] = value

        for param in TECH_PARAMS:
            row[f"Source_{param}"] = src.get(param)
            row[f"Target_{param}"] = cand.get(param)

        rows.append(row)

    if not rows:
        return pd.DataFrame(
            columns=[
                "Target_Company",
                "Target_Model",
                "Similarity_Score",
                "Data_Coverage",
            ]
        )

    return (
        pd.DataFrame(rows)
        .sort_values(
            ["Similarity_Score", "Data_Coverage"],
            ascending=[False, False],
        )
        .head(cfg.top_n)
        .reset_index(drop=True)
    )


def list_companies(df: pd.DataFrame) -> List[str]:
    return sorted(df["Manufacturer"].dropna().astype(str).unique().tolist())


def list_models(df: pd.DataFrame, company: str) -> List[str]:
    return sorted(
        df.loc[df["Manufacturer"] == company, "MODEL_ID"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )
