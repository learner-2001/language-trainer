#!/usr/bin/env python3
"""أداة طوارئ: تطبيق كود جلسة على progress.json.

الصفحة تحفظ النتائج بنفسها عبر مفتاح GitHub. استعمل هذه الأداة فقط لكود لم تستطع الصفحة حفظه.

    apply_results.py progress.json "<كود v2>"            > new_progress.json
    apply_results.py progress.json "<كود v1>" plan.json  > new_progress.json   (قديم)

كود v2:  v2|DATE|<id>.<حرف النمط><1|0>.<الزمن بعُشر الثانية>|...
  r استدعاء، v ترجمة عكسية، d إملاء سمعي، f قراءة سريعة. 1 صحيح، 0 خطأ أو انتهى الوقت.

التكرار الموزّع: إجابات صحيحة متتالية 0,1,2,3,4,5+ تعني المراجعة بعد 1,2,4,7,14,30 يوماً. الخطأ يُرجع الكلمة ليوم واحد.
يجب أن تبقى هذه الأداة مطابقة تماماً لدالة applyToProgress في index.html (الاختبارات تقارن بينهما).
"""
import datetime as dt
import hashlib
import json
import re
import sys

INTERVALS = [1, 2, 4, 7, 14, 30]
LETTER = {'r': 'recall', 'v': 'reverse', 'd': 'dictation', 'f': 'flash'}
LIM_DEF = {'recall': 6, 'reverse': 7, 'dictation': 9, 'flash': 6}


def die(msg):
    sys.stderr.write('ERROR: ' + msg + '\n')
    sys.exit(1)


def rnd(x):  # round half up, same as JS Math.round for positive numbers
    return int(x + 0.5)


def ensure_shape(p):
    p.setdefault('items', {})
    p.setdefault('settings', {'sessionSize': 30})
    p.setdefault('sessions', [])
    if 'daily' not in p:
        d = {}
        for s in p['sessions']:
            x = d.setdefault(s['date'], {'n': 0, 'c': 0, 's': 0})
            x['n'] += s['n']
            x['c'] += rnd(s['acc'] * s['n'])
            x['s'] += 1
        p['daily'] = d
    return p


def parse(code, plan_path):
    parts = code.split('|')
    if parts[0] == 'v2':
        if len(parts) < 3 or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', parts[1]):
            die('bad v2 code')
        out = []
        for e in parts[2:]:
            if not e:
                continue
            f = e.split('.')
            if len(f) != 3 or not re.fullmatch(r'[rvdf][01]', f[1]) or not f[2].isdigit():
                die('bad entry: ' + e)
            out.append((f[0], LETTER[f[1][0]], f[1][1] == '1', int(f[2]) * 100))
        return parts[1], out
    if parts[0] == 'v1':
        if not plan_path:
            die('v1 code needs the plan json as the third argument')
        plan = json.load(open(plan_path, encoding='utf-8'))
        if len(parts) != 4 or parts[1] != plan['date']:
            die('v1 code does not match the plan')
        marks, ts = parts[2], parts[3]
        n = len(plan['q'])
        try:
            times = [int(x) for x in ts.split(',')]
        except ValueError:
            die('bad times')
        if len(marks) != 2 * n or len(times) != n:
            die('v1 length mismatch')
        out = []
        for i, q in enumerate(plan['q']):
            ml, r = marks[2 * i], marks[2 * i + 1]
            if ml not in LETTER or r not in '01x':
                die('bad mark at question %d' % (i + 1))
            if r != 'x':
                out.append((q['id'], LETTER[ml], r == '1', times[i] * 100))
        return parts[1], out
    die('unknown code version')


def main(pp, code, plan_path=None):
    prog = ensure_shape(json.load(open(pp, encoding='utf-8')))
    code = code.strip()
    date, entries = parse(code, plan_path)
    if not entries:
        die('empty session')
    h = hashlib.sha1(code.encode('utf-8')).hexdigest()[:10]
    if any(s.get('h') == h for s in prog['sessions']):
        die('this code was already applied')

    P, S, by = prog['items'], prog['settings'], {}
    for wid, mode, ok, ms in entries:
        p = P.setdefault(wid, {'s': 0, 'c': 0, 'k': 0, 'l': None, 'd': None, 'm': None, 'ms': 0})
        p['s'] += 1
        p['ms'] = rnd((p['ms'] * (p['s'] - 1) + ms) / p['s'])
        if ok:
            p['c'] += 1
            p['k'] += 1
        else:
            p['k'] = 0
        p['l'] = date
        p['m'] = mode
        p['d'] = (dt.date.fromisoformat(date) + dt.timedelta(days=INTERVALS[min(p['k'], 5)])).isoformat()
        b = by.setdefault(mode, {'n': 0, 'c': 0, 'ms': 0})
        b['n'] += 1
        b['c'] += 1 if ok else 0
        b['ms'] += ms
    total = sum(b['n'] for b in by.values())
    right = sum(b['c'] for b in by.values())
    stats = {m: {'n': b['n'], 'c': b['c'], 'ms': rnd(b['ms'] / b['n'])} for m, b in by.items()}
    weakest = None
    if len(stats) > 1:
        weakest = sorted(stats, key=lambda m: (stats[m]['c'] / stats[m]['n'], -stats[m]['ms']))[0]

    hist = prog['sessions']
    limits = dict(LIM_DEF)
    limits.update(S.get('limits', {}))
    for m, b in stats.items():
        if b['n'] < 5:
            continue
        a = b['c'] / b['n']
        prev = [s['byMode'][m] for s in hist if m in s.get('byMode', {}) and s['byMode'][m]['n'] >= 5][-2:]
        if a < 0.6:
            limits[m] = min(12, limits[m] + 0.5)
        elif a >= 0.9 and len(prev) == 2 and all(x['c'] / x['n'] >= 0.9 for x in prev):
            limits[m] = max(3, limits[m] - 0.5)
    S['limits'] = limits

    dd = prog['daily'].setdefault(date, {'n': 0, 'c': 0, 's': 0})
    dd['n'] += total
    dd['c'] += right
    dd['s'] += 1
    hist.append({'date': date, 'h': h, 'n': total, 'acc': rnd(right / total * 1000) / 1000 if total else 0,
                 'byMode': stats, 'weakest': weakest})
    prog['sessions'] = hist[-100:]
    json.dump(prog, sys.stdout, ensure_ascii=False, separators=(',', ':'))


if __name__ == '__main__':
    if len(sys.argv) not in (3, 4):
        die(__doc__.strip().splitlines()[2])
    main(*sys.argv[1:])
