import logging

import typer

# Import functions/methods from other modules
from my_future_data.file_aggregator import main as run_file_aggregator
from my_future_data.many_files_to_one import combine_markdown_files
from my_future_data.wav_process_pipeline import AudioProcessor

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = typer.Typer()


@app.command()
def aggregate_files() -> None:
    """Aggregates files from for_struct/ into data/struct/ and data/raw/."""
    logger.info("Running file aggregator...")
    try:
        run_file_aggregator()
        logger.info("File aggregation finished.")
    except Exception:
        logger.exception("Error during file aggregation.")
        raise typer.Exit(code=1)


@app.command()
def combine_files() -> None:
    """Combines all markdown files in data/struct/ into one file."""
    logger.info("Combining markdown files...")
    try:
        combine_markdown_files()
        logger.info("Files combined successfully.")
    except Exception:
        logger.exception("Error during file combination.")
        raise typer.Exit(code=1)


@app.command()
def process_audio_pipeline() -> None:
    """Runs the full audio processing pipeline (VAD, Transcribe, Structure)."""
    logger.info("Starting audio processing pipeline...")
    try:
        processor = AudioProcessor()
        processor.process_audio_files()
        logger.info("Audio processing pipeline finished.")
    except Exception:
        logger.exception("Error during audio processing pipeline.")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
