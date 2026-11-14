# WLED configuration (stock firmware)

These settings follow the proposed design (requirements doc, Part B9). They are **provisional**:
the GPIO map changes if the schematic's final pin assignment differs from B7.

## Firmware

- An official WLED release for **ESP32-S3** that includes the **AudioReactive** usermod.
- Flash over the board's USB-C port, either with the WLED web installer or with `esptool`.

## Config → LED Preferences

| Setting | Value |
|---|---|
| Output 1 | GPIO **16**, WS281x, length = your strip |
| Output 2 | GPIO **18**, WS281x, length = your strip |
| Automatic Brightness Limiter | **Enabled** |
| Maximum current | **1700 mA** (keeps the total ≤ 2 A, see PWR-02) |
| LED current | as specified for your strip (55 mA typical for WS2812B) |
| Button 0 | GPIO **0** (BOOT) |
| Button 1 | GPIO **15** (USER) |

## Usermods → AudioReactive

| Setting | Value |
|---|---|
| Type | Generic I2S |
| I2S SD | GPIO **4** |
| I2S WS | GPIO **5** |
| I2S SCK | GPIO **6** |
| MCLK | unused |
| Channel | Left (mic L/R pin tied low) |

## Pins reserved for future usermods (not used by stock WLED)

| Signal | GPIO | Purpose |
|---|---|---|
| eFuse FLT/PG | 7 | strip-rail trip indication |
| CC1 / CC2 sense | 1 / 2 | USB-C source capability (PWR-06) |
| VBUS sense | 8 | sag detection for adaptive limiting (PWR-08) |
| BC1.2 status | 9, 10 | USB-A charger type (PWR-07) |
| Status LED | 38 | optional status output |
