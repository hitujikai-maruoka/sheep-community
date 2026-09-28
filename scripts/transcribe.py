"""
音声ファイルを無料・ローカルで文字起こしするスクリプト。

使い方:
  pip install sherpa-onnx soundfile imageio-ffmpeg
  python3 scripts/transcribe.py 音声ファイル.m4a > transcript.txt

- 初回実行時に models/ へ SenseVoice（日本語対応）と Silero VAD のモデルを
  GitHub (k2-fsa/sherpa-onnx のリリース) からダウンロードします。
- APIキー不要・利用料金なし。処理はすべて手元のPC上で行われます。
- 出力は「[分:秒] テキスト」の形式です。自動認識のため誤字があるので、公開前に確認してください。
"""
import os
import subprocess
import sys
import tarfile
import tempfile
import urllib.request

import imageio_ffmpeg
import sherpa_onnx
import soundfile as sf

BASE = 'https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models'
MODEL_DIR = os.path.join(os.path.dirname(__file__), '..', 'models')
SENSE_VOICE = 'sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17'
SAMPLE_RATE = 16000


def download_models():
    os.makedirs(MODEL_DIR, exist_ok=True)
    model_path = os.path.join(MODEL_DIR, SENSE_VOICE)
    if not os.path.isdir(model_path):
        archive = model_path + '.tar.bz2'
        print('モデルをダウンロード中...', file=sys.stderr)
        urllib.request.urlretrieve(f'{BASE}/{SENSE_VOICE}.tar.bz2', archive)
        with tarfile.open(archive) as tar:
            tar.extractall(MODEL_DIR)
        os.remove(archive)
    vad_path = os.path.join(MODEL_DIR, 'silero_vad.onnx')
    if not os.path.exists(vad_path):
        urllib.request.urlretrieve(f'{BASE}/silero_vad.onnx', vad_path)
    return model_path, vad_path


def to_wav(src, dst):
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run(
        [ffmpeg, '-y', '-loglevel', 'error', '-i', src, '-ar', str(SAMPLE_RATE), '-ac', '1', dst],
        check=True,
    )


def main():
    if len(sys.argv) < 2:
        print('使い方: python3 scripts/transcribe.py 音声ファイル', file=sys.stderr)
        sys.exit(1)

    model_path, vad_path = download_models()
    recognizer = sherpa_onnx.OfflineRecognizer.from_sense_voice(
        model=os.path.join(model_path, 'model.int8.onnx'),
        tokens=os.path.join(model_path, 'tokens.txt'),
        language='ja',
        use_itn=True,
        num_threads=4,
    )

    config = sherpa_onnx.VadModelConfig()
    config.silero_vad.model = vad_path
    config.silero_vad.min_silence_duration = 0.4
    config.silero_vad.max_speech_duration = 20
    config.sample_rate = SAMPLE_RATE
    vad = sherpa_onnx.VoiceActivityDetector(config, buffer_size_in_seconds=60)

    with tempfile.TemporaryDirectory() as tmp:
        wav = os.path.join(tmp, 'audio.wav')
        to_wav(sys.argv[1], wav)
        samples, _ = sf.read(wav, dtype='float32')

    def drain():
        while not vad.empty():
            segment = vad.front
            stream = recognizer.create_stream()
            stream.accept_waveform(SAMPLE_RATE, segment.samples)
            recognizer.decode_stream(stream)
            sec = segment.start / SAMPLE_RATE
            print(f'[{int(sec // 60):02d}:{int(sec % 60):02d}] {stream.result.text}', flush=True)
            vad.pop()

    window = config.silero_vad.window_size
    for i in range(0, len(samples), window):
        vad.accept_waveform(samples[i : i + window])
        drain()
    vad.flush()
    drain()


if __name__ == '__main__':
    main()
