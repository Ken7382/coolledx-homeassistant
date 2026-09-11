# CoolLEDX Home Assistant App

Home Assistant OS app for controlling CoolLEDX signs through an ESPHome Bluetooth Proxy.

## Repository structure

- `repository.yaml`
- `coolledx_sign/config.yaml`
- `coolledx_sign/Dockerfile`
- `coolledx_sign/run.sh`
- `coolledx_sign/server.py`

## Setup

1. Add this GitHub repository to Home Assistant Apps:
   `https://github.com/Ken7382/coolledx-homeassistant`
2. Install **CoolLEDX Sign**.
3. Configure:
   - `proxy_host`: hostname/IP of the ESPHome Bluetooth proxy
   - `proxy_port`: normally `6053`
   - `noise_psk`: the ESPHome API encryption key for that proxy
   - `sign_address`: optional initially; use `/scan` to discover the sign
4. Start the app.
5. The HTTP API is available on port `8099`.

The underlying CoolLEDX driver is fetched directly from:
https://github.com/UpDryTwist/coolledx-driver

## API

### Scan

`GET /scan`

### Send text

`POST /text`

Example JSON:

```json
{
  "text": "Hello!",
  "color": "white",
  "background_color": "black",
  "speed": 80,
  "brightness": 180,
  "mode": 2
}
```

### Settings

`POST /settings`

Example:

```json
{
  "brightness": 180,
  "speed": 80,
  "mode": 2,
  "on": true
}
```

### Image

`POST /image` as multipart form-data with field `file`.

### Animation

`POST /animation` as multipart form-data with field `file`, with optional `speed` query parameter.

## Notes

The sign must be a CoolLEDX device compatible with the CoolLED1248 app. The original driver documents CoolLEDX support and specifically notes that CoolLEDM devices use a different protocol.
