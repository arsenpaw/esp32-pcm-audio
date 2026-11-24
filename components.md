# Components

This is everything you need to build **one** finished board, `hardware/PCB/iot_led_strip_pcb`,
including the parts that aren't soldered onto it. Part numbers are LCSC numbers, and each one
links to its LCSC page. Prices are in USD at qty 1.
- **Checked live on lcsc.com (2026-11-17/18):** U3, J3, and LCSC's lack of stock for MK1 and J4.
- **Everything else:** from the JLCPCB/LCSC parts snapshot dated 2026-11-14.

See [shop.md](shop.md) for why each part was chosen and for ways to cut cost.

## Decide first

The board has three spots where you either fit a switch to choose later or set the choice once
with a solder bridge. These choices change what you buy.

| Choice | Switchable (buy more) | Fixed (buy less) |
|---|---|---|
| **Strip voltage** (overvoltage protection) | Fit **SW5** ("Vdd Sel") and **both** TVS pairs, D1/D2 (5 V) and D7/D8 (12 V). | Skip SW5. Fit only **D1/D2** and bridge **JP4** for 5 V strips, or only **D7/D8** and bridge **JP8** for 12 V strips. JP4 and JP8 are on the back. |
| **Data-line resistor** per strip | Fit **SW3** and **SW4** and **all four** resistors: R7/R17 (33 Ω) and R16/R18 (220 Ω). | Skip SW3/SW4. Bridge JP5/JP6 toward the resistor you want. Fit only R7/R17 (33 Ω), when data and GND share a cable, or only R16/R18 (220 Ω), when they're separate wires. |
| **USB powers the board** | Fit the **JP1 header and jumper cap**, so you can pull the cap before connecting USB while external power is on. The board's back silkscreen warns about this. | Solder-bridge **JP3** instead. USB and the barrel jack are then always joined, so never plug in both. |

The tables below list the **switchable** version, which is everything.

## Parts soldered on the board

### Modules and ICs

| Ref | Qty | Part | What it does | LCSC | Unit $ |
|---|---|---|---|---|---|
| U3 | 1 | ESP32-S3-WROOM-1-N4 | Wi-Fi MCU that runs WLED. Use the S3, not the S2, so the PDM mic works. | [C2913197](https://www.lcsc.com/product-detail/C2913197.html) | 4.31 |
| MK1 | 1 | Knowles SPH0641LM4H-1 | PDM MEMS microphone for sound-reactive effects. **LCSC has none in stock.** Order it through JLCPCB assembly or from DigiKey/Mouser. SPH0641LU4H-1 also fits. | [C497724](https://www.lcsc.com/product-detail/C497724.html) | 1.68 |
| U4 | 1 | 74HCT125T14-13, TSSOP-14 | Shifts the 3.3 V data signal up to 5 V for the strips. | [C842453](https://www.lcsc.com/product-detail/C842453.html) | 0.24 |
| U1 | 1 | AMS1117-3.3, SOT-223 | 3.3 V regulator for the ESP32. | [C6186](https://www.lcsc.com/product-detail/C6186.html) | 0.21 |
| U2 | 1 | TAR5S50, SSOP-5 | 5 V regulator for the level shifter and relay coil, needed when running 12 V strips. | [C146354](https://www.lcsc.com/product-detail/C146354.html) | 0.36 |
| Q1 | 1 | AO3400A N-MOSFET, SOT-23 | Relay driver. | [C20917](https://www.lcsc.com/product-detail/C20917.html) | 0.09 |

### Connectors, relay and fuse holder

| Ref | Qty | Part | What it does | LCSC | Unit $ |
|---|---|---|---|---|---|
| J3 | 1 | G-Switch GT-USB-7010ASV, USB-C 16P | Programming and USB power. LCSC sells a minimum of 5. | [C2988369](https://www.lcsc.com/product-detail/C2988369.html) | 0.09 |
| J4 | 1 | **Würth 694106301002** DC barrel jack | Main power input. **Buy the genuine Würth part from DigiKey/Mouser.** LCSC only has DC005 lookalikes, rated 0.5–2 A, which may not fit this footprint. | — | — |
| J1, J2 | 2 | 3-pin 5.08 mm screw terminal | LED strip outputs (5V / DATA / GND). | [C500022](https://www.lcsc.com/product-detail/C500022.html) | 0.15 |
| K2 | 1 | Songle SRD-05VDC-SL-C relay | Lets WLED switch the strip power on and off. | [C35449](https://www.lcsc.com/product-detail/C35449.html) | 0.44 |
| F2 | 1 | XF-505P blade fuse holder, through-hole | Holds the main fuse, F3. | [C843270](https://www.lcsc.com/product-detail/C843270.html) | 0.11 |
| JP1 | 1 | 1×2 pin header, 2.54 mm | USB power link (see "Decide first"). | [C358684](https://www.lcsc.com/product-detail/C358684.html) | 0.01 |
| JP1 | 1 | Jumper cap, 2.54 mm | Fits the header above. | [C18185737](https://www.lcsc.com/product-detail/C18185737.html) | 0.01 |

### Switches

| Ref | Qty | Part | What it does | LCSC | Unit $ |
|---|---|---|---|---|---|
| SW1, SW2 | 2 | Tactile switch, 5.1 mm | RESET and FLASH (boot) buttons. | [C318884](https://www.lcsc.com/product-detail/C318884.html) | 0.02 |
| SW3, SW4 | 2 | SK-3296S-01-L1 slide switch | Picks the 33 Ω or 220 Ω data resistor for each strip. Optional. | [C319020](https://www.lcsc.com/product-detail/C319020.html) | 0.08 |
| SW5 | 1 | SK-3296S-01-L1 slide switch | Picks 5 V or 12 V strip protection. Optional. | [C319020](https://www.lcsc.com/product-detail/C319020.html) | 0.08 |

### Diodes and LEDs

| Ref | Qty | Part | What it does | LCSC | Unit $ |
|---|---|---|---|---|---|
| D1, D2 | 2 | SMF5.0A TVS, SMF | Overvoltage protection for **5 V** strips. Only 130 in stock; the fallback is [C1972946](https://www.lcsc.com/product-detail/C1972946.html) ($0.16). | [C20883238](https://www.lcsc.com/product-detail/C20883238.html) | 0.02 |
| D7, D8 | 2 | PTVSHC3D12VU TVS, SOD-323 | Overvoltage protection for **12 V** strips. | [C169336](https://www.lcsc.com/product-detail/C169336.html) | 0.04 |
| D3 | 1 | 1N5819WS Schottky, SOD-323 | Protects the 3.3 V regulator if its input drops below its output. | [C191023](https://www.lcsc.com/product-detail/C191023.html) | 0.01 |
| D6 | 1 | 1N4148W, SOD-123 | Flyback diode across the relay coil. | [C81598](https://www.lcsc.com/product-detail/C81598.html) | 0.01 |
| D4 | 1 | Green LED, 0805 | "STAT" status LED on GPIO2. | [C2297](https://www.lcsc.com/product-detail/C2297.html) | 0.02 |
| D5 | 1 | Red LED, 0805 | "PWR" power LED. You can disable it with JP2. | [C84256](https://www.lcsc.com/product-detail/C84256.html) | 0.01 |

### Capacitors (all 0805)

| Ref | Qty | Part | LCSC | Unit $ |
|---|---|---|---|---|
| C1-C3, C5, C8, C13, C15-C17 | 9 | 10 µF 25 V X5R | [C15850](https://www.lcsc.com/product-detail/C15850.html) | 0.07 |
| C4, C6, C7, C9-C12, C14, C18 | 9 | 100 nF 50 V X7R | [C49678](https://www.lcsc.com/product-detail/C49678.html) | 0.02 |

### Resistors (all 0805)

| Ref | Qty | Value | What it does | LCSC | Unit $ |
|---|---|---|---|---|---|
| R1, R4, R5 | 3 | 10 kΩ | Pull-ups and pull-downs. | [C17414](https://www.lcsc.com/product-detail/C17414.html) | 0.003 |
| R8, R9 | 2 | 5.1 kΩ | USB-C CC pins, so a USB-C charger supplies 5 V. | [C27834](https://www.lcsc.com/product-detail/C27834.html) | 0.006 |
| R12, R14 | 2 | 1 kΩ | LED current limiting. | [C17513](https://www.lcsc.com/product-detail/C17513.html) | 0.004 |
| R3, R10 | 2 | 27 Ω | USB data lines. | [C17594](https://www.lcsc.com/product-detail/C17594.html) | 0.003 |
| R6 | 1 | 100 Ω | Mic data line. | [C17408](https://www.lcsc.com/product-detail/C17408.html) | 0.004 |
| R7, R17 | 2 | 33 Ω | Strip data resistor, when data and GND share a cable. | [C17634](https://www.lcsc.com/product-detail/C17634.html) | 0.005 |
| R16, R18 | 2 | 220 Ω | Strip data resistor, when data and power run as separate wires. | [C17557](https://www.lcsc.com/product-detail/C17557.html) | 0.006 |

Not bought: JP2–JP8 are solder jumpers, and the TP test points, H mounting holes, FID fiducials
and J7 (power-injection wire pads) are bare copper.

## Parts not soldered on the board

| Item | Qty | Notes |
|---|---|---|
| **PCB** | 1 | `hardware/PCB/iot_led_strip_pcb.kicad_pcb`, about 57 × 56 mm. Order from JLCPCB or similar. |
| **F3 blade fuse** | 1 | A low-profile blade fuse to fit the XF-505P holder. Pick it for your strip current; the board is labelled max 10 A, and the holder is rated 15 A. |
| **Power supply** | 1 | 5 V or 12 V to match your strips, with a 5.5 × 2.1 mm barrel plug, sized for the strip current. A USB-C charger works for short strips. |
| **USB-C cable** | 1 | For flashing WLED. |
| **LED strips** | 1–2 | WS2812B (5 V) or WS2811 (12 V), connected to J1/J2 as 5V / DATA / GND. |
| **Case** (optional) | 1 | 3D-print `hardware/case/` in PLA at 10% infill. You need the top, plus **one** of the two bottoms (with or without the screw tab). The case was designed for an earlier revision of this board, so check the fit first. |
| **M2 × 8 mm machine screws** | 5 | Hold the case together; they self-tap into the printed plastic. |

## Totals

- **Parts on the board, switchable version:** about **$9.17**. That's every priced line above,
  and it leaves out J4 and the off-board items.
- **Fixed version** (no SW3–SW5, one TVS pair, one resistor pair): about **$0.34** less.
- **The ESP32 module is almost half the total**, and the mic adds $1.68.
