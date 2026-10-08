#!/usr/bin/env python3
"""Apply a session result code to progress.json.
Usage: apply_results.py progress.json today.json "v1|DATE|r1v0d1f1...|ts,ts,..." > new_progress.json
Code: per question one mode letter (r/v/d/f) + result (1 right, 0 wrong, x skipped); then times in tenths of a second.
Spaced repetition: consecutive-correct 0,1,2,3,4,5+ -> next review after 1,2,4,7,14,30 days. A wrong answer resets to 1 day."""
import json, sys, hashlib, datetime as dt

INTERVALS = [1, 2, 4, 7, 14, 30]
LETTER = {'r': 'recall', 'v': 'reverse', 'd': 'dictation', 'f': 'flash'}
DEFAULT_LIMITS = {'recall': 6, 'reverse': 7, 'dictation': 9, 'flash': 6}

def die(msg): sys.stderr.write('ERROR: ' + msg + '\n'); sys.exit(1)

def main(pp, plp, code):
    prog = json.load(open(pp, encoding='utf-8')); plan = json.load(open(plp, encoding='utf-8'))
    code = code.strip(); parts = code.split('|')
    if len(parts) != 4 or parts[0] != 'v1': die('bad code format')
    date, marks, ts = parts[1], parts[2], parts[3]
    if date != plan['date']: die(f"code date {date} != plan date {plan['date']}")
    n = len(plan['q'])
    if len(marks) != 2 * n: die(f'expected {2*n} mark chars, got {len(marks)}')
    try: times = [int(x) for x in ts.split(',')] if ts else []
    except ValueError: die('bad times list')
    if len(times) != n: die(f'expected {n} times, got {len(times)}')
    h = hashlib.sha1(code.encode()).hexdigest()[:10]
    if any(s.get('h') == h for s in prog.get('sessions', [])): die('this code was already applied')

    P = prog.setdefault('items', {}); S = prog.setdefault('settings', {'sessionSize': 30})
    by = {}
    for i, q in enumerate(plan['q']):
        ml, r = marks[2 * i], marks[2 * i + 1]
        if ml not in LETTER or r not in '01x': die(f'bad mark at question {i+1}')
        if r == 'x': continue
        mode = LETTER[ml]; ok = r == '1'; ms = times[i] * 100
        p = P.setdefault(q['id'], {'s': 0, 'c': 0, 'k': 0, 'l': None, 'd': None, 'm': None, 'ms': 0})
        p['s'] += 1; p['ms'] = round((p['ms'] * (p['s'] - 1) + ms) / p['s'])
        if ok: p['c'] += 1; p['k'] += 1
        else: p['k'] = 0
        p['l'] = date; p['m'] = mode
        p['d'] = (dt.date.fromisoformat(date) + dt.timedelta(days=INTERVALS[min(p['k'], 5)])).isoformat()
        b = by.setdefault(mode, {'n': 0, 'c': 0, 'ms': 0}); b['n'] += 1; b['c'] += ok; b['ms'] += ms
    total = sum(b['n'] for b in by.values()); right = sum(b['c'] for b in by.values())
    stats = {m: {'n': b['n'], 'c': b['c'], 'ms': round(b['ms'] / b['n'])} for m, b in by.items()}
    weakest = None
    if len(stats) > 1:
        weakest = sorted(stats, key=lambda m: (stats[m]['c'] / stats[m]['n'], -stats[m]['ms']))[0]
    hist = prog.setdefault('sessions', [])

    # adaptive time limits: 3 sessions in a row >=90% -> tighter by 0.5s (min 3); this session <60% -> looser (max 12)
    limits = dict(DEFAULT_LIMITS); limits.update(S.get('limits', {}))
    for m, b in stats.items():
        if b['n'] < 5: continue
        a = b['c'] / b['n']
        prev = [s['byMode'][m] for s in hist if m in s.get('byMode', {}) and s['byMode'][m]['n'] >= 5][-2:]
        if a < 0.6: limits[m] = min(12, limits[m] + 0.5)
        elif a >= 0.9 and len(prev) == 2 and all(x['c'] / x['n'] >= 0.9 for x in prev): limits[m] = max(3, limits[m] - 0.5)
    S['limits'] = limits
    hist.append({'date': date, 'h': h, 'n': total, 'acc': round(right / total, 3) if total else 0, 'byMode': stats, 'weakest': weakest})
    prog['sessions'] = hist[-200:]
    json.dump(prog, sys.stdout, ensure_ascii=False, indent=1)

if __name__ == '__main__':
    main(*sys.argv[1:4])
