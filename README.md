# test-nb-cr

Testing notebook review workflows.

## Deepgram Transcription Script

`deepgram_transcriber.py` sends a WAV file to Deepgram for transcription.
Install requirements with [uv](https://github.com/astral-sh/uv) and run:

```bash
uv pip install requests
python deepgram_transcriber.py path/to/audio.wav --speed 2.0
```
Set `DEEPGRAM_API_KEY` in your environment or pass `--api-key`.
The script sends audio with speaker diarization enabled by default and the
language set to English. Disable diarization with `--no-diarize`.
The optional `--speed` argument sends a version of the audio sped up by the
factor provided (e.g. `2.0` for 2x speed).
