"""Standalone (system python3, PIL+numpy) extraction of real proportions from the Hud Lab
reference photos, so the parametric Blender build uses MEASURED curves instead of hand-guessed
control points. Run with: python3 extract_reference_profiles.py
Writes numeric arrays to /home/user/Blender/blender/output/extracted_profiles.json
"""
import numpy as np
from PIL import Image
import json

REF = "/home/user/Blender/reference"
OUT = "/home/user/Blender/blender/output/extracted_profiles.json"

THRESH = 235  # pixels darker than this (out of 255) count as "product"


def load_mask(path):
    im = Image.open(path).convert("L")
    arr = np.array(im)
    return arr < THRESH


def find_column_gaps(mask):
    """Find the empty (all-white) vertical gap that separates the left/right shoe."""
    col_has_product = mask.any(axis=0)
    return col_has_product


def split_pair(mask):
    """Split a left+right pair image into two masks, one per shoe, by finding the white gap."""
    col_has_product = find_column_gaps(mask)
    cols = np.where(col_has_product)[0]
    xmin, xmax = cols.min(), cols.max()
    # find the widest gap of all-False columns between xmin and xmax
    region = col_has_product[xmin:xmax + 1]
    gap_start, gap_len, best_start, best_len = None, 0, None, 0
    for i, v in enumerate(region):
        if not v:
            if gap_start is None:
                gap_start = i
            gap_len += 1
        else:
            if gap_len > best_len:
                best_len, best_start = gap_len, gap_start
            gap_start, gap_len = None, 0
    if gap_len > best_len:
        best_len, best_start = gap_len, gap_start
    split_col = xmin + best_start + best_len // 2
    left_mask = mask[:, :split_col]
    right_mask = mask[:, split_col:]
    return left_mask, right_mask


def bbox(mask):
    rows = np.where(mask.any(axis=1))[0]
    cols = np.where(mask.any(axis=0))[0]
    return rows.min(), rows.max(), cols.min(), cols.max()


def top_view_width_profile(mask, n_samples=120):
    """Row-wise width extent, normalized. Returns list of (t, half_width_normalized)
    where t=0..1 along the row axis (image rows), half_width normalized by overall shoe length
    (so it can be directly compared/scaled to real mm later)."""
    rmin, rmax, cmin, cmax = bbox(mask)
    length_px = rmax - rmin
    profile = []
    for i in range(n_samples + 1):
        r = int(round(rmin + i * length_px / n_samples))
        r = min(r, mask.shape[0] - 1)
        row = mask[r, :]
        cols = np.where(row)[0]
        if len(cols) == 0:
            half_width_norm = 0.0
        else:
            width_px = cols.max() - cols.min()
            half_width_norm = (width_px / 2) / length_px
        t = i / n_samples
        profile.append((round(t, 4), round(float(half_width_norm), 5)))
    return profile, length_px


def side_view_profiles(mask, n_samples=140):
    """Column-wise top-line and bottom-line, normalized by the overall length (x-extent)."""
    rmin, rmax, cmin, cmax = bbox(mask)
    length_px = cmax - cmin
    top_line, bottom_line = [], []
    for i in range(n_samples + 1):
        c = int(round(cmin + i * length_px / n_samples))
        c = min(c, mask.shape[1] - 1)
        col = mask[:, c]
        rows = np.where(col)[0]
        t = i / n_samples
        if len(rows) == 0:
            top_line.append((t, None))
            bottom_line.append((t, None))
        else:
            # image rows increase downward; "top" of the product = min row, "bottom" = max row
            top_norm = (rows.min() - rmin) / length_px
            bottom_norm = (rows.max() - rmin) / length_px
            top_line.append((round(t, 4), round(float(top_norm), 5)))
            bottom_line.append((round(t, 4), round(float(bottom_norm), 5)))
    return top_line, bottom_line, length_px


def main():
    result = {}

    # --- Top view (ref_01): sole width profile ---
    mask_top = load_mask(f"{REF}/ref_01_top_pair.webp")
    left, right = split_pair(mask_top)
    profile_l, len_l = top_view_width_profile(left)
    profile_r, len_r = top_view_width_profile(right)
    result["top_view_width_profile_left"] = profile_l
    result["top_view_width_profile_right"] = profile_r
    result["top_view_length_px"] = {"left": int(len_l), "right": int(len_r)}

    # --- Side view (ref_05): overall silhouette top/bottom lines ---
    mask_side = load_mask(f"{REF}/ref_05_side_profile.webp")
    top_line, bottom_line, len_side = side_view_profiles(mask_side)
    result["side_view_top_line"] = top_line
    result["side_view_bottom_line"] = bottom_line
    result["side_view_length_px"] = int(len_side)

    with open(OUT, "w") as f:
        json.dump(result, f, indent=2)
    print("Wrote", OUT)
    print("Top view left bbox:", bbox(left))
    print("Top view right bbox:", bbox(right))
    print("Side view bbox:", bbox(mask_side))


if __name__ == "__main__":
    main()
