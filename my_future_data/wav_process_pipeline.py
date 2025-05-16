"""
Audio Processing Pipeline

This script processes audio files (WAV and MP3) from for_struct directory:
1. Converts audio to MP3 using Voice Activity Detection (VAD) if needed
2. Uses ElevenLabs to transcribe the audio
3. Uses an LLM to structure the transcription
4. Saves the transcription and structured data to appropriate directories
"""

import logging
import os
from io import BytesIO
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from openai import OpenAI
from pydub import AudioSegment  # type: ignore

from my_future_data.vad_processor import VADProcessor

load_dotenv()

logger = logging.getLogger(__name__)

TRANSCRIPTION_PROMPT = """
Ты эксперт по обработке речевых транскрипций. Проанализируй следующую транскрипцию и преобразуй ее в структурированный обзор, который передает суть и настроение обсуждения, оставаясь при этом понятным. Работай по этим правилам:

1.  Выдели основную тему и главные мысли.
2.  Собери связанные идеи в логичные блоки с понятными подзаголовками.
3.  Важные моменты, цифры или данные можешь выделить (например, полужирным).
4.  Для перечислений используй списки с маркерами.
5.  Формулируй мысли четко и кратко, но не слишком официально.
6.  Важные или характерные цитаты оставляй в кавычках.
7.  Структурируй информацию так, как она идет в обсуждении, или по важности.
8.  В конце основного текста добавь короткое резюме или вывод.
9.  После заключения создай отдельный раздел "Ключевые факты". Тут перечисли упомянутые факты строго и по делу, без эмоций и оценок рассказчика. Каждый факт — отдельный пункт списка.
10. Весь ответ должен быть оформлен как валидный Markdown документ.
11. Ответь на том же языке, что и транскрипция.

Транскрипция:
{transcription}
"""


class AudioProcessor:
    def __init__(self) -> None:
        """Initialize the audio processor with necessary clients and paths."""
        # Initialize paths
        self.base_dir = Path("data")
        self.voice_dir = self.base_dir / "voice"
        self.voice_raw_dir = self.voice_dir / "raw"
        self.voice_mp3_dir = self.voice_dir / "mp3"
        self.text_struct_dir = self.base_dir / "struct"
        self.voice_processed_dir = self.voice_raw_dir / "processed"
        self.text_raw_dir = self.base_dir / "raw"

        # Initialize API clients
        self.elevenlabs_api_key = os.environ["ELEVENLABS_API_KEY_MY_APPS"]
        self.openai_api_key = os.environ["OPENROUTER_API_KEY_MY_APPS"]
        self.openai_model = os.environ["OPENAI_MODEL"]
        self.openai_base_url = os.environ.get("OPENAPI_BASE_URL")

        self.elevenlabs_client = ElevenLabs(api_key=self.elevenlabs_api_key, timeout=60 * 20)
        self.openai_client = OpenAI(api_key=self.openai_api_key, base_url=self.openai_base_url)
        self.vad_processor = VADProcessor()

    def process_audio_to_mp3(self, audio_files: List[Path]) -> List[Path]:
        """
        Process audio files (WAV or MP3) to MP3 using Voice Activity Detection (VAD) if needed.

        Args:
            audio_files: List of audio file paths to process

        Returns:
            List of paths to processed MP3 files
        """
        processed_mp3_files: List[Path] = []

        for audio_file in audio_files:
            try:
                mp3_file = self.voice_mp3_dir / f"{audio_file.stem}.mp3"

                if mp3_file.exists():
                    logger.info("MP3 file %s already exists, skipping...", mp3_file.name)
                    processed_mp3_files.append(mp3_file)
                    continue

                # Process with VAD
                temp_processed = self.voice_mp3_dir / f"{audio_file.stem}_processed{audio_file.suffix}"
                self.vad_processor.process_audio_vad(audio_file, temp_processed)

                # Convert to MP3 if not already MP3
                if audio_file.suffix.lower() != ".mp3":
                    audio = AudioSegment.from_wav(temp_processed)
                    # Use optimal settings for speech audio:
                    # - 48kbps bitrate (good quality while keeping file size small)
                    # - Mono channel (speech doesn't benefit from stereo)
                    # - 22kHz sample rate (sufficient for speech frequencies)
                    audio = audio.set_frame_rate(22000)
                    audio.export(mp3_file, format="mp3", bitrate="48k")
                else:
                    # If already MP3, just rename the processed file
                    temp_processed.rename(mp3_file)

                logger.info("Processed %s to %s", audio_file.name, mp3_file.name)

                # Clean up temporary file if it still exists
                if temp_processed.exists():
                    temp_processed.unlink()

                processed_mp3_files.append(mp3_file)

            except Exception as e:
                logger.exception("Error processing %s: %s", audio_file.name, str(e))

        return processed_mp3_files

    def transcribe_with_elevenlabs(self, audio_path: Path) -> Optional[str]:
        """
        Transcribe audio file using ElevenLabs API client.

        Args:
            audio_path: Path to the audio file to transcribe

        Returns:
            Transcription text or None if transcription failed
        """
        try:
            with open(audio_path, "rb") as audio_file:
                audio_data = BytesIO(audio_file.read())
                transcription = self.elevenlabs_client.speech_to_text.convert(
                    file=audio_data,
                    model_id="scribe_v1",
                    tag_audio_events=True,
                    diarize=True,
                    # это баг в elevenlabs, пока работает только так
                    additional_formats='[{"format": "txt"}]'  # type: ignore
                )
                return transcription.additional_formats[0].content  # type: ignore
        except Exception as e:
            logger.exception("Error transcribing %s: %s", audio_path.name, str(e))
            return None

    def structure_with_llm(self, transcription: str) -> Optional[str]:
        """
        Structure transcription text using OpenAI LLM.

        Args:
            transcription: Raw transcription text to structure

        Returns:
            Structured text or None if structuring failed
        """
        try:
            response = self.openai_client.chat.completions.create(
                model=self.openai_model,
                messages=[{"role": "user", "content": TRANSCRIPTION_PROMPT.format(transcription=transcription)}],
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.exception("Error structuring text with OpenAI: %s", str(e))
            return None

    def process_audio_files(self) -> None:
        """Main method to process all audio files in the raw directory."""
        # Find both WAV and MP3 files
        audio_files = list(self.voice_raw_dir.glob("*.wav")) + list(self.voice_raw_dir.glob("*.mp3"))
        logger.info("Found %d audio files to process", len(audio_files))

        # Step 1: Process audio files to MP3
        logger.info("Step 1: Processing audio files to MP3")
        mp3_files = self.process_audio_to_mp3(audio_files)

        logger.info("Successfully processed %d MP3 files", len(mp3_files))

        # Process each MP3 file
        for mp3_file in mp3_files:
            file_id = mp3_file.stem

            # Step 2: Transcribe MP3
            logger.info("Step 2: Transcribing %s", mp3_file.name)
            transcription_file = self.text_raw_dir / f"transcription_{file_id}.txt"

            if not transcription_file.exists():
                transcription = self.transcribe_with_elevenlabs(mp3_file)

                if not transcription:
                    logger.error("Failed to transcribe %s, skipping...", mp3_file.name)
                    continue

                transcription_file.write_text(transcription)
                logger.info("Saved transcription to %s", transcription_file)
            else:
                transcription = transcription_file.read_text()
                logger.info("Loaded transcription from %s", transcription_file)

            # Step 3: Structure transcription
            logger.info("Step 3: Structuring transcription for %s", file_id)
            structured_file = self.text_struct_dir / f"structured_text_{file_id}.md"

            if not structured_file.exists():
                structured_text = self.structure_with_llm(transcription)
                if not structured_text:
                    logger.error("Failed to structure text for %s, skipping...", file_id)
                    continue

                structured_file.write_text(structured_text)
                logger.info("Saved structured text to %s", structured_file)
            else:
                structured_text = structured_file.read_text()
                logger.info("Loaded structured text from %s", structured_file)

            # Move processed audio file
            original_audio = self.voice_raw_dir / f"{file_id}{mp3_file.stem[-4:]}"
            if original_audio.exists():
                original_audio.rename(self.voice_processed_dir / original_audio.name)
                logger.info("Moved %s to processed directory", original_audio.name)

        logger.info("Processing complete")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    processor = AudioProcessor()
    processor.process_audio_files()
