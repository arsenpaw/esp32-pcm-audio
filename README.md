# ESP32 WLED Sound-Reactive Controller

A small, portable USB-C board that runs [WLED](https://kno.wled.ge/). It drives two addressable
LED strips and has an on-board I2S microphone for sound-reactive effects.

- **Power:** USB-C 5 V, with a hard **2 A total** budget. A latch-off eFuse cuts the strips on
  overcurrent or VBUS sag, while the MCU keeps running.
- **MCU:** ESP32-S3-MINI-1 (proposed). WLED is flashed over the same USB-C port.
- **Outputs:** 2 × 3-pin JST-XH (5V / DATA / GND), with 5 V data level shifting.
- **Audio:** ICS-43434 I2S MEMS microphone.

> Status: **rev A — schematic drawn, ERC clean.** Part numbers are not checked against assembler
> stock. The 66 × 32 mm board is placed and routed; DRC shows no errors and no open
> connections. JLCPCB files are generated in `hardware/fab/` (not committed). The layout has
> not been reviewed by a person, and nothing has been ordered.

## Documents

- [Requirements & proposed design](docs/requirements/wled-audio-board.md): Part A is the binding
  requirements; Part B is a non-binding proposed design.
- [WLED configuration](firmware/wled-config.md): provisional pin map and settings for stock WLED.

## Repo layout

```
.mcp.json                   KiCad MCP server registration for Claude Code
tools/kicad-mcp-server/     mixelpixx/KiCAD-MCP-Server (git submodule, pinned v2.9.0)
scripts/setup-mcp.sh        builds the MCP server + KiCad-Python venv
docs/requirements/          requirements & proposed design
hardware/                   KiCad 10 project
  esp32-wled-audio.kicad_pro
  esp32-wled-audio.kicad_sch   top sheet → power / usb / mcu / leds / audio
  esp32-wled-audio.kicad_pcb   4-layer, 66×32 mm, placed and routed
  lib/                      project-specific symbols, footprints, 3D models
  fab/                      generated outputs (gitignored until release)
firmware/                   WLED configuration notes
```

## Tooling

- **KiCad 10** (developed on 10.0.8).
- **KiCad MCP** for Claude Code:
  [`mixelpixx/KiCAD-MCP-Server`](https://github.com/mixelpixx/KiCAD-MCP-Server) v2.9.0.
  - **Where it lives:** it's vendored as a git submodule at `tools/kicad-mcp-server` and
    registered in `.mcp.json`.
  - **What it does:** about 250 tools for schematic editing, placement, routing, DRC/ERC,
    library and JLCPCB part search, and Gerber/BOM export.
  - **One-time setup** after cloning. This needs Node 18+ and KiCad 10 in `/Applications`:

    ```bash
    git submodule update --init
    ```

    ```bash
    ./scripts/setup-mcp.sh
    ```

    The script builds the server and creates `tools/kicad-mcp-server/venv` on **KiCad's bundled
    Python**, which is required for the `pcbnew` API.
  - **Starting it:** launch Claude Code from the repo root, because `.mcp.json` uses paths
    relative to it. Approve the `kicad` project server when asked.
  - **How it edits:** it works on the files directly through KiCad's Python (SWIG) API, so
    KiCad doesn't need to be running. The live-editing (IPC) backend is experimental. To use it,
    open the project in KiCad and enable *Preferences → Plugins → Enable KiCad API*.
  - **Upgrading:** check out a newer tag or commit inside the submodule, commit the new pointer,
    then re-run `./scripts/setup-mcp.sh`.

### Checks from the command line

```bash
kicad-cli sch erc hardware/esp32-wled-audio.kicad_sch
kicad-cli pcb drc hardware/esp32-wled-audio.kicad_pcb
```

On macOS, `kicad-cli` lives at `/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli`.
