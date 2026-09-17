#!/usr/bin/env python3
"""Analyse listening-test results straight from the Google Sheet.

usage: python3 analyze_results.py [--sheet-id ID] [--csv local.csv] [--out results_long.csv]
Keeps the newest row per participant (complete preferred), drops test rows and practice pages,
reports per-direction/per-system means with 95% CIs, paired differences, and anchor-based screening.
"""
import argparse, csv, json, math, sys, urllib.request, collections, statistics as st
SHEET='1qRxViXx4qAvAtxjXLQw1dCbe36WDaRlobOrqpigRtBg'
NAMES={'gt':'Ground truth','anchor':'Mismatched (low anchor)','cascaded':'Cascaded','model_a':'E2E model A','model_b':'E2E model B','ours':'E2E (ours)'}
ORDER=['gt','cascaded','model_a','model_b','ours','anchor']
def tcrit(df):  # two-sided 95% t critical value (small table, falls back to 1.96)
    T={1:12.71,2:4.30,3:3.18,4:2.78,5:2.57,6:2.45,7:2.36,8:2.31,9:2.26,10:2.23,12:2.18,15:2.13,20:2.09,25:2.06,30:2.04,40:2.02,60:2.00,120:1.98}
    for k in sorted(T):
        if df<=k: return T[k]
    return 1.96
def ci(xs):
    n=len(xs); m=st.mean(xs)
    if n<2: return m, float('nan'), n
    return m, tcrit(n-1)*st.stdev(xs)/math.sqrt(n), n

ap=argparse.ArgumentParser(); ap.add_argument('--sheet-id',default=SHEET); ap.add_argument('--csv'); ap.add_argument('--out',default='results_long.csv'); ap.add_argument('--min-ms',type=int,default=0,help='drop sessions whose median page time is below this (ms)'); ap.add_argument('--no-screen',action='store_true',help='keep every session (for pilots / dry runs)')
a=ap.parse_args()
if a.csv: raw=open(a.csv,encoding='utf-8').read()
else: raw=urllib.request.urlopen(f'https://docs.google.com/spreadsheets/d/{a.sheet_id}/export?format=csv').read().decode('utf-8')
rows=list(csv.DictReader(raw.splitlines()))
# newest row per participant, complete preferred
best={}
for r in rows:
    if r['status']=='test' or not r['participant']: continue
    key=r['participant']; cur=best.get(key)
    rank=(r['status']=='complete', r['received_utc'])
    if cur is None or rank>cur[0]: best[key]=(rank,r)
sessions=[]
for pid,(rank,r) in best.items():
    try: d=json.loads(r['json'])
    except Exception: print('bad json for',pid,file=sys.stderr); continue
    pages=[x for x in d.get('results',[]) if not x.get('practice')]
    if not pages: continue
    med=st.median(x['ms'] for x in pages)
    anchor_fail=sum(1 for x in pages if x['ratings']['anchor']['overall']>=x['ratings']['gt']['overall'])
    sessions.append(dict(pid=pid,status=r['status'],pages=pages,median_ms=med,anchor_fail=anchor_fail))
print(f'{len(rows)} sheet rows -> {len(sessions)} sessions')
print('\nSessions:')
print(f"{'participant':12} {'status':9} {'pages':>5} {'median s/page':>14} {'anchor>=GT':>10}  flag")
keep=[]
for s in sessions:
    flags=[]
    if s['status']!='complete': flags.append('incomplete')
    if s['anchor_fail']>2: flags.append('fails anchor screen')
    if s['median_ms']<a.min_ms: flags.append('too fast')
    print(f"{s['pid']:12} {s['status']:9} {len(s['pages']):5} {s['median_ms']/1000:14.1f} {s['anchor_fail']:>6}/{len(s['pages']):<3}  {', '.join(flags)}")
    if not flags or a.no_screen: keep.append(s)
print(f'\nKept {len(keep)} of {len(sessions)} sessions (drop: incomplete, >2 pages with anchor >= ground truth, median page time < {a.min_ms/1000:.0f}s)')
# long table
long=[]
for s in keep:
    for x in s['pages']:
        for sysk,v in x['ratings'].items():
            long.append(dict(participant=s['pid'],direction=x['dir'],sample=x['sample'],anchor_sample=x['anchor_sample'],system=sysk,label=v['label'],score=v['overall'],plays=v['plays'],page_ms=x['ms']))
with open(a.out,'w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(long[0].keys()) if long else ['participant']); w.writeheader(); w.writerows(long)
print(f'Long-format ratings written to {a.out} ({len(long)} rows)')
for d in ['a2s','s2a']:
    sub=[r for r in long if r['direction']==d]
    if not sub: continue
    print(f"\n=== {'Audio -> Speech' if d=='a2s' else 'Speech -> Audio'}  ({len({(r['participant'],r['sample']) for r in sub})} pages, {len({r['participant'] for r in sub})} raters, {len({r['sample'] for r in sub})} distinct samples)")
    print(f"{'system':24} {'mean':>6} {'±95%CI':>7} {'sd':>6} {'n':>4}")
    stats={}
    for k in ORDER:
        xs=[r['score'] for r in sub if r['system']==k]
        if not xs: continue
        m,h,n=ci(xs); stats[k]=xs
        print(f"{NAMES[k]:24} {m:6.1f} {h:7.1f} {st.stdev(xs) if n>1 else float('nan'):6.1f} {n:4}")
    # paired differences vs cascaded (same page)
    bypage=collections.defaultdict(dict)
    for r in sub: bypage[(r['participant'],r['sample'])][r['system']]=r['score']
    print('  paired difference vs Cascaded (positive = better than cascade):')
    for k in ORDER:
        if k=='cascaded' or k not in stats: continue
        diffs=[p[k]-p['cascaded'] for p in bypage.values() if k in p and 'cascaded' in p]
        if diffs: m,h,n=ci(diffs); print(f"    {NAMES[k]:24} {m:+6.1f} ± {h:4.1f}  (n={n})")
