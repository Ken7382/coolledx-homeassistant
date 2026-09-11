#!/usr/bin/with-contenv bashio

set -e

export PROXY_HOST="$(bashio::config 'proxy_host')"
export PROXY_PORT="$(bashio::config 'proxy_port')"
export NOISE_PSK="$(bashio::config 'noise_psk')"
export SIGN_ADDRESS="$(bashio::config 'sign_address')"
export SIGN_NAME="$(bashio::config 'sign_name')"
export LOG_LEVEL="$(bashio::config 'log_level')"

bashio::log.info "Starting CoolLEDX Sign service"
bashio::log.info "ESPHome proxy: ${PROXY_HOST}:${PROXY_PORT}"
if [ -n "${SIGN_ADDRESS}" ]; then
  bashio::log.info "Configured sign address: ${SIGN_ADDRESS}"
else
  bashio::log.info "No sign address configured; use /scan to discover the sign"
fi

exec python3 /server.py
