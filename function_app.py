import json
from io import BytesIO

import azure.functions as func
import numpy as np
from pedalboard import NoiseGate
from pedalboard.io import AudioFile

app = func.FunctionApp()


def reduce_noise(audio_data: np.ndarray, samplerate: float) -> np.ndarray:
    """
    Reduce noise from the passed audio data.

    :param audio_data: Audio Data
    :param samplerate: Sample Rate
    :return: Processed audio data
    """

    # Create the Noise Gate
    noise_gate = NoiseGate(
        threshold_db=-12,
        ratio=10,
        attack_ms=10
    )

    # Process the audio data
    for _ in range(2):
        audio_data = noise_gate.process(audio_data, sample_rate=samplerate)

    return audio_data


def remove_silence(audio_data: np.ndarray, sample_rate: float, silence_threshold=-100.0, chunk_size=10) -> np.ndarray:
    """
    Remove silence at the beginning and end of the passed audio data.

    :param audio_data: Audio Data
    :param sample_rate: Sample Rate
    :param silence_threshold: Silence threshold in dB
    :param chunk_size: Chunks size in ms
    :return: Processed audio data
    """

    # Convert silence threshold from dB to amplitude ratio
    silence_threshold = 10 ** (silence_threshold / 20)

    # Calculate the chunk size in samples
    chunk_samples = int(chunk_size * (sample_rate / 1000))  # chunk size in ms

    # Split audio data into chunks
    chunks = [audio_data[i:i + chunk_samples] for i in range(0, len(audio_data), chunk_samples)]

    # Keep only chunks with max amplitude above silence threshold
    chunks = [chunk for chunk in chunks if np.max(np.abs(chunk)) > silence_threshold]

    # Concatenate chunks and return
    return np.concatenate(chunks)


@app.function_name(name="HttpTrigger")
@app.route(route="process", methods=["POST"])
async def main(req: func.HttpRequest):
    raw_body = req.get_body()
    if not raw_body:
        return func.HttpResponse(json.dumps({
            "status": False,
            "error": "No body provided"
        }), status_code=400, mimetype="application/json")

    try:
        body = BytesIO(raw_body)
        body.name = "audio.flac"

        # Load the audio file
        with AudioFile(body) as f:
            audio_data, samplerate = f.read(f.frames), f.samplerate

        # If the audio file is stereo, convert it to mono
        if len(audio_data.shape) > 1:
            audio_data = np.mean(audio_data, axis=0)

        # Remove noise
        processed_audio_data = reduce_noise(audio_data, samplerate)

        # Remove silence
        processed_audio_data = remove_silence(processed_audio_data, samplerate, chunk_size=50)

        result_body = BytesIO()
        result_body.name = "audio.wav"
        with AudioFile(result_body, "w", samplerate=samplerate, num_channels=1) as f:
            f.write(processed_audio_data)

        return func.HttpResponse(
            result_body.getvalue(),
            mimetype="audio/wav",
            headers={
                "Content-Disposition": "attachment; filename=audio.wav"
            })
    except Exception as e:
        from traceback import format_exc

        return func.HttpResponse(json.dumps({
            "status": False,
            "error": str(e),
            "stack": format_exc()
        }), status_code=500, mimetype="application/json")
