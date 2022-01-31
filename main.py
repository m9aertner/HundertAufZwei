#############################
#
# HundertAufZwei - Schwimmuhr
#
# Hardware: D1 Mini Pro
# Software: Micropython 1.18
#
#############################

import time
from machine import Pin, SPI, PWM, Timer, WDT
import max7219


##############
#
# Init Section
#
##############


# Watchdog. Can't hurt.
wdt = WDT()


# Buzzer D3 (GPIO 0)
# Duty 0 = initially off
beeper = PWM(Pin(0), freq=640, duty=0)


# Touch Sensor D0 (GPI16), ESP Pin 4
# Pin Input / Touch Sensor an D0, GPIO16, ESP Pin 4
touch = Pin(16, Pin.IN)


# Display MAX7219 4x8x8 LED on SPI (D7 DIN, D8 CS, D5 CLK)
spi = SPI(1, baudrate=10000000, polarity=0, phase=0)
display = max7219.Matrix8x8(spi, Pin(15), 4)
display.brightness(8)
display.fill(0)
display.show()


# Main state variables
_x = 0  # 0=cfg, 10=ready, 20=set, 30=go!
_z = 0  # 100ms ticks
_n = 0  # Number of 100s counter


# Helper functions

def beepOn():
    beeper.duty(512)

def beepOff():
    beeper.duty(0)

def digit(m):
    return chr(m+48)


#####################################
#
# tick - called every 100ms via timer
#
#####################################


def tick(t):
    global _x, _z, _n

    # Config phase -- how many 100s?
    if _x == 0:
        _y = _z
        if touch.value():
            _z = (_z + 1) % 60
        elif _n > 0:
            _z = 0
            _x = 10
        else:
            _z = _n = 0

        if _z == 0:
            if _y != _z:
                display.fill(0)
                display.show()
        elif _z % 6 == 0:
            _n = 2 + 2 * (_z // 6)  # _n = 4 .. 20
            display.fill(0)
            display.text(str(_n), 0, 0)
            display.show()

    # Ready phase -- wait for start
    if 10 <= _x < 20:
        _z = (_z + 1) % 8
        display.fill(0)
        if _z >= 4:
            display.text(str(_n), 0, 0)
        display.show()

        if touch.value():
            _x = 11
        elif _x == 11:
            _x = 20
            _z = 0

    # Set phase -- beep three times, show 3, 2, 1, ...
    if 20 <= _x < 30:
        if touch.value():
            beepOff()
            _x = _z = _n = 0
        else:
            if _z % 10 == 0:
                _321 = 3 - (_z // 10)
                display.fill(0)
                display.text(str(_n) + ' ' +str(_321), 0, 0)
                display.show()
            if _z % 10 < 2:
                beepOn()
            else:
                beepOff()

            _z = _z + 1
            if _z > 30:
                _x = 30
                _z = 0

    # Swim!
    if 30 <= _x < 40:
        # BEEP Control
        if 1170 <= _z < 1172:    # Alert Beep 3 200ms
            beepOn()
        elif 1180 <= _z < 1182:  # Alert Beep 2 200ms
            beepOn()
        elif 1190 <= _z < 1192:  # Alert Beep 1 200ms
            beepOn()
        elif 0 <= _z < 4:        # Start Beep ON 400ms
            beepOn()
        else:
            beepOff()

        # Display Control
        if touch.value():
            display.fill(0)
            display.text(str(_n), 0, 0)
            display.show()
        elif _z == 0:
            display.fill(0)
            display.text('-GO-', 0, 0)
            display.show()
        elif _z % 10 == 0:
            zz = _z // 10
            m0 = zz % 10
            zz = zz // 10
            m1 = zz % 6
            zz = zz // 6
            s = digit(zz) + ':' + digit(m1) + digit(m0)
            display.fill(0)
            display.text(s, 0, 0)
            display.show()

        _z = _z + 1
        if _z >= 1200:
            _z = 0
            _n = _n - 1
            if _n == 0:
                _x = 40

    # Done
    if 40 <= _x < 50:
        _z = (_z + 1) % 8
        display.fill(0)
        if _z >= 4:
            display.text('DONE', 0, 0)
        display.show()

        if _x == 41:
            display.fill(0)
            display.show()
            machine.reset()
        if touch.value():
            _x = 41
        _n = _n + 1
        if _n > 300:
            _x = 41


##################
#
# Ticker Heartbeat
#
##################

ticker = Timer(-1)
ticker.init(period=100, mode=Timer.PERIODIC, callback=tick)


# Main loop
while True:
    wdt.feed()
    time.sleep(1.5)

# END
