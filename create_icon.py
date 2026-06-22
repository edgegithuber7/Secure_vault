"""
create_icon.py – Generate SecureVault icon files.

Run this once before packaging:
    pip install Pillow
    python create_icon.py

Outputs:
    assets/icon_16.png  … assets/icon_512.png
    assets/icon.ico          (Windows – multi-size)

On macOS the build script converts the PNGs to icon.icns automatically via
`iconutil`.  You don't need to do anything extra there.
"""

from __future__ import annotations

import os
from PIL import Image, ImageDraw

SIZES   = [16, 32, 48, 64, 128, 256, 512]
BG      = (10,  12,  32)   # dark navy
ACCENT  = (99,  102, 241)  # indigo
ASSETS  = os.path.join(os.path.dirname(__file__), "assets")


def draw_icon(size: int) -> Image.Image:
    img  = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # ── Background rounded rectangle ──────────────────────────────────
    pad  = max(1, size // 12)
    r_bg = max(4, size // 5)
    draw.rounded_rectangle(
        [pad, pad, size - pad, size - pad],
        radius=r_bg,
        fill=(*BG, 255),
    )

    cx = size // 2

    # ── Padlock proportions (relative to size) ─────────────────────────
    body_w  = int(size * 0.52)
    body_h  = int(size * 0.32)
    body_x  = cx - body_w // 2
    body_y  = int(size * 0.51)
    body_r  = max(2, size // 22)

    shackle_cx    = cx
    shackle_cy    = body_y                        # shackle centred at body top
    shackle_outer = int(size * 0.20)              # outer radius
    shackle_thick = max(2, int(size * 0.07))      # ring thickness
    shackle_inner = shackle_outer - shackle_thick

    # ── Draw shackle (ring, then cut bottom half) ──────────────────────
    # 1. Outer filled circle in accent colour
    draw.ellipse(
        [shackle_cx - shackle_outer, shackle_cy - shackle_outer,
         shackle_cx + shackle_outer, shackle_cy + shackle_outer],
        fill=(*ACCENT, 255),
    )
    # 2. Inner filled circle in background colour (creates ring)
    draw.ellipse(
        [shackle_cx - shackle_inner, shackle_cy - shackle_inner,
         shackle_cx + shackle_inner, shackle_cy + shackle_inner],
        fill=(*BG, 255),
    )
    # 3. Cover bottom half of ring (lock body will redraw over this area)
    draw.rectangle(
        [shackle_cx - shackle_outer - 1, shackle_cy,
         shackle_cx + shackle_outer + 1, shackle_cy + shackle_outer + 1],
        fill=(*BG, 255),
    )

    # ── Draw lock body ─────────────────────────────────────────────────
    draw.rounded_rectangle(
        [body_x, body_y, body_x + body_w, body_y + body_h],
        radius=body_r,
        fill=(*ACCENT, 255),
    )

    # ── Keyhole ────────────────────────────────────────────────────────
    if size >= 32:
        kh_r  = max(2, int(size * 0.045))
        kh_cx = cx
        kh_cy = body_y + body_h * 2 // 5
        draw.ellipse(
            [kh_cx - kh_r, kh_cy - kh_r, kh_cx + kh_r, kh_cy + kh_r],
            fill=(*BG, 255),
        )
        slot_w = max(1, kh_r - 1)
        slot_h = int(body_h * 0.30)
        draw.rectangle(
            [kh_cx - slot_w // 2, kh_cy,
             kh_cx + slot_w // 2, kh_cy + slot_h],
            fill=(*BG, 255),
        )

    return img


def main() -> None:
    os.makedirs(ASSETS, exist_ok=True)

    images: list[Image.Image] = []
    for size in SIZES:
        img  = draw_icon(size)
        path = os.path.join(ASSETS, f"icon_{size}.png")
        img.save(path, "PNG")
        images.append(img)
        print(f"  {path}")

    # Windows ICO (multi-resolution)
    ico_path = os.path.join(ASSETS, "icon.ico")
    images[0].save(
        ico_path,
        format="ICO",
        sizes=[(s, s) for s in SIZES if s <= 256],
        append_images=images[1:],
    )
    print(f"  {ico_path}")
    print("Done.  On macOS run build.sh to convert PNGs to icon.icns automatically.")


if __name__ == "__main__":
    main()
