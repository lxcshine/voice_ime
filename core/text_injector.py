import platform
import time
import pyperclip
from pynput.keyboard import Controller, Key
from utils.logger import logger
from utils.config import Config


class TextInjector:
    def __init__(self):
        self.kb = Controller()
        self.os = platform.system()
        self.last_inject_time = 0
        self._ctrl = Key.cmd if self.os == "Darwin" else Key.ctrl

    def inject(self, text: str, mode="replace"):
        if not text:
            return

        if mode == "append" and Config.SPACE_APPEND:
            self._type_text_with_paste(" " + text)
        elif mode == "newline":
            self._type_text_with_paste("\n" + text)
        else:
            self._type_text_with_paste(text)

        logger.info(f"Text injected: {text[:30]}...")

    def _type_text_with_paste(self, text: str):
        try:
            old_clip = pyperclip.paste()
        except Exception:
            old_clip = ""

        pyperclip.copy(text)
        time.sleep(0.05)

        self.kb.press(self._ctrl)
        self.kb.press('v')
        self.kb.release('v')
        self.kb.release(self._ctrl)

        time.sleep(0.1)
        try:
            pyperclip.copy(old_clip)
        except Exception:
            pass

    def inject_command(self, command: str):
        if command == "enter":
            self.kb.press(Key.enter)
            self.kb.release(Key.enter)
            logger.info("Command: Enter")

        elif command == "backspace":
            self.kb.press(Key.backspace)
            self.kb.release(Key.backspace)
            logger.info("Command: Backspace")

        elif command == "space":
            self.kb.press(Key.space)
            self.kb.release(Key.space)
            logger.info("Command: Space")

        elif command == "undo":
            self.kb.press(self._ctrl)
            self.kb.press('z')
            self.kb.release('z')
            self.kb.release(self._ctrl)
            logger.info("Command: Undo")

        elif command == "backspace_word":
            self.kb.press(self._ctrl)
            self.kb.press(Key.backspace)
            self.kb.release(Key.backspace)
            self.kb.release(self._ctrl)
            logger.info("Command: Backspace word")

        elif command == "backspace_sentence":
            self._select_last_sentence()
            self.kb.press(Key.backspace)
            self.kb.release(Key.backspace)
            logger.info("Command: Backspace sentence")

        elif command == "select_all_delete":
            self.kb.press(self._ctrl)
            self.kb.press('a')
            self.kb.release('a')
            self.kb.release(self._ctrl)
            time.sleep(0.05)
            self.kb.press(Key.backspace)
            self.kb.release(Key.backspace)
            logger.info("Command: Delete all")

        elif command == "select_all":
            self.kb.press(self._ctrl)
            self.kb.press('a')
            self.kb.release('a')
            self.kb.release(self._ctrl)
            logger.info("Command: Select all")

        elif command == "copy":
            self.kb.press(self._ctrl)
            self.kb.press('c')
            self.kb.release('c')
            self.kb.release(self._ctrl)
            logger.info("Command: Copy")

        elif command == "paste":
            self.kb.press(self._ctrl)
            self.kb.press('v')
            self.kb.release('v')
            self.kb.release(self._ctrl)
            logger.info("Command: Paste")

        elif command == "ctrl_home":
            self.kb.press(self._ctrl)
            self.kb.press(Key.home)
            self.kb.release(Key.home)
            self.kb.release(self._ctrl)
            logger.info("Command: Ctrl+Home")

        elif command == "ctrl_end":
            self.kb.press(self._ctrl)
            self.kb.press(Key.end)
            self.kb.release(Key.end)
            self.kb.release(self._ctrl)
            logger.info("Command: Ctrl+End")

    def _select_last_sentence(self):
        self.kb.press(Key.shift)
        self.kb.press(self._ctrl)
        self.kb.press(Key.left)
        self.kb.release(Key.left)
        self.kb.release(self._ctrl)
        self.kb.release(Key.shift)