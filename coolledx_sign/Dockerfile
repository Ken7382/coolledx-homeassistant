FROM ghcr.io/home-assistant/base:latest

ARG BUILD_VERSION
ARG BUILD_ARCH

RUN apk add --no-cache     python3     py3-pip     git

RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"     PYTHONUNBUFFERED=1     PIP_NO_CACHE_DIR=1

RUN pip install --upgrade pip setuptools wheel     && pip install "bleak-esphome==4.1.0" "fastapi>=0.115,<1" "uvicorn[standard]>=0.34,<1" "python-multipart>=0.0.20,<1"

RUN git clone --depth 1 https://github.com/UpDryTwist/coolledx-driver.git /opt/coolledx-driver     && pip install /opt/coolledx-driver

COPY run.sh /run.sh
COPY server.py /server.py

RUN chmod +x /run.sh

LABEL     io.hass.version="${BUILD_VERSION}"     io.hass.type="app"     io.hass.arch="${BUILD_ARCH}"

CMD ["/run.sh"]
