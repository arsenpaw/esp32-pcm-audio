# ESP32 WLED LED Driver

> **The active hardware is [`hardware/`](hardware/).** The earlier rev A design
> is kept read-only in [`hardware_deprecated/`](hardware_deprecated/) and is no longer maintained.

## Active board: `hardware/`

A WS2812B LED strip driver with:

- USB-C programming, a DC barrel jack, and screw-terminal inputs.
- Two strip outputs with a 74xx125 level shifter.
- A slide switch for 5 V or 12 V strips.
- A relay and a blade fuse.
- An SPH0641 PDM MEMS microphone (MK1).

We fit an **ESP32-S3-WROOM-1-N4** in the footprint drawn for the ESP32-S2-SOLO, because the S2
can't read PDM microphones. The pad-by-pad check is in [shop.md](shop.md).

### WLED pin map

| Function | GPIO |
|---|---|
| LED strip 1 data | 17 |
| LED strip 2 data | 21 |
| Relay | 7 |
| Status LED | 2 |
| Button (BOOT) | 0 |
| Microphone (PDM) | CLK 5, DATA 6 |

- KiCad project: `hardware/PCB/iot_led_strip_pcb.kicad_pro` (KiCad 10).
- Shopping list: [shop.md](shop.md). It uses the cheapest in-stock part for each line.
- Case: `hardware/case/`.

### Checks from the command line

```bash
kicad-cli sch erc hardware/PCB/iot_led_strip_pcb.kicad_sch
```

```bash
kicad-cli pcb drc hardware/PCB/iot_led_strip_pcb.kicad_pcb
```

On macOS, `kicad-cli` lives at `/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli`.

## Deprecated: `hardware_deprecated/` (rev A)

This was the earlier design: a 66 × 32 mm, 4-layer, USB-C-only board.

- MCU: ESP32-S3-MINI-1.
- Power: a 2 A eFuse.
- Microphone: ICS-43434 I2S.

Its schematic is drawn and the board is routed, but it was never reviewed or ordered. These
documents belong to it:

- [Requirements & proposed design](docs/requirements/wled-audio-board.md)
- [WLED configuration](firmware/wled-config.md)

## Tooling

- **KiCad 10** (developed on 10.0.8).
- **KiCad MCP** for Claude Code:
  [`mixelpixx/KiCAD-MCP-Server`](https://github.com/mixelpixx/KiCAD-MCP-Server) v2.9.0.
  It's vendored as a git submodule at `tools/kicad-mcp-server` and registered in `.mcp.json`.
  One-time setup after cloning needs Node 18+ and KiCad 10 in `/Applications`:

  ```bash
  git submodule update --init
  ```

  ```bash
  ./scripts/setup-mcp.sh
  ```

  Launch Claude Code from the repo root, because `.mcp.json` uses paths relative to it.
