# -*- coding: utf-8 -*-
from utils.logger import logger


class VoiceCommandParser:
    """
    Parses voice commands from recognized text.
    Supports: newline, delete, send, undo, select all, copy, paste, etc.
    """

    COMMANDS = {
        "newline": {
            "keywords": ["newline", "next line", "line break"],
            "action": "enter",
            "strip_command": True,
            "description": "Insert a newline"
        },
        "send": {
            "keywords": ["send"],
            "action": "enter",
            "strip_command": True,
            "description": "Send / Press Enter"
        },
        "delete_last_word": {
            "keywords": ["delete last word", "remove last word", "delete word"],
            "action": "backspace_word",
            "strip_command": True,
            "description": "Delete the last word"
        },
        "delete_last_sentence": {
            "keywords": ["delete sentence", "remove sentence", "delete last sentence"],
            "action": "backspace_sentence",
            "strip_command": True,
            "description": "Delete the last sentence"
        },
        "delete_all": {
            "keywords": ["delete all", "remove all", "clear all"],
            "action": "select_all_delete",
            "strip_command": True,
            "description": "Delete all text"
        },
        "undo": {
            "keywords": ["undo"],
            "action": "undo",
            "strip_command": True,
            "description": "Undo last action"
        },
        "select_all": {
            "keywords": ["select all"],
            "action": "select_all",
            "strip_command": True,
            "description": "Select all text"
        },
        "copy": {
            "keywords": ["copy"],
            "action": "copy",
            "strip_command": True,
            "description": "Copy selected text"
        },
        "paste": {
            "keywords": ["paste"],
            "action": "paste",
            "strip_command": True,
            "description": "Paste from clipboard"
        },
        "go_to_start": {
            "keywords": ["go to start", "beginning", "top of document"],
            "action": "ctrl_home",
            "strip_command": True,
            "description": "Go to document start"
        },
        "go_to_end": {
            "keywords": ["go to end", "bottom", "end of document"],
            "action": "ctrl_end",
            "strip_command": True,
            "description": "Go to document end"
        }
    }

    def __init__(self):
        self._enabled = True
        self._command_patterns = {}
        for cmd_name, cmd_info in self.COMMANDS.items():
            for kw in cmd_info["keywords"]:
                self._command_patterns[kw] = cmd_name
        logger.info(f"Voice command parser initialized: {len(self._command_patterns)} patterns")

    def is_enabled(self) -> bool:
        return self._enabled

    def set_enabled(self, enabled: bool):
        self._enabled = enabled

    def parse(self, text: str) -> dict:
        """
        Parse text for voice commands.
        Returns dict with: is_command, command, action, remaining_text, description
        """
        if not self._enabled or not text:
            return {"is_command": False, "remaining_text": text}

        found_commands = []
        for keyword, cmd_name in self._command_patterns.items():
            if keyword in text:
                cmd_info = self.COMMANDS[cmd_name]
                found_commands.append((keyword, cmd_name, cmd_info))

        if not found_commands:
            return {"is_command": False, "remaining_text": text}

        found_commands.sort(key=lambda x: len(x[0]), reverse=True)
        keyword, cmd_name, cmd_info = found_commands[0]

        remaining = text.replace(keyword, "", 1).strip()
        remaining = remaining.strip(",.:;!? \t")
        remaining = " ".join(remaining.split())

        return {
            "is_command": True,
            "command": cmd_name,
            "action": cmd_info["action"],
            "keyword": keyword,
            "remaining_text": remaining,
            "description": cmd_info["description"]
        }

    def get_available_commands(self) -> list:
        return [
            {"name": name, "keywords": info["keywords"], "description": info["description"]}
            for name, info in self.COMMANDS.items()
        ]