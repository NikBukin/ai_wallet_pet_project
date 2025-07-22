import os
import tempfile

from pydub import AudioSegment
from transformers import pipeline


asr = pipeline(
    'automatic-speech-recognition',
    model='openai/whisper-tiny',
    device='cpu'
)


def generate_text_from_voice(ogg_bytes):
    """
    Генерирует текстовую расшифровку сообщения из голосового сообщения пользователя
    :param ogg_bytes: скачанное голосовое сообщение пользователя
    :return:
    """
    # 2) Конвертируем OGG → моно WAV 16 кГц
    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp_ogg:
        tmp_ogg.write(ogg_bytes)
        ogg_path = tmp_ogg.name

    wav_fd, wav_path = tempfile.mkstemp(suffix=".wav")
    os.close(wav_fd)
    try:
        audio = AudioSegment.from_ogg(ogg_path)
        audio = audio.set_channels(1).set_frame_rate(16000)
        audio.export(wav_path, format="wav")
    except Exception as e:
        try: os.remove(ogg_path)
        except: pass
        try: os.remove(wav_path)
        except: pass
        print(f"⚠️ Ошибка конвертации OGG→WAV: {e}")
        return f"⚠️ Ошибка конвертации OGG→WAV: {e}"
    finally:
        try: os.remove(ogg_path)
        except: pass

    # 3) Распознаём через Whisper
    recognized_text = None
    try:
        result = asr(wav_path)
        recognized_text = result.get("text", "").strip()
    except Exception as e:
        try: os.remove(wav_path)
        except: pass
        print(f"⚠️ Ошибка распознавания: {e}")
        return f"⚠️ Ошибка распознавания: {e}"
    finally:
        try: os.remove(wav_path)
        except: pass

    if not recognized_text:
        print("⚠️ Не удалось распознать голос.")
        return "⚠️ Не удалось распознать голос."

    return recognized_text

