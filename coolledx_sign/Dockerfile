```dockerfile
ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base:latest
FROM ${BUILD_FROM}

WORKDIR /opt

RUN apk add --no-cache \
    git

RUN pip install --upgrade pip setuptools wheel \
    && pip install \
        "bleak-esphome==4.1.0" \
        "habluetooth" \
        "fastapi>=0.115,<1" \
        "uvicorn[standard]>=0.34,<1" \
        "python-multipart>=0.0.20,<1"

RUN git clone --depth 1 https://github.com/UpDryTwist/coolledx-driver.git /opt/coolledx-driver \
    && sed -i 's/name = "CoolLEDX Driver"/name = "coolledx-driver"/' /opt/coolledx-driver/pyproject.toml \
    && sed -i '/^from \.hardware import CoolLED$/d' /opt/coolledx-driver/src/coolledx/commands.py \
    && sed -i '/^COLOR_TYPE_FULLRGB = 0x02$/a from .hardware import CoolLED' /opt/coolledx-driver/src/coolledx/commands.py \
    && pip install /opt/coolledx-driver

COPY run.sh /run.sh
RUN chmod a+x /run.sh

COPY server.py /server.py

CMD ["/run.sh"]
```
