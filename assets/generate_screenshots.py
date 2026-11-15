import os
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

OUTPUT_DIR = Path("D:/Projeler/media-viewer/assets/screenshots")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
ASSETS_DIR = Path("D:/Projeler/media-viewer/assets")

# Fonts
FONT_BOLD = "C:/Windows/Fonts/segoeuib.ttf"
FONT_REG = "C:/Windows/Fonts/segoeui.ttf"

def get_font(size, bold=False):
    path = FONT_BOLD if bold else FONT_REG
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()

def draw_header(draw, title, subtitle):
    # Top title banner
    f_title = get_font(56, bold=True)
    f_sub = get_font(28, bold=False)
    
    # Title centered
    draw.text((540, 100), title, font=f_title, fill=(255, 255, 255), anchor="mm")
    # Subtitle centered
    draw.text((540, 160), subtitle, font=f_sub, fill=(56, 189, 248), anchor="mm")

def draw_phone_frame(base_img, x1=90, y1=240, x2=990, y2=1820, radius=54):
    # Outer drop shadow
    shadow = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(shadow)
    s_draw.rounded_rectangle([x1 - 10, y1 - 5, x2 + 10, y2 + 25], radius=radius + 10, fill=(0, 0, 0, 120))
    shadow = shadow.filter(ImageFilter.GaussianBlur(30))
    base_img.paste(shadow, (0, 0), shadow)

    # Phone bezel
    draw = ImageDraw.Draw(base_img)
    draw.rounded_rectangle([x1, y1, x2, y2], radius=radius, fill=(30, 41, 59), outline=(71, 85, 105), width=6)
    
    # Inner screen
    screen_rect = [x1 + 10, y1 + 10, x2 - 10, y2 - 10]
    draw.rounded_rectangle(screen_rect, radius=radius - 8, fill=(15, 23, 42))
    return screen_rect

def draw_status_bar(draw, x1, y1, x2):
    f_stat = get_font(22, bold=True)
    # Time
    draw.text((x1 + 35, y1 + 18), "09:41", font=f_stat, fill=(203, 213, 225))
    # Icons: 5G, Wifi, Bat
    draw.text((x2 - 120, y1 + 18), "5G  📶 🔋", font=get_font(18, bold=False), fill=(203, 213, 225))

# ── Screenshot 1: Gallery Screen ──────────────────────────────────────────
def create_screenshot_1():
    img = Image.new("RGB", (1080, 1920), color=(11, 15, 25))
    draw = ImageDraw.Draw(img)

    # Ambient background glow
    glow = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    g_draw = ImageDraw.Draw(glow)
    g_draw.ellipse([100, 50, 980, 800], fill=(37, 99, 235, 45))
    glow = glow.filter(ImageFilter.GaussianBlur(90))
    img.paste(glow, (0, 0), glow)
    draw = ImageDraw.Draw(img)

    draw_header(draw, "Hızlı & Akıcı Medya Galerisi", "Fotoğraf, video ve ses dosyalarınızı anında keşfedin")
    sx1, sy1, sx2, sy2 = draw_phone_frame(img)
    draw_status_bar(draw, sx1, sy1, sx2)

    # Top App Bar inside screen
    bar_y = sy1 + 55
    draw.rectangle([sx1, bar_y, sx2, bar_y + 80], fill=(30, 41, 59))
    
    # App Logo
    logo_path = ASSETS_DIR / "icon.png"
    if logo_path.exists():
        logo = Image.open(logo_path).resize((50, 50), Image.Resampling.LANCZOS)
        img.paste(logo, (sx1 + 25, bar_y + 15), logo)
    
    f_title = get_font(26, bold=True)
    draw.text((sx1 + 90, bar_y + 25), "Media Viewer", font=f_title, fill=(255, 255, 255))
    draw.text((sx1 + 90, bar_y + 53), "1.428 medya öğesi", font=get_font(18), fill=(148, 163, 184))

    # Top bar action icons
    draw.text((sx2 - 95, bar_y + 26), "📁   ⋮", font=get_font(28, bold=True), fill=(56, 189, 248))

    # Filter Tabs
    tab_y = bar_y + 95
    tabs = [("Tümü (1428)", True), ("Fotoğraflar", False), ("Videolar", False), ("Ses", False)]
    tx = sx1 + 25
    for label, active in tabs:
        bg_col = (37, 99, 235) if active else (30, 41, 59)
        txt_col = (255, 255, 255) if active else (148, 163, 184)
        tw = int(draw.textlength(label, font=get_font(20, bold=active))) + 36
        draw.rounded_rectangle([tx, tab_y, tx + tw, tab_y + 44], radius=22, fill=bg_col)
        draw.text((tx + 18, tab_y + 11), label, font=get_font(20, bold=active), fill=txt_col)
        tx += tw + 15

    # Media Grid (3 columns)
    grid_y = tab_y + 65
    cell_w = (sx2 - sx1 - 40) // 3
    
    # Palette of rich photo/video thumbnails
    colors = [
        ((220, 38, 38), "4K 02:45"),
        ((14, 165, 233), ""),
        ((168, 85, 247), "HEVC 00:38"),
        ((234, 88, 12), ""),
        ((16, 185, 129), "4K 04:12"),
        ((245, 158, 11), ""),
        ((99, 102, 241), "1080p 01:15"),
        ((236, 72, 153), ""),
        ((6, 182, 212), "60FPS 03:20"),
        ((139, 92, 246), ""),
        ((34, 197, 94), "4K 00:54"),
        ((244, 63, 94), ""),
    ]

    idx = 0
    for r in range(4):
        for c in range(3):
            if idx >= len(colors):
                break
            cx1 = sx1 + 15 + c * (cell_w + 5)
            cy1 = grid_y + r * (cell_w + 5)
            col, badge = colors[idx]
            
            # Simulated thumbnail photo gradient
            draw.rounded_rectangle([cx1, cy1, cx1 + cell_w, cy1 + cell_w], radius=12, fill=col)
            
            # If video, draw play icon and duration badge
            if badge:
                draw.rounded_rectangle([cx1 + 8, cy1 + cell_w - 32, cx1 + cell_w - 8, cy1 + cell_w - 8], radius=6, fill=(0, 0, 0, 180))
                draw.text((cx1 + 14, cy1 + cell_w - 28), f"▶ {badge}", font=get_font(14, bold=True), fill=(255, 255, 255))
            idx += 1

    # Bottom Banner Ad View
    ad_y = sy2 - 80
    draw.rectangle([sx1, ad_y, sx2, sy2], fill=(24, 24, 37))
    draw.rounded_rectangle([sx1 + 40, ad_y + 12, sx2 - 40, ad_y + 60], radius=8, fill=(39, 39, 58), outline=(71, 85, 105), width=1)
    draw.text((540, ad_y + 26), "📢 Google AdMob Sponsorlu Reklam Alanı", font=get_font(18, bold=True), fill=(148, 163, 184), anchor="mm")

    out_file = OUTPUT_DIR / "screenshot_1_gallery.png"
    img.save(out_file, format="PNG")
    print(f"Saved: {out_file}")

# ── Screenshot 2: 4K & HEVC Video Player ──────────────────────────────────
def create_screenshot_2():
    img = Image.new("RGB", (1080, 1920), color=(11, 15, 25))
    draw = ImageDraw.Draw(img)

    glow = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    g_draw = ImageDraw.Draw(glow)
    g_draw.ellipse([100, 50, 980, 800], fill=(168, 85, 247, 45))
    glow = glow.filter(ImageFilter.GaussianBlur(90))
    img.paste(glow, (0, 0), glow)
    draw = ImageDraw.Draw(img)

    draw_header(draw, "4K UHD & HEVC Video Oynatıcı", "Donanım hızlandırmalı, pürüzsüz ve parmakla yakınlaştırılabilir")
    sx1, sy1, sx2, sy2 = draw_phone_frame(img)
    draw_status_bar(draw, sx1, sy1, sx2)

    # Simulated Video Content (Panoramic Nature Gradient)
    vid_y1 = sy1 + 55
    vid_y2 = sy2 - 160
    
    # Draw rich dramatic landscape in video view
    v_img = Image.new("RGBA", (sx2 - sx1, vid_y2 - vid_y1))
    v_draw = ImageDraw.Draw(v_img)
    vh = vid_y2 - vid_y1
    for y in range(vh):
        ratio = y / vh
        r = int(15 * (1 - ratio) + 240 * ratio * (0.8 if ratio > 0.6 else 0.3))
        g = int(30 * (1 - ratio) + 120 * ratio)
        b = int(70 * (1 - ratio) + 80 * ratio)
        v_draw.line([(0, y), (sx2 - sx1, y)], fill=(r, g, b, 255))
    
    # Mountains & Sun
    v_draw.ellipse([400, vh//2 - 120, 600, vh//2 + 80], fill=(251, 191, 36, 230))
    v_draw.polygon([(50, vh - 200), (320, vh - 450), (600, vh - 200)], fill=(30, 41, 59, 255))
    v_draw.polygon([(400, vh - 200), (680, vh - 520), (950, vh - 200)], fill=(15, 23, 42, 255))
    img.paste(v_img, (sx1, vid_y1), v_img)

    draw = ImageDraw.Draw(img)

    # Top overlay bar (Video title + badges)
    draw.rectangle([sx1, vid_y1, sx2, vid_y1 + 80], fill=(0, 0, 0, 160))
    draw.text((sx1 + 30, vid_y1 + 25), "← 2026_Yaz_Tatili_4K_60FPS.mp4", font=get_font(24, bold=True), fill=(255, 255, 255))
    
    # Badges
    draw.rounded_rectangle([sx2 - 180, vid_y1 + 22, sx2 - 30, vid_y1 + 60], radius=8, fill=(37, 99, 235))
    draw.text((sx2 - 105, vid_y1 + 33), "HEVC / 4K", font=get_font(18, bold=True), fill=(255, 255, 255), anchor="mm")

    # Center Pinch-to-zoom indicator hint
    draw.rounded_rectangle([540 - 150, 850, 540 + 150, 910], radius=30, fill=(0, 0, 0, 170), outline=(56, 189, 248), width=2)
    draw.text((540, 878), "🔍 1.8x Yakınlaştırıldı (Pinch-to-Zoom)", font=get_font(18, bold=True), fill=(56, 189, 248), anchor="mm")

    # Video Player Bottom Controller Bar
    ctrl_y = vid_y2 - 150
    draw.rectangle([sx1, ctrl_y, sx2, sy2], fill=(15, 23, 42, 240))

    # Time labels & Scrubber slider
    draw.text((sx1 + 35, ctrl_y + 25), "02:14", font=get_font(20, bold=True), fill=(203, 213, 225))
    draw.text((sx2 - 95, ctrl_y + 25), "05:48", font=get_font(20), fill=(148, 163, 184))
    
    # Progress track
    track_x1, track_x2 = sx1 + 110, sx2 - 110
    draw.rounded_rectangle([track_x1, ctrl_y + 32, track_x2, ctrl_y + 40], radius=4, fill=(51, 65, 85))
    # Played progress
    cur_x = track_x1 + int((track_x2 - track_x1) * 0.42)
    draw.rounded_rectangle([track_x1, ctrl_y + 32, cur_x, ctrl_y + 40], radius=4, fill=(56, 189, 248))
    draw.ellipse([cur_x - 10, ctrl_y + 26, cur_x + 10, ctrl_y + 46], fill=(255, 255, 255))

    # Buttons row: Speed, Prev, Play, Next, Fullscreen, Trim
    btn_y = ctrl_y + 80
    draw.text((sx1 + 50, btn_y + 5), "1.0x", font=get_font(22, bold=True), fill=(56, 189, 248))
    draw.text((540 - 110, btn_y - 2), "⏮", font=get_font(32), fill=(255, 255, 255), anchor="mm")
    
    # Play circle button
    draw.ellipse([540 - 36, btn_y - 36, 540 + 36, btn_y + 36], fill=(37, 99, 235))
    draw.text((540 + 2, btn_y), "▶", font=get_font(30), fill=(255, 255, 255), anchor="mm")
    
    draw.text((540 + 110, btn_y - 2), "⏭", font=get_font(32), fill=(255, 255, 255), anchor="mm")
    draw.text((sx2 - 140, btn_y), "✂️ Kırp", font=get_font(20, bold=True), fill=(203, 213, 225), anchor="mm")
    draw.text((sx2 - 55, btn_y), "⛶", font=get_font(28), fill=(255, 255, 255), anchor="mm")

    out_file = OUTPUT_DIR / "screenshot_2_player.png"
    img.save(out_file, format="PNG")
    print(f"Saved: {out_file}")

# ── Screenshot 3: RTSP & M3U Live Stream ──────────────────────────────────
def create_screenshot_3():
    img = Image.new("RGB", (1080, 1920), color=(11, 15, 25))
    draw = ImageDraw.Draw(img)

    glow = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    g_draw = ImageDraw.Draw(glow)
    g_draw.ellipse([100, 50, 980, 800], fill=(16, 185, 129, 45))
    glow = glow.filter(ImageFilter.GaussianBlur(90))
    img.paste(glow, (0, 0), glow)
    draw = ImageDraw.Draw(img)

    draw_header(draw, "RTSP & M3U8 Canlı Ağ Akışı", "IP güvenlik kameraları ve canlı IPTV yayınları")
    sx1, sy1, sx2, sy2 = draw_phone_frame(img)
    draw_status_bar(draw, sx1, sy1, sx2)

    # Stream Dialog Panel
    p_x1, p_y1 = sx1 + 30, sy1 + 80
    p_x2, p_y2 = sx2 - 30, sy2 - 60
    draw.rounded_rectangle([p_x1, p_y1, p_x2, p_y2], radius=24, fill=(30, 41, 59), outline=(51, 65, 85), width=2)

    # Dialog Header
    draw.text((p_x1 + 30, p_y1 + 40), "📺 Ağ Akışı Aç (RTSP / HLS / M3U)", font=get_font(28, bold=True), fill=(255, 255, 255))
    draw.text((p_x1 + 30, p_y1 + 78), "IP kamera, NVR veya canlı HLS m3u8 akış linkini girin", font=get_font(18), fill=(148, 163, 184))

    # URL Input Box
    inp_y = p_y1 + 130
    draw.rounded_rectangle([p_x1 + 30, inp_y, p_x2 - 30, inp_y + 70], radius=12, fill=(15, 23, 42), outline=(56, 189, 248), width=2)
    draw.text((p_x1 + 50, inp_y + 22), "rtsp://admin:pass@192.168.1.100:554/stream1", font=get_font(20), fill=(241, 245, 249))

    # Protocol badges
    badge_y = inp_y + 90
    b_list = [("RTSP Kamera", True), ("M3U8 / HLS Canlı", False), ("RTMP Yayını", False)]
    bx = p_x1 + 30
    for b_title, b_active in b_list:
        b_col = (16, 185, 129) if b_active else (51, 65, 85)
        bw = int(draw.textlength(b_title, font=get_font(18, bold=True))) + 30
        draw.rounded_rectangle([bx, badge_y, bx + bw, badge_y + 38], radius=10, fill=b_col)
        draw.text((bx + 15, badge_y + 9), b_title, font=get_font(18, bold=True), fill=(255, 255, 255))
        bx += bw + 15

    # Simulated Live Camera Preview Window
    cam_y1 = badge_y + 70
    cam_y2 = cam_y1 + 540
    draw.rounded_rectangle([p_x1 + 30, cam_y1, p_x2 - 30, cam_y2], radius=16, fill=(15, 23, 42), outline=(71, 85, 105), width=2)
    
    # Cam preview pattern
    cam_img = Image.new("RGBA", (p_x2 - p_x1 - 60, cam_y2 - cam_y1))
    c_draw = ImageDraw.Draw(cam_img)
    ch = cam_y2 - cam_y1
    cw = p_x2 - p_x1 - 60
    for y in range(ch):
        c_draw.line([(0, y), (cw, y)], fill=(int(20 + y/15), int(35 + y/12), int(55 + y/10), 255))
    c_draw.rectangle([50, 100, cw - 50, ch - 80], fill=(24, 34, 53, 200), outline=(51, 65, 85), width=2)
    c_draw.text((cw // 2, ch // 2 - 20), "OFFICE_ENTRANCE_CAM_01", font=get_font(26, bold=True), fill=(255, 255, 255), anchor="mm")
    c_draw.text((cw // 2, ch // 2 + 25), "Bitrate: 4.8 Mbps  |  FPS: 30  |  Codec: H.265", font=get_font(18), fill=(56, 189, 248), anchor="mm")
    
    # Live recording indicator
    c_draw.rounded_rectangle([20, 20, 160, 60], radius=8, fill=(239, 68, 68, 220))
    c_draw.text((90, 40), "🔴 CANLI", font=get_font(20, bold=True), fill=(255, 255, 255), anchor="mm")
    
    img.paste(cam_img, (p_x1 + 30, cam_y1), cam_img)
    draw = ImageDraw.Draw(img)

    # Saved Bookmarks section
    book_y = cam_y2 + 30
    draw.text((p_x1 + 35, book_y), "⭐ Kayıtlı Canlı Akışlar", font=get_font(22, bold=True), fill=(255, 255, 255))

    streams = [
        ("Bahçe Güvenlik Kamerası (RTSP)", "rtsp://192.168.1.108:554/h264"),
        ("Ulusal Haber Kanalı Canlı (HLS)", "https://stream.provider.com/live.m3u8"),
    ]
    sy = book_y + 40
    for s_name, s_url in streams:
        draw.rounded_rectangle([p_x1 + 30, sy, p_x2 - 30, sy + 70], radius=12, fill=(15, 23, 42))
        draw.text((p_x1 + 50, sy + 14), s_name, font=get_font(20, bold=True), fill=(241, 245, 249))
        draw.text((p_x1 + 50, sy + 42), s_url, font=get_font(15), fill=(148, 163, 184))
        draw.text((p_x2 - 70, sy + 22), "▶", font=get_font(24), fill=(16, 185, 129))
        sy += 85

    # Action button
    draw.rounded_rectangle([p_x1 + 30, p_y2 - 80, p_x2 - 30, p_y2 - 20], radius=14, fill=(16, 185, 129))
    draw.text((540, p_y2 - 50), "▶ Akışı Başlat", font=get_font(24, bold=True), fill=(255, 255, 255), anchor="mm")

    out_file = OUTPUT_DIR / "screenshot_3_stream.png"
    img.save(out_file, format="PNG")
    print(f"Saved: {out_file}")

# ── Screenshot 4: Photo Editing & HD Upscale ──────────────────────────────
def create_screenshot_4():
    img = Image.new("RGB", (1080, 1920), color=(11, 15, 25))
    draw = ImageDraw.Draw(img)

    glow = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    g_draw = ImageDraw.Draw(glow)
    g_draw.ellipse([100, 50, 980, 800], fill=(234, 88, 12, 45))
    glow = glow.filter(ImageFilter.GaussianBlur(90))
    img.paste(glow, (0, 0), glow)
    draw = ImageDraw.Draw(img)

    draw_header(draw, "Fotoğraf Düzenleme & HD Netleştirme", "Renk ayarları, kayıpsız kırpma ve akıllı yükseltme")
    sx1, sy1, sx2, sy2 = draw_phone_frame(img)
    draw_status_bar(draw, sx1, sy1, sx2)

    # Top Toolbar
    bar_y = sy1 + 55
    draw.rectangle([sx1, bar_y, sx2, bar_y + 70], fill=(30, 41, 59))
    draw.text((sx1 + 30, bar_y + 22), "← Düzenle", font=get_font(24, bold=True), fill=(255, 255, 255))
    draw.rounded_rectangle([sx2 - 140, bar_y + 16, sx2 - 30, bar_y + 56], radius=8, fill=(37, 99, 235))
    draw.text((sx2 - 85, bar_y + 27), "Kaydet", font=get_font(18, bold=True), fill=(255, 255, 255), anchor="mm")

    # Center Image with Crop Grid Overlay
    img_y1 = bar_y + 75
    img_y2 = img_y1 + 820
    
    # Colorful portrait photo simulation
    c_img = Image.new("RGBA", (sx2 - sx1, img_y2 - img_y1))
    c_draw = ImageDraw.Draw(c_img)
    ch = img_y2 - img_y1
    cw = sx2 - sx1
    for y in range(ch):
        c_draw.line([(0, y), (cw, y)], fill=(int(40 + y/10), int(60 + y/8), int(90 + y/6), 255))
    c_draw.ellipse([cw//2 - 160, ch//2 - 200, cw//2 + 160, ch//2 + 120], fill=(244, 114, 182, 230))
    
    # Crop overlay box (Rule of Thirds)
    cx1, cy1 = 80, 100
    cx2, cy2 = cw - 80, ch - 100
    c_draw.rectangle([cx1, cy1, cx2, cy2], outline=(255, 255, 255), width=3)
    # Third lines
    w_third = (cx2 - cx1) // 3
    h_third = (cy2 - cy1) // 3
    c_draw.line([(cx1 + w_third, cy1), (cx1 + w_third, cy2)], fill=(255, 255, 255, 160), width=1)
    c_draw.line([(cx1 + 2 * w_third, cy1), (cx1 + 2 * w_third, cy2)], fill=(255, 255, 255, 160), width=1)
    c_draw.line([(cx1, cy1 + h_third), (cx2, cy1 + h_third)], fill=(255, 255, 255, 160), width=1)
    c_draw.line([(cx1, cy1 + 2 * h_third), (cx2, cy1 + 2 * h_third)], fill=(255, 255, 255, 160), width=1)

    img.paste(c_img, (sx1, img_y1), c_img)
    draw = ImageDraw.Draw(img)

    # Editing Tools Sheet (Bottom)
    sheet_y = img_y2 + 10
    draw.rounded_rectangle([sx1 + 20, sheet_y, sx2 - 20, sy2 - 20], radius=20, fill=(30, 41, 59))

    # Tool Tabs (Işık, Renk, Kırp, Akıllı HD)
    tool_tabs = ["🎨 Renk & Işık", "✂️ Kırp", "🔄 Döndür", "✨ Akıllı HD"]
    tx = sx1 + 40
    for idx, t_name in enumerate(tool_tabs):
        active = (idx == 0)
        t_col = (56, 189, 248) if active else (148, 163, 184)
        draw.text((tx, sheet_y + 25), t_name, font=get_font(20, bold=active), fill=t_col)
        if active:
            draw.rectangle([tx, sheet_y + 55, tx + 120, sheet_y + 58], fill=(56, 189, 248))
        tx += 175

    # Sliders (Parlaklık, Kontrast, Doygunluk)
    sliders = [
        ("Parlaklık", 0.65, "+15"),
        ("Kontrast", 0.72, "+22"),
        ("Doygunluk", 0.58, "+8"),
    ]
    s_y = sheet_y + 80
    for s_name, s_val, s_text in sliders:
        draw.text((sx1 + 45, s_y), s_name, font=get_font(18, bold=True), fill=(203, 213, 225))
        draw.text((sx2 - 90, s_y), s_text, font=get_font(18, bold=True), fill=(56, 189, 248))
        
        # Track
        sl_x1, sl_x2 = sx1 + 45, sx2 - 45
        draw.rounded_rectangle([sl_x1, s_y + 30, sl_x2, s_y + 38], radius=4, fill=(51, 65, 85))
        # Active
        act_x = sl_x1 + int((sl_x2 - sl_x1) * s_val)
        draw.rounded_rectangle([sl_x1, s_y + 30, act_x, s_y + 38], radius=4, fill=(56, 189, 248))
        draw.ellipse([act_x - 12, s_y + 22, act_x + 12, s_y + 46], fill=(255, 255, 255))
        s_y += 75

    out_file = OUTPUT_DIR / "screenshot_4_editor.png"
    img.save(out_file, format="PNG")
    print(f"Saved: {out_file}")

if __name__ == "__main__":
    print("Generating 4 Play Store Showcase Screenshots (1080x1920)...")
    create_screenshot_1()
    create_screenshot_2()
    create_screenshot_3()
    create_screenshot_4()
    print("All screenshots generated successfully!")
