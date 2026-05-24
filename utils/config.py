import os
import json
from dotenv import load_dotenv

load_dotenv()


class Settings:
    _instance = None
    _settings_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "settings.json")

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_settings()
        return cls._instance

    def _load_settings(self):
        defaults = {
            "hotkey": "f8",
            "exit_key": "f12",
            "vad_threshold": 0.5,
            "llm_enabled": True,
            "llm_mode": "online",
            "gemini_model": "gemini-2.5-flash",
            "gemini_base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
            "gemini_api_key": "",
            "asr_model": "paraformer-large",
            "continuous_mode": False,
            "auto_punctuation": True,
            "space_append": True,
            "sample_rate": 16000,
            "show_volume_bar": True,
            "auto_start_on_boot": False,
            "theme": "dark"
        }

        if os.path.exists(self._settings_file):
            try:
                with open(self._settings_file, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                    defaults.update(saved)
            except Exception:
                pass

        self._data = defaults
        self._apply_to_env()

    def _apply_to_env(self):
        os.environ["HOTKEY"] = self._data.get("hotkey", "f8")
        os.environ["VAD_THRESHOLD"] = str(self._data.get("vad_threshold", 0.5))
        os.environ["LLM_MODE"] = self._data.get("llm_mode", "online")
        os.environ["GEMINI_MODEL"] = self._data.get("gemini_model", "gemini-2.5-flash")
        os.environ["GEMINI_BASE_URL"] = self._data.get("gemini_base_url", "")
        os.environ["GEMINI_API_KEY"] = self._data.get("gemini_api_key", "")
        os.environ["ASR_MODEL"] = self._data.get("asr_model", "paraformer-large")

    def save(self):
        with open(self._settings_file, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)

    def get(self, key, default=None):
        return self._data.get(key, default)

    def set(self, key, value):
        self._data[key] = value
        self.save()
        self._apply_to_env()

    @property
    def HOTKEY(self):
        return self._data.get("hotkey", "f8")

    @property
    def EXIT_KEY(self):
        return self._data.get("exit_key", "f12")

    @property
    def VAD_THRESHOLD(self):
        return float(self._data.get("vad_threshold", 0.5))

    @property
    def LLM_ENABLED(self):
        return self._data.get("llm_enabled", True)

    @property
    def LLM_MODE(self):
        return self._data.get("llm_mode", "online")

    @property
    def GEMINI_MODEL(self):
        return self._data.get("gemini_model", "gemini-2.5-flash")

    @property
    def GEMINI_BASE_URL(self):
        return self._data.get("gemini_base_url", "https://generativelanguage.googleapis.com/v1beta/openai/")

    @property
    def GEMINI_API_KEY(self):
        return self._data.get("gemini_api_key", "")

    @property
    def ASR_MODEL(self):
        return self._data.get("asr_model", "paraformer-large")

    @property
    def CONTINUOUS_MODE(self):
        return self._data.get("continuous_mode", False)

    @property
    def AUTO_PUNCTUATION(self):
        return self._data.get("auto_punctuation", True)

    @property
    def SPACE_APPEND(self):
        return self._data.get("space_append", True)

    @property
    def SAMPLE_RATE(self):
        return int(self._data.get("sample_rate", 16000))

    @property
    def SHOW_VOLUME_BAR(self):
        return self._data.get("show_volume_bar", True)


settings = Settings()


class Config:
    HOTKEY = settings.HOTKEY
    EXIT_KEY = settings.EXIT_KEY
    VAD_THRESHOLD = settings.VAD_THRESHOLD
    LLM_ENABLED = settings.LLM_ENABLED
    LLM_MODE = settings.LLM_MODE
    GEMINI_MODEL = settings.GEMINI_MODEL
    GEMINI_BASE_URL = settings.GEMINI_BASE_URL
    GEMINI_API_KEY = settings.GEMINI_API_KEY
    ASR_MODEL = settings.ASR_MODEL
    CONTINUOUS_MODE = settings.CONTINUOUS_MODE
    AUTO_PUNCTUATION = settings.AUTO_PUNCTUATION
    SPACE_APPEND = settings.SPACE_APPEND
    SAMPLE_RATE = settings.SAMPLE_RATE
    SHOW_VOLUME_BAR = settings.SHOW_VOLUME_BAR
