import json, sys
src = r"C:\Users\shsas\Desktop\Industrial Motor_Protection and Condition_Monitoring system\Industry_PCB.kicad_pro"
import os
if os.path.exists('orig.kicad_pro'):
    src = 'orig.kicad_pro'
d = json.load(open(src, encoding='utf-8'))
json.dump(d, open('orig.kicad_pro', 'w', encoding='utf-8'), indent=2)
base = dict(d['net_settings']['classes'][0])
base.update(clearance=0.2, track_width=0.25, via_diameter=0.8, via_drill=0.4)
pw = dict(base); pw.update(name='Power', track_width=0.8, priority=0)
p5 = dict(base); p5.update(name='Supply', track_width=0.4, priority=1)
ld = dict(base); ld.update(name='Load', track_width=2.0, clearance=0.2, priority=2)
d['net_settings']['classes'] = [base, pw, p5, ld]
d['net_settings']['netclass_patterns'] = (
    [{'netclass': 'Power', 'pattern': p} for p in ['+12V', '/VIN_RAW', '/VIN_FUSED', '/FAN_N']] +
    [{'netclass': 'Supply', 'pattern': p} for p in ['+5V', '+3V3', '/RELAY_N', '/BUZZ_N']] +
    [{'netclass': 'Load', 'pattern': p} for p in ['/RLY_NO', '/RLY_COM', '/RLY_NC']])
r = d['board']['design_settings']['rules']
r.update(min_clearance=0.2, min_track_width=0.2, min_copper_edge_clearance=0.3, min_via_diameter=0.6,
         min_through_hole_diameter=0.3, min_hole_clearance=0.25, min_hole_to_hole=0.25, min_via_annular_width=0.13)
d['board']['design_settings']['track_widths'] = [0.0, 0.25, 0.4, 0.8, 2.0]
d['board']['design_settings']['via_dimensions'] = [{'diameter': 0.0, 'drill': 0.0}, {'diameter': 0.8, 'drill': 0.4}]
d['meta']['filename'] = 'Industry_PCB.kicad_pro'
d['libraries'] = {'pinned_footprint_libs': [], 'pinned_symbol_libs': []}
json.dump(d, open('build/Industry_PCB.kicad_pro', 'w', encoding='utf-8'), indent=2)
print('pro ok')
