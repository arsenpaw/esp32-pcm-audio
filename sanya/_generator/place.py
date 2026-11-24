"""Board outline + placement table. Coordinates: local mm, origin = board top-left.
Each entry: ref -> (cx, cy, rot)  where (cx,cy) is the desired centre of the footprint
courtyard bounding box after rotation."""
W, H = 90.0, 65.0
OX, OY = 100.0, 80.0   # board origin on the KiCad page

P = {
    # mounting
    'H1': (4, 4, 0), 'H2': (86, 4, 0), 'H3': (4, 61, 0), 'H4': (86, 61, 0),
    # power (top-left)
    'J1': (13.5, 6.0, 180), 'J7': (27, 6.0, 180), 'C1': (22.7, 24.5, 0),
    'F1': (10.5, 15, 0), 'D1': (19, 15, 180), 'D2': (27.5, 15, 180),
    'U1': (13, 23.5, 180), 'C2': (20.5, 19.2, 0), 'U2': (29.3, 20.2, 0), 'C3': (29.5, 24.2, 0),
    # driver / alarm / relay (top-right)
    'BZ1': (39, 20, 0), 'U5': (50.5, 19, 0), 'K1': (66.5, 19, 0), 'J6': (84.1, 19, 90), 'D7': (57, 31, 0),
    # MCU (centre)
    'U3': (40, 43, 180), 'C4': (47.6, 43.5, 90), 'C5': (32.6, 42, 90),
    'Y1': (53.5, 42, 90), 'C6': (58.5, 38.5, 0), 'C7': (58.5, 45.5, 0),
    'RN1': (37, 30.5, 90), 'D4': (22, 32, 90), 'D5': (26, 32, 90), 'D6': (30, 32, 90),
    'SW1': (7.5, 35, 90), 'SW2': (7.5, 46.5, 90),
    # pressure (bottom-left)
    'J4': (15, 60.5, 0), 'R1': (13, 53.5, 0), 'R2': (17.5, 53.5, 0), 'C9': (22, 53.5, 0), 'D3': (27, 52.5, 0),
    # temperature (bottom)
    'J3': (31, 60.5, 0), 'D8': (38.5, 57, 90),
    # programming (bottom)
    'J2': (47, 60, 90),
    # i2c: pull-ups, accelerometer, oled
    'RN2': (48, 53.2, 0), 'U4': (77, 57, 0), 'FB1': (70.5, 53, 0), 'C8': (72, 57, 90),
    'J5': (86.5, 41, 0),
    # test points
    'TP1': (43.5, 4.5, 0), 'TP2': (24.6, 19.7, 0), 'TP3': (29.5, 27.2, 0), 'TP4': (4, 20, 0),
    'TP5': (64, 50, 0), 'TP6': (68, 50, 0), 'TP7': (30, 48, 0), 'TP8': (56, 52.5, 0), 'TP9': (60, 52.5, 0),
}

# net widths (mm)
WIDTH = {'+12V': 0.8, '/VIN_RAW': 0.8, '/VIN_FUSED': 0.8, '/FAN_N': 0.8,
         '+5V': 0.4, '+3V3': 0.4, '/RELAY_N': 0.4, '/BUZZ_N': 0.4,
         '/RLY_NO': 2.0, '/RLY_COM': 2.0, '/RLY_NC': 2.0}
