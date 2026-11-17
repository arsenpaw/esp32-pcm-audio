# Shopping list: `hardware` board

This is the parts list for **one board**, using the cheapest in-stock part for each line. The
board is `hardware/PCB/iot_led_strip_pcb.kicad_sch`. It's built with an ESP32-S3 so the
PDM microphone works with WLED's sound-reactive mode.

- **Prices** are unit prices at qty 1 in USD.
  - U3 and J3 were checked live on lcsc.com on **2026-11-17**.
  - Everything else comes from the JLCPCB/LCSC parts snapshot dated **2026-11-14**, so check it
    before ordering.
- **"—"** means no price was found.
- **Type** is the JLCPCB assembly library. Basic and Preferred parts have no fee. Each Extended
  part costs a **$3 setup fee** if JLCPCB assembles it.

## Parts changed (2026-11-17)

The schematic and PCB fields have been updated to match the table below.

| Ref | Was | Now | Why |
|---|---|---|---|
| U3 | ESP32-S2-SOLO-2-N4 `C3040594` | **ESP32-S3-WROOM-1-N4** `C2913197` ($4.31) | The ESP32-S2 can't receive from PDM mics, so MK1 would be useless on it. The S3 fits the same footprint, and every pad this board uses carries the same GPIO number (see below). |
| U4 | SN74AHCT125PWR `C36365` | 74HCT125T14-13 `C842453` ($0.24) | Old part not stocked. It's a pin-identical TSSOP-14 '125, and HCT logic accepts 3.3 V input. A pin-identical AHCT alternative is 74AHCT125T14-13 `C176917` ($0.40). |
| D1, D2 | SMF5V0A `C1972946` ($0.16) | SMF5.0A `C20883238` ($0.017) | Same 5 V TVS diode in the same SMF package, about 9× cheaper. The cheap one has only 130 in stock; if it's gone, go back to `C1972946`. |
| J1, J2 | `C5188425` | DB128L-5.08-3P `C500022` ($0.15) | `C5188425` is actually a 5.0 mm wire-to-board plug, not the 5.08 mm screw terminal this footprint needs. Another option is WJ500V-5.08-03P `C72334` ($0.22, large stock). |
| MK1 | SPH0641LU4H-1 `C5454543` | SPH0641LM4H-1 `C497724` ($1.68) | The old LCSC number is delisted. The new part has the same LGA-5 footprint and pinout. See "Where to buy MK1" below. |
| J3, R12, R14 | `"C2988369 "`, `" C17513 "` | `C2988369`, `C17513` | Removed stray spaces that broke BOM lookups. |

## Bill of materials

| Ref | Qty | Part | LCSC | Type | Unit $ | Line $ |
|---|---|---|---|---|---|---|
| U3 | 1 | **ESP32-S3-WROOM-1-N4** module | C2913197 | Extended | 4.308 | 4.31 |
| MK1 | 1 | SPH0641LM4H-1 PDM mic | C497724 | Extended | 1.679 | 1.68 |
| C1-3, C5, C8, C13, C15-17 | 9 | 10 µF 25 V X5R 0805 | C15850 | Basic | 0.069 | 0.62 |
| C4, C6, C7, C9-12, C14, C18 | 9 | 100 nF 50 V X7R 0805 | C49678 | Basic | 0.019 | 0.17 |
| D1, D2 | 2 | SMF5.0A 5 V TVS, SMF | C20883238 | Extended | 0.017 | 0.03 |
| D3 | 1 | 1N5819WS Schottky, SOD-323 | C191023 | Basic | 0.014 | 0.01 |
| D4 | 1 | Green LED 0805 (STAT) | C2297 | Basic | 0.016 | 0.02 |
| D5 | 1 | Red LED 0805 (PWR) | C84256 | Basic | 0.014 | 0.01 |
| D6 | 1 | 1N4148W, SOD-123 | C81598 | Basic | 0.012 | 0.01 |
| D7, D8 | 2 | PTVSHC3D12VU 12 V TVS, SOD-323 | C169336 | Extended | 0.042 | 0.08 |
| F2 | 1 | XF-505P blade fuse holder (TH) | C843270 | Extended | 0.113 | 0.11 |
| F3 | 1 | Low-profile blade fuse | — | — | — | — |
| J1, J2 | 2 | 3-pin 5.08 mm screw terminal | C500022 | Extended | 0.154 | 0.31 |
| J3 | 1 | GT-USB-7010ASV USB-C 16P (LCSC minimum 5) | C2988369 | Extended | 0.089 | 0.09 |
| J4 | 1 | DC barrel jack, Würth 694106301002 footprint | — | — | — | — |
| K2 | 1 | SRD-05VDC-SL-C relay | C35449 | Extended | 0.444 | 0.44 |
| Q1 | 1 | AO3400A N-MOSFET, SOT-23 | C20917 | Basic | 0.090 | 0.09 |
| R1, R4, R5 | 3 | 10 k 0805 | C17414 | Basic | 0.003 | 0.01 |
| R3, R10 | 2 | 27 Ω 0805 | C17594 | Preferred | 0.003 | 0.01 |
| R6 | 1 | 100 Ω 0805 | C17408 | Basic | 0.004 | 0.00 |
| R7, R17 | 2 | 33 Ω 0805 (fit this pair **or** R16/R18) | C17634 | Basic | 0.005 | 0.01 |
| R8, R9 | 2 | 5.1 k 0805 (USB-C CC) | C27834 | Basic | 0.006 | 0.01 |
| R12, R14 | 2 | 1 k 0805 | C17513 | Basic | 0.004 | 0.01 |
| R16, R18 | 2 | 220 Ω 0805 (fit this pair **or** R7/R17) | C17557 | Basic | 0.006 | 0.01 |
| SW1, SW2 | 2 | Tactile switch 5.1 mm (RESET, FLASH) | C318884 | Basic | 0.021 | 0.04 |
| SW3-5 | 3 | SK-3296S-01-L1 SPDT slide switch | C319020 | Extended | 0.082 | 0.25 |
| U1 | 1 | AMS1117-3.3, SOT-223 | C6186 | Basic | 0.209 | 0.21 |
| U2 | 1 | TAR5S50 5 V LDO (buffer supply) | C146354 | Extended | 0.361 | 0.36 |
| U4 | 1 | 74HCT125T14-13, TSSOP-14 | C842453 | Extended | 0.238 | 0.24 |

**Total: about $9.15 per board** for every priced line. This leaves out J4, F3 and the PCB.
The ESP32 module is almost half the cost.

## Where to buy MK1

LCSC currently has **no SPH0641 in stock**: the `C497724` page is gone, and a search for
"SPH0641" finds nothing. You can still get it two ways:

- **JLCPCB assembly:** JLCPCB's own stock listed 233 of `C497724` on 2026-11-14. Have them place
  MK1. It's an LGA part and hard to hand-solder anyway.
- **Hand assembly:** buy SPH0641LU4H-1 or SPH0641LM4H-1 from DigiKey or Mouser. Both fit the
  footprint.

When soldering MK1, keep the sound port (a hole through the PCB) covered, as the schematic note
says.

## Why the ESP32-S3 drops in

Both modules use the same 41-pad, 18 × 25.5 mm land pattern. Here is every pad this board
connects, with the same GPIO on both modules:

| Pad | Net | GPIO |
|---|---|---|
| 3 | RST | EN |
| 5 / 6 | MIC_CLK / MIC_DATA | GPIO5 / GPIO6 |
| 7 | RELAY_PIN | GPIO7 |
| 10 | LED strip 1 data (LV_DIN1) | GPIO17 |
| 23 | LED strip 2 data (LV_DIN2) | GPIO21 |
| 13 / 14 | USB D- / D+ | GPIO19 / GPIO20 |
| 17 / 18 | test pads TP8 / TP9 | GPIO9 / GPIO10 |
| 27 | BOOT | GPIO0 |
| 36 / 37 | UART RX / TX | GPIO44 / GPIO43 |
| 38 | Status LED (via R12) | GPIO2 |

- **Pads that differ between the modules are unconnected here.** Pads 24, 25 and 28–30 are
  GPIO33–37 on the S2 but GPIO47/48 and GPIO35–37 on the S3.
- **The S3's strapping pins are safe.** GPIO45 and GPIO46 are unconnected, so their internal
  pull-downs give the correct boot setting for 3.3 V flash.
- **Which variant:** the plain **-N4** is the cheapest. -N4R2 and -N4R8 also fit but cost more,
  and WLED doesn't need PSRAM.
- The KiCad symbol and footprint are still the S2-SOLO ones, because the land pattern is the
  same. U3's Value, LCSC and Description fields now name the S3 module.

## Ways to cut cost

1. **Fit only one strip-resistor pair.** The schematic note says to use 33 Ω (R7, R17) when data
   and GND share a cable, and 220 Ω (R16, R18) when they're separate wires. Buy only the pair you
   need.
2. **Hand-solder the through-hole parts** (F2, J1, J2, J4, K2) even if JLCPCB assembles the rest.
   Every Extended part you leave off the assembly order saves $3.
3. **Watch LCSC minimums when hand-assembling.** 0805 passives usually come in strips of 50 or
   100. Each resistor line will cost about $0.20–0.50 no matter how few you need, so ordering
   parts for 2–5 boards costs barely more than for one.

## Not checked yet

- **Live prices for most lines.** Only U3, J3 and MK1's availability were checked live on LCSC.
  The rest come from the 2026-11-14 snapshot.
- **J4's part number.** The barrel jack has no LCSC number. Buy a Würth 694106301002 or a jack
  that fits that footprint.
- **F3's rating.** Its Value says 10 A but its Description says 8 A. Pick a rating that suits your
  strip current.
- **Real hardware.** The S3 swap is checked only on paper, against the module pinouts and the PCB
  nets. It hasn't been built.
