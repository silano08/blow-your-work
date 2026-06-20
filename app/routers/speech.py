import os
import tempfile
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

from app.speech_service import transcribe_file, transcribe_stream_from_bytes

router = APIRouter(prefix="/speech", tags=["speech"])

ALLOWED_EXTENSIONS = {".wav", ".mp3", ".ogg", ".flac", ".webm", ".m4a"}


@router.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """
    오디오 파일을 업로드하면 Azure Speech (ko-KR)로 텍스트 변환합니다.
    지원 형식: wav, mp3, ogg, flac, webm, m4a
    """
    ext = os.path.splitext(file.filename or "")[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"지원하지 않는 형식입니다. 지원: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    audio_bytes = await file.read()
    if len(audio_bytes) == 0:
        raise HTTPException(status_code=400, detail="빈 파일입니다.")

    # 임시 파일로 저장 후 인식
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        result = transcribe_file(tmp_path)
    finally:
        os.unlink(tmp_path)

    if not result["success"]:
        raise HTTPException(status_code=422, detail=result["error"])

    return JSONResponse({"text": result["text"], "duration_ms": result.get("duration_ms")})


@router.post("/transcribe-pcm")
async def transcribe_pcm(
    file: UploadFile = File(...),
    sample_rate: int = 16000,
):
    """
    Raw PCM(16bit mono) 바이트를 업로드하면 Azure Speech (ko-KR)로 텍스트 변환합니다.
    웹 브라우저 마이크 스트리밍에 적합합니다.
    """
    audio_bytes = await file.read()
    if len(audio_bytes) == 0:
        raise HTTPException(status_code=400, detail="빈 데이터입니다.")

    result = transcribe_stream_from_bytes(audio_bytes, sample_rate=sample_rate)

    if not result["success"]:
        raise HTTPException(status_code=422, detail=result["error"])

    return JSONResponse({"text": result["text"], "duration_ms": result.get("duration_ms")})
