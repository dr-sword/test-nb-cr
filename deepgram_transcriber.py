import argparse
import os
import io
import wave
import audioop
import requests


def speed_up_wav(path: str, factor: float = 2.0) -> io.BytesIO:
    """Return a BytesIO object containing the WAV audio sped up by the factor."""
    if factor <= 0:
        raise ValueError("factor must be > 0")
    with wave.open(path, 'rb') as wf:
        params = wf.getparams()
        audio = wf.readframes(params.nframes)
    # Resample to a higher frame rate then write out using the original rate
    new_rate = int(params.framerate * factor)
    converted, _ = audioop.ratecv(audio, params.sampwidth, params.nchannels,
                                  params.framerate, new_rate, None)
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as out:
        out.setnchannels(params.nchannels)
        out.setsampwidth(params.sampwidth)
        out.setframerate(params.framerate)
        out.writeframes(converted)
    buf.seek(0)
    return buf


def transcribe(audio_handle, api_key: str, diarize: bool = True) -> dict:
    """Send audio_handle (file or BytesIO) to Deepgram and return the JSON response."""
    url = "https://api.deepgram.com/v1/listen"
    params = {
        "punctuate": "true",
        "diarize": str(diarize).lower(),
        "language": "en",
    }
    headers = {
        "Authorization": f"Token {api_key}",
        "Content-Type": "audio/wav",
    }
    response = requests.post(url, params=params, headers=headers, data=audio_handle)
    response.raise_for_status()
    return response.json()


def extract_cost(resp: dict):
    paths = [
        ("metadata", "total_cost"),
        ("metadata", "request_cost"),
        ("metadata", "cost"),
        ("usage", "total_cost"),
    ]
    for obj, key in paths:
        val = resp.get(obj, {}).get(key)
        if val is not None:
            return val
    return None


def main():
    parser = argparse.ArgumentParser(description="Transcribe audio with Deepgram")
    parser.add_argument("audio", help="Path to WAV audio file")
    parser.add_argument(
        "--speed",
        type=float,
        default=1.0,
        help="Speed factor (e.g. 2.0 for 2x). 1.0 sends original audio",
    )
    parser.add_argument(
        "--no-diarize",
        action="store_true",
        help="Disable speaker diarization",
    )
    parser.add_argument(
        "--api-key",
        default=os.environ.get("DEEPGRAM_API_KEY"),
        help="Deepgram API key (or set DEEPGRAM_API_KEY)",
    )
    args = parser.parse_args()

    if not args.api_key:
        parser.error("Deepgram API key required via --api-key or DEEPGRAM_API_KEY")

    if args.speed == 1.0:
        with open(args.audio, "rb") as f:
            response = transcribe(f, args.api_key, not args.no_diarize)
    else:
        audio_buf = speed_up_wav(args.audio, args.speed)
        response = transcribe(audio_buf, args.api_key, not args.no_diarize)

    # Basic transcript
    transcript = (
        response.get("results", {})
        .get("channels", [{}])[0]
        .get("alternatives", [{}])[0]
        .get("transcript")
    )
    print("Transcript:\n", transcript, sep="")

    # Diarized results
    utterances = response.get("results", {}).get("utterances", [])
    if utterances:
        print("\nDiarized:")
        for utt in utterances:
            speaker = utt.get("speaker", "?")
            start = utt.get("start", 0.0)
            end = utt.get("end", 0.0)
            text = utt.get("transcript", "")
            print(f"[Speaker {speaker}] ({start:.2f}-{end:.2f}) {text}")

    cost = extract_cost(response)
    if cost is not None:
        print(f"\nEstimated cost: {cost}")
    else:
        print("\nCost information not provided in response.")


if __name__ == "__main__":
    main()
