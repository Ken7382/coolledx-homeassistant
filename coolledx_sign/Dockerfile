ARG BUILD_FROM
FROM ${BUILD_FROM}

WORKDIR /opt

RUN apk add --no-cache \
    git

RUN echo "==================================================" \
    && echo "BUILDING NEW COOLLEDX IMAGE - PATCHED VERSION" \
    && echo "==================================================" \
    && grep -n "COLOR_TYPE_MONO" /opt/coolledx-driver/src/coolledx/hardware.py

RUN pip install --upgrade pip setuptools wheel \
    && pip install \
        "bleak-esphome==4.1.0" \
        "habluetooth" \
        "fastapi>=0.115,<1" \
        "uvicorn[standard]>=0.34,<1" \
        "python-multipart>=0.0.20,<1"

RUN git clone --depth 1 https://github.com/UpDryTwist/coolledx-driver.git /opt/coolledx-driver \
    && sed -i 's/name = "CoolLEDX Driver"/name = "coolledx-driver"/' /opt/coolledx-driver/pyproject.toml \
    && sed -i 's/from \.commands import COLOR_TYPE_MONO/COLOR_TYPE_MONO = 0x00/' /opt/coolledx-driver/src/coolledx/hardware.py \
    && echo "===== SOURCE FILE AFTER PATCH =====" \
    && grep -n "COLOR_TYPE_MONO" /opt/coolledx-driver/src/coolledx/hardware.py \
    && pip install --no-cache-dir /opt/coolledx-driver \
    && echo "===== INSTALLED FILE =====" \
    && grep -n "COLOR_TYPE_MONO" /opt/venv/lib/python3.14/site-packages/coolledx/hardware.py

COPY run.sh /run.sh
RUN chmod a+x /run.sh

COPY server.py /server.py

CMD ["/run.sh"]
