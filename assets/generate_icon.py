import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

def create_media_viewer_icon():
    # Render at 1024x1024 for pristine downsampling
    size = 1024
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 1. Base Squircle / Rounded App Badge with deep dark gradient
    # Create mask for squircle
    mask = Image.new("L", (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    margin = 48
    radius = 210
    mask_draw.rounded_rectangle(
        [margin, margin, size - margin, size - margin],
        radius=radius,
        fill=255
    )

    # Create background gradient
    bg = Image.new("RGBA", (size, size))
    for y in range(size):
        ratio = y / size
        # Dark sapphire to deep midnight slate
        r = int(24 * (1 - ratio) + 12 * ratio)
        g = int(32 * (1 - ratio) + 16 * ratio)
        b = int(52 * (1 - ratio) + 28 * ratio)
        for x in range(size):
            # Diagonal gradient influence
            diag = (x + y) / (2 * size)
            r_val = int(28 * (1 - diag) + 10 * diag)
            g_val = int(38 * (1 - diag) + 14 * diag)
            b_val = int(62 * (1 - diag) + 24 * diag)
            bg.putpixel((x, y), (r_val, g_val, b_val, 255))

    img.paste(bg, (0, 0), mask)

    # 2. Outer Border with subtle glow
    border_img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    border_draw = ImageDraw.Draw(border_img)
    border_draw.rounded_rectangle(
        [margin, margin, size - margin, size - margin],
        radius=radius,
        outline=(56, 189, 248, 180),  # Cyan-blue highlight
        width=10
    )
    img = Image.alpha_composite(img, border_img)

    draw = ImageDraw.Draw(img)

    # 3. Camera Top Viewfinder Accent
    vf_x1, vf_y1 = 430, 200
    vf_x2, vf_y2 = 594, 260
    draw.rounded_rectangle([vf_x1, vf_y1, vf_x2, vf_y2], radius=22, fill=(45, 60, 92, 255), outline=(70, 95, 140, 255), width=6)

    # Red recording / flash dot
    dot_x, dot_y, dot_r = 740, 310, 24
    draw.ellipse([dot_x - dot_r, dot_y - dot_r, dot_x + dot_r, dot_y + dot_r], fill=(239, 68, 68, 255))
    # Flash dot small cyan status
    st_x, st_y, st_r = 284, 310, 16
    draw.ellipse([st_x - st_r, st_y - st_r, st_x + st_r, st_y + st_r], fill=(56, 189, 248, 255))

    # 4. Stylized Camera Body / Frame
    cam_x1, cam_y1 = 180, 250
    cam_x2, cam_y2 = 844, 794
    cam_radius = 110

    # Draw camera body
    draw.rounded_rectangle(
        [cam_x1, cam_y1, cam_x2, cam_y2],
        radius=cam_radius,
        fill=(22, 28, 46, 240),
        outline=(60, 80, 125, 255),
        width=10
    )

    # 5. Central Lens Ring (Vibrant Gradient Ring)
    cx, cy = 512, 522
    lens_r_outer = 210
    lens_r_inner = 158

    # Draw multi-colored gradient ring
    ring_img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ring_draw = ImageDraw.Draw(ring_img)

    steps = 360
    for i in range(steps):
        angle_rad = math.radians(i)
        next_rad = math.radians(i + 1.5)
        # Gradient from Cyan (0, 180, 255) -> Purple (168, 85, 247) -> Blue (37, 99, 235)
        t = i / 360.0
        if t < 0.5:
            r = int(0 * (1 - 2*t) + 168 * (2*t))
            g = int(180 * (1 - 2*t) + 85 * (2*t))
            b = int(255 * (1 - 2*t) + 247 * (2*t))
        else:
            t2 = (t - 0.5) * 2
            r = int(168 * (1 - t2) + 14 * t2)
            g = int(85 * (1 - t2) + 165 * t2)
            b = int(247 * (1 - t2) + 233 * t2)

        # Segment polygon
        p1 = (cx + lens_r_outer * math.cos(angle_rad), cy + lens_r_outer * math.sin(angle_rad))
        p2 = (cx + lens_r_outer * math.cos(next_rad), cy + lens_r_outer * math.sin(next_rad))
        p3 = (cx + lens_r_inner * math.cos(next_rad), cy + lens_r_inner * math.sin(next_rad))
        p4 = (cx + lens_r_inner * math.cos(angle_rad), cy + lens_r_inner * math.sin(angle_rad))
        ring_draw.polygon([p1, p2, p3, p4], fill=(r, g, b, 255))

    img = Image.alpha_composite(img, ring_img)

    # 6. Lens Center Dark Disc
    draw = ImageDraw.Draw(img)
    draw.ellipse(
        [cx - lens_r_inner + 4, cy - lens_r_inner + 4, cx + lens_r_inner - 4, cy + lens_r_inner - 4],
        fill=(15, 18, 30, 255)
    )

    # 7. Sleek Video Play Triangle (Center)
    # Triangle points with smooth optical center
    tx1 = cx - 45
    ty1 = cy - 95
    tx2 = cx - 45
    ty2 = cy + 95
    tx3 = cx + 80
    ty3 = cy

    # Soft drop shadow for play button
    shadow_img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(shadow_img)
    s_draw.polygon([(tx1 + 4, ty1 + 8), (tx2 + 4, ty2 + 8), (tx3 + 4, ty3 + 8)], fill=(0, 0, 0, 140))
    shadow_img = shadow_img.filter(ImageFilter.GaussianBlur(10))
    img = Image.alpha_composite(img, shadow_img)

    draw = ImageDraw.Draw(img)
    # Brilliant white play triangle with rounded appearance
    draw.polygon([(tx1, ty1), (tx2, ty2), (tx3, ty3)], fill=(255, 255, 255, 255))

    # Photo mountain/sun small accent in bottom-right of camera
    # A small subtle golden sun dot
    draw.ellipse([cam_x2 - 120, cam_y2 - 110, cam_x2 - 80, cam_y2 - 70], fill=(251, 191, 36, 220))

    # 8. Downscale with high quality Lanczos anti-aliasing to 512x512
    icon_512 = img.resize((512, 512), Image.Resampling.LANCZOS)

    assets_dir = Path("D:/Projeler/media-viewer/assets")
    assets_dir.mkdir(exist_ok=True)

    png_path = assets_dir / "icon.png"
    ico_path = assets_dir / "icon.ico"

    icon_512.save(png_path, format="PNG")
    print(f"Saved {png_path}")

    # Save Windows Multi-Resolution .ICO
    icon_sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    icon_512.save(ico_path, format="ICO", sizes=icon_sizes)
    print(f"Saved {ico_path} with sizes: {icon_sizes}")

if __name__ == "__main__":
    create_media_viewer_icon()
