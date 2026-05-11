import time

from ev3dev2.motor import MoveTank, OUTPUT_A, OUTPUT_B, OUTPUT_D, MediumMotor
from ev3dev2.sensor import INPUT_1, INPUT_2
from ev3dev2.sensor.lego import ColorSensor


DEBUG = False

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

STATE_FOLLOW_MAIN_LINE = "follow_main_line"
STATE_APPROACH_PICKUP_TILE = "approach_pickup_tile"
STATE_PICKUP_TILE_PROCEDURE = "pickup_tile_procedure"
STATE_REACQUIRE_LINE = "reacquire_line"

SIDE_LEFT = "left"
SIDE_RIGHT = "right"
SIDE_NONE = "none"

MOVE_FORWARD = "forward"
MOVE_ROTATE = "rotate"
MOVE_HARD_LEFT = "hard_left"
MOVE_HARD_RIGHT = "hard_right"
MOVE_SOFT_RIGHT = "soft_right"
MOVE_SOFT_LEFT = "soft_left"

MOVEMENTS = {
    MOVE_FORWARD: (15, 15),
    MOVE_ROTATE: (-60, 60),
    MOVE_HARD_LEFT: (-35, 20),
    MOVE_HARD_RIGHT: (20, -35),
    MOVE_SOFT_RIGHT: (12, -28),
    MOVE_SOFT_LEFT: (-28, 12),
}

DEFAULT_INTERVAL = 0.01
REACQUIRE_INTERVAL = 0.01
TILE_DRIVE_INTERVAL = 0.01

BRANCH_TURN_TIME = 0.25
TURN_AROUND_TIME = 0.85

PICKUP_TILE_CONFIRM_TIME = 1.00
PICKUP_TILE_MIN_FORWARD_TIME = 0.35
PICKUP_TILE_MAX_FORWARD_TIME = 3.00
RETURN_TILE_MAX_FORWARD_TIME = 4.00
TILE_LEFT_CONFIRM_READS = 3

GRABBER_DOWN_SPEED = -80
GRABBER_DOWN_TIME = 0.30
GRABBER_UP_SPEED = 80
GRABBER_UP_TIME = 0.35


def debug(message):
    """Prints a debug message only when debug mode is enabled."""

    if DEBUG:
        print(message)


def wait(interval=0.05):
    """Pauses program execution for the given number of seconds."""

    time.sleep(interval)


def read_color_name(color_sensor):
    """Converts the EV3 color sensor code into a color name used by the program logic."""

    return COLOR_NAMES.get(color_sensor.color, COLOR_OTHER)


def read_sensor_colors(left_color_sensor, right_color_sensor):
    """Reads current colors detected by the left and right color sensors."""

    return read_color_name(left_color_sensor), read_color_name(right_color_sensor)


def drive(tank, movement_name):
    """Runs the drive motors using the selected movement from the MOVEMENTS configuration."""

    left_speed, right_speed = MOVEMENTS[movement_name]
    tank.on(left_speed, right_speed)


def stop(tank):
    """Stops the drive motors."""

    tank.off()


def sees_color(left_color, right_color, expected_color):
    """Checks whether any color sensor sees the expected color."""

    return left_color == expected_color or right_color == expected_color


def both_sensors_see_color(left_color, right_color, expected_color):
    """Checks whether both color sensors see the expected color."""

    return left_color == expected_color and right_color == expected_color


def get_color_side(left_color, right_color, expected_color):
    """Returns the side where exactly one sensor sees the expected color."""

    if left_color == expected_color and right_color != expected_color:
        return SIDE_LEFT

    if right_color == expected_color and left_color != expected_color:
        return SIDE_RIGHT

    return SIDE_NONE


def get_line_movement(left_color, right_color):
    """Selects the robot movement based on the colors detected by the line sensors."""

    if left_color == COLOR_WHITE and right_color == COLOR_WHITE:
        debug("forward")
        return MOVE_FORWARD

    if left_color == COLOR_WHITE and right_color == COLOR_BLACK:
        debug("correction right")
        return MOVE_SOFT_RIGHT

    if left_color == COLOR_BLACK and right_color == COLOR_WHITE:
        debug("correction left")
        return MOVE_SOFT_LEFT

    if left_color == COLOR_BLACK and right_color == COLOR_BLACK:
        debug("forward")
        return MOVE_FORWARD

    debug("forward")
    return MOVE_FORWARD


def get_colored_line_movement(left_color, right_color, line_color):
    """Selects the robot movement for following a colored branch line."""

    if left_color == line_color and right_color == line_color:
        debug("colored line forward")
        return MOVE_FORWARD

    if left_color == line_color and right_color != line_color:
        debug("colored line correction left")
        return MOVE_SOFT_LEFT

    if right_color == line_color and left_color != line_color:
        debug("colored line correction right")
        return MOVE_SOFT_RIGHT

    return get_line_movement(left_color, right_color)


def follow_line_step(tank, left_color, right_color):
    """Performs a single line-following step."""

    movement_name = get_line_movement(left_color, right_color)
    drive(tank, movement_name)
    wait(DEFAULT_INTERVAL)


def follow_colored_or_black_line_step(tank, left_color, right_color, line_color):
    """Follows the colored branch line when visible and falls back to the black line otherwise."""

    movement_name = get_colored_line_movement(left_color, right_color, line_color)
    drive(tank, movement_name)
    wait(DEFAULT_INTERVAL)


def turn_to_pickup_branch(tank, branch_side):
    """Turns the robot into the pickup branch based on the side of the pickup marker."""

    if branch_side == SIDE_LEFT:
        debug("turn to left pickup branch")
        drive(tank, MOVE_HARD_LEFT)
        wait(BRANCH_TURN_TIME)
        stop(tank)
        return

    if branch_side == SIDE_RIGHT:
        debug("turn to right pickup branch")
        drive(tank, MOVE_HARD_RIGHT)
        wait(BRANCH_TURN_TIME)
        stop(tank)
        return


def move_grabber_down_to_limit(servo):
    """Moves the grabber down until it reaches the mechanical lower limit."""

    servo.on(GRABBER_DOWN_SPEED)
    wait(GRABBER_DOWN_TIME)
    servo.off()


def move_grabber_up_to_limit(servo):
    """Moves the grabber up until it reaches the mechanical upper limit."""

    servo.on(GRABBER_UP_SPEED)
    wait(GRABBER_UP_TIME)
    servo.off()


def rotate_around(tank):
    """Rotates the robot in place for a calibrated 180 degree turn."""

    drive(tank, MOVE_ROTATE)
    wait(TURN_AROUND_TIME)
    stop(tank)


def drive_forward_until_tile_crossed(tank, left_color_sensor, right_color_sensor, expected_color, min_time, max_time):
    """Drives forward until the expected tile color is detected and then left again."""

    start_time = time.time()
    color_was_seen = False
    lost_reads = 0

    while time.time() - start_time < max_time:
        drive(tank, MOVE_FORWARD)

        left_color, right_color = read_sensor_colors(left_color_sensor, right_color_sensor)
        elapsed_time = time.time() - start_time

        if sees_color(left_color, right_color, expected_color):
            color_was_seen = True
            lost_reads = 0
        elif color_was_seen and elapsed_time >= min_time:
            lost_reads += 1

        if color_was_seen and lost_reads >= TILE_LEFT_CONFIRM_READS:
            break

        wait(TILE_DRIVE_INTERVAL)

    stop(tank)


def run_pickup_tile_procedure(tank, servo, left_color_sensor, right_color_sensor):
    """Runs the complete pickup sequence on the colored pickup tile."""

    debug("pickup tile procedure started")

    stop(tank)
    move_grabber_down_to_limit(servo)

    drive_forward_until_tile_crossed(
        tank,
        left_color_sensor,
        right_color_sensor,
        PICKUP_COLOR,
        PICKUP_TILE_MIN_FORWARD_TIME,
        PICKUP_TILE_MAX_FORWARD_TIME,
    )

    move_grabber_up_to_limit(servo)
    rotate_around(tank)

    drive_forward_until_tile_crossed(
        tank,
        left_color_sensor,
        right_color_sensor,
        PICKUP_COLOR,
        PICKUP_TILE_MIN_FORWARD_TIME,
        RETURN_TILE_MAX_FORWARD_TIME,
    )

    debug("pickup tile procedure finished")


def handle_follow_main_line_state(tank, left_color, right_color, has_object):
    """Handles line following on the main route and detects the pickup branch marker."""

    if has_object:
        follow_line_step(tank, left_color, right_color)
        return STATE_FOLLOW_MAIN_LINE

    branch_side = get_color_side(left_color, right_color, PICKUP_COLOR)

    if branch_side != SIDE_NONE:
        turn_to_pickup_branch(tank, branch_side)
        return STATE_APPROACH_PICKUP_TILE

    follow_line_step(tank, left_color, right_color)
    return STATE_FOLLOW_MAIN_LINE


def update_pickup_tile_seen_since(left_color, right_color, pickup_tile_seen_since):
    """Updates the timestamp used to confirm that the robot is on the pickup tile."""

    if both_sensors_see_color(left_color, right_color, PICKUP_COLOR):
        if pickup_tile_seen_since is None:
            return time.time()

        return pickup_tile_seen_since

    return None


def is_pickup_tile_confirmed(pickup_tile_seen_since):
    """Checks whether the pickup tile has been detected for the required continuous time."""

    if pickup_tile_seen_since is None:
        return False

    return time.time() - pickup_tile_seen_since >= PICKUP_TILE_CONFIRM_TIME


def handle_approach_pickup_tile_state(tank, left_color, right_color, pickup_tile_seen_since):
    """Handles following the pickup branch and confirms the pickup tile after stable color detection."""

    next_pickup_tile_seen_since = update_pickup_tile_seen_since(left_color, right_color, pickup_tile_seen_since)

    if is_pickup_tile_confirmed(next_pickup_tile_seen_since):
        stop(tank)
        return STATE_PICKUP_TILE_PROCEDURE, None

    follow_colored_or_black_line_step(tank, left_color, right_color, PICKUP_COLOR)
    return STATE_APPROACH_PICKUP_TILE, next_pickup_tile_seen_since


def handle_reacquire_line_state(tank, left_color, right_color):
    """Drives forward until the black line is detected again."""

    if sees_color(left_color, right_color, COLOR_BLACK):
        debug("line reacquired")
        stop(tank)
        return STATE_FOLLOW_MAIN_LINE

    drive(tank, MOVE_FORWARD)
    wait(REACQUIRE_INTERVAL)

    return STATE_REACQUIRE_LINE


def main():
    tank = MoveTank(OUTPUT_A, OUTPUT_B)
    servo = MediumMotor(OUTPUT_D)

    left_color_sensor = ColorSensor(INPUT_2)
    right_color_sensor = ColorSensor(INPUT_1)

    state = STATE_FOLLOW_MAIN_LINE
    has_object = False
    pickup_tile_seen_since = None

    try:
        print("Starting")
        move_grabber_down_to_limit(servo)

        while True:
            left_color, right_color = read_sensor_colors(left_color_sensor, right_color_sensor)

            if state == STATE_FOLLOW_MAIN_LINE:
                state = handle_follow_main_line_state(tank, left_color, right_color, has_object)

                if state == STATE_APPROACH_PICKUP_TILE:
                    pickup_tile_seen_since = None

                continue

            if state == STATE_APPROACH_PICKUP_TILE:
                state, pickup_tile_seen_since = handle_approach_pickup_tile_state(tank, left_color, right_color, pickup_tile_seen_since)
                continue

            if state == STATE_PICKUP_TILE_PROCEDURE:
                run_pickup_tile_procedure(tank, servo, left_color_sensor, right_color_sensor)
                has_object = True
                state = STATE_REACQUIRE_LINE
                pickup_tile_seen_since = None
                continue

            if state == STATE_REACQUIRE_LINE:
                state = handle_reacquire_line_state(tank, left_color, right_color)
                continue

    except KeyboardInterrupt:
        stop(tank)
        servo.off()


if __name__ == "__main__":
    main()