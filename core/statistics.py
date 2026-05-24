import os
import json
import time
from datetime import datetime
from utils.logger import logger


class Statistics:
    _instance = None
    _stats_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "history", "statistics.json")

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load()
        return cls._instance

    def _load(self):
        self.start_time = time.time()
        self.total_chars = 0
        self.total_sessions = 0
        self.total_time_seconds = 0
        self.daily_stats = {}
        self.accuracy_feedback = []

        if os.path.exists(self._stats_file):
            try:
                with open(self._stats_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.total_chars = data.get("total_chars", 0)
                    self.total_sessions = data.get("total_sessions", 0)
                    self.total_time_seconds = data.get("total_time_seconds", 0)
                    self.daily_stats = data.get("daily_stats", {})
                    self.accuracy_feedback = data.get("accuracy_feedback", [])
            except Exception as e:
                logger.error(f"Failed to load statistics: {e}")

    def save(self):
        try:
            os.makedirs(os.path.dirname(self._stats_file), exist_ok=True)
            data = {
                "total_chars": self.total_chars,
                "total_sessions": self.total_sessions,
                "total_time_seconds": self.total_time_seconds,
                "daily_stats": self.daily_stats,
                "accuracy_feedback": self.accuracy_feedback
            }
            with open(self._stats_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save statistics: {e}")

    def record_session(self, text: str):
        if not text:
            return
        char_count = len(text)
        self.total_chars += char_count
        self.total_sessions += 1

        today = datetime.now().strftime("%Y-%m-%d")
        if today not in self.daily_stats:
            self.daily_stats[today] = {"chars": 0, "sessions": 0}
        self.daily_stats[today]["chars"] += char_count
        self.daily_stats[today]["sessions"] += 1

        self.save()
        logger.info(f"Stats: +{char_count} chars, total: {self.total_chars}")

    def record_accuracy(self, rating: int, text: str = ""):
        self.accuracy_feedback.append({
            "time": datetime.now().isoformat(),
            "rating": rating,
            "text_preview": text[:50]
        })
        self.save()

    def get_summary(self) -> dict:
        elapsed = time.time() - self.start_time
        today = datetime.now().strftime("%Y-%m-%d")
        today_stats = self.daily_stats.get(today, {"chars": 0, "sessions": 0})

        avg_accuracy = 0
        if self.accuracy_feedback:
            ratings = [f["rating"] for f in self.accuracy_feedback]
            avg_accuracy = sum(ratings) / len(ratings) * 20

        return {
            "today_chars": today_stats["chars"],
            "today_sessions": today_stats["sessions"],
            "total_chars": self.total_chars,
            "total_sessions": self.total_sessions,
            "session_duration": f"{int(elapsed // 60)}m {int(elapsed % 60)}s",
            "avg_accuracy": f"{avg_accuracy:.0f}%" if avg_accuracy > 0 else "N/A"
        }


stats = Statistics()
