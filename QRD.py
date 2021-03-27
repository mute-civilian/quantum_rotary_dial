import logging
import os
import serial
from multiprocessing import Process, Value

from pynput.keyboard import Key, Controller
import rumps

import config

logging.basicConfig(
    filename=config.log_file,
    filemode="w",
    encoding="utf-8",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s: %(message)s",
    datefmt="%m/%d/%Y %I:%M:%S %p",
)

# rumps.debug_mode(True)

keyboard = Controller()

alphas = {
    10: " ",
    11: "\n",
    12: ".",
    13: ",",
    20: "a",
    21: "b",
    22: "c",
    30: "d",
    31: "e",
    32: "f",
    40: "g",
    41: "h",
    42: "i",
    50: "j",
    51: "k",
    52: "l",
    60: "m",
    61: "n",
    62: "o",
    70: "p",
    71: "r",
    72: "s",
    80: "t",
    81: "u",
    82: "v",
    90: "w",
    91: "x",
    92: "y",
}

shifted_num = {
    "1": "!",
    "2": "@",
    "3": "#",
    "4": "$",
    "5": "%",
    "6": "^",
    "7": "&",
    "8": "*",
    "9": "(",
    "0": ")",
}

mode_list = [
    "operation_mode",
    "numpad_mode",
    "alpha_mode",
    "phrases_mode",
    "alfred_mode",
    "apps_mode",
    "shift_mode",
    "caps_lock_mode",
    "backspace_mode",
]

mode = Value("i", mode_list.index(config.default_mode))
capslock = Value("b", False)
shift = Value("b", False)


class QRDStatusBarApp(rumps.App):
    def __init__(self):
        self.config = {"app_name": "QRD", "interval": 1}
        self.app = rumps.App(self.config["app_name"], quit_button=None)
        self.timer = rumps.Timer(self.set_title, 1)
        self.interval = self.config["interval"]
        self.set_up_menu()
        self.app.menu = []

    def run(self):
        logging.debug("Running statusbar app")
        self.timer.start()
        self.app.run()

    def set_up_menu(self):
        self.app.title = "QRD"
        self.app.icon = "images/app.icns"

    def set_title(self, sender):
        current_mode = mode_list[int(mode.value)]
        shift_flag = "Shifted " if shift.value else ""
        capslock_flag = "Capslocked " if capslock.value else ""

        self.app.title = shift_flag + capslock_flag + current_mode


@rumps.clicked("Quit")
def clean_up_before_quit(_):
    QRD_process.terminate()
    rumps.quit_application()


def read_port(ser):
    return int((str(ser.read())[2:3]))


def alpha(ser, num):
    letter_key = num * 10
    logging.debug("Base Alpha letter_key is %s", letter_key)
    add = read_port(ser)

    while add is not mode_list.index("operation_mode"):
        logging.debug("Adding this to letter_key: %s", add)
        letter_key += add
        add = read_port(ser)

    return alphas.get(letter_key, "")


def backspace(num):
    logging.info("Sending backspace %s times", num)
    while num:
        keyboard.press(Key.backspace)
        keyboard.release(Key.backspace)
        num -= 1


def get_code(ser, num):
    logging.debug("getting code")
    code = str(num)
    next_digit = read_port(ser)
    while next_digit is not mode_list.index("operation_mode"):
        code += str(next_digit)
        next_digit = read_port(ser)
    logging.info("Code is %s", code)
    return code


def alfred(ser, num):
    code = get_code(ser, num)
    try:
        return config.alfred_codes[code]
    except KeyError:
        logging.warning("Code %s is not valid, returning blank string")
        return ""


def send_Alfred_Hotkey(key):
    logging.info("Sending Alfred Hotkey")
    with keyboard.pressed(Key.shift):
        with keyboard.pressed(Key.cmd):
            with keyboard.pressed(Key.alt):
                with keyboard.pressed(Key.ctrl):
                    keyboard.type(key)
    return True


def send_shifted_key(mode, key):
    logging.info('Sending shifted "%s" to keyboard', key)
    # NOTE: cannot shift numbers with this library, so pull from dictionary
    if mode_list[mode.value] == "numpad_mode":
        keyboard.type(shifted_num[key])
    else:
        with keyboard.pressed(Key.shift):
            keyboard.type(key)
    return True


def main(mode, capslock, shift):
    # to read the serial data from terminal: screen /dev/cu.usbserial-AM00GQIK 9600
    ser = serial.Serial(config.serial_port, config.baud_rate, timeout=None)
    logging.info("Listening on %s", ser.name)

    while True:
        output = ""

        rotary_dial_number = read_port(ser)
        logging.debug("Rotary Dial number is %s", rotary_dial_number)

        if rotary_dial_number == mode_list.index("operation_mode"):
            previous_mode = mode.value
            mode.value = read_port(ser)
            logging.info("Switched to %s", mode_list[mode.value])
            if mode_list[mode.value] == "operation_mode":
                mode.value = previous_mode
                logging.info("Switched back to %s", mode_list[mode.value])
                output = mode_list.index("operation_mode")
            else:
                if mode_list[mode.value] == "shift_mode":
                    logging.info("Setting shift to True")
                    shift.value = True
                    mode.value = previous_mode
                    logging.info("Switched back to mode %s", mode_list[mode.value])
                elif mode_list[mode.value] == "caps_lock_mode":
                    logging.info("Toggling Caps lock")
                    capslock.value = not capslock.value
                    mode.value = previous_mode
                    logging.info("Switched back to %s", mode_list[mode.value])
                continue

        if mode_list[mode.value] == "numpad_mode":
            output = str(rotary_dial_number)
        elif mode_list[mode.value] == "alpha_mode":
            output = alpha(ser, rotary_dial_number)
        elif mode_list[mode.value] == "phrases_mode" and rotary_dial_number <= len(
            config.phrases
        ):
            output = config.phrases[rotary_dial_number - 1]
        elif mode_list[mode.value] == "apps_mode" and rotary_dial_number <= len(
            config.apps
        ):
            os.system(f"open -a '{config.apps[rotary_dial_number - 1]}'")
            output = ""
        elif mode_list[mode.value] == "alfred_mode":
            output = alfred(ser, rotary_dial_number)
        elif mode_list[mode.value] == "backspace_mode":
            backspace(rotary_dial_number)
            mode.value = previous_mode
            logging.info("Switched back to %s", mode_list[mode.value])
            output = ""

        if len(output) < 1:
            logging.debug("Output is blank, not sending")
            continue

        if mode_list[mode.value] == "alfred_mode":
            send_Alfred_Hotkey(output)
        elif shift.value or capslock.value:
            send_shifted_key(mode, output)
            shift.value = False
        else:
            logging.debug('Sending "%s" to keyboard', output)
            keyboard.type(output)

    ser.close()


if __name__ == "__main__":
    QRD_process = Process(target=main, args=(mode, capslock, shift))
    QRD_process.start()
    app = QRDStatusBarApp()
    app.run()
