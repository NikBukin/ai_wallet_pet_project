import os
import tempfile

from pydub import AudioSegment
from transformers import pipeline


from models import llm_insert_active


asr = pipeline(
    "automatic-speech-recognition",
    model="openai/whisper-small",
    device=0
)


def generate_text_from_voice(ogg_bytes):
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
        return f"⚠️ Ошибка распознавания: {e}"
    finally:
        try: os.remove(wav_path)
        except: pass

    if not recognized_text:
        return "⚠️ Не удалось распознать голос."

    return recognized_text

def generate_answer(recognized_text):
    # 4) Первичный парсинг LLM
    try:
        # insert_active возвращает словарь с ключами:
        # "name_active", "shortname_active", "type_active", "count", "price", "currency", "day_buy"
        parsed = llm_insert_active.insert_active(recognized_text)
    except Exception as e:
        return f"⚠️ Ошибка LLM: {e}"

    # parsed может быть None, если LLM не нашла JSON вовсе
    if not parsed:
        return "⚠️ LLM не вернула структуру. Попробуйте иначе."

    # 5) Определяем, каких полей не хватает
    missing = []
    print(parsed)
    for key in ["name_active", "count", "price", "currency", "day_buy"]:
        val = parsed.get(key) if key in parsed else None
        if val is None or (isinstance(val, str) and not val.strip()) or (isinstance(val, (int, float)) and val == 0 and key not in ["count"]):
            missing.append(key)

    return parsed, missing
