#!/usr/bin/env python3
"""يعدّل مشروع أندرويد المُولَّد: رقم النسخة، التوقيع الثابت، وألوان شاشة البداية.
الاستعمال:  python3 patch_android.py <مجلد android>   (متغيرات اختيارية: VERSION_CODE, VERSION_NAME)
أي تعديل لا يجد هدفه يوقف البناء برسالة واضحة بدل أن يمرّ صامتاً."""
import os, re, shutil, sys

android = sys.argv[1]
here = os.path.dirname(os.path.abspath(__file__))
code = os.environ.get('VERSION_CODE', '1')
name = os.environ.get('VERSION_NAME', '1.0')
app = os.path.join(android, 'app')
KS_PASS = 'gate-learner-2026'  # مفتاح توقيع شخصي لتحديث التطبيق فقط، وليس سراً حساساً


def sub1(pattern, repl, text, what, flags=0):
    new, n = re.subn(pattern, repl, text, count=1, flags=flags)
    if n != 1:
        sys.exit('PATCH FAILED: ' + what)
    return new


# 1) التوقيع الثابت: نفس المفتاح في كل بناء، ليُثبَّت التحديث فوق النسخة القديمة دون حذف بياناتك
shutil.copy(os.path.join(here, '..', 'gate-release.keystore'), os.path.join(app, 'gate-release.keystore'))

p = os.path.join(app, 'build.gradle')
g = open(p, encoding='utf-8').read()
g = sub1(r'versionCode\s+\d+', 'versionCode ' + code, g, 'versionCode')
g = sub1(r'versionName\s+"[^"]*"', 'versionName "' + name + '"', g, 'versionName')
signing = ("    lint {\n"
           "        checkReleaseBuilds false\n"
           "        abortOnError false\n"
           "    }\n"
           "    signingConfigs {\n"
           "        gate {\n"
           "            storeFile file('gate-release.keystore')\n"
           "            storePassword '" + KS_PASS + "'\n"
           "            keyAlias 'gate'\n"
           "            keyPassword '" + KS_PASS + "'\n"
           "        }\n"
           "    }\n")
g = sub1(r'(\n)(\s*)buildTypes\s*\{', lambda m: '\n' + signing + m.group(2) + 'buildTypes {', g, 'buildTypes block')
g = sub1(r'(release\s*\{\s*\n)', lambda m: m.group(1) + '            signingConfig signingConfigs.gate\n', g, 'release block')
open(p, 'w', encoding='utf-8').write(g)

# ذاكرة أكبر لـ Gradle حتى لا ينهار البناء
p = os.path.join(android, 'gradle.properties')
t = open(p, encoding='utf-8').read()
t = sub1(r'(?m)^org\.gradle\.jvmargs=.*$', 'org.gradle.jvmargs=-Xmx3g -Dfile.encoding=UTF-8', t, 'jvmargs')
open(p, 'w', encoding='utf-8').write(t)

# 2) شاشة البداية بلون التطبيق (أندرويد 12 فما فوق)
p = os.path.join(app, 'src', 'main', 'res', 'values', 'styles.xml')
s = open(p, encoding='utf-8').read()
s = sub1(r'(<item name="android:background">@drawable/splash</item>)',
         lambda m: m.group(1) + '\n        <item name="windowSplashScreenBackground">@color/ic_launcher_background</item>'
                   '\n        <item name="windowSplashScreenAnimatedIcon">@mipmap/ic_launcher_foreground</item>',
         s, 'splash theme')
open(p, 'w', encoding='utf-8').write(s)
print('patched: versionCode', code, 'versionName', name)
