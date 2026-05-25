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

import time

from ev3dev2.motor import MoveTank, OUTPUT_A, OUTPUT_B, OUTPUT_D, MediumMotor, SpeedPercent
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

PICKUP_COLOR = COLOR_GREEN
DROPOFF_COLOR = COLOR_RED

STATE_FOLLOW_MAIN_LINE = "follow_main_line"
STATE_APPROACH_PICKUP_TILE = "approach_pickup_tile"
STATE_PICKUP_TILE_PROCEDURE = "pickup_tile_procedure"
STATE_APPROACH_DROPOFF_TILE = "approach_dropoff_tile"
STATE_DROPOFF_TILE_PROCEDURE = "dropoff_tile_procedure"
STATE_TASK_DONE = "task_done"

SIDE_LEFT = "left"
SIDE_RIGHT = "right"
SIDE_NONE = "none"

MOVE_FORWARD = "forward"
MOVE_BACKWARD = "backward"
MOVE_HARD_LEFT = "hard_left"
MOVE_HARD_RIGHT = "hard_right"
MOVE_SOFT_RIGHT = "soft_right"
MOVE_SOFT_LEFT = "soft_left"
MOVE_SPIN_LEFT = "spin_left"
MOVE_SPIN_RIGHT = "spin_right"

MOVEMENTS = {
    MOVE_FORWARD: (15, 15),
    MOVE_BACKWARD: (-15, -15),
    MOVE_HARD_LEFT: (-35, 20),
    MOVE_HARD_RIGHT: (20, -35),
    MOVE_SOFT_RIGHT: (12, -28),
    MOVE_SOFT_LEFT: (-28, 12),
    MOVE_SPIN_LEFT: (-30, 30),
    MOVE_SPIN_RIGHT: (30, -30),
}

DEFAULT_INTERVAL = 0.01
BACKUP_INTERVAL = 0.01

BRANCH_TURN_TIME = 0.25
RETURN_TO_MAIN_TURN_TIME = 0.25
TURN_180_TIME = 1.40

DRIVE_BACK_TO_MAIN_LINE_MAX_TIME = 6.00

GRABBER_DOWN_SPEED = -80
GRABBER_DOWN_TIME = 0.3
GRABBER_UP_SPEED = 80
GRABBER_UP_TIME = 0.35



def wait(interval=0.05):
    time.sleep(interval)


def read_color_name(color_sensor):
    return COLOR_NAMES.get(color_sensor.color, COLOR_OTHER)


def read_sensor_colors(left_color_sensor, right_color_sensor):
    left_color = read_color_name(left_color_sensor)
    right_color = read_color_name(right_color_sensor)
    return left_color, right_color


def drive(tank, movement_name):
    left_speed, right_speed = MOVEMENTS[movement_name]
    tank.on(left_speed, right_speed)


def stop(tank):
    tank.off()


def sees_color(left_color, right_color, expected_color):
    return left_color == expected_color or right_color == expected_color


def both_sensors_see_color(left_color, right_color, expected_color):
    return left_color == expected_color and right_color == expected_color


def get_color_side(left_color, right_color, expected_color):
    if left_color == expected_color and right_color != expected_color:
        return SIDE_LEFT
    if right_color == expected_color and left_color != expected_color:
        return SIDE_RIGHT
    return SIDE_NONE


def get_line_movement(left_color, right_color, line_colors):
    if isinstance(line_colors, str):
        line_colors = (line_colors,)
    left_on_line = left_color in line_colors
    right_on_line = right_color in line_colors
    if not left_on_line and right_on_line:
        return MOVE_SOFT_RIGHT
    if left_on_line and not right_on_line:
        return MOVE_SOFT_LEFT
    return MOVE_FORWARD


def follow_line_step(tank, left_color, right_color, line_color):
    movement_name = get_line_movement(left_color, right_color, line_color)
    drive(tank, movement_name)
    wait(DEFAULT_INTERVAL)


def turn_to_color_branch(tank, branch_side, branch_color):
    if branch_side == SIDE_LEFT:
        drive(tank, MOVE_HARD_LEFT)
        wait(BRANCH_TURN_TIME)
        stop(tank)
        return

    if branch_side == SIDE_RIGHT:
        drive(tank, MOVE_HARD_RIGHT)
        wait(BRANCH_TURN_TIME)
        stop(tank)
        return

    stop(tank)


def turn_to_continue_main_line_after_180(tank, branch_side):
    if branch_side == SIDE_LEFT:
        drive(tank, MOVE_HARD_LEFT)
        wait(RETURN_TO_MAIN_TURN_TIME)
        stop(tank)
        return

    if branch_side == SIDE_RIGHT:
        drive(tank, MOVE_HARD_RIGHT)
        wait(RETURN_TO_MAIN_TURN_TIME)
        stop(tank)
        return

    stop(tank)


def spin_180_degrees(tank, left_color_sensor, right_color_sensor):
    drive(tank, MOVE_SPIN_LEFT)

    start_time = time.time()
    while time.time() - start_time < TURN_180_TIME:
        read_sensor_colors(left_color_sensor, right_color_sensor)
        wait(DEFAULT_INTERVAL)

    stop(tank)


def move_grabber_down_to_limit(servo):
    print("grabber down speed_sp=" + str(servo.speed_sp) + " max_speed=" + str(servo.max_speed))
    servo.on(SpeedPercent(GRABBER_DOWN_SPEED))
    wait(GRABBER_DOWN_TIME)
    servo.off()
    print("grabber down done position=" + str(servo.position))


def move_grabber_up_to_limit(servo):
    print("grabber up speed_sp=" + str(servo.speed_sp) + " max_speed=" + str(servo.max_speed))
    servo.on(SpeedPercent(GRABBER_UP_SPEED))
    wait(GRABBER_UP_TIME)
    servo.off()
    print("grabber up done position=" + str(servo.position))


def drive_forward_following_color_until_black(tank, left_color_sensor, right_color_sensor, line_color):
    start_time = time.time()

    while time.time() - start_time < DRIVE_BACK_TO_MAIN_LINE_MAX_TIME:
        left_color, right_color = read_sensor_colors(left_color_sensor, right_color_sensor)

        if sees_color(left_color, right_color, COLOR_BLACK):
            stop(tank)
            return True

        follow_line_step(tank, left_color, right_color, line_color)

    stop(tank)
    return False


def run_pickup_tile_procedure(tank, servo, left_color_sensor, right_color_sensor, pickup_branch_side):

    stop(tank)
    move_grabber_up_to_limit(servo)
    spin_180_degrees(tank, left_color_sensor, right_color_sensor)

    main_line_was_reached = drive_forward_following_color_until_black(
        tank,
        left_color_sensor,
        right_color_sensor,
        PICKUP_COLOR,
    )

    if main_line_was_reached:
        turn_to_continue_main_line_after_180(tank, pickup_branch_side)



def run_dropoff_tile_procedure(tank, servo):

    stop(tank)
    move_grabber_down_to_limit(servo)



def handle_follow_main_line_state(tank, left_color, right_color, has_object):
    if has_object:
        branch_side = get_color_side(left_color, right_color, DROPOFF_COLOR)

        if branch_side != SIDE_NONE:
            turn_to_color_branch(tank, branch_side, DROPOFF_COLOR)
            return STATE_APPROACH_DROPOFF_TILE, branch_side

        follow_line_step(tank, left_color, right_color, COLOR_BLACK)
        return STATE_FOLLOW_MAIN_LINE, SIDE_NONE

    branch_side = get_color_side(left_color, right_color, PICKUP_COLOR)

    if branch_side != SIDE_NONE:
        turn_to_color_branch(tank, branch_side, PICKUP_COLOR)
        return STATE_APPROACH_PICKUP_TILE, branch_side

    follow_line_step(tank, left_color, right_color, COLOR_BLACK)
    return STATE_FOLLOW_MAIN_LINE, SIDE_NONE


def handle_approach_pickup_tile_state(tank, left_color, right_color):
    if both_sensors_see_color(left_color, right_color, PICKUP_COLOR):
        stop(tank)
        return STATE_PICKUP_TILE_PROCEDURE

    follow_line_step(tank, left_color, right_color, (PICKUP_COLOR, COLOR_BLACK))
    return STATE_APPROACH_PICKUP_TILE


def handle_approach_dropoff_tile_state(tank, left_color, right_color):
    if both_sensors_see_color(left_color, right_color, DROPOFF_COLOR):
        stop(tank)
        return STATE_DROPOFF_TILE_PROCEDURE

    follow_line_step(tank, left_color, right_color, (DROPOFF_COLOR, COLOR_BLACK))
    return STATE_APPROACH_DROPOFF_TILE


def main():
    tank = MoveTank(OUTPUT_A, OUTPUT_B)
    servo = MediumMotor(OUTPUT_D)

    left_color_sensor = ColorSensor(INPUT_2)
    right_color_sensor = ColorSensor(INPUT_1)

    state = STATE_FOLLOW_MAIN_LINE
    has_object = False
    pickup_branch_side = SIDE_NONE

    try:
        move_grabber_down_to_limit(servo)

        while True:
            left_color, right_color = read_sensor_colors(left_color_sensor, right_color_sensor)

            if state == STATE_FOLLOW_MAIN_LINE:
                state, branch_side = handle_follow_main_line_state(tank, left_color, right_color, has_object)

                if state == STATE_APPROACH_PICKUP_TILE:
                    pickup_branch_side = branch_side

                continue

            if state == STATE_APPROACH_PICKUP_TILE:
                state = handle_approach_pickup_tile_state(tank, left_color, right_color)
                continue

            if state == STATE_PICKUP_TILE_PROCEDURE:
                run_pickup_tile_procedure(tank, servo, left_color_sensor, right_color_sensor, pickup_branch_side)
                has_object = True
                state = STATE_FOLLOW_MAIN_LINE
                pickup_branch_side = SIDE_NONE
                continue

            if state == STATE_APPROACH_DROPOFF_TILE:
                state = handle_approach_dropoff_tile_state(tank, left_color, right_color)
                continue

            if state == STATE_DROPOFF_TILE_PROCEDURE:
                run_dropoff_tile_procedure(tank, servo)
                has_object = False
                state = STATE_TASK_DONE
                continue

            if state == STATE_TASK_DONE:
                stop(tank)
                wait(DEFAULT_INTERVAL)
                continue

    except KeyboardInterrupt:
        stop(tank)
        servo.off()


if __name__ == "__main__":
    main()
