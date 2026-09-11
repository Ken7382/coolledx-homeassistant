from __future__ import annotations

import asyncio
import logging
import os
import tempfile
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import habluetooth
from bleak import BleakScanner
from bleak.exc import BleakError
from bleak_esphome import APIConnectionManager, ESPHomeDeviceConfig
from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from coolledx import (
    HeightTreatment,
    HorizontalAlignment,
    Mode,
    VerticalAlignment,
    WidthTreatment,
)
from coolledx.client import Client
from coolledx.commands import (
    InvertDisplay,
    SetAnimation,
    SetBrightness,
    SetImage,
    SetMode,
    SetSpeed,
    SetText,
    TurnOnOffApp,
)

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
LOGGER = logging.getLogger("coolledx_sign")

PROXY_HOST = os.environ["PROXY_HOST"]
PROXY_PORT = int(os.getenv("PROXY_PORT", "6053"))
NOISE_PSK = os.getenv("NOISE_PSK") or None
DEFAULT_ADDRESS = os.getenv("SIGN_ADDRESS") or None
DEFAULT_NAME = os.getenv("SIGN_NAME", "CoolLEDX")

proxy_manager: APIConnectionManager | None = None
proxy_task: asyncio.Task[Any] | None = None
command_lock = asyncio.Lock()


class TextRequest(BaseModel):
    text: str = Field(min_length=1, max_length=4096)
    address: str | None = None
    color: str = "white"
    background_color: str = "black"
    font: str = "arial"
    font_height: int = 13
    speed: int | None = Field(default=None, ge=0, le=255)
    brightness: int | None = Field(default=None, ge=0, le=255)
    mode: int | None = Field(default=None, ge=0, le=255)
    on: bool | None = None


class SettingRequest(BaseModel):
    address: str | None = None
    speed: int | None = Field(default=None, ge=0, le=255)
    brightness: int | None = Field(default=None, ge=0, le=255)
    mode: int | None = Field(default=None, ge=0, le=255)
    on: bool | None = None
    invert: bool | None = None


async def start_proxy() -> None:
    global proxy_manager
    global proxy_task

    await habluetooth.BluetoothManager().async_setup()

    config: ESPHomeDeviceConfig = {
        "address": PROXY_HOST,
        "port": PROXY_PORT,
        "noise_psk": NOISE_PSK,
    }
    proxy_manager = APIConnectionManager(config)
    LOGGER.info("Connecting to ESPHome Bluetooth proxy %s:%s", PROXY_HOST, PROXY_PORT)
    await proxy_manager.start()
    LOGGER.info("ESPHome Bluetooth proxy connected")


async def proxy_supervisor() -> None:
    while True:
        try:
            await start_proxy()
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            raise
        except Exception:
            LOGGER.exception("ESPHome proxy connection failed; retrying in 10 seconds")
            await asyncio.sleep(10)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global proxy_task
    proxy_task = asyncio.create_task(proxy_supervisor())
    # Give the proxy a moment to establish before serving requests.
    await asyncio.sleep(1)
    yield
    if proxy_task:
        proxy_task.cancel()
        await asyncio.gather(proxy_task, return_exceptions=True)
    if proxy_manager:
        try:
            await proxy_manager.stop()
        except Exception:
            LOGGER.exception("Error stopping ESPHome proxy manager")


app = FastAPI(title="CoolLEDX Sign", version="0.1.0", lifespan=lifespan)


def get_address(requested: str | None) -> str | None:
    return requested or DEFAULT_ADDRESS


async def scan_signs() -> list[dict[str, Any]]:
    devices = await BleakScanner.discover(timeout=8, return_adv=True)
    results: list[dict[str, Any]] = []

    for device, advertisement in devices.values():
        name = device.name or advertisement.local_name or ""
        if name.lower() not in {"coolledx", "coolledux"}:
            continue

        dimensions: dict[str, Any] = {}
        if advertisement.manufacturer_data:
            try:
                value = next(iter(advertisement.manufacturer_data.values()))
                if len(value) >= 11:
                    dimensions = {
                        "height": value[6],
                        "width": (value[7] << 8) | value[8],
                        "color_mode": value[9],
                        "firmware_version": value[10],
                    }
            except (StopIteration, IndexError):
                pass

        results.append(
            {
                "name": name,
                "address": device.address,
                "rssi": advertisement.rssi,
                **dimensions,
            }
        )
    return results


async def with_client(address: str | None):
    client = Client(
        address=address,
        device_name=DEFAULT_NAME,
        connection_timeout=15,
        connection_retries=3,
    )
    await client.connect()
    return client


@app.get("/health")
async def health() -> dict[str, Any]:
    return {
        "ok": True,
        "proxy": PROXY_HOST,
        "sign_address": DEFAULT_ADDRESS,
    }


@app.get("/scan")
async def scan() -> dict[str, Any]:
    try:
        return {"devices": await scan_signs()}
    except Exception as err:
        LOGGER.exception("BLE scan failed")
        raise HTTPException(status_code=500, detail=str(err)) from err


@app.post("/text")
async def text(request: TextRequest) -> dict[str, Any]:
    address = get_address(request.address)
    async with command_lock:
        client = await with_client(address)
        try:
            await client.send_command(
                SetText(
                    request.text,
                    default_color=request.color,
                    background_color=request.background_color,
                    font=request.font,
                    font_height=request.font_height,
                    render_as_text=False,
                    width_treatment=WidthTreatment.LEFT_AS_IS,
                    height_treatment=HeightTreatment.CROP_PAD,
                    horizontal_alignment=HorizontalAlignment.NONE,
                    vertical_alignment=VerticalAlignment.CENTER,
                )
            )
            if request.speed is not None:
                await client.send_command(SetSpeed(request.speed))
            if request.brightness is not None:
                await client.send_command(SetBrightness(request.brightness))
            if request.mode is not None:
                await client.send_command(SetMode(request.mode))
            if request.on is not None:
                await client.send_command(TurnOnOffApp(request.on))
        except (BleakError, TimeoutError) as err:
            LOGGER.exception("Failed to send text")
            raise HTTPException(status_code=502, detail=str(err)) from err
        finally:
            await client.disconnect()

    return {"ok": True, "address": address, "text": request.text}


@app.post("/settings")
async def settings(request: SettingRequest) -> dict[str, Any]:
    address = get_address(request.address)
    async with command_lock:
        client = await with_client(address)
        try:
            if request.speed is not None:
                await client.send_command(SetSpeed(request.speed))
            if request.brightness is not None:
                await client.send_command(SetBrightness(request.brightness))
            if request.mode is not None:
                await client.send_command(SetMode(request.mode))
            if request.on is not None:
                await client.send_command(TurnOnOffApp(request.on))
            if request.invert is not None:
                await client.send_command(InvertDisplay(inverted=request.invert))
        except (BleakError, TimeoutError) as err:
            LOGGER.exception("Failed to change sign settings")
            raise HTTPException(status_code=502, detail=str(err)) from err
        finally:
            await client.disconnect()

    return {"ok": True, "address": address}


@app.post("/image")
async def image(
    file: UploadFile = File(...),
    address: str | None = None,
) -> dict[str, Any]:
    suffix = Path(file.filename or "image.png").suffix or ".png"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        temp_path = Path(tmp.name)
        while chunk := await file.read(1024 * 1024):
            tmp.write(chunk)

    try:
        async with command_lock:
            client = await with_client(get_address(address))
            try:
                await client.send_command(
                    SetImage(
                        str(temp_path),
                        width_treatment=WidthTreatment.LEFT_AS_IS,
                        height_treatment=HeightTreatment.CROP_PAD,
                        horizontal_alignment=HorizontalAlignment.NONE,
                        vertical_alignment=VerticalAlignment.CENTER,
                    )
                )
            except (BleakError, TimeoutError) as err:
                LOGGER.exception("Failed to send image")
                raise HTTPException(status_code=502, detail=str(err)) from err
            finally:
                await client.disconnect()
    finally:
        temp_path.unlink(missing_ok=True)

    return {"ok": True, "address": get_address(address), "filename": file.filename}


@app.post("/animation")
async def animation(
    file: UploadFile = File(...),
    address: str | None = None,
    speed: int = 512,
) -> dict[str, Any]:
    suffix = Path(file.filename or "animation.gif").suffix or ".gif"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        temp_path = Path(tmp.name)
        while chunk := await file.read(1024 * 1024):
            tmp.write(chunk)

    try:
        async with command_lock:
            client = await with_client(get_address(address))
            try:
                await client.send_command(
                    SetAnimation(
                        str(temp_path),
                        speed=speed,
                        width_treatment=WidthTreatment.LEFT_AS_IS,
                        height_treatment=HeightTreatment.CROP_PAD,
                        horizontal_alignment=HorizontalAlignment.NONE,
                        vertical_alignment=VerticalAlignment.CENTER,
                    )
                )
            except (BleakError, TimeoutError) as err:
                LOGGER.exception("Failed to send animation")
                raise HTTPException(status_code=502, detail=str(err)) from err
            finally:
                await client.disconnect()
    finally:
        temp_path.unlink(missing_ok=True)

    return {"ok": True, "address": get_address(address), "filename": file.filename}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8099)
