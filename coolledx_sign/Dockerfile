FROM ghcr.io/home-assistant/base:latest

WORKDIR /opt

RUN apk add --no-cache \
    python3 \
    py3-pip \
    git

RUN python3 -m venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN pip install --upgrade pip setuptools wheel \
    && pip install \
        "bleak-esphome==4.1.0" \
        "habluetooth" \
        "fastapi>=0.115,<1" \
        "uvicorn[standard]>=0.34,<1" \
        "python-multipart>=0.0.20,<1"

RUN rm -rf /opt/coolledx-driver \
    && git clone --depth 1 https://github.com/UpDryTwist/coolledx-driver.git /opt/coolledx-driver \
    && sed -i 's/name = "CoolLEDX Driver"/name = "coolledx-driver"/' /opt/coolledx-driver/pyproject.toml \
    && sed -i 's/from \.commands import COLOR_TYPE_MONO/COLOR_TYPE_MONO = 0x00/' /opt/coolledx-driver/src/coolledx/hardware.py \
    && sed -i 's/return \[self.create_command(x) for x in raw_data_chunks\]/return raw_data_chunks/' /opt/coolledx-driver/src/coolledx/commands.py \
    && grep -n "COLOR_TYPE_MONO" /opt/coolledx-driver/src/coolledx/hardware.py \
    && grep -n "get_command_chunks" -A8 /opt/coolledx-driver/src/coolledx/commands.py \
    && pip install /opt/coolledx-driver
    
COPY run.sh /run.sh
RUN chmod a+x /run.sh

COPY server.py /server.py

CMD ["/run.sh"]
