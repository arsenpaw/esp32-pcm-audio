# WLED Sound-Reactive LED Controller — Requirements & Proposed Design

Date: 2026-11-15
Status: Draft

This document has two parts.

- **Part A — Requirements** says *what* the board must do. It is binding. Changes need the
  owner's agreement.
- **Part B — Proposed design** is *one way* to meet Part A. It is not binding. The technical
  implementation (exact parts, values, schematic, layout) is still to be defined. Anything in
  Part B can change as long as Part A is still met.

---

# Part A — Requirements

## A1. Purpose

A small, portable board that runs **WLED** and drives **two addressable LED strips**. It has an
on-board **microphone** for WLED's sound-reactive effects and is powered from **USB-C 5 V**.

## A2. Requirements

Source: **Owner** = stated by the project owner. **Derived** = follows from an owner requirement,
or was proposed by Claude and not objected to. Derived items should be confirmed.

### Power

| ID | Requirement | Source |
|---|---|---|
| PWR-01 | The board is powered only from an external source through a **USB-C** connector at **5 V**. | Owner |
| PWR-02 | Total current drawn from the USB-C source must not exceed **2 A** under any operating condition. | Owner |
| PWR-03 | If the LED strips try to draw more than their share of the 2 A budget, **strip power is cut in hardware**. | Owner |
| PWR-04 | A strip overcurrent cut or a strip short **must not reset or brown out the MCU**. | Derived |
| PWR-05 | **CC1 and CC2 each have their own 5.1 kΩ pull-down.** A single resistor shared between them is not allowed. | Owner |
| PWR-06 | The board can **read the CC voltage** to tell Default, 1.5 A and 3 A sources apart. | Owner |
| PWR-07 | The board can run **BC1.2 detection on D+/D−** to identify USB-A chargers. Apple and Samsung proprietary detection is desirable. | Owner |
| PWR-08 | The board has **adaptive input current limiting**: when VBUS starts to sag on a weak or mislabelled source, load is shed **before** the MCU browns out. | Owner |
| PWR-09 | After a hardware strip cut, the strips stay off until the board is power-cycled. | Derived (confirm, the alternative is auto-retry) |

### MCU & firmware

| ID | Requirement | Source |
|---|---|---|
| MCU-01 | The MCU is from the **ESP32** family. ESP8266 is excluded. | Owner |
| MCU-02 | The board runs **stock WLED** with sound-reactive (AudioReactive) support, with no custom firmware needed for basic operation. | Owner |
| MCU-03 | Firmware can be flashed and updated **over the same USB-C port** that powers the board. | Derived |

### LED outputs

| ID | Requirement | Source |
|---|---|---|
| LED-01 | **Two** addressable LED strip outputs, 5 V, 3-wire (5V / DATA / GND), for WS2812B/SK6812-class strips. | Owner (count); Derived (type) |
| LED-02 | Strip data must be reliable on typical 1–2 m strips, which means 5 V logic levels at the connector. | Derived |
| LED-03 | Strip power for both outputs comes from the same 2 A budget (PWR-02). | Owner |

### Audio

| ID | Requirement | Source |
|---|---|---|
| AUD-01 | An **on-board digital microphone** that WLED AudioReactive can use. The owner said "I2C". WLED needs an **I2S** mic, and the owner accepted I2S. | Owner |

### Mechanical

| ID | Requirement | Source |
|---|---|---|
| MEC-01 | **Small and portable.** | Owner |
| MEC-02 | Connectors on board edges, with mounting holes, so the board fits an enclosure. | Derived |

### Tooling

| ID | Requirement | Source |
|---|---|---|
| TOL-01 | The design is made in **KiCad 10** (10.0.8 installed locally). | Owner |
| TOL-02 | The repo includes an **MCP server for KiCad 10** so Claude Code can work on the design. | Owner |

## A3. Non-goals

- No battery or battery charger on the board.
- No USB Power Delivery voltage negotiation. 5 V only.
- No more than two strip outputs in this revision.
- No extra sensors, displays or expansion headers in this revision.
- Custom firmware (for example, reacting to source detection) is not required for this
  revision. The hardware must still support it later (PWR-06/07/08).
- Enclosure design.

## A4. Anti-goals (failure even if it "works")

- The MCU resets or browns out when the strips go bright, the strips are cut, or the source
  is weak.
- The device can pull noticeably more than 2 A from the source.
- C-to-C chargers refuse to supply power (for example, because the CC resistor is shared).
- Unreliable strip data.
- A bulky board, such as a dev board on a carrier or through-hole modules.

## A5. Open questions

1. **Size / enclosure:** no target named. The board is placed at 66 × 32 mm (Derived, B8).
2. **After a strip cut** (PWR-09): working assumption is latch off until replugged (Derived).
3. **Strip type and length:** answered by the owner on 2026-11-15. Strip length is flexible.
   The 2 A budget stays, and WLED's brightness limiter scales output to fit it. 5 V
   WS2812B/SK6812-class strips remain the assumption (LED-01).

## A6. Acceptance criteria

- Full white on both strips with WLED's limiter: measured source current ≤ 2 A (PWR-02).
- A short on the strip rail cuts the strips, and the MCU keeps running (PWR-03, PWR-04).
- C-to-C chargers advertising Default, 1.5 A and 3 A: each one powers the board and is
  correctly identified (PWR-05, PWR-06).
- A USB-A DCP charger and an Apple charger are identified (PWR-07).
- A weak source (a 500 mA laptop port) with full-white strips: the load is shed and the MCU
  does not reset (PWR-08).
- WLED is flashed over USB-C, both strips run, and AudioReactive responds to sound
  (MCU-02/03, LED-01, AUD-01).
- ERC and DRC are clean, and every BOM line has an MPN.

---

# Part B — Proposed Design (non-binding, to be defined)

Everything below is Claude's proposal. Exact parts, values and layout are decided during
implementation. Each item lists the requirements it serves.

## B1. MCU — ESP32-S3-MINI-1 (N8 or N4R2) · MCU-01/02/03, MEC-01

- The module is about 15.4 × 20.5 mm, with an integrated antenna and pre-certification.
- Native USB on GPIO19/20, so no USB-UART bridge is needed. WLED flashes over USB-C.
- WLED supports the S3, including AudioReactive with an I2S mic.
- The antenna goes at a board edge, with the keep-out from the datasheet.

## B2. Power architecture · PWR-01..04, PWR-08, PWR-09

```
USB-C VBUS (5 V) ──► ESD/TVS ──┬──► 3.3 V LDO (1 A) ──► ESP32-S3, mic, logic
                               │
                               ├──► VBUS sense divider ──► ESP32 ADC1
                               │
                               └──► eFuse (ILIM ≈ 1.7 A, latch-off, UVLO ≈ 4.4 V) ──► bulk cap ──► Strip 1 & 2
                                          │
                                          └── FLT/PG ──► ESP32 GPIO
```

- **Budget split:** about 1.7 A for the strips (the eFuse limit) and about 0.3 A for the ESP32
  at Wi-Fi peak, for 2 A total.
- **eFuse:** a 5 V integrated eFuse with:
  - a resistor-set current limit, with worst-case trip ≤ 1.8 A;
  - soft-start;
  - a fault/PG output;
  - a latch-off variant;
  - an EN/UV divider.

  Candidates are the TI TPS25947x / TPS2595x families, to be chosen.
- **MCU isolation:** the LDO sits upstream of the eFuse, so a strip fault doesn't collapse
  3.3 V. Add about 22 µF on VBUS and keep inrush near the USB guidance. The strip bulk
  capacitance sits behind the eFuse soft-start.
- **3.3 V:** an LDO of at least 1 A (for example AP7361C-33), with 10 µF + 22 µF on the output.
  It dissipates about 0.5 W, so it needs a copper pour.
- **Strip bulk capacitance:** about 470 µF after the eFuse, plus 100 nF at each connector.

## B3. USB-C and source detection · PWR-05..08, MCU-03

- A 16-pin USB 2.0 Type-C receptacle on a board edge. D+/D− are joined at the connector and
  routed as a 90 Ω differential pair.
- ESD: a USBLC6-2SC6 on D+/D−, and a TVS on VBUS (for example SMF5.0A).
- **PWR-05:** two separate 5.1 kΩ resistors (R_CC1, R_CC2) to GND.
- **PWR-06:** both CC pins go to ESP32 **ADC1**, high impedance. The readings mean:
  - 0.25–0.61 V: Default
  - 0.70–1.16 V: 1.5 A
  - 1.31–2.04 V: 3 A

  Fallback if the ADC readings prove unreliable: a **TI TUSB320** (I2C), used instead of the ADC.
- **PWR-07:** a BC1.2 detector with **D+/D− pass-through to the ESP32** once detection finishes,
  so USB flashing still works. A candidate is the **TI BQ24392**, to be confirmed. Its status
  outputs go to GPIOs. Charger ICs like the BQ2589x aren't used, because there is no battery.
- **PWR-08:** true VINDPM only exists in battery-charger ICs, so this is approximated:
  - **Hardware:** eFuse UVLO at about 4.4 V cuts the strips before the LDO drops out.
  - **Measurement:** a VBUS divider (100 k / 100 k + 100 nF) into ADC1, so a future usermod can
    lower WLED's limiter (ABL) as VBUS sags.
- **Future usermod logic** (out of scope, but the hardware supports it):
  1. Take the source capability from CC, or from BC1.2 when CC reads Default.
  2. Set ABL to that capability minus the ESP32's share, and never above 1.7 A.
  3. Trim further when VBUS sags.

  The eFuse limit and UVLO remain the hard safety net.

## B4. LED strip outputs · LED-01..03

- **Connectors:** 2 × JST-XH 3-pin (rated 3 A), pin order 5V / DATA / GND, marked on silkscreen.
- **Level shift:** an **SN74LV1T125** per channel (3.3 V input, 5 V output, Ioff), powered from
  the strip rail after the eFuse, with a 220 Ω series resistor on each output. When the eFuse
  trips, the buffer loses power and its output goes high-impedance. The data line therefore
  can't back-power a strip that has been cut. Stock WLED doesn't know about the trip and keeps
  sending data, so this matters.
- **Traces:** strip power traces are sized for 2 A continuous (≥ 1 mm on 1 oz copper, or a pour).

## B5. Microphone · AUD-01

- A **TDK ICS-43434**: I2S, bottom port, LGA. It's the WLED community reference part, in the
  same family as the INMP441.
- L/R is tied low. A PCB through-hole goes under the acoustic port, per TDK's land pattern.
- It sits away from the LDO, with 100 nF + 1 µF decoupling.

## B6. User interface

- **Buttons:**
  - BOOT on GPIO0, which also works as WLED button 0.
  - RESET on EN, with a 10 k / 1 µF RC.
  - USER on a free GPIO, as WLED button 1.
- **LEDs:** a status LED on a GPIO, and a dim power LED on 3.3 V.

## B7. Suggested GPIO map (to be verified)

| Function | GPIO |
|---|---|
| USB D− / D+ | 19 / 20 |
| Strip 1 / Strip 2 data | 16 / 18 |
| I2S SCK / WS / SD | 6 / 5 / 4 |
| eFuse FLT/PG | 7 |
| CC1 / CC2 sense (ADC1) | 1 / 2 |
| VBUS sense (ADC1) | 8 |
| BC1.2 status | 9, 10 |
| USER button | 15 |
| Status LED | 38 |
| BOOT | 0 |

Avoid the strapping pins 3, 45 and 46, and the module's flash/PSRAM pins. Use ADC1 only,
because ADC2 doesn't work while Wi-Fi is on.

## B8. Board

- **Size:** **66 × 32 mm** as placed (2026-11-15). The parts do not fit single-sided in
  45 × 25 mm: the footprints alone cover about 1,040 mm² of its 1,125 mm². Getting back
  toward 45 × 25 mm needs parts on both sides.
- **Layers:** 4 layers, 1.6 mm (signal / GND / power / signal). Two layers are acceptable if the
  layout closes.
- **Assembly:** single-sided SMD, so it can be fully assembled (JLCPCB by default, preferring
  Basic parts). Passives are 0603, or 0402 where space is tight.
- **Mounting:** 2 × M2 mounting holes. USB-C on one short edge, strip connectors on the
  opposite or long edges.

## B9. WLED configuration (stock firmware)

- An official ESP32-S3 build that includes AudioReactive.
- **LED outputs:** GPIO16 and GPIO18. ABL enabled at **1500 mA** (see B11).
- **AudioReactive:** generic I2S, SD=4, WS=5, SCK=6.
- **Buttons:** GPIO0 and GPIO15.

## B10. Tooling and repo · TOL-01/02

- **MCP server:** [`mixelpixx/KiCAD-MCP-Server`](https://github.com/mixelpixx/KiCAD-MCP-Server)
  v2.9.0 (MIT).
  - Vendored as a git submodule at `tools/kicad-mcp-server`, and built by
    `scripts/setup-mcp.sh` (Node build plus a venv on KiCad's bundled Python).
  - Supports KiCad 9 and 10, with about 250 tools: schematic, placement, routing, DRC/ERC,
    library and JLCPCB search, and exports.
  - It edits files through KiCad's SWIG `pcbnew` API. IPC live editing is experimental.
  - Project-scoped `.mcp.json`, using paths relative to the repo root:

  ```json
  {
    "mcpServers": {
      "kicad": {
        "command": "node",
        "args": ["tools/kicad-mcp-server/dist/index.js"],
        "env": {
          "KICAD_PYTHON": "tools/kicad-mcp-server/venv/bin/python3",
          "LOG_LEVEL": "info"
        }
      }
    }
  }
  ```
- **Repo layout:**

  ```
  .mcp.json
  README.md
  tools/kicad-mcp-server/     MCP server (git submodule)
  scripts/setup-mcp.sh        MCP server build + KiCad-Python venv
  docs/requirements/          this document
  hardware_deprecated/        KiCad 10 project (hierarchical sheets: power, usb, mcu, leds, audio)
    lib/                      project symbols/footprints/3D
    fab/                      generated outputs (gitignored until release)
  firmware/wled-config.md     WLED settings from B9
  .gitignore                  KiCad backups/caches, fab/
  ```

## B11. Schematic as drawn (2026-11-15)

The schematic follows B1–B7 with these concrete choices. ERC is clean. Values come from the
datasheets; LCSC stock and MPNs for passives are not checked yet.

- **eFuse:** TI **TPS259630DDA** (latch-off after thermal shutdown, adjustable OVLO).
  - R_ILM = 562 Ω gives 1.62 A typical, about 1.49–1.73 A over tolerance. It limits the
    current actively and latches off when it overheats, so a short is held at the limit
    for a moment before the cut.
  - Divider 75 k / 6.04 k / 20 k: strips off below 4.27 V, on above 4.66 V, off above 6.06 V.
    The undervoltage cut is not latched; the strips return when VBUS recovers.
  - C_dVdt = 47 nF, about 0.9 V/ms, so the 470 µF bulk cap charges at roughly 0.4 A.
  - FLT is pulled up to 3.3 V and goes to GPIO7.
- **WLED limiter:** set ABL to **1500 mA**, not 1700 mA, so it stays under the eFuse's
  minimum limit.
- **BC1.2:** TI **BQ24392**. GOOD_BAT is tied high so the D+/D− switch closes on a PC port.
  - CHG_DET (5 V level, divided 10 k / 20 k) → GPIO9. SW_OPEN (pulled up to 3.3 V) → GPIO10.
  - GPIO9 low + GPIO10 low: standard PC port. High + low: charging PC port. High + high:
    wall charger, including Apple. Low + high: unknown source.
  - Apple chargers are reported as "charger" only; the 1 A / 2.1 A / 2.4 A classes are not
    told apart.
- **CC sense:** each CC pin goes through 10 k and 100 nF to GPIO1 / GPIO2.
- **LED data:** 100 k pull-downs on the buffer inputs keep the outputs low during boot.
- **Nets** cross sheets by global label; the sheets have no hierarchical pins.
- **Part numbers:** every BOM line has an MPN and an LCSC number, checked against the JLCPCB
  catalog of 2026-11-14. Two parts are not in JLCPCB assembly stock and must be pre-ordered
  from LCSC: **ESP32-S3-MINI-1-N8** (C2913206) and **ICS-43434** (C5656610). The owner asked
  for the cheapest option; both are cheaper than the in-stock alternatives
  (ESP32-S3-MINI-1U-N4R2 plus an antenna, ICS-43432). Several distributors mark the ICS-43434
  as not recommended for new designs, so re-check before any later revision.
- **Strip connectors:** Megastar ZX-XH2.54-3PWT (JST XH compatible). Check its pads against
  the JST footprint at layout.

## B12. Layout as routed (2026-11-15)

- **Stackup use:** signals on the top and bottom layers. Inner layer 1 is a solid ground
  plane. Inner layer 2 is split into a VBUS plane (USB side) and a +5V_STRIP plane (eFuse
  output to the strip connectors).
- **How it was routed:** Freerouting 2.5.0 for the bulk, then `scripts/finish_route.py` for
  what it left open: vias from power and ground pads into the planes (two per high-current
  pad where they fit), and rip-up-and-retry for boxed-in nets. No hand routing.
- **Rules:** 0.15 mm clearance, 0.2 mm signal tracks, 0.5 mm power tracks, 0.6/0.3 mm vias.
  `hardware_deprecated/esp32-wled-audio.kicad_dru` allows 0.1 mm against the BQ24392's pads.
- **DRC:** no errors, no unconnected items, schematic parity clean. Remaining warnings: the
  library silkscreen of J1 and U5 crosses the board edge. The thermal-relief check is
  relaxed to one spoke.
- **Review pass (2026-11-15):** measured the copper and fixed four things, then re-routed.
  - The module's 100 nF cap (C14) moved from 13 mm to 2 mm from its 3V3 pin.
  - The eFuse input cap (C2) moved from 14 mm to 2 mm from VIN.
  - The regulator output cap (C5) moved from the ground tab to 2.6 mm from VO.
  - Ground pins of both strip connectors and the USB connector, and both pads of the bulk
    cap, now have plane vias within 2.3 mm. Before, the strip return had none nearby.
  - Result: 118 vias (15 VBUS, 11 strip power, 19 ground). Power tracks are 0.3–0.5 mm.
    The module's 10 µF cap (C13) and the EN RC stay about 13 mm from their pins.
- **Not reviewed:** USB D+/D− are not routed as a matched 90 Ω pair (the ESP32-S3 port is
  full-speed only). The 2 A paths rely on plane vias and 0.5 mm stubs and should be checked
  by eye. Most reference designators are hidden on silkscreen to clear overlaps.

## B13. To be defined during implementation

- The exact eFuse, ILIM and UVLO resistor values.
- The exact BC1.2 detector, and whether to fall back to TUSB320.
- The exact LDO, TVS, connector and capacitor MPNs, chosen from assembler stock.
- The final GPIO map, placement, routing and board outline.
