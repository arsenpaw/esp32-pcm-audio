import csv, re, sys
from design import C
out = sys.argv[1]
def key(r):
    m = re.match(r'([A-Z]+)(\d+)', r); return (m.group(1), int(m.group(2)))
groups = {}
for ref, c in C.items():
    if not c['bom']: continue
    groups.setdefault((c['val'], c['fp'], c['mpn'], c['mfr']), []).append(ref)
rows = sorted(groups.items(), key=lambda kv: key(sorted(kv[1], key=key)[0]))
with open(out + '/BOM.csv', 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.writer(f)
    w.writerow(['Item', 'Qty', 'Reference', 'Value', 'Footprint', 'MPN', 'Manufacturer'])
    for i, ((val, fp, mpn, mfr), refs) in enumerate(rows, 1):
        w.writerow([i, len(refs), ' '.join(sorted(refs, key=key)), val, fp, mpn, mfr])
n = sum(len(r) for _, r in rows)
print('bom lines', len(rows), 'parts', n)
md = ['| Ref | Value | Footprint | MPN | Виробник | Блок |', '|---|---|---|---|---|---|']
for ref in sorted([r for r in C if C[r]['bom']], key=key):
    c = C[ref]
    md.append('| %s | %s | %s | %s | %s | %s |' % (ref, c['val'], c['fp'].split(':')[1], c['mpn'], c['mfr'], c['block']))
open('bom_table.md', 'w', encoding='utf-8').write('\n'.join(md))
blocks = {}
for ref, c in C.items():
    if c['bom']: blocks.setdefault(c['block'], []).append(ref)
md = ['| Блок | К-сть | Компоненти |', '|---|---|---|']
for b, refs in blocks.items():
    md.append('| %s | %d | %s |' % (b, len(refs), ', '.join(sorted(refs, key=key))))
md.append('| **Разом** | **%d** | |' % n)
open('block_table.md', 'w', encoding='utf-8').write('\n'.join(md))
print(open('block_table.md', encoding='utf-8').read())
