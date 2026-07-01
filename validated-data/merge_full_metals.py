#!/usr/bin/env python3
"""
Merge the full TAL metals panel (EPA R9 portal export) into the R1 (SS-series)
samples. Adds 19 additional metals per sample as a `metals` dict; leaves the
four ROD COCs (Hg/As/Sb/Tl) that drive HI/exceedances/DUs untouched.

Source: validated-data/107684567_EPAR9_SBMM_ARII_20260701074335.xlsx
Targets: abp_samples.geojson  +  embedded const DATA in index.html
"""
import openpyxl, re, json
from collections import defaultdict

PORTAL = 'validated-data/107684567_EPAR9_SBMM_ARII_20260701074335.xlsx'
GEOJSON = 'abp_samples.geojson'
INDEX   = 'index.html'

# chemical name -> (symbol, display group).  ROD COCs are already in the app.
ROD = {'Mercury','Arsenic','Antimony','Thallium'}
SYM = {
    'Lead':'Pb','Cadmium':'Cd','Chromium':'Cr','Copper':'Cu','Zinc':'Zn','Nickel':'Ni',
    'Selenium':'Se','Silver':'Ag','Barium':'Ba','Beryllium':'Be','Cobalt':'Co','Vanadium':'V',
    'Aluminum':'Al','Calcium':'Ca','Iron':'Fe','Potassium':'K','Magnesium':'Mg',
    'Manganese':'Mn','Sodium':'Na',
}

wb = openpyxl.load_workbook(PORTAL, data_only=True, read_only=True)
ws = wb['Sheet1']
rows = list(ws.iter_rows(values_only=True))
hdr = rows[0]; H = {h:i for i,h in enumerate(hdr)}
def col(row, name): return row[H[name]] if name in H else None

def appid(loc):
    m = re.match(r'SBM-ABP-SO-SS(\d+)', str(loc))
    return f"SS-{int(m.group(1)):02d}" if m else None

# extract the 19 extra metals per SS (R1) sample
metals = defaultdict(dict)      # appid -> { sym: {n,v,dl,q} }
dates  = {}
for r in rows[1:]:
    chem = col(r,'CHEMICAL_NAME')
    if not chem or chem in ROD:
        continue
    sym = SYM.get(chem)
    if not sym:                 # unexpected analyte -> skip, but report
        continue
    aid = appid(col(r,'SYS_LOC_CODE'))
    if not aid:
        continue
    detect = col(r,'DETECT_FLAG') == 'Y'
    val = col(r,'REPORT_RESULT_VALUE')
    dl  = col(r,'REPORT_REPORTING_LIMIT') or col(r,'REPORT_METHOD_DETECTION_LIMIT')
    q   = col(r,'VALIDATOR_QUALIFIERS') or col(r,'INTERPRETED_QUALIFIERS') or col(r,'LAB_QUALIFIERS') or ''
    def num(x):
        try: return round(float(x), 4)
        except (TypeError, ValueError): return None
    metals[aid][sym] = {
        'n': chem,
        'v': (num(val) if detect else None),
        'dl': num(dl),
        'q': str(q).strip(),
    }
    dates[aid] = str(col(r,'SAMPLE_DATE'))[:10]

print(f"Parsed metals for {len(metals)} R1 SS samples "
      f"({sum(len(v) for v in metals.values())} metal results).")

# merge into geojson
gj = json.load(open(GEOJSON))
matched, unmatched = 0, []
for f in gj['features']:
    aid = f['properties'].get('id')
    if aid in metals:
        f['properties']['metals'] = metals[aid]
        f['properties']['metals_date'] = dates.get(aid)
        matched += 1
for aid in metals:
    if not any(f['properties'].get('id') == aid for f in gj['features']):
        unmatched.append(aid)

json.dump(gj, open(GEOJSON,'w'), indent=2)
print(f"Attached metals to {matched} features in {GEOJSON}.")
if unmatched:
    print(f"  WARNING: {len(unmatched)} portal samples had no matching app feature: {sorted(unmatched)}")

# re-sync embedded const DATA in index.html
html = open(INDEX, encoding='utf-8').read()
m = re.search(r'(const DATA = )(\{.*?\});\n', html, flags=re.DOTALL)
assert m, "could not find const DATA in index.html"
minified = json.dumps(gj, separators=(',',':'), ensure_ascii=False)
html = html[:m.start()] + 'const DATA = ' + minified + ';\n' + html[m.end():]
open(INDEX,'w',encoding='utf-8').write(html)
print(f"Re-synced const DATA in {INDEX}.")

# summary: detect/ND tally per metal
tally = defaultdict(lambda: [0,0])
for s in metals.values():
    for sym,d in s.items():
        if d['v'] is not None: tally[sym][0]+=1
        else: tally[sym][1]+=1
print("\n=== extra-metal detect / non-detect tally (R1 SS panel) ===")
for sym in sorted(tally):
    det,nd = tally[sym]
    print(f"  {sym:3s}: {det} detect, {nd} ND")
