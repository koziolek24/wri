import time

from ev3dev2.motor import MoveTank, OUTPUT_A, OUTPUT_B, OUTPUT_D, MediumMotor
from ev3dev2.sensor import INPUT_1, INPUT_2
from ev3dev2.sensor.lego import ColorSensor


COLOR_BLACK = "Black"
COLOR_GREEN = "Green"
COLOR_RED = "Red"
COLOR_WHITE = "White"
COLOR_OTHER = "Other"

COLOR_NAMES = {
    1: COLOR_BLACK,
    3: COLOR_GREEN,
    5: COLOR_RED,
    6: COLOR_WHITE,
}

MOVE_FORWARD = "forward"
MOVE_ROTATE = "rotate"
MOVE_HARD_LEFT = "hard_left"
MOVE_HARD_RIGHT = "hard_right"
MOVE_SOFT_RIGHT = "soft_right"
MOVE_SOFT_LEFT = "soft_left"

MOVEMENTS = {
    MOVE_FORWARD: (15, 15),
    MOVE_ROTATE: (-50, 50),
    MOVE_HARD_LEFT: (15, -15),
    MOVE_HARD_RIGHT: (-15, 0),
    MOVE_SOFT_RIGHT: (0, -25),
    MOVE_SOFT_LEFT: (-25, 0),
}

DEFAULT_INTERVAL = 0.0
SERVO_INTERVAL = 0.1


def wait(interval=0.05):
    """Pauses program execution for the given number of seconds."""

    time.sleep(interval)


def read_color_name(color_sensor):
    """Converts the EV3 color sensor code into a color name used by the program logic."""

    return COLOR_NAMES.get(color_sensor.color, COLOR_OTHER)


def get_changed_color(color_sensor, previous_color):
    """Returns the new color only when it differs from the previously stored color."""

    current_color = read_color_name(color_sensor)

    if current_color == previous_color:
        return None

    return current_color


def update_last_color(color_sensor, previous_color):
    """Updates the last stored color for a single color sensor."""

    changed_color = get_changed_color(color_sensor, previous_color)

    if changed_color is None:
        return previous_color

    return changed_color


def read_sensor_colors(left_color_sensor, right_color_sensor, last_left_color, last_right_color):
    """Reads and updates the last colors detected by the left and right color sensors."""

    current_left_color = update_last_color(left_color_sensor, last_left_color)
    current_right_color = update_last_color(right_color_sensor, last_right_color)

    return current_left_color, current_right_color


def move_grabber_up(servo):
    """Raises the grabber by briefly running the medium motor."""

    servo.on(60)
    wait(0.1)
    servo.off()


def move_grabber_down(servo):
    """Lowers the grabber by briefly running the medium motor."""

    servo.on(-80)
    wait(0.05)
    servo.off()


def drive(tank, movement_name):
    """Runs the drive motors using the selected movement from the MOVEMENTS configuration."""

    left_speed, right_speed = MOVEMENTS[movement_name]
    tank.on(left_speed, right_speed)


def sees_color(left_color, right_color, expected_color):
    """Checks whether any color sensor sees the expected color."""

    return left_color == expected_color or right_color == expected_color


def get_line_movement(left_color, right_color):
    """Selects the robot movement based on the colors detected by the line sensors."""

    if left_color == COLOR_WHITE and right_color == COLOR_WHITE:
        return MOVE_FORWARD

    if left_color == COLOR_WHITE and right_color == COLOR_BLACK:
        print("lewo")
        return MOVE_SOFT_RIGHT

    if left_color == COLOR_BLACK and right_color == COLOR_WHITE:
        print("prawo")
        return MOVE_SOFT_LEFT

    if left_color == COLOR_BLACK and right_color == COLOR_BLACK:
        print("prosto")
        return MOVE_FORWARD

    print("prosto")
    return MOVE_FORWARD


def handle_color_action(tank, servo, left_color, right_color):
    """Handles the grabber reaction to special colors."""

    if sees_color(left_color, right_color, COLOR_GREEN):
        drive(tank, MOVE_FORWARD)
        wait(0.005)
        move_grabber_up(servo)
        drive(tank, MOVE_ROTATE)
        wait(0.01)
        return True

    if sees_color(left_color, right_color, COLOR_RED):
        drive(tank, MOVE_FORWARD)
        wait(0.005)
        move_grabber_down(servo)
        drive(tank, MOVE_ROTATE)
        wait(0.01)
        return True

    return False


def follow_line_step(tank, left_color, right_color):
    """Performs a single line-following step."""

    movement_name = get_line_movement(left_color, right_color)
    drive(tank, movement_name)
    wait(DEFAULT_INTERVAL)


def main():
    tank = MoveTank(OUTPUT_A, OUTPUT_B)
    servo = MediumMotor(OUTPUT_D)

    left_color_sensor = ColorSensor(INPUT_2)
    right_color_sensor = ColorSensor(INPUT_1)

    last_left_color = COLOR_OTHER
    last_right_color = COLOR_OTHER

    try:
        print("Starting")
        move_grabber_down(servo)

        while True:
            last_left_color, last_right_color = read_sensor_colors(left_color_sensor, right_color_sensor, last_left_color, last_right_color)

            action_handled = handle_color_action(tank, servo, last_left_color, last_right_color)

            if action_handled:
                wait(SERVO_INTERVAL)
                continue

            follow_line_step(tank, last_left_color, last_right_color)

    except KeyboardInterrupt:
        tank.off()
        servo.off()


if __name__ == "__main__":
    main()