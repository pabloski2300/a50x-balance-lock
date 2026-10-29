# /// script
# requires-python = ">=3.10"
# dependencies = ["hidapi>=0.14"]
# ///
"""Bloquea el balance juego/chat de los Astro A50 X.

Escucha la interfaz HID del casco y, cada vez que el balance se mueve
(botones del auricular o G HUB), lo devuelve al valor fijado en config.json.
Los cambios en config.json se aplican al momento, sin reiniciar.

Protocolo (informe 0x02, 64 bytes, sacado capturando G HUB):
  aviso del casco:   02 0c 04 00 0a 00 VV   (VV = balance actual)
  fijar balance:     02 0c 04 00 0a 1b VV
  confirmación:      02 0c 03 00 0a 1b
VV va de 0x00 (todo chat) a 0x0c (todo juego); 0x06 es el centro.
"""
import json
import logging
import time
from logging.handlers import RotatingFileHandler
from pathlib import Path

import hid

VID, PID = 0x046D, 0x0B0B
USAGE_PAGE = 0xFF32
MAX_BALANCE = 0x0C
HERE = Path(__file__).resolve().parent
CONFIG = HERE / "config.json"
DEFAULTS = {"target": 6, "enabled": True}

log = logging.getLogger("a50x")


def load_config():
    try:
        cfg = {**DEFAULTS, **json.loads(CONFIG.read_text(encoding="utf-8"))}
    except (OSError, ValueError):
        cfg = dict(DEFAULTS)
    cfg["target"] = max(0, min(MAX_BALANCE, int(cfg["target"])))
    return cfg


def config_mtime():
    try:
        return CONFIG.stat().st_mtime
    except OSError:
        return None


def find_path():
    for d in hid.enumerate(VID, PID):
        if d["usage_page"] == USAGE_PAGE:
            return d["path"]
    return None


def set_balance(dev, value):
    pkt = bytes([0x02, 0x0C, 0x04, 0x00, 0x0A, 0x1B, value]) + bytes(57)
    dev.write(pkt)


def balance_event(report):
    """Devuelve el balance si el informe es un aviso de cambio, si no None."""
    r = bytes(report) + bytes(8)
    if r[0] == 0x02 and r[1] == 0x0C and r[2] == 0x04 and r[4] == 0x0A and r[5] == 0x00:
        return r[6]
    return None


def run():
    cfg, mtime = load_config(), config_mtime()
    while True:
        path = find_path()
        if not path:
            time.sleep(3)
            continue
        dev = hid.device()
        try:
            dev.open_path(path)
            log.info("casco conectado (balance %d, bloqueo %s)",
                     cfg["target"], "activo" if cfg["enabled"] else "desactivado")
            if cfg["enabled"]:
                set_balance(dev, cfg["target"])
            while True:
                if config_mtime() != mtime:
                    cfg, mtime = load_config(), config_mtime()
                    log.info("config cambiada: balance %d, bloqueo %s",
                             cfg["target"], "activo" if cfg["enabled"] else "desactivado")
                    if cfg["enabled"]:
                        set_balance(dev, cfg["target"])
                report = dev.read(64, 1000)
                if not report or not cfg["enabled"]:
                    continue
                value = balance_event(report)
                if value is not None and value != cfg["target"]:
                    log.info("balance movido a %d, devuelto a %d", value, cfg["target"])
                    set_balance(dev, cfg["target"])
        except OSError as e:
            log.warning("casco desconectado (%s), reintentando", e)
            time.sleep(3)
        finally:
            dev.close()


def main():
    handler = RotatingFileHandler(HERE / "a50x_balance_lock.log", maxBytes=256_000,
                                  backupCount=1, encoding="utf-8")
    logging.basicConfig(level=logging.INFO, handlers=[handler],
                        format="%(asctime)s %(levelname)s %(message)s")
    run()


if __name__ == "__main__":
    main()
