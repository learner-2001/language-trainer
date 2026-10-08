#!/usr/bin/env python3
"""Build today's drill plan.
Usage: plan.py words.json progress.json YYYY-MM-DD > today.json
Rules: weak (<70% accuracy) and due items first, then new items (A1 before A2, types interleaved),
then oldest practised. Each item gets a drill mode different from its last one; modes are balanced
and never repeat twice in a row."""
import json, sys, random

MODES = ['recall', 'reverse', 'dictation', 'flash']
DEFAULT_LIMITS = {'recall': 6, 'reverse': 7, 'dictation': 9, 'flash': 6}
NEW_TYPE_CYCLE = ['word', 'verb', 'adjective', 'phrase', 'word', 'verb', 'adjective', 'phrasal', 'phrase', 'sentence']

def main(wp, pp, today):
    words = json.load(open(wp, encoding='utf-8'))
    prog = json.load(open(pp, encoding='utf-8'))
    items = words['items']; P = prog.get('items', {})
    settings = prog.get('settings', {})
    size = settings.get('sessionSize', 30)
    limits = dict(DEFAULT_LIMITS); limits.update(settings.get('limits', {}))
    rnd = random.Random(today)

    def acc(p): return p['c'] / p['s'] if p['s'] else 0
    due = [i for i in items if i['id'] in P and P[i['id']]['d'] and P[i['id']]['d'] <= today]
    due.sort(key=lambda i: (acc(P[i['id']]) >= 0.7, P[i['id']]['d']))
    chosen = due[:size]

    if len(chosen) < size:
        new = [i for i in items if i['id'] not in P]
        for lv in sorted({i['lv'] for i in new}):
            if len(chosen) >= size: break
            buckets = {}
            for i in new:
                if i['lv'] == lv: buckets.setdefault(i['ty'], []).append(i)
            for b in buckets.values(): rnd.shuffle(b)
            k = 0
            while len(chosen) < size and any(buckets.values()):
                ty = NEW_TYPE_CYCLE[k % len(NEW_TYPE_CYCLE)]; k += 1
                if buckets.get(ty): chosen.append(buckets[ty].pop())

    if len(chosen) < size:
        have = {i['id'] for i in chosen}
        rest = [i for i in items if i['id'] in P and i['id'] not in have]
        rest.sort(key=lambda i: P[i['id']].get('l') or '')
        chosen += rest[:size - len(chosen)]

    # assign modes: avoid last mode, keep counts balanced
    counts = {m: 0 for m in MODES}; assigned = []
    for it in chosen:
        allowed = [m for m in MODES if not (m == 'flash' and it['ty'] == 'sentence')]
        last = P.get(it['id'], {}).get('m')
        if last in allowed and len(allowed) > 1: allowed.remove(last)
        low = min(counts[m] for m in allowed)
        m = rnd.choice([m for m in allowed if counts[m] == low])
        counts[m] += 1; assigned.append((it, m))

    # order: shuffled, then greedy so the same mode (and type if possible) rarely repeats back-to-back
    rnd.shuffle(assigned); ordered = []
    while assigned:
        pm, pt = (ordered[-1][1], ordered[-1][0]['ty']) if ordered else (None, None)
        pick = next((a for a in assigned if a[1] != pm and a[0]['ty'] != pt), None) \
            or next((a for a in assigned if a[1] != pm), None) or assigned[0]
        assigned.remove(pick); ordered.append(pick)

    q = []
    for it, m in ordered:
        t = limits[m] + (3 if it['ty'] == 'sentence' else 1 if it['ty'] == 'phrase' and len(it['w'].split()) >= 3 else 0)
        q.append({'id': it['id'], 'mode': m, 't': t})
    json.dump({'v': 1, 'date': today, 'size': len(q), 'flashMs': 800, 'limits': limits, 'q': q},
              sys.stdout, ensure_ascii=False, separators=(',', ':'))

if __name__ == '__main__':
    main(*sys.argv[1:4])
