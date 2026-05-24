# -*- coding: utf-8 -*-
from collections import deque
from utils.logger import logger


class ContextManager:
    """
    Multi-turn context manager for speech recognition disambiguation.
    Stores recent utterances and uses conversation context to improve
    LLM correction accuracy, especially for homophone resolution.
    """

    def __init__(self, max_context=5):
        self.max_context = max_context
        self.history = deque(maxlen=max_context)
        self.current_topic = None
        self.topic_keywords = []

    def add_utterance(self, text: str):
        if not text or len(text) < 2:
            return
        self.history.append(text)
        self._extract_topic(text)
        logger.debug(f"Context updated: {len(self.history)} turns, topic={self.current_topic}")

    def get_context(self) -> str:
        if not self.history:
            return ""
        lines = []
        for i, utterance in enumerate(self.history):
            lines.append(f"[Turn {i + 1}]: {utterance}")
        return "\n".join(lines)

    def get_recent(self, n=3) -> list:
        items = list(self.history)
        return items[-n:] if len(items) >= n else items

    def build_correction_prompt(self, current_text: str) -> str:
        context = self.get_context()
        topic_hint = ""
        if self.current_topic:
            topic_hint = f"\nCurrent topic is about: {self.current_topic}."

        if not context:
            return ""

        prompt = (
            f"Previous conversation context:\n{context}\n{topic_hint}\n\n"
            f"Using the context above, correct this speech recognition result. "
            f"Resolve homophones and ambiguities based on the topic and context. "
            f"Remove filler words, fix punctuation. Output only the corrected text:\n"
            f"{current_text}"
        )
        return prompt

    def _extract_topic(self, text: str):
        topic_indicators = {
            "Programming": ["code", "function", "algorithm", "bug", "compile", "runtime"],
            "Speech": ["recognition", "audio", "microphone", "recording", "voice"],
            "IME": ["typing", "keyboard", "input", "text", "characters"],
            "Meeting": ["discuss", "project", "requirements", "plan", "progress"],
        }

        matched = False
        for topic, keywords in topic_indicators.items():
            score = sum(1 for kw in keywords if kw in text)
            if score >= 2:
                self.current_topic = topic
                self.topic_keywords = keywords
                matched = True
                break

        if not matched:
            if len(self.history) >= 3:
                all_text = " ".join(self.get_recent())
                for topic, keywords in topic_indicators.items():
                    if sum(1 for kw in keywords if kw in all_text) >= 3:
                        self.current_topic = topic
                        self.topic_keywords = keywords
                        break

    def clear(self):
        self.history.clear()
        self.current_topic = None
        self.topic_keywords = []

    def is_empty(self) -> bool:
        return len(self.history) == 0