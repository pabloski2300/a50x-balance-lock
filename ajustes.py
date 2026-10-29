# /// script
# requires-python = ">=3.10"
# dependencies = ["hidapi>=0.14"]
# ///
"""Ventana para cambiar el balance fijo del A50 X (escribe config.json)."""
import json
import tkinter as tk
from pathlib import Path
from tkinter import ttk

from a50x_balance_lock import CONFIG, MAX_BALANCE, load_config


def describe(v):
    if v == 6:
        return "Centro (juego y chat al máximo)"
    if v < 6:
        return f"Más chat ({6 - v} de 6 hacia chat)"
    return f"Más juego ({v - 6} de 6 hacia juego)"


def main():
    cfg = load_config()
    root = tk.Tk()
    root.title("A50 X · Balance")
    root.resizable(False, False)
    frm = ttk.Frame(root, padding=16)
    frm.grid()

    target = tk.IntVar(value=cfg["target"])
    enabled = tk.BooleanVar(value=cfg["enabled"])
    status = tk.StringVar()

    ttk.Label(frm, text="Balance fijo", font=("Segoe UI", 11, "bold")).grid(column=0, row=0, columnspan=3, sticky="w")
    ttk.Label(frm, text="Chat").grid(column=0, row=1)
    scale = tk.Scale(frm, from_=0, to=MAX_BALANCE, orient="horizontal", length=260,
                     variable=target, showvalue=True, resolution=1)
    scale.grid(column=1, row=1)
    ttk.Label(frm, text="Juego").grid(column=2, row=1)
    desc = ttk.Label(frm, text=describe(target.get()))
    desc.grid(column=0, row=2, columnspan=3, pady=(0, 8))
    target.trace_add("write", lambda *_: desc.config(text=describe(target.get())))

    ttk.Checkbutton(frm, text="Bloquear los botones del casco", variable=enabled).grid(
        column=0, row=3, columnspan=3, sticky="w")

    def save():
        CONFIG.write_text(json.dumps({"target": target.get(), "enabled": enabled.get()}, indent=2),
                          encoding="utf-8")
        status.set("Guardado, aplicado al momento" if enabled.get()
                   else "Guardado, botones libres")

    btns = ttk.Frame(frm)
    btns.grid(column=0, row=4, columnspan=3, pady=(12, 0))
    ttk.Button(btns, text="Centrar", command=lambda: target.set(6)).grid(column=0, row=0, padx=4)
    ttk.Button(btns, text="Guardar", command=save).grid(column=1, row=0, padx=4)
    ttk.Label(frm, textvariable=status, foreground="#2a7").grid(column=0, row=5, columnspan=3, pady=(8, 0))

    root.mainloop()


if __name__ == "__main__":
    main()
