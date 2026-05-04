import random
import time

from ev3dev2.motor import MoveTank, OUTPUT_A, OUTPUT_B, OUTPUT_D, MediumMotor
from ev3dev2.sensor import INPUT_1, INPUT_2
from ev3dev2.sensor.lego import TouchSensor, ColorSensor
from ev3dev2.led import Leds

def colorChange(colorSensor):
    if colorSensor.color == 1:
        return "Black"
    if colorSensor.color == 5:
        return "Red"
    if colorSensor.color == 6:
        return "White"
    if colorSensor.color == 3:
        return "Green"
    if colorSensor.color == 5:
        return "Green"
    return "Other"

def detect_color(colorSensor, oldColor, side):
    colorNew = colorChange(colorSensor)
    if colorNew == oldColor:
        return None
    return colorNew

def wait(interval=0.05):
    time.sleep(interval)

def moveUp(servo):
    servo.on(60)
    wait(0.1)
    servo.off()

def moveDown(servo):
    servo.on(-80)
    wait(0.05)
    servo.off()

def main():
    tank = MoveTank(OUTPUT_A, OUTPUT_B)
    servo = MediumMotor(OUTPUT_D)
    colorSensorLeft = ColorSensor(INPUT_2)
    colorSensorRight = ColorSensor(INPUT_1)
    movements = [
        (15, 15), # 0 prosto
        (-50, 50), # 1 do tylu
        (15, -15), # 2 mocno w lewo
        (-15, 0), # 3 mocno w prawo
        (0, -25), # 4 lekko w prawo
        (-25, 0), # 5 lekko w lewo
    ]

    try:
        lastLeft = -1
        lastRight = -1
        moveID = 0
        interval = 0.02
        print("Starting")
        moveDown(servo)
        while True:
            # duration = random.uniform(0.4, 1.5)
            shouldUp = 0
            shouldDown = 0
            useServo = False

            changeLeft = detect_color(colorSensorLeft, lastLeft, "left")
            if changeLeft:
                lastLeft = changeLeft
            changeRight = detect_color(colorSensorRight, lastRight, "right")
            if changeRight:
                lastRight = changeRight
            
            if lastLeft == "White" and lastRight == "White":
                interval = 0.0
                moveID = 0
            elif lastLeft == "White" and lastRight == "Black":
                interval = 0.0
                moveID = 4
                print("lewo")
            elif lastLeft == "Black" and lastRight == "White":
                interval = 0.0
                moveID = 5
                print("prawo")
            elif lastLeft == "Black" and lastRight == "Black":
                interval = 0.0
                moveID = 0
                print("prosto")
            elif lastLeft == "Green" or lastRight == "Green":
                useServo = True
                interval = 0.1
                moveID = 0
                shouldUp = 1
            elif lastLeft == "Red" or lastRight == "Red":
                useServo = True
                interval = 0.1
                moveID = 0
                shouldDown = 1
            else:
                interval = 0.0
                moveId = 0
                print("prosto")
            if useServo is False:
                left_speed, right_speed = movements[moveID]
                tank.on(left_speed, right_speed)
                wait(interval)
            else:
                tank.on(left_speed, right_speed)
                wait(0.005)
                if shouldUp:
                    moveUp(servo)
                    left_speed, right_speed = movements[1]
                    tank.on(left_speed, right_speed)
                    wait(0.01)
                if shouldDown:
                    moveDown(servo)
                    left_speed, right_speed = movements[1]
                    tank.on(left_speed, right_speed)
                    wait(0.01)
    except KeyboardInterrupt:
        tank.off()


if __name__ == "__main__":
    main()