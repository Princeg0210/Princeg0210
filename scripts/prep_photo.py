#!/usr/bin/env python3
"""
Prepare a photo or avatar for clean ASCII conversion:
  1. Isolate the subject / remove background
  2. Increase contrast and balance tones
  3. Crop square and save as source-prepped.png

Usage:
    python scripts/prep_photo.py <input.png> [output.png]
"""
import os
import sys
import numpy as np
from PIL import Image, ImageOps, ImageEnhance, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
INP = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "source-photo.png")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "source-prepped.png")

has_cv2 = False
has_rembg = False

try:
    import cv2
    has_cv2 = True
except ImportError:
    pass

try:
    from rembg import remove
    has_rembg = True
except ImportError:
    pass


def prep_advanced(inp_path, out_path):
    LINE_WEIGHT = 0.6
    cut = remove(Image.open(inp_path).convert("RGBA"))
    rgb = np.array(cut.convert("RGB"))
    alpha = np.array(cut.split()[-1])
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)

    smooth = gray
    for _ in range(3):
        smooth = cv2.bilateralFilter(smooth, 9, 40, 9)

    subject_mask = alpha > 128
    if np.any(subject_mask):
        lo, hi = np.percentile(smooth[subject_mask], [2, 92])
        tone = np.clip((smooth.astype(np.float32) - lo) / max(1e-5, (hi - lo)), 0, 1)
    else:
        tone = smooth.astype(np.float32) / 255.0

    fine = cv2.GaussianBlur(smooth, (0, 0), 1.5).astype(np.float32)
    coarse = cv2.GaussianBlur(smooth, (0, 0), 6).astype(np.float32)
    lines = np.clip((coarse - fine) / 40.0, 0, 1)
    out = np.clip(tone - LINE_WEIGHT * lines, 0, 1) * 255

    mask = cv2.GaussianBlur(alpha.astype(np.float32) / 255.0, (0, 0), 1.0)
    out = out * mask + 255.0 * (1.0 - mask)

    ys, xs = np.where(alpha > 20)
    if len(xs) > 0 and len(ys) > 0:
        side = max(xs.max() - xs.min(), ys.max() - ys.min()) + 60
        cx, cy = (xs.min() + xs.max()) // 2, (ys.min() + ys.max()) // 2
        canvas = np.full((side, side), 255, np.uint8)
        x0, y0 = cx - side // 2, cy - side // 2
        sx0, sy0 = max(x0, 0), max(y0, 0)
        sx1, sy1 = min(x0 + side, out.shape[1]), min(y0 + side, out.shape[0])
        canvas[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0] = out[sy0:sy1, sx0:sx1].astype(np.uint8)
        img_out = Image.fromarray(canvas, mode="L")
    else:
        img_out = Image.fromarray(out.astype(np.uint8), mode="L")

    img_out.save(out_path)
    print("Wrote (rembg+cv2):", out_path)


def prep_pillow(inp_path, out_path):
    img = Image.open(inp_path).convert("RGBA")
    # Make background white if transparent
    bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
    combined = Image.alpha_composite(bg, img).convert("L")

    # Center crop square
    w, h = combined.size
    side = min(w, h)
    left = (w - side) // 2
    top = (h - side) // 2
    cropped = combined.crop((left, top, left + side, top + side))

    # Enhance contrast
    enhancer = ImageEnhance.Contrast(cropped)
    enhanced = enhancer.enhance(1.4)
    enhanced.save(out_path)
    print("Wrote (pillow fallback):", out_path)


if __name__ == "__main__":
    if has_cv2 and has_rembg:
        try:
            prep_advanced(INP, OUT)
        except Exception as e:
            print("Advanced prep failed, falling back to pillow:", e)
            prep_pillow(INP, OUT)
    else:
        prep_pillow(INP, OUT)
