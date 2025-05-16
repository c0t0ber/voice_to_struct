import logging
from pathlib import Path

import torch
from pydub import AudioSegment  # type: ignore

logger = logging.getLogger(__name__)


SAMPLING_RATE = 16000
MILLISECONDS_IN_SECOND = 1000


class VADProcessor:
    def __init__(self) -> None:
        self.model, self.utils = torch.hub.load(  # type: ignore
            repo_or_dir="snakers4/silero-vad", model="silero_vad", force_reload=False, onnx=False
        )

    def process_audio_vad(
        self,
        audio_path: Path,
        output_path: Path,
        min_speech_duration_ms: int = MILLISECONDS_IN_SECOND * 4,
        min_silence_duration_ms: int = MILLISECONDS_IN_SECOND * 5,
    ) -> None:
        logger.info("Processing audio with VAD %s", audio_path)

        (get_speech_timestamps, save_audio, read_audio, VADIterator, collect_chunks) = self.utils

        audio_path_str = str(audio_path)

        audio_data = read_audio(audio_path_str, sampling_rate=SAMPLING_RATE)

        speech_timestamps = get_speech_timestamps(
            audio_data,
            self.model,
            sampling_rate=SAMPLING_RATE,
            min_speech_duration_ms=min_speech_duration_ms,
            min_silence_duration_ms=min_silence_duration_ms,
        )

        original_audio = AudioSegment.from_file(audio_path_str)
        
        output_audio = AudioSegment.empty()
        
        for segment in speech_timestamps:
            start_ms = segment["start"] * 1000 // SAMPLING_RATE
            end_ms = segment["end"] * 1000 // SAMPLING_RATE
            output_audio += original_audio[start_ms:end_ms]
            
        output_audio.export(
            output_path,
            format=audio_path.suffix.replace(".", ""),
        )

        logger.info("File %s processed with VAD", audio_path_str)
