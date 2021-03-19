import logging
import os
import serial

from pynput.keyboard import Key, Controller
import rumps

import config

logging.basicConfig(
    filename=config.log_file,
    filemode="w",
    encoding="utf-8",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s: %(message)s",
    datefmt="%m/%d/%Y %I:%M:%S %p",
)

rumps.debug_mode(True)

# to read the serial data from terminal: screen /dev/cu.usbserial-AM00GQIK 9600
ser = serial.Serial(config.serial_port, config.baud_rate, timeout=None)
logging.info("Listening on %s", ser.name)
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


def read_port():
    return int((str(ser.read())[2:3]))


def alpha(num):
    letter_key = num * 10
    logging.debug("Base Alpha letter_key is %s", letter_key)
    add = read_port()

    while add is not mode_list.index("operation_mode"):
        logging.debug("Adding this to letter_key: %s", add)
        letter_key += add
        add = read_port()

    return alphas.get(letter_key, "")


def backspace(num):
    logging.info("Sending backspace %s times", num)
    while num:
        keyboard.press(Key.backspace)
        keyboard.release(Key.backspace)
        num -= 1


def get_code(num):
    logging.debug("Getting code")
    code = str(num)
    add = read_port()
    while add is not mode_list.index("operation_mode"):
        code += str(add)
    logging.info("Code is %s", code)
    return code


def alfred(num):
    code = get_code(num)
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
    if mode == mode_list.index("numpad_mode"):
        keyboard.type(shifted_num[key])
    else:
        with keyboard.pressed(Key.shift):
            keyboard.type(key)
    return True


def main():
    logging.info("I'm in main!")
    capslock = False
    shift = False
    mode = mode_list.index(config.default_mode)

    while True:
        output = ""

        rotary_dial_number = read_port()
        logging.debug("Rotary Dial number is %s", rotary_dial_number)

        if rotary_dial_number == mode_list.index("operation_mode"):
            previous_mode = mode
            mode = read_port()
            logging.info("Switched to %s", mode_list[mode])
            if mode == mode_list.index("operation_mode"):
                mode = previous_mode
                logging.info("Switched back to %s", mode_list[mode])
                output = mode_list.index("operation_mode")
            else:
                if mode == mode_list.index("shift_mode"):
                    logging.info("Setting shift to True")
                    shift = True
                    mode = previous_mode
                    logging.info("Switched back to mode %s", mode_list[mode])
                elif mode == mode_list.index("caps_lock_mode"):
                    logging.info("Toggling Caps lock")
                    capslock = not capslock
                    mode = previous_mode
                    logging.info("Switched back to %s", mode_list[mode])
                continue

        if mode == mode_list.index("numpad_mode"):
            output = str(rotary_dial_number)
        elif mode == mode_list.index("alpha_mode"):
            output = alpha(rotary_dial_number)
        elif mode == mode_list.index("phrases_mode") and rotary_dial_number <= len(
            config.phrases
        ):
            output = config.phrases[rotary_dial_number - 1]
        elif mode == mode_list.index("apps_mode") and rotary_dial_number <= len(
            config.apps
        ):
            os.system(f"open -a '{config.apps[rotary_dial_number - 1]}'")
            output = ""
        elif mode == mode_list.index("alfred_mode"):
            output = alfred(rotary_dial_number)
        elif mode == mode_list.index("backspace_mode"):
            backspace(rotary_dial_number)
            mode = previous_mode
            logging.info("Switched back to %s", mode_list[mode])
            output = ""

        if len(output) < 1:
            logging.debug("Output is blank, not sending")
            continue

        if mode == mode_list.index("alfred_mode"):
            send_Alfred_Hotkey(output)
        elif shift or capslock:
            send_shifted_key(mode, output)
            shift = False
        else:
            logging.debug('Sending "%s" to keyboard', output)
            keyboard.type(output)

    ser.close()


if __name__ == "__main__":
    main()
