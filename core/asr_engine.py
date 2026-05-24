import numpy as np
import noisereduce as nr
from funasr import AutoModel
from utils.logger import logger
from utils.config import Config


class ASREngine:
    def __init__(self):
        logger.info("Loading FunASR model (first run requires download, please wait)...")
        self.model = AutoModel(
            model="iic/speech_paraformer-large-vad-punc_asr_nat-zh-cn-16k-common-vocab8404-pytorch",
            vad_model="fsmn-vad",
            punc_model="ct-punc-c",
            device="cuda:0" if self._check_cuda() else "cpu",
            disable_update=True
        )
        self.retry_count = 0
        self.max_retries = 2
        logger.info("ASR engine loaded successfully")

    def _check_cuda(self):
        try:
            import torch
            return torch.cuda.is_available()
        except Exception:
            return False

    def transcribe(self, audio: np.ndarray) -> str:
        if len(audio) < 1600:
            return ""

        for attempt in range(self.max_retries + 1):
            try:
                audio_clean = nr.reduce_noise(y=audio, sr=Config.SAMPLE_RATE, prop_decrease=0.8)

                res = self.model.generate(
                    input=audio_clean,
                    batch_size_s=300,
                    use_itn=True,
                    is_final=True
                )

                if res and "text" in res[0]:
                    text = res[0]["text"].strip()
                    if text:
                        self.retry_count = 0
                        return text

                if attempt < self.max_retries:
                    logger.warning(f"ASR attempt {attempt + 1} failed, retrying...")
                    continue
                return ""

            except Exception as e:
                logger.error(f"ASR error (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries:
                    continue
                raise

        return ""
