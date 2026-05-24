from datetime import datetime
import os
from utils.logger import logger


class HistoryLogger:
    def __init__(self, mode="normal"):
        base_dir = os.path.dirname(os.path.dirname(__file__))
        
        if mode == "continuous":
            history_dir = os.path.join(base_dir, "history", "continuous")
            file_prefix = "continuous"
        else:
            history_dir = os.path.join(base_dir, "history")
            file_prefix = "voice"
        
        if not os.path.exists(history_dir):
            os.makedirs(history_dir)
        
        date_str = datetime.now().strftime("%Y%m%d")
        self.filepath = os.path.join(history_dir, f"{file_prefix}_{date_str}.txt")
        self.mode = mode

    def log(self, text: str):
        if not text:
            return
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with open(self.filepath, "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] {text}\n")
            logger.info(f"[{self.mode}] History logged: {text[:20]}...")
        except Exception as e:
            logger.error(f"Failed to log history: {e}")
