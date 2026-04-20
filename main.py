import random
import time

from facade import hello
from ev3dev2.motor import MoveTank, OUTPUT_A, OUTPUT_B


def main():
    tank = MoveTank(OUTPUT_A, OUTPUT_B)

    movements = [
        (100, 100),
        (-100, -100),
        (100, -100),
        (-100, 100),
        (100, 40),
        (40, 100),
        (-100, -40),
        (-40, -100),
    ]

    try:
        while True:
            hello()
            left_speed, right_speed = random.choice(movements)
            duration = random.uniform(0.4, 1.5)

            tank.on(left_speed, right_speed)
            time.sleep(duration)
            tank.off()
            time.sleep(0.2)
    except KeyboardInterrupt:
        tank.off()


if __name__ == "__main__":
    main()