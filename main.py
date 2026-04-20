from facade import hello

from ev3dev2.motor import LargeMotor, OUTPUT_A, OUTPUT_B, SpeedPercent, MoveTank
from ev3dev2.sensor import INPUT_1
from ev3dev2.sensor.lego import TouchSensor
from ev3dev2.led import Leds

if __name__ == "__main__":
    m = LargeMotor(OUTPUT_A)
    while True:
        hello()
        m.on_for_rotations(SpeedPercent(75), 5)
        time.sleep(1)