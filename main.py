from facade import hello

import time

from ev3dev2.motor import LargeMotor, OUTPUT_A, OUTPUT_B, SpeedPercent, MoveTank
from ev3dev2.sensor import INPUT_1
from ev3dev2.sensor.lego import TouchSensor
from ev3dev2.led import Leds

if __name__ == "__main__":
    m = LargeMotor(OUTPUT_A)
    r = LargeMotor(OUTPUT_B)
    while True:
        hello()
        m.on_for_rotations(SpeedPercent(100), 5)
        time.sleep(1)

        r.on_for_rotations(SpeedPercent(100), 5)
        time.sleep(1)