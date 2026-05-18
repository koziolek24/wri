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

MOVEMENTS = {
    MOVE_FORWARD: (15, 15),
    MOVE_BACKWARD: (-15, -15),
    MOVE_HARD_LEFT: (-35, 20),
    MOVE_HARD_RIGHT: (20, -35),
    MOVE_SOFT_RIGHT: (12, -28),
    MOVE_SOFT_LEFT: (-28, 12),
}

DEFAULT_INTERVAL = 0.01
TILE_DRIVE_INTERVAL = 0.01
BACKUP_INTERVAL = 0.01

BRANCH_TURN_TIME = 0.25
RETURN_TO_MAIN_TURN_TIME = 0.25

PICKUP_TILE_CONFIRM_TIME = 1.00
PICKUP_TILE_MIN_FORWARD_TIME = 0.35
PICKUP_TILE_MAX_FORWARD_TIME = 3.00
BACKUP_TO_MAIN_LINE_MAX_TIME = 5.00
BACKUP_MIN_TIME_BEFORE_BLACK_DETECTION = 0.35
TILE_LEFT_CONFIRM_READS = 3

GRABBER_DOWN_SPEED = -80
GRABBER_DOWN_TIME = 0.15
GRABBER_UP_SPEED = 80
GRABBER_UP_TIME = 0.35
GRABBER_INITIAL_UP_TIME = 0.80


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


def get_line_movement(left_color, right_color, line_color):
    """Selects movement for following a line with the selected color."""

    if left_color != line_color and right_color != line_color:
        debug("line forward")
        return MOVE_FORWARD

    if left_color != line_color and right_color == line_color:
        debug("line correction right")
        return MOVE_SOFT_RIGHT

    if left_color == line_color and right_color != line_color:
        debug("line correction left")
        return MOVE_SOFT_LEFT

    if left_color == line_color and right_color == line_color:
        debug("line forward")
        return MOVE_FORWARD

    debug("line forward")
    return MOVE_FORWARD


def follow_line_step(tank, left_color, right_color, line_color):
    """Performs a single line-following step for the selected line color."""

    movement_name = get_line_movement(left_color, right_color, line_color)
    drive(tank, movement_name)
    wait(DEFAULT_INTERVAL)


def turn_to_color_branch(tank, branch_side, branch_color):
    """Turns the robot into a colored branch based on the side of the detected marker."""

    if branch_side == SIDE_LEFT:
        debug("turn to left " + branch_color + " branch")
        drive(tank, MOVE_HARD_LEFT)
        wait(BRANCH_TURN_TIME)
        stop(tank)
        return

    if branch_side == SIDE_RIGHT:
        debug("turn to right " + branch_color + " branch")
        drive(tank, MOVE_HARD_RIGHT)
        wait(BRANCH_TURN_TIME)
        stop(tank)
        return

    debug("missing branch side")
    stop(tank)


def turn_to_continue_main_line(tank, branch_side):
    """Turns the robot back to the previous main route direction after reversing from a branch."""

    if branch_side == SIDE_LEFT:
        debug("turn right to continue main line")
        drive(tank, MOVE_HARD_RIGHT)
        wait(RETURN_TO_MAIN_TURN_TIME)
        stop(tank)
        return

    if branch_side == SIDE_RIGHT:
        debug("turn left to continue main line")
        drive(tank, MOVE_HARD_LEFT)
        wait(RETURN_TO_MAIN_TURN_TIME)
        stop(tank)
        return

    debug("missing branch side")
    stop(tank)


def move_grabber_down_to_limit(servo):
    """Moves the grabber down by the calibrated drop distance."""

    servo.on(GRABBER_DOWN_SPEED)
    wait(GRABBER_DOWN_TIME)
    servo.off()


def move_grabber_up_for_duration(servo, duration):
    """Moves the grabber up for the selected duration."""

    servo.on(GRABBER_UP_SPEED)
    wait(duration)
    servo.off()


def move_grabber_up_to_limit(servo):
    """Moves the grabber up by the calibrated pickup lift distance."""

    move_grabber_up_for_duration(servo, GRABBER_UP_TIME)


def move_grabber_up_to_start_position(servo):
    """Moves the grabber to a high default position before driving."""

    move_grabber_up_for_duration(servo, GRABBER_INITIAL_UP_TIME)


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


def drive_backward_until_black_line_seen(tank, left_color_sensor, right_color_sensor):
    """Drives backward for a minimum time and then stops when at least one sensor detects the black main line."""

    start_time = time.time()

    while time.time() - start_time < BACKUP_TO_MAIN_LINE_MAX_TIME:
        elapsed_time = time.time() - start_time

        drive(tank, MOVE_BACKWARD)

        left_color, right_color = read_sensor_colors(left_color_sensor, right_color_sensor)

        if elapsed_time >= BACKUP_MIN_TIME_BEFORE_BLACK_DETECTION and sees_color(left_color, right_color, COLOR_BLACK):
            debug("black main line reached while backing up")
            stop(tank)
            return True

        wait(BACKUP_INTERVAL)

    debug("black main line was not reached while backing up")
    stop(tank)
    return False


def run_pickup_tile_procedure(tank, servo, left_color_sensor, right_color_sensor, pickup_branch_side):
    """Runs the pickup sequence and returns to the main route by reversing instead of rotating around."""

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

    main_line_was_reached = drive_backward_until_black_line_seen(
        tank,
        left_color_sensor,
        right_color_sensor,
    )

    if main_line_was_reached:
        turn_to_continue_main_line(tank, pickup_branch_side)

    debug("pickup tile procedure finished")


def run_dropoff_tile_procedure(tank, servo, left_color_sensor, right_color_sensor, dropoff_branch_side):
    """Drops the object on the dropoff tile and returns to the main route by reversing."""

    debug("dropoff tile procedure started")

    stop(tank)
    move_grabber_down_to_limit(servo)

    main_line_was_reached = drive_backward_until_black_line_seen(
        tank,
        left_color_sensor,
        right_color_sensor,
    )

    move_grabber_up_to_start_position(servo)

    if main_line_was_reached:
        turn_to_continue_main_line(tank, dropoff_branch_side)

    debug("dropoff tile procedure finished")


def handle_follow_main_line_state(tank, left_color, right_color, has_object):
    """Handles main route following and detects the next required colored branch."""

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


def is_dropoff_tile_detected(left_color, right_color):
    """Checks whether the robot has entered the dropoff tile."""

    return both_sensors_see_color(left_color, right_color, DROPOFF_COLOR)


def handle_approach_pickup_tile_state(tank, left_color, right_color, pickup_tile_seen_since):
    """Handles following the pickup color line and confirms the pickup tile after stable color detection."""

    next_pickup_tile_seen_since = update_pickup_tile_seen_since(left_color, right_color, pickup_tile_seen_since)

    if is_pickup_tile_confirmed(next_pickup_tile_seen_since):
        stop(tank)
        return STATE_PICKUP_TILE_PROCEDURE, None

    follow_line_step(tank, left_color, right_color, PICKUP_COLOR)
    return STATE_APPROACH_PICKUP_TILE, next_pickup_tile_seen_since


def handle_approach_dropoff_tile_state(tank, left_color, right_color):
    """Handles following the dropoff color line and detects the dropoff tile immediately."""

    if is_dropoff_tile_detected(left_color, right_color):
        stop(tank)
        return STATE_DROPOFF_TILE_PROCEDURE

    follow_line_step(tank, left_color, right_color, DROPOFF_COLOR)
    return STATE_APPROACH_DROPOFF_TILE


def main():
    tank = MoveTank(OUTPUT_A, OUTPUT_B)
    servo = MediumMotor(OUTPUT_D)

    left_color_sensor = ColorSensor(INPUT_2)
    right_color_sensor = ColorSensor(INPUT_1)

    state = STATE_FOLLOW_MAIN_LINE
    has_object = False
    pickup_tile_seen_since = None
    pickup_branch_side = SIDE_NONE
    dropoff_branch_side = SIDE_NONE

    try:
        print("Starting")
        move_grabber_up_to_start_position(servo)

        while True:
            left_color, right_color = read_sensor_colors(left_color_sensor, right_color_sensor)

            if state == STATE_FOLLOW_MAIN_LINE:
                state, branch_side = handle_follow_main_line_state(tank, left_color, right_color, has_object)

                if state == STATE_APPROACH_PICKUP_TILE:
                    pickup_tile_seen_since = None
                    pickup_branch_side = branch_side

                if state == STATE_APPROACH_DROPOFF_TILE:
                    dropoff_branch_side = branch_side

                continue

            if state == STATE_APPROACH_PICKUP_TILE:
                state, pickup_tile_seen_since = handle_approach_pickup_tile_state(
                    tank,
                    left_color,
                    right_color,
                    pickup_tile_seen_since,
                )
                continue

            if state == STATE_PICKUP_TILE_PROCEDURE:
                run_pickup_tile_procedure(tank, servo, left_color_sensor, right_color_sensor, pickup_branch_side)
                has_object = True
                state = STATE_FOLLOW_MAIN_LINE
                pickup_tile_seen_since = None
                pickup_branch_side = SIDE_NONE
                continue

            if state == STATE_APPROACH_DROPOFF_TILE:
                state = handle_approach_dropoff_tile_state(tank, left_color, right_color)
                continue

            if state == STATE_DROPOFF_TILE_PROCEDURE:
                run_dropoff_tile_procedure(tank, servo, left_color_sensor, right_color_sensor, dropoff_branch_side)
                has_object = False
                state = STATE_TASK_DONE
                dropoff_branch_side = SIDE_NONE
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