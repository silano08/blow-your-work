import os
import azure.cognitiveservices.speech as speechsdk


def _get_speech_config() -> speechsdk.SpeechConfig:
    key = os.getenv("AZURE_SPEECH_KEY")
    region = os.getenv("AZURE_SPEECH_REGION", "koreacentral")
    if not key:
        raise ValueError("AZURE_SPEECH_KEY 환경변수가 설정되지 않았습니다.")
    config = speechsdk.SpeechConfig(subscription=key, region=region)
    config.speech_recognition_language = "ko-KR"
    # 한국어 인식률 향상 옵션
    config.set_property(
        speechsdk.PropertyId.SpeechServiceConnection_EndSilenceTimeoutMs, "2000"
    )
    config.set_property(
        speechsdk.PropertyId.SpeechServiceResponse_ProfanityOption, "raw"
    )
    return config


def transcribe_file(audio_path: str) -> dict:
    """업로드된 오디오 파일을 한국어로 음성인식합니다."""
    config = _get_speech_config()
    audio_config = speechsdk.audio.AudioConfig(filename=audio_path)
    recognizer = speechsdk.SpeechRecognizer(
        speech_config=config, audio_config=audio_config
    )
    result = recognizer.recognize_once_async().get()

    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        return {"success": True, "text": result.text, "duration_ms": result.duration // 10000}
    elif result.reason == speechsdk.ResultReason.NoMatch:
        return {"success": False, "text": "", "error": "음성을 인식하지 못했습니다."}
    else:
        cancellation = speechsdk.CancellationDetails.from_result(result)
        return {"success": False, "text": "", "error": f"인식 실패: {cancellation.reason} / {cancellation.error_details}"}


def transcribe_stream_from_bytes(audio_bytes: bytes, sample_rate: int = 16000) -> dict:
    """PCM bytes를 직접 받아 한국어로 음성인식합니다 (마이크 스트리밍용)."""
    config = _get_speech_config()
    stream = speechsdk.audio.PushAudioInputStream(
        speechsdk.audio.AudioStreamFormat.get_wave_format_pcm(sample_rate, 16, 1)
    )
    stream.write(audio_bytes)
    stream.close()
    audio_config = speechsdk.audio.AudioConfig(stream=stream)
    recognizer = speechsdk.SpeechRecognizer(
        speech_config=config, audio_config=audio_config
    )
    result = recognizer.recognize_once_async().get()

    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        return {"success": True, "text": result.text, "duration_ms": result.duration // 10000}
    elif result.reason == speechsdk.ResultReason.NoMatch:
        return {"success": False, "text": "", "error": "음성을 인식하지 못했습니다."}
    else:
        cancellation = speechsdk.CancellationDetails.from_result(result)
        return {"success": False, "text": "", "error": f"인식 실패: {cancellation.reason} / {cancellation.error_details}"}
