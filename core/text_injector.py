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

        cmd_key = Key.cmd if self.os == "Darwin" else Key.ctrl
        self.kb.press(cmd_key)
        self.kb.press('v')
        self.kb.release('v')
        self.kb.release(cmd_key)

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
            cmd_key = Key.cmd if self.os == "Darwin" else Key.ctrl
            self.kb.press(cmd_key)
            self.kb.press('z')
            self.kb.release('z')
            self.kb.release(cmd_key)
            logger.info("Command: Undo")
