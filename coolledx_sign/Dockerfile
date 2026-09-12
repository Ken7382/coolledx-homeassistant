FROM ghcr.io/home-assistant/base:latest

SHELL ["/bin/ash", "-o", "pipefail", "-c"]

RUN apk add --no-cache \
    git \
    python3 \
    py3-pip

RUN python3 -m venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH"

RUN pip install --no-cache-dir --upgrade pip setuptools wheel

RUN pip install --no-cache-dir \
    "bleak-esphome==4.1.0" \
    "fastapi>=0.115,<1" \
    "uvicorn[standard]>=0.34,<1" \
    "python-multipart>=0.0.20,<1" \
    "Pillow>=11,<12"

RUN git clone --depth 1 \
    https://github.com/UpDryTwist/coolledx-driver.git \
    /opt/coolledx-driver

# The upstream package metadata is invalid, so install the source manually.
#RUN cp -r /opt/coolledx-driver/src/coolledx \
#    /opt/venv/lib/python3.14/site-packages/coolledx

RUN SITE_PACKAGES="$(python3 -c 'import site; print(site.getsitepackages()[0])')" \
    && cp -r /opt/coolledx-driver/src/coolledx \
    "$SITE_PACKAGES/coolledx"

COPY run.sh /run.sh
COPY server.py /server.py

RUN chmod +x /run.sh

LABEL \
    io.hass.name="CoolLEDX Sign" \
    io.hass.description="Control a CoolLEDX Bluetooth LED sign through an ESPHome Bluetooth proxy" \
    io.hass.type="addon" \
    io.hass.version="0.1.0"

CMD ["/run.sh"]
