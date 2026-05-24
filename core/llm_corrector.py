import time
from openai import OpenAI, APITimeoutError
from utils.logger import logger
from utils.config import Config


class LLMCorrector:
    def __init__(self):
        self.client = None
        self.model = None
        self.short_prompt = (
            "You are a voice recognition correction assistant. "
            "Remove filler words (um, ah, uh, like), fix typos, add proper punctuation. "
            "Output only the corrected text, no explanations."
        )
        self.long_prompt = (
            "You are a professional speech-to-text editor. Please intelligently edit the following continuous speech recognition result:\n"
            "1. Remove ALL filler words (um, ah, uh, like, you know, so, then, etc.)\n"
            "2. Fix homophone errors and speech recognition mistakes\n"
            "3. Add correct punctuation based on context (periods, commas, question marks, etc.)\n"
            "4. Keep the original meaning, make the text fluent and natural\n"
            "5. Remove repeated or self-corrected parts\n"
            "Output ONLY the edited text, no explanations, prefixes, suffixes, or Markdown."
        )

        if not Config.LLM_ENABLED:
            logger.info("LLM correction disabled")
            return

        if not Config.GEMINI_API_KEY:
            logger.warning("LLM correction disabled: No API key configured")
            return

        try:
            self.client = OpenAI(
                api_key=Config.GEMINI_API_KEY,
                base_url=Config.GEMINI_BASE_URL,
                timeout=5.0
            )
            self.model = Config.GEMINI_MODEL
            logger.info(f"LLM correction enabled ({self.model})")
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")

    def correct(self, text: str) -> str:
        if not self.client or len(text) < 4:
            return text

        prompt = self.long_prompt if len(text) > 50 else self.short_prompt
        max_tokens = 512 if len(text) > 50 else 256

        try:
            t0 = time.time()
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": text}
                ],
                temperature=0.1,
                max_tokens=max_tokens
            )
            corrected = resp.choices[0].message.content.strip()
            logger.debug(f"LLM time: {time.time() - t0:.2f}s, input: {len(text)} chars, output: {len(corrected)} chars")

            if corrected.startswith('"') and corrected.endswith('"'):
                corrected = corrected[1:-1]
            return corrected or text
        except APITimeoutError:
            logger.warning("LLM timeout, using original text")
            return text
        except Exception as e:
            logger.error(f"LLM error: {e}")
            return text
