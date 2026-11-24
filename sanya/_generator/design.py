"""Single source of truth: components, nets, schematic placement."""
U = 2.54
POWER = {'GND', '+12V', '+5V', '+3V3'}
NC = 'NC'

# ref: dict(lib, val, fp, mpn, mfr, at=(ux,uy), rot, pins={num: net | (net, stub_u)}, desc)
C = {}


def add(ref, lib, val, fp, mpn, mfr, at, rot, pins, block, bom=True):
    C[ref] = dict(lib=lib, val=val, fp=fp, mpn=mpn, mfr=mfr, at=at, rot=rot, pins=pins, block=block, bom=bom)


R0603 = 'Resistor_SMD:R_0603_1608Metric'
C0603 = 'Capacitor_SMD:C_0603_1608Metric'
LED0805 = 'LED_SMD:LED_0805_2012Metric'
TB2 = 'TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-2-5.08_1x02_P5.08mm_Horizontal'
TB3 = 'TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-3-5.08_1x03_P5.08mm_Horizontal'
XH3 = 'Connector_JST:JST_XH_B3B-XH-A_1x03_P2.50mm_Vertical'

# ---------------- 1 POWER ----------------
add('J1', 'Connector:Screw_Terminal_01x02', '12V_IN', TB2, 'MKDS 1,5/2-5,08 (1715721)', 'Phoenix Contact',
    (12, 16), 0, {'1': 'VIN_RAW', '2': 'GND'}, 'POWER')
add('F1', 'Device:Polyfuse', '1.1A/16V PTC', 'Fuse:Fuse_1812_4532Metric_Pad1.30x3.40mm_HandSolder',
    'MF-MSMF110/16-2', 'Bourns', (25, 16), 90, {'1': 'VIN_RAW', '2': 'VIN_FUSED'}, 'POWER')
add('D1', 'Device:D_Schottky', 'SS34', 'Diode_SMD:D_SMA', 'SS34', 'onsemi / MCC',
    (39, 16), 180, {'2': 'VIN_FUSED', '1': '+12V'}, 'POWER')
add('D2', 'Device:D_TVS', 'SMBJ15CA', 'Diode_SMD:D_SMB', 'SMBJ15CA', 'Littelfuse',
    (48, 19), 90, {'2': '+12V', '1': 'GND'}, 'POWER')
add('C1', 'Device:C_Polarized', '100uF/35V', 'Capacitor_THT:CP_Radial_D6.3mm_P2.50mm', 'ECA-1VM101', 'Panasonic',
    (56, 19), 0, {'1': '+12V', '2': 'GND'}, 'POWER')
add('U1', 'Regulator_Linear:L7805', 'L7805CDT', 'Package_TO_SOT_SMD:TO-252-2', 'L7805CDT-TR', 'STMicroelectronics',
    (66, 17), 0, {'1': '+12V', '2': 'GND', '3': '+5V'}, 'POWER')
add('C2', 'Device:C', '10uF/16V', 'Capacitor_SMD:C_0805_2012Metric', 'CL21A106KOQNNNE', 'Samsung',
    (76, 19), 0, {'1': '+5V', '2': 'GND'}, 'POWER')
add('U2', 'Regulator_Linear:MCP1700x-330xxTT', 'MCP1700-3302E/TT', 'Package_TO_SOT_SMD:SOT-23', 'MCP1700T-3302E/TT',
    'Microchip', (88, 17), 0, {'3': '+5V', '1': 'GND', '2': '+3V3'}, 'POWER')
add('C3', 'Device:C', '1uF/16V', C0603, 'CL10A105KO8NNNC', 'Samsung',
    (98, 19), 0, {'1': '+3V3', '2': 'GND'}, 'POWER')

# ---------------- 2 MCU ----------------
add('U3', 'MCU_Microchip_ATmega:ATmega328P-A', 'ATmega328P-AU', 'Package_QFP:TQFP-32_7x7mm_P0.8mm', 'ATMEGA328P-AU',
    'Microchip', (28, 47), 0, {
        '4': '+3V3', '18': ('JOIN', '4'), '3': 'GND',
        '20': NC, '19': NC, '22': NC,
        '12': 'LED_GREEN', '13': 'LED_YELLOW', '14': 'LED_RED',
        '15': 'MOSI', '16': 'MISO', '17': 'SCK',
        '7': 'XTAL1', '8': 'XTAL2',
        '23': 'PRESS_ADC', '24': NC, '25': NC, '26': NC,
        '27': 'SDA', '28': 'SCL', '29': 'RESET',
        '30': 'UART_RX', '31': 'UART_TX', '32': 'ADXL_INT1',
        '1': 'FAN_PWM', '2': 'ONEWIRE_DQ', '9': 'BUZZER_CTRL', '10': 'RELAY_CTRL', '11': 'BTN_ACK',
    }, 'MCU')
add('C4', 'Device:C', '100nF', C0603, 'CL10B104KB8NNNC', 'Samsung', (8, 36), 0, {'1': '+3V3', '2': 'GND'}, 'MCU')
add('C5', 'Device:C', '100nF', C0603, 'CL10B104KB8NNNC', 'Samsung', (14, 36), 0, {'1': '+3V3', '2': 'GND'}, 'MCU')
add('Y1', 'Device:Crystal', '8MHz', 'Crystal:Crystal_SMD_HC49-SD', 'ABLS-8.000MHZ-B4-T', 'Abracon',
    (52, 35), 0, {'1': 'XTAL1', '2': 'XTAL2'}, 'MCU')
add('C6', 'Device:C', '22pF', C0603, 'CL10C220JB8NNNC', 'Samsung', (47, 42), 0, {'1': 'XTAL1', '2': 'GND'}, 'MCU')
add('C7', 'Device:C', '22pF', C0603, 'CL10C220JB8NNNC', 'Samsung', (57, 42), 0, {'1': 'XTAL2', '2': 'GND'}, 'MCU')
add('SW1', 'Switch:SW_Push', 'RESET', 'Button_Switch_THT:SW_PUSH_6mm', 'B3F-1000', 'Omron',
    (52, 51), 0, {'1': 'RESET', '2': 'GND'}, 'MCU')
add('RN2', 'Device:R_Pack04', '4x4.7k', 'Resistor_SMD:R_Array_Convex_4x0603', 'YC164-JR-074K7L', 'Yageo',
    (52, 59), 0, {'8': '+3V3', '7': ('JOIN', '8'), '6': ('JOIN', '7'), '5': ('JOIN', '6'),
                  '1': 'SDA', '2': 'SCL', '3': 'ONEWIRE_DQ', '4': 'RESET'}, 'MCU')

# ---------------- 3 VIBRATION ----------------
add('U4', 'Sensor_Motion:ADXL343', 'ADXL345BCCZ', 'Package_LGA:LGA-14_3x5mm_P0.8mm_LayoutBorder1x6y',
    'ADXL345BCCZ-RL7', 'Analog Devices', (92, 37), 0, {
        '1': '+3V3A', '6': '+3V3A', '3': '+3V3A', '2': 'GND', '11': 'GND',
        '7': '+3V3A', '12': ('GND', 2), '13': 'SDA', '14': 'SCL', '8': 'ADXL_INT1', '9': NC}, 'VIBRATION')
add('FB1', 'Device:FerriteBead', '220R@100MHz', 'Inductor_SMD:L_0603_1608Metric', 'BLM18PG221SN1D', 'Murata',
    (71, 33), 90, {'1': '+3V3', '2': '+3V3A'}, 'VIBRATION')
add('C8', 'Device:C', '100nF', C0603, 'CL10B104KB8NNNC', 'Samsung', (71, 40), 0, {'1': '+3V3A', '2': 'GND'}, 'VIBRATION')

# ---------------- 4 TEMPERATURE ----------------
add('J3', 'Connector_Generic:Conn_01x03', 'DS18B20', XH3, 'B3B-XH-A', 'JST',
    (136, 36), 0, {'1': '+3V3', '2': 'ONEWIRE_DQ', '3': 'GND'}, 'TEMPERATURE')
add('D8', 'Device:D_TVS', 'PESD5V0S1BA', 'Diode_SMD:D_SOD-323', 'PESD5V0S1BA,115', 'Nexperia',
    (150, 38), 90, {'2': 'ONEWIRE_DQ', '1': 'GND'}, 'TEMPERATURE')

# ---------------- 5 PRESSURE ----------------
add('J4', 'Connector_Generic:Conn_01x03', 'PRESSURE_0-5V', XH3, 'B3B-XH-A', 'JST',
    (74, 56), 0, {'1': '+5V', '2': 'PRESS_IN', '3': 'GND'}, 'PRESSURE')
add('R1', 'Device:R', '10k', R0603, 'RC0603FR-0710KL', 'Yageo', (84, 54), 90, {'1': 'PRESS_IN', '2': 'PRESS_ADC'}, 'PRESSURE')
add('R2', 'Device:R', '18k', R0603, 'RC0603FR-0718KL', 'Yageo', (93, 58), 0, {'1': 'PRESS_ADC', '2': 'GND'}, 'PRESSURE')
add('C9', 'Device:C', '100nF', C0603, 'CL10B104KB8NNNC', 'Samsung', (99, 58), 0, {'1': 'PRESS_ADC', '2': 'GND'}, 'PRESSURE')
add('D3', 'Diode:BAT54S', 'BAT54S', 'Package_TO_SOT_SMD:SOT-23', 'BAT54S,215', 'Nexperia',
    (106, 54), 0, {'1': 'GND', '2': '+3V3', '3': 'PRESS_ADC'}, 'PRESSURE')

# ---------------- 6 DISPLAY ----------------
add('J5', 'Connector_Generic:Conn_01x04', 'OLED_SSD1306_I2C', 'Connector_PinSocket_2.54mm:PinSocket_1x04_P2.54mm_Vertical',
    'PPTC041LFBN-RC', 'Sullins', (136, 56), 0, {'1': ('GND', 1, 'side'), '2': ('+3V3', 3, 3), '3': 'SCL', '4': 'SDA'}, 'DISPLAY')

# ---------------- 7 USER INTERFACE ----------------
add('RN1', 'Device:R_Pack04', '4x330R', 'Resistor_SMD:R_Array_Convex_4x0603', 'YC164-JR-07330RL', 'Yageo',
    (13, 80), 0, {'1': 'LED_GREEN', '2': 'LED_YELLOW', '3': 'LED_RED', '4': 'RELAY_CTRL',
                  '8': 'LED_G_A', '7': 'LED_Y_A', '6': 'LED_R_A', '5': 'LED_RLY_A'}, 'USER INTERFACE')
add('D4', 'Device:LED', 'GREEN', LED0805, 'APT2012SGC', 'Kingbright', (28, 74), 0, {'2': 'LED_G_A', '1': 'GND'}, 'USER INTERFACE')
add('D5', 'Device:LED', 'YELLOW', LED0805, 'APT2012SYCK', 'Kingbright', (28, 80), 0, {'2': 'LED_Y_A', '1': 'GND'}, 'USER INTERFACE')
add('D6', 'Device:LED', 'RED', LED0805, 'APT2012SRCPRV', 'Kingbright', (28, 86), 0, {'2': 'LED_R_A', '1': 'GND'}, 'USER INTERFACE')
add('SW2', 'Switch:SW_Push', 'ACK/SET', 'Button_Switch_THT:SW_PUSH_6mm', 'B3F-1000', 'Omron',
    (43, 80), 0, {'1': 'BTN_ACK', '2': 'GND'}, 'USER INTERFACE')

# ---------------- 8 ALARM + driver ----------------
add('U5', 'Transistor_Array:ULN2003A', 'ULN2003ADR', 'Package_SO:SOIC-16_3.9x9.9mm_P1.27mm', 'ULN2003ADR',
    'Texas Instruments', (70, 80), 0, {
        '1': 'RELAY_CTRL', '2': 'BUZZER_CTRL', '3': 'FAN_PWM', '4': 'FAN_PWM', '5': 'FAN_PWM',
        '6': ('GND', 2), '7': 'GND', '8': 'GND', '9': '+12V',
        '16': 'RELAY_N', '15': 'BUZZ_N', '14': 'FAN_N', '13': 'FAN_N', '12': 'FAN_N', '11': NC, '10': NC}, 'ALARM')
add('BZ1', 'Device:Buzzer', 'Buzzer 5V active', 'Buzzer_Beeper:Buzzer_12x9.5RM7.6', 'TMB12A05', 'generic 12x9.5 mm',
    (87, 72), 0, {'1': '+5V', '2': 'BUZZ_N'}, 'ALARM')

# ---------------- 9 RELAY ----------------
add('K1', 'Relay:SANYOU_SRD_Form_C', 'SRD-12VDC-SL-C', 'Relay_THT:Relay_SPDT_SANYOU_SRD_Series_Form_C',
    'SRD-12VDC-SL-C', 'Songle / Sanyou', (108, 80), 0,
    {'5': '+12V', '2': 'RELAY_N', '1': 'RLY_COM', '3': 'RLY_NO', '4': 'RLY_NC'}, 'RELAY / ACTUATOR')
add('D7', 'Device:LED', 'ORANGE (RELAY ON)', LED0805, 'APT2012SECK', 'Kingbright', (122, 88), 0,
    {'2': 'LED_RLY_A', '1': 'GND'}, 'RELAY / ACTUATOR')
add('J6', 'Connector:Screw_Terminal_01x03', 'LOAD NO/COM/NC', TB3, 'MKDS 1,5/3-5,08 (1715734)', 'Phoenix Contact',
    (127, 78), 0, {'1': 'RLY_NO', '2': 'RLY_COM', '3': 'RLY_NC'}, 'RELAY / ACTUATOR')

# ---------------- 10 FAN ----------------
add('J7', 'Connector:Screw_Terminal_01x02', 'FAN_12V', TB2, 'MKDS 1,5/2-5,08 (1715721)', 'Phoenix Contact',
    (150, 80), 0, {'1': '+12V', '2': 'FAN_N'}, 'FAN CONTROL')

# ---------------- 11 PROGRAMMING ----------------
add('J2', 'Connector:AVR-ISP-6', 'AVR-ISP-6', 'Connector_PinHeader_2.54mm:PinHeader_2x03_P2.54mm_Vertical',
    'PRPC003DAAN-RC', 'Sullins', (136, 16), 0,
    {'1': 'MISO', '2': '+3V3', '3': 'SCK', '4': 'MOSI', '5': 'RESET', '6': 'GND'}, 'PROGRAMMING')

# ---------------- test points / mechanics (not counted as electronic components) -------------
TP = 'TestPoint:TestPoint_Pad_D1.5mm'
for i, n in enumerate(['+12V', '+5V', '+3V3', 'GND', 'SDA', 'SCL', 'PRESS_ADC', 'UART_RX', 'UART_TX']):
    add('TP%d' % (i + 1), 'Connector:TestPoint', n, TP, '', '', (10 + 7 * i, 99), 0, {'1': n}, 'TEST', bom=False)
for i in range(4):
    add('H%d' % (i + 1), 'Mechanical:MountingHole', 'M3', 'MountingHole:MountingHole_3.2mm_M3', '', '',
        (82 + 7 * i, 100), 0, {}, 'TEST', bom=False)

# schematic block frames: name -> (x0,y0,x1,y1) in U, note
BLOCKS = {
    '1. POWER  12V -> fuse -> reverse-polarity diode -> TVS -> 5V (L7805) -> 3.3V (MCP1700)': (4, 6, 112, 25),
    '11. PROGRAMMING (AVR ISP, 3.3V!)': (114, 6, 160, 25),
    '2. MCU  ATmega328P-AU @ 3.3V / 8MHz': (4, 27, 62, 66),
    '3. VIBRATION SENSOR  ADXL345 (I2C addr 0x53)': (64, 27, 112, 46),
    '4. TEMPERATURE SENSOR  DS18B20 (external, 1-Wire)': (114, 27, 160, 46),
    '5. PRESSURE INPUT  0-5V -> divider 0.643 -> RC -> clamp -> ADC0': (64, 48, 112, 66),
    '6. DISPLAY  OLED SSD1306 I2C (optional module)': (114, 48, 160, 66),
    '7. USER INTERFACE  LEDs + ACK button': (4, 68, 50, 92),
    '8. ALARM + ULN2003A driver': (52, 68, 92, 92),
    '9. RELAY / ACTUATOR': (94, 68, 134, 92),
    '10. FAN CONTROL': (136, 68, 160, 92),
    'TEST POINTS / MOUNTING HOLES': (4, 94, 112, 106),
}
