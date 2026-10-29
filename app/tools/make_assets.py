#!/usr/bin/env python3
"""يرسم أيقونة التطبيق وشاشة البداية ويضعها داخل مشروع أندرويد المُولَّد.
الاستعمال:  python3 make_assets.py <مسار مجلد res>
نفس الشعار الموجود في icon.svg (سهم أصفر على أزرق داكن)."""
import os, sys
from PIL import Image, ImageDraw

NAVY = (0x17, 0x40, 0x6b, 255)
AMBER = (0xf2, 0xb0, 0x1e, 255)
SS = 4  # تكبير داخلي لنعومة الحواف

# حدود الشعار في فضاء 512 (من icon.svg)
MX0, MY0, MX1, MY1 = 104, 118, 408, 392
MW, MH = MX1 - MX0, MY1 - MY0


def mark_layer(canvas, width_frac):
    """طبقة شفافة canvas×canvas فيها الشعار في الوسط بعرض width_frac من العرض."""
    big = canvas * SS
    s = (width_frac * big) / MW
    ox = big / 2 - (MX0 + MW / 2) * s
    oy = big / 2 - (MY0 + MH / 2) * s
    P = lambda x, y: (ox + x * s, oy + y * s)
    layer = Image.new('RGBA', (big, big), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    # الشريط السفلي (نصف شفاف)
    bar = Image.new('RGBA', (big, big), (0, 0, 0, 0))
    bd = ImageDraw.Draw(bar)
    x0, y0 = P(104, 372); x1, y1 = P(408, 392)
    bd.rounded_rectangle([x0, y0, x1, y1], radius=10 * s, fill=AMBER[:3] + (128,))
    layer = Image.alpha_composite(layer, bar)
    d = ImageDraw.Draw(layer)
    # الخط المائل بنهايات مدوّرة
    (ax, ay), (bx, by) = P(150, 330), P(322, 158)
    w = 52 * s
    d.line([(ax, ay), (bx, by)], fill=AMBER, width=int(round(w)))
    for cx, cy in ((ax, ay), (bx, by)):
        d.ellipse([cx - w / 2, cy - w / 2, cx + w / 2, cy + w / 2], fill=AMBER)
    # رأس السهم
    d.polygon([P(236, 118), P(394, 118), P(394, 276)], fill=AMBER)
    return layer.resize((canvas, canvas), Image.LANCZOS)


def save(img, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path, optimize=True)


def legacy_icon(size, round_=False):
    big = size * SS
    base = Image.new('RGBA', (big, big), (0, 0, 0, 0))
    d = ImageDraw.Draw(base)
    if round_:
        d.ellipse([0, 0, big - 1, big - 1], fill=NAVY)
    else:
        d.rounded_rectangle([0, 0, big - 1, big - 1], radius=int(big * 0.219), fill=NAVY)
    base = base.resize((size, size), Image.LANCZOS)
    m = mark_layer(size, 0.54 if round_ else 0.60)
    return Image.alpha_composite(base, m)


def main(res):
    dens = {'mdpi': 1, 'hdpi': 1.5, 'xhdpi': 2, 'xxhdpi': 3, 'xxxhdpi': 4}
    for name, k in dens.items():
        d = os.path.join(res, 'mipmap-' + name)
        save(mark_layer(int(108 * k), 0.46), os.path.join(d, 'ic_launcher_foreground.png'))
        save(legacy_icon(int(48 * k)), os.path.join(d, 'ic_launcher.png'))
        save(legacy_icon(int(48 * k), True), os.path.join(d, 'ic_launcher_round.png'))
    # خلفية الأيقونة التكيفية = الأزرق الداكن
    os.makedirs(os.path.join(res, 'values'), exist_ok=True)
    with open(os.path.join(res, 'values', 'ic_launcher_background.xml'), 'w', encoding='utf-8') as f:
        f.write('<?xml version="1.0" encoding="utf-8"?>\n<resources>\n'
                '    <color name="ic_launcher_background">#17406B</color>\n</resources>\n')
    # الأيقونة التكيفية الافتراضية القديمة (متجه أخضر) لم تعد مستعملة؛ نتركها كما هي
    # شعار شاشة البداية (خلفية شفافة)، وملف يرسم الخلفية والشعار في الوسط دون تمطيط
    save(mark_layer(512, 0.62), os.path.join(res, 'drawable-nodpi', 'splash_logo.png'))
    os.makedirs(os.path.join(res, 'drawable'), exist_ok=True)
    with open(os.path.join(res, 'drawable', 'splash.xml'), 'w', encoding='utf-8') as f:
        f.write('<?xml version="1.0" encoding="utf-8"?>\n'
                '<layer-list xmlns:android="http://schemas.android.com/apk/res/android">\n'
                '    <item><shape android:shape="rectangle"><solid android:color="#17406B"/></shape></item>\n'
                '    <item android:gravity="center" android:width="200dp" android:height="200dp"\n'
                '          android:drawable="@drawable/splash_logo"/>\n'
                '</layer-list>\n')
    # نحذف صور البداية الجاهزة (splash.png) لأن splash.xml يحلّ محلها
    removed = 0
    for root, _, files in os.walk(res):
        for fn in files:
            if fn == 'splash.png':
                os.remove(os.path.join(root, fn)); removed += 1
    print('assets ok; removed old splash.png:', removed)


if __name__ == '__main__':
    main(sys.argv[1])
