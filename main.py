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
MOVE_BACKWARD = "backward"
MOVE_HARD_LEFT = "hard_left"
MOVE_HARD_RIGHT = "hard_right"
MOVE_SOFT_RIGHT = "soft_right"
MOVE_SOFT_LEFT = "soft_left"

MOVEMENTS = {
    MOVE_FORWARD: (25, 25),
    MOVE_BACKWARD: (-25, -25),
    MOVE_HARD_LEFT: (25, -25),
    MOVE_HARD_RIGHT: (-25, 25),
    MOVE_SOFT_RIGHT: (0, -25),
    MOVE_SOFT_LEFT: (-25, 0),
}

DEFAULT_INTERVAL = 0.0
SERVO_INTERVAL = 0.1


def wait(interval=0.05):
    """Zatrzymuje robota na podany czas w sekundach."""

    time.sleep(interval)


def read_color_name(color_sensor):
    """Zamienia kod koloru z czujnika EV3 na nazwę używaną w logice programu."""

    return COLOR_NAMES.get(color_sensor.color, COLOR_OTHER)


def get_changed_color(color_sensor, previous_color):
    """Zwraca nowy kolor tylko wtedy, gdy różni się od poprzednio zapamiętanego."""

    current_color = read_color_name(color_sensor)

    if current_color == previous_color:
        return None

    return current_color


def update_last_color(color_sensor, previous_color):
    """Aktualizuje ostatnio zapamiętany kolor dla pojedynczego czujnika."""

    changed_color = get_changed_color(color_sensor, previous_color)

    if changed_color is None:
        return previous_color

    return changed_color


def read_sensor_colors(left_color_sensor, right_color_sensor, last_left_color, last_right_color):
    """Odczytuje i aktualizuje ostatnie kolory widziane przez lewy oraz prawy czujnik."""

    current_left_color = update_last_color(left_color_sensor, last_left_color)
    current_right_color = update_last_color(right_color_sensor, last_right_color)

    return current_left_color, current_right_color


def move_grabber_up(servo):
    """Podnosi manipulator przez krótki ruch silnika średniego."""

    servo.on(60)
    wait(0.1)
    servo.off()


def move_grabber_down(servo):
    """Opuszcza manipulator przez krótki ruch silnika średniego."""

    servo.on(-80)
    wait(0.05)
    servo.off()


def drive(tank, movement_name):
    """Uruchamia silniki według wybranego ruchu z konfiguracji MOVEMENTS."""

    left_speed, right_speed = MOVEMENTS[movement_name]
    tank.on(left_speed, right_speed)


def sees_color(left_color, right_color, expected_color):
    """Sprawdza, czy którykolwiek z czujników widzi oczekiwany kolor."""

    return left_color == expected_color or right_color == expected_color


def get_line_movement(left_color, right_color):
    """Dobiera ruch robota na podstawie kolorów widzianych przez czujniki linii."""

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
    """Obsługuje reakcję manipulatora na kolory specjalne."""

    if sees_color(left_color, right_color, COLOR_GREEN):
        drive(tank, MOVE_FORWARD)
        wait(0.005)
        move_grabber_up(servo)
        drive(tank, MOVE_BACKWARD)
        wait(0.01)
        return True

    if sees_color(left_color, right_color, COLOR_RED):
        drive(tank, MOVE_FORWARD)
        wait(0.005)
        move_grabber_down(servo)
        drive(tank, MOVE_BACKWARD)
        wait(0.01)
        return True

    return False


def follow_line_step(tank, left_color, right_color):
    """Wykonuje pojedynczy krok podążania po linii."""

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