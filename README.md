# Quantum Rotary Dial (QRD)
python serial port listener for rotary dial or anything that sends serial data of numbers 0-9. Converts to keyboard input and more!

For instance, if I want to type the phrase `I love QRD!` into a text editor I would simply dial
```
051024200642010520620820310100703102710300110702110
```
Which breaks down to

| Dial | Function               |
|------|------------------------|
| 05   | Select App Switch Mode |
| 1    | Open MacVim            |
| 02   | Select Alpha mode      |
| 420  | Type "i"               |
| 06   | Enable Shift           |
| 420  | Type "i"               |
| 10   | Type space             |
| 520  | Type "l"               |
| 620  | Type "o"               |
| 820  | Type "v"               |
| 310  | Type "e"               |
| 10   | Type space             |
| 07   | Toggle Caps Lock       |
| 03   | Select Phrases mode    |
| 1    | Type phrase "q"        |
| 02   | Select Alpha mode      |
| 710  | Type "r"               |
| 30   | Type "d"               |
| 01   | Select Numpad mode     |
| 1    | Type "1"               |
| 07   | Toggle Caps Lock       |
| 02   | Select Alpha mode      |
| 110  | Type Newline           |

# Package Dependencies
This app requires pynput. You can install it directly with 
```bash
pip install pynput
```
or with the requirements.txt file
```bash
pip install -r requirements.txt
```

# Setting up the Config
## Defining the Serial Port
This is the serial port of the Arduino.

The easiest way to determine the port is to:
1. Open the Arduino IDE
2. Go to Tools > Port

Alter the `serial_port` variable in [the config](config.py) with the appropriate value.

You shouldn't need to alter the `baud_rate`

## Auto Launching

1. Add the `launch_qrd.sh` script to you login items
	1. System Preferences > Users & Groups > Login Items
2. Be sure to have the script set to open with a terminal, not a text editor
	1. Right-click script file > Get Info > Open with: Terminal

## Logging
The app will write logs to the file defined by `log_file` in [the config](config.py)

## Default Mode
This is the mode the rotary dial will be in at start up. It must be one of the below options:
* numpad_mode
* alpha_mode
* phrases_mode
* alfred_mode
* apps_mode

## Adding Phrases and Apps
The phrases to type and the applications to switch between are defined in [the config](config.py). They've been prepopulated with popular phrases and apps.

### Known Limitations
Can only have 9 elements in the list.

## Adding Alfred Hotkeys
The hotkeys are defined by the dictionary "alfred_codes" in [the config](config.py)

| Code | Stands For | Triggers             |
|------|------------|----------------------|
| 44   | hi         | Sign On Workflow     |
| 293  | bye        | Sign Off Workflow    |
| 328  | eat        | Go To Lunch Workflow |

# Using the Rotary Dial
Once the app is running, it'll listen to the serial port and react to the dialed input.

It is important to note that "0" is treated as a special character. It is used to switch modes and acts as a signal to commit (see Alpha Mode or Alfred Mode below)

## Switching Modes

Dialing "0" enters an Operational Mode which allows for switching to a different mode.

| Mode         | Dial |
|--------------|------|
| Numpad       | 1    |
| Alpha        | 2    |
| Phrases      | 3    |
| Alfred       | 4    |
| App Switcher | 5    |
| Shift        | 6    |
| Caps Lock    | 7    |
| Backspace    | 8    |

### Known Limitations
There can be at most 9 modes.

## Numpad Mode
Simply dial the number you want, which one notable exception.

Since 0 is a special character, you'll need to dial it twice in order to type it. For example, to type the number "10" you'd actually have to dial "100". To type "50630" you'd have to dial "5006300"

## Alpha Mode
The letter groupings on the dial are accurate. Simply dial the number corresponding with the letter grouping you want, then add 1 or 2 (or 1 twice) if you want a letter later in the group. Once you've selected the letter, enter 0 to type it.

For example, the letter grouping "GHI" is assigned to 4. To type "g", dial "40"; to type "h", dial "410"; to type "i", dial "420" or "4110"
 
### Basic Punctuation
In addition to letters, this mode allows for typing basic punctuation.

| Punctuation Mark | Dial                         |
|------------------|------------------------------|
| Space            | 10                           |
| Newline          | 110                          |
| Period           | 120 or 1110                  |
| Comma            | 130 or 1120 or 1210 or 11110 |

### Known Limitations
As you can see on the dial, there's no "Q" or "Z" in any letter grouping. So you cannot type them.

**It's not a bug, it's a feature!**

If you insist on using those letters, they've been included as phrases

## Phrases and App-switching Mode
While Python uses 0-indexing, this does not. The list index starts at 1 for convenience.

For example, if the phrase list is `["a", "b", "c"]` then you would type "a" by dialing 1

## Alfred Mode
This requires setting up Hotkey triggers for your workflows. The Hotkey triggers should have all the modifiers (control, command, option, shift) enabled.

Simply dial the code as defined by "alfred_codes" in [the config](config.pyh) and then dial 0 to trigger it.

## Shifted and Caps Lock Mode
Selecting shift mode applies the shift modifier to only the next typed output. Selecting Caps Lock mode will apply shift to all typed output until you select Caps Lock mode again.

In both cases, once you've selected that mode it will automatically switch back to the previous mode. You won't have to switch back to it.

For instance, if you want to type the "@" character:
1. Start in Numpad mode
2. select Shift mode, by dialing "06"
3. Dial "2" which will type "@"

## Backspace Mode
You made a mistake. It happens to us all. You can backspace over typed text by invoking Backspace mode. Once you enter the mode, the next number you dial will be how far back to erase. As with the shift and caps lock modes, it'll switch back to the previous mode after backspacing.

For example, if you typed "Hello Word", you could erase the d by entering Backspace mode and dialing "1". You could then type "l" by entering "520" (assuming you were in alpha mode prior to backspacing).

If you typed "Helllo World", you could erase the extra L by entering Backspace mode and dialing "8". You would then retype the rest of the phrase.

## Known Limitation
At most, you can backspace 9 spaces at a time. To erase more, you'll have to enter Backspace mode multiple times
