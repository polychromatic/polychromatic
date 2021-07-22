#!/usr/bin/python3

import math

def play(fx, params=[]):
    rows = fx.rows                   # 5
    cols = fx.cols                   # 20
    name = fx.name                   # BlackWidow Chroma
    backend = fx.backend             # OpenRazer
    form_factor = fx.form_factor     # keyboard

    fx.rgb_to_hex(0, 255, 0)         #> #00FF00
    fx.hex_to_rgb("#00FF00")         #> [0, 255, 0]

    while True:
        import time
        for y in range(0, rows):
            for x in range(0, cols):
                fx.clear()
                fx.set(x, y, 0, 255, 0)
                fx.draw()
                time.sleep(0.05)
