"""语音对话路由 /voice/chat"""
import io
import wave
import tempfile
import os
import numpy as np

import httpx
from fastapi import APIRouter, Request, Response
from openai import AsyncOpenAI

router = APIRouter(prefix="/voice", tags=["voice"])

try:
    import whisper
    _whisper_model = whisper.load_model("base")
    print("[voice] Whisper base model loaded")
except Exception as e:
    _whisper_model = None
    print(f"[voice] Whisper failed: {e}")

def _build_llm() -> AsyncOpenAI:
    proxy = os.getenv("LLM_PROXY", "")
    kwargs = {
        "api_key": os.getenv("DEEPSEEK_API_KEY", "sk-xxx"),
        "base_url": os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
        "http_client": httpx.AsyncClient(
            timeout=httpx.Timeout(60.0, connect=15.0),
            follow_redirects=True,
            trust_env=False,
        ),
    }
    if proxy:
        kwargs["http_client"].proxy = proxy
    return AsyncOpenAI(**kwargs)

WAKE_WORDS = ["樊玉明", "玉明", "明哥"]

# 保存最后一段录音用于调试
_debug_dir = tempfile.gettempdir()


@router.post("/chat")
async def voice_chat(request: Request):
    pcm = await request.body()
    if len(pcm) < 16000 * 2:
        return Response(content=b"", status_code=400)

    # 保存调试录音
    dbg_path = os.path.join(_debug_dir, "last_voice.pcm")
    with open(dbg_path, "wb") as f:
        f.write(pcm)
    print(f"[voice] Saved {len(pcm)} bytes to {dbg_path}")

    # PCM → numpy。ESP32 是小端，试试大端字节序
    samples_le = np.frombuffer(pcm, dtype=np.int16).astype(np.float32) / 32768.0
    samples_be = np.frombuffer(pcm, dtype=np.dtype('>i2')).astype(np.float32) / 32768.0
    # 用小端（正常）
    samples = samples_le
    print(f"[voice] Samples: {len(samples)}, max={samples.max():.4f}, min={samples.min():.4f}")
    # 同时保存 WAV 方便调试
    wav_dbg = dbg_path.replace(".pcm", ".wav")
    import wave as _wv
    with _wv.open(wav_dbg, "wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(16000)
        wf.writeframes(pcm)
    print(f"[voice] Debug WAV: {wav_dbg}")

    # Whisper — 直接喂 WAV 文件路径
    text = ""
    if _whisper_model is not None:
        try:
            result = _whisper_model.transcribe(wav_dbg, language="zh", fp16=False)
            text = result["text"].strip()
            print(f"[voice] STT: '{text}'")
        except Exception as e:
            print(f"[voice] Whisper error: {e}")
            # 回退：尝试 numpy 数组
            try:
                result = _whisper_model.transcribe(samples, language="zh", fp16=False)
                text = result["text"].strip()
                print(f"[voice] STT-fallback: '{text}'")
            except Exception as e2:
                print(f"[voice] Whisper fallback error: {e2}")
                return Response(content=b"", status_code=500)
    else:
        return Response(content=b"", status_code=500)

    if not text:
        print("[voice] Empty STT - no speech detected")
        return Response(content=b"", status_code=200)

    # 唤醒词
    is_wake = any(w in text for w in WAKE_WORDS)
    if not is_wake:
        print(f"[voice] No wake word in: '{text}'")
        return Response(content=b"", status_code=200)

    question = text
    for w in WAKE_WORDS:
        question = question.replace(w, "").strip()
    if not question:
        question = "你好"

    print(f"[voice] Question: '{question}'")

    # DeepSeek
    reply = await _ask_llm(question)
    print(f"[voice] Reply: '{reply}'")

    # TTS
    wav_bytes = await _tts_edge(reply)
    if wav_bytes:
        return Response(content=wav_bytes, media_type="audio/wav")
    return Response(content=b"", status_code=200)


async def _ask_llm(question: str) -> str:
    client = _build_llm()
    try:
        resp = await client.chat.completions.create(
            model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
            messages=[
                {"role": "system", "content": "你是桌面助手，回答简洁口语化，50字以内，像朋友。"},
                {"role": "user", "content": question},
            ],
            temperature=0.7,
            max_tokens=150,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        print(f"[voice] LLM: {e}")
        return "抱歉，我现在有点反应不过来。"


async def _tts_edge(text: str) -> bytes | None:
    try:
        import edge_tts
        wav_path = tempfile.mktemp(suffix=".wav")
        communicate = edge_tts.Communicate(text, "zh-CN-XiaoxiaoNeural")
        await communicate.save(wav_path)
        with open(wav_path, "rb") as f:
            data = f.read()
        os.unlink(wav_path)
        print(f"[voice] TTS: {len(data)} bytes")
        return data
    except Exception as e:
        print(f"[voice] TTS error: {e}")
        return None
