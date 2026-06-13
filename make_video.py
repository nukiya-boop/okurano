"""
PR動画生成スクリプト
おもてなし・カウンターライブ感テーマ
"""

import os
import glob
import unicodedata
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from moviepy import ImageClip, concatenate_videoclips, CompositeVideoClip, VideoClip
from moviepy.video.fx import CrossFadeIn, CrossFadeOut

IMG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images")
OUTPUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pr_video.mp4")
FONT_PATH = "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf"
W, H = 1280, 720
FPS = 30

# glob でパスを解決し、NFC正規化してマップ化
_all_images = {
    unicodedata.normalize("NFC", os.path.basename(p)): p
    for p in glob.glob(os.path.join(IMG_DIR, "*.jpg"))
}

def img_path(name):
    return _all_images[name]

# 各画像に対するテロップ設定
SCENES = [
    {
        "file": "イメージ_接客0032.jpg",
        "main": "一期一会の\nおもてなし",
        "sub": "— 心を込めたサービスをお届けします —",
        "duration": 5.0,
    },
    {
        "file": "イメージ_接客0034修.jpg",
        "main": "あなたの笑顔が\n私たちの誇り",
        "sub": "— すべてのお客様に最高の時間を —",
        "duration": 5.0,
    },
    {
        "file": "イメージ_接客0128.jpg",
        "main": "カウンターで\n紡ぐひととき",
        "sub": "— 目の前で広がる、臨場感あふれる空間 —",
        "duration": 5.0,
    },
    {
        "file": "イメージ_接客0136.jpg",
        "main": "ライブ感あふれる\nカウンター席",
        "sub": "— 職人の技を間近で感じてください —",
        "duration": 5.0,
    },
    {
        "file": "切子グラス0004.jpg",
        "main": "美しい器に\n宿る粋",
        "sub": "— 細部までこだわり抜いた、上質な空間 —",
        "duration": 5.0,
    },
    {
        "file": "切子グラス0006 (1).jpg",
        "main": "伝統と革新が\n交わる場所",
        "sub": "— 特別な夜を、ぜひ私たちと —",
        "duration": 5.0,
    },
    {
        "file": "イメージ_お食事シーン0183.jpg",
        "main": "食で彩る\n至福のひととき",
        "sub": "— 全力のおもてなしで、お待ちしております —",
        "duration": 6.0,
    },
]

CROSSFADE = 1.2  # 秒


def load_font(size):
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except Exception:
        return ImageFont.load_default()


def fit_image(img: Image.Image, w: int, h: int) -> Image.Image:
    """アスペクト比を保ちながらクロップしてリサイズ"""
    iw, ih = img.size
    scale = max(w / iw, h / ih)
    nw, nh = int(iw * scale), int(ih * scale)
    img = img.resize((nw, nh), Image.LANCZOS)
    left = (nw - w) // 2
    top = (nh - h) // 2
    return img.crop((left, top, left + w, top + h))


def make_gradient_overlay(w, h, alpha_top=180, alpha_bottom=220):
    """下部グラデーションオーバーレイ"""
    arr = np.zeros((h, w, 4), dtype=np.uint8)
    for y in range(h):
        t = y / h
        if t < 0.45:
            a = 0
        elif t < 0.65:
            a = int((t - 0.45) / 0.20 * alpha_top)
        else:
            a = int(alpha_top + (t - 0.65) / 0.35 * (alpha_bottom - alpha_top))
        arr[y, :, 3] = min(a, 255)
    return Image.fromarray(arr, "RGBA")


def draw_telop(img: Image.Image, main_text: str, sub_text: str, progress: float) -> Image.Image:
    """
    テロップを描画。progress=0→1 でフェードイン。
    """
    canvas = img.convert("RGBA")
    overlay = make_gradient_overlay(W, H)
    canvas = Image.alpha_composite(canvas, overlay)

    draw = ImageDraw.Draw(canvas)

    # --- メインテロップ ---
    font_main = load_font(72)
    font_sub = load_font(30)

    alpha = int(min(progress * 3, 1.0) * 255)

    # メインテキスト（中央下寄り）
    lines = main_text.split("\n")
    line_height = 80
    total_h = len(lines) * line_height
    y_start = H - 240

    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font_main)
        tw = bbox[2] - bbox[0]
        x = (W - tw) // 2
        y = y_start + i * line_height

        # 影
        shadow_img = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        sd = ImageDraw.Draw(shadow_img)
        sd.text((x + 3, y + 3), line, font=font_main, fill=(0, 0, 0, alpha // 2))
        canvas = Image.alpha_composite(canvas, shadow_img)

        # 本文（ゴールド）
        text_img = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        td = ImageDraw.Draw(text_img)
        td.text((x, y), line, font=font_main, fill=(220, 185, 120, alpha))
        canvas = Image.alpha_composite(canvas, text_img)

    # --- サブテロップ ---
    bbox = draw.textbbox((0, 0), sub_text, font=font_sub)
    tw = bbox[2] - bbox[0]
    x = (W - tw) // 2
    y = y_start + total_h + 12

    sub_alpha = int(min(max(progress * 3 - 0.5, 0), 1.0) * 200)
    sub_img = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    sd2 = ImageDraw.Draw(sub_img)
    sd2.text((x, y), sub_text, font=font_sub, fill=(240, 230, 210, sub_alpha))
    canvas = Image.alpha_composite(canvas, sub_img)

    # --- 装飾ライン ---
    line_alpha = int(min(progress * 4, 1.0) * 180)
    line_img = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(line_img)
    lw = 400
    lx = (W - lw) // 2
    ly = y_start - 18
    ld.line([(lx, ly), (lx + lw, ly)], fill=(220, 185, 120, line_alpha), width=1)
    canvas = Image.alpha_composite(canvas, line_img)

    return canvas.convert("RGB")


def make_scene_clip(scene: dict, zoom: bool = True) -> VideoClip:
    path = img_path(scene["file"])
    base_img = fit_image(Image.open(path).convert("RGB"), W, H)
    base_arr = np.array(base_img)
    duration = scene["duration"]
    main_text = scene["main"]
    sub_text = scene["sub"]

    def make_frame(t):
        progress = min(t / 1.5, 1.0)

        if zoom:
            # ゆっくりズームイン (1.0 → 1.06)
            scale = 1.0 + 0.06 * (t / duration)
            nw = int(W * scale)
            nh = int(H * scale)
            img = Image.fromarray(base_arr).resize((nw, nh), Image.LANCZOS)
            ox = (nw - W) // 2
            oy = (nh - H) // 2
            img = img.crop((ox, oy, ox + W, oy + H))
        else:
            img = Image.fromarray(base_arr)

        img = draw_telop(img, main_text, sub_text, progress)
        return np.array(img)

    clip = VideoClip(make_frame, duration=duration)
    clip = clip.with_fps(FPS)
    return clip


def make_opening_clip(duration=3.0):
    """黒背景にタイトル"""
    font_title = load_font(90)
    font_sub = load_font(36)

    def make_frame(t):
        progress = min(t / 1.2, 1.0)
        img = Image.new("RGB", (W, H), (8, 8, 8))
        canvas = img.convert("RGBA")
        alpha = int(progress * 255)

        # タイトル
        title = "OKURANO"
        draw = ImageDraw.Draw(canvas)
        bbox = draw.textbbox((0, 0), title, font=font_title)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        x = (W - tw) // 2
        y = H // 2 - th // 2 - 30

        t_img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        td = ImageDraw.Draw(t_img)
        td.text((x, y), title, font=font_title, fill=(220, 185, 120, alpha))
        canvas = Image.alpha_composite(canvas, t_img)

        # サブタイトル
        sub = "— 最高のおもてなしを、あなたへ —"
        sub_alpha = int(min(max(progress * 2 - 0.5, 0), 1.0) * 200)
        bbox2 = draw.textbbox((0, 0), sub, font=font_sub)
        tw2 = bbox2[2] - bbox2[0]
        sx = (W - tw2) // 2
        sy = y + th + 20
        s_img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        sd = ImageDraw.Draw(s_img)
        sd.text((sx, sy), sub, font=font_sub, fill=(240, 230, 210, sub_alpha))
        canvas = Image.alpha_composite(canvas, s_img)

        return np.array(canvas.convert("RGB"))

    return VideoClip(make_frame, duration=duration).with_fps(FPS)


def make_ending_clip(duration=3.5):
    """エンディング"""
    font_title = load_font(80)
    font_sub = load_font(32)

    def make_frame(t):
        fade_in = min(t / 1.0, 1.0)
        fade_out = 1.0 - min(max(t - (duration - 1.0), 0) / 1.0, 1.0)
        alpha = int(min(fade_in, fade_out) * 255)

        img = Image.new("RGB", (W, H), (8, 8, 8))
        canvas = img.convert("RGBA")

        draw = ImageDraw.Draw(canvas)

        texts = [
            ("OKURANO", font_title, (220, 185, 120), H // 2 - 70),
            ("心よりお待ちしております", font_sub, (240, 230, 210), H // 2 + 30),
        ]
        for text, font, color, y in texts:
            bbox = draw.textbbox((0, 0), text, font=font)
            tw = bbox[2] - bbox[0]
            x = (W - tw) // 2
            t_img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            td = ImageDraw.Draw(t_img)
            td.text((x, y), text, font=font, fill=(*color, alpha))
            canvas = Image.alpha_composite(canvas, t_img)

        return np.array(canvas.convert("RGB"))

    return VideoClip(make_frame, duration=duration).with_fps(FPS)


# --- 各クリップ生成 ---
print("クリップ生成中...")
clips = [make_opening_clip(3.0)]
for scene in SCENES:
    clips.append(make_scene_clip(scene))
clips.append(make_ending_clip(3.5))

# クロスフェードで繋ぐ
print("クロスフェード結合中...")
cf = CROSSFADE
result_clips = [clips[0].with_effects([CrossFadeOut(cf)])]
for i, clip in enumerate(clips[1:], 1):
    if i < len(clips) - 1:
        c = clip.with_start(result_clips[-1].end - cf).with_effects([CrossFadeIn(cf), CrossFadeOut(cf)])
    else:
        c = clip.with_start(result_clips[-1].end - cf).with_effects([CrossFadeIn(cf)])
    result_clips.append(c)

final = CompositeVideoClip(result_clips)

print(f"動画書き出し中 → {OUTPUT}")
final.write_videofile(OUTPUT, fps=FPS, codec="libx264", audio=False,
                      preset="fast", threads=4, logger=None)
print("完成！")
