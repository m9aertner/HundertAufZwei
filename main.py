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
_x = 0  # 0=logo, 1=cfg, 10=ready, 20=set, 30=go!
_z = 0  # 100ms ticks
_n = 0  # Number of 100s counter


# Helper functions

def beepOn():
    beeper.duty(512)


def beepOff():
    beeper.duty(0)


def digit(m):
    return chr(m+48)

# SUPER "Visual"
SUPER = [
    0b01110010,0b00101111,0b00111110,0b11110001,
    0b10000010,0b00101000,0b10100000,0b10001001,
    0b10000010,0b00101000,0b10100000,0b10001001,
    0b01110010,0b00101111,0b00111100,0b11110001,
    0b00001010,0b00101000,0b00100000,0b10001001,
    0b00001010,0b00101000,0b00100000,0b10001001,
    0b10001010,0b00101000,0b00100000,0b10001000,
    0b01110001,0b11001000,0b00111110,0b10001001,
]

#####################################
#
# tick - called every 100ms via timer
#
#####################################


def tick(t):
    global _x, _z, _n

    # Logo - some eye candy
    if _x == 0:
        s = None
        d = 6
        dx = 0
        if _z == 0:
            s = ' SG '
        elif _z == 1*d:
            s = 'ELBE'
        elif _z == 2*d:
            s = 'Hun-'
        elif _z == 3*d:
            s = 'dert'
        elif _z == 4*d:
            s = 'auf'
            dx = 4
        elif _z == 5*d:
            s = 'Zwei'
        elif _z == 6*d:
            s = '    ' # This is really the OFF state
            _x = 1
            _z = 0

        if s is not None:
            display.fill(0)
            display.text(s, 0, 0)
            for dd in range(dx):
                display.scroll(1,0)
            display.show()
        if _x == 0:
            _z = _z + 1

    # Config phase -- how many 100s?
    elif _x == 1:
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
    elif 10 <= _x < 20:
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

    # Set phase -- beep three times, show remaining N and 3, 2, 1, ...
    elif 20 <= _x < 30:
        if touch.value():
            beepOff()
            _x = 1
            _z = _n = 0
        else:
            if _z % 10 == 0:
                _321 = 3 - (_z // 10)
                display.fill(0)
                display.text(str(_n) + ' ' + str(_321), 0, 0)
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
    elif 30 <= _x < 400:
        # GO BEEP Control
        if 0 <= _z < 4:        # Start Beep ON 400ms
            beepOn()
        else:
            beepOff()

        if touch.value():
            if _x < 30 + 12:
                _x = _x + 1
            else:
                _x = 30
        else:
            if _x > 30 + 8:
                machine.reset()
            _x = 30

        # Display Control
        if _x > 30:
            display.fill(0)
            if _x > 30 + 8:
                display.text('OFF', 4, 0)
            else:
                display.text(str(_n), 0, 0)
            display.hline(0, 7, _x - 30, 7)
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
        if _n > 1 and _z >= 1169: # three seconds before 2:00min, but not on the last one
            _x = 20
            _z = 0
            _n = _n - 1
        if _n == 1 and _z >= 1199: # DONE!
            _n = 0
            _z = 0
            _x = 400

    # Done
    elif 400 <= _x < 410:
        _z = (_z + 1) % 8
        display.fill(0)
        if _z >= 4:
            display.text('SUPR', 0, 0)
            # ToDo
        display.show()

        if _x == 401:
            machine.reset()
        if touch.value():
            _x = 401
        _n = _n + 1
        if _n > 200:
            _x = 401


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
