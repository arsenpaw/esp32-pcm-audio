import sx
def load(p):
    t = sx.parse(open(p, encoding='utf-8').read())
    got = {}
    for net in sx.find(sx.first(t, 'nets'), 'net'):
        name = str(sx.first(net, 'name')[1])
        for nd in sx.find(net, 'node'):
            got[(str(sx.first(nd, 'ref')[1]), str(sx.first(nd, 'pin')[1]))] = name
    comps = {str(sx.first(c, 'ref')[1]): (str(sx.first(c, 'value')[1]), str(sx.first(c, 'footprint')[1]), str(sx.first(c, 'tstamps')[1]).split()[0]) for c in sx.find(sx.first(t, 'components'), 'comp')}
    return got, comps
a, ca = load('build/ref.net'); b, cb = load('build/net.net')
bad = 0
for k in sorted(set(a) | set(b)):
    if a.get(k) != b.get(k):
        print('NET DIFF', k, 'ref:', a.get(k), 'new:', b.get(k)); bad += 1
for k in sorted(set(ca) | set(cb)):
    if ca.get(k) != cb.get(k):
        print('COMP DIFF', k, ca.get(k), cb.get(k)); bad += 1
print('pins', len(b), 'components', len(cb), 'differences', bad)
