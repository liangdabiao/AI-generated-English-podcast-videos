import warnings
from enum import Enum
from typing import Any, List, Optional, Union

import pydantic
from pydantic import BaseModel

warnings.filterwarnings("ignore", category=UserWarning, message="Field name.*shadows an attribute in parent.*")

class VideoConcatMode(str, Enum):
    random = "random"
    sequential = "sequential"

class VideoTransitionMode(str, Enum):
    none = None
    shuffle = "Shuffle"
    fade_in = "FadeIn"
    fade_out = "FadeOut"
    slide_in = "SlideIn"
    slide_out = "SlideOut"

class VideoAspect(str, Enum):
    landscape = "16:9"
    portrait = "9:16"
    square = "1:1"

    def to_resolution(self):
        if self == VideoAspect.landscape.value:
            return 1920, 1080
        elif self == VideoAspect.portrait.value:
            return 1080, 1920
        elif self == VideoAspect.square.value:
            return 1080, 1080
        return 1080, 1920

class _Config:
    arbitrary_types_allowed = True

@pydantic.dataclasses.dataclass(config=_Config)
class MaterialInfo:
    provider: str = "pexels"
    url: str = ""
    duration: int = 0

class PodcastScript(BaseModel):
    """播客对话脚本"""
    speaker_1: str
    speaker_2: str
    speaker_1_voice: str
    speaker_2_voice: str

class VideoParams(BaseModel):
    """专为播客视频设计的参数"""
    podcast_mode: bool = False  # 是否为播客模式
    article_text: str = ""
    podcast_script: Optional[List[PodcastScript]] = None
    video_terms: Optional[str | list] = None
    video_aspect: Optional[VideoAspect] = VideoAspect.portrait.value
    video_concat_mode: Optional[VideoConcatMode] = VideoConcatMode.random.value
    video_transition_mode: Optional[VideoTransitionMode] = None
    video_clip_duration: Optional[int] = 5
    video_count: Optional[int] = 1
    video_source: Optional[str] = "pexels"
    video_materials: Optional[List[MaterialInfo]] = None
    video_language: Optional[str] = ""
    speaker_1_voice: str = "zh-CN-XiaoxiaoNeural-Female"
    speaker_2_voice: str = "zh-CN-YunxiNeural-Male"
    voice_name: Optional[str] = ""
    voice_volume: Optional[float] = 1.0
    voice_rate: Optional[float] = 1.0
    bgm_type: Optional[str] = "random"
    bgm_file: Optional[str] = ""
    bgm_volume: Optional[float] = 0.2
    subtitle_enabled: Optional[bool] = True
    subtitle_position: Optional[str] = "bottom"
    custom_position: float = 70.0
    font_name: Optional[str] = "STHeitiMedium.ttc"
    text_fore_color: Optional[str] = "#FFFFFF"
    text_background_color: Union[bool, str] = True
    font_size: int = 60
    stroke_color: Optional[str] = "#000000"
    stroke_width: float = 1.5
    n_threads: Optional[int] = 2
    paragraph_number: Optional[int] = 1

class SubtitleRequest(BaseModel):
    podcast_script: Optional[List[PodcastScript]] = None
    video_script: str = ""
    video_language: Optional[str] = ""
    voice_name: Optional[str] = "zh-CN-XiaoxiaoNeural-Female"
    voice_volume: Optional[float] = 1.0
    voice_rate: Optional[float] = 1.2
    bgm_type: Optional[str] = "random"
    bgm_file: Optional[str] = ""
    bgm_volume: Optional[float] = 0.2
    subtitle_position: Optional[str] = "bottom"
    font_name: Optional[str] = "STHeitiMedium.ttc"
    text_fore_color: Optional[str] = "#FFFFFF"
    text_background_color: Union[bool, str] = True
    font_size: int = 60
    stroke_color: Optional[str] = "#000000"
    stroke_width: float = 1.5
    video_source: Optional[str] = "local"
    subtitle_enabled: Optional[str] = "true"

class AudioRequest(BaseModel):
    podcast_script: Optional[List[PodcastScript]] = None
    video_script: str = ""
    video_language: Optional[str] = ""
    voice_name: Optional[str] = "zh-CN-XiaoxiaoNeural-Female"
    voice_volume: Optional[float] = 1.0
    voice_rate: Optional[float] = 1.2
    bgm_type: Optional[str] = "random"
    bgm_file: Optional[str] = ""
    bgm_volume: Optional[float] = 0.2
    video_source: Optional[str] = "local"

class PodcastGenerateRequest(BaseModel):
    """播客生成请求"""
    article_text: str
    language: Optional[str] = ""
    speaker_1_voice: Optional[str] = "zh-CN-XiaoxiaoNeural-Female"
    speaker_2_voice: Optional[str] = "zh-CN-YunxiNeural-Male"

class VideoFromPodcastRequest(BaseModel):
    """基于播客生成视频的请求"""
    podcast_script: List[PodcastScript]
    audio_path: str
    video_params: VideoParams

class VideoScriptParams:
    article_text: Optional[str] = ""
    language: Optional[str] = ""
    speaker_1_voice: Optional[str] = "zh-CN-XiaoxiaoNeural-Female"
    speaker_2_voice: Optional[str] = "zh-CN-YunxiNeural-Male"

class VideoTermsParams:
    podcast_script: Optional[List[PodcastScript]] = None
    amount: Optional[int] = 5

class BaseResponse(BaseModel):
    status: int = 200
    message: Optional[str] = "success"
    data: Any = None

class TaskVideoRequest(VideoParams, BaseModel):
    pass

class TaskQueryRequest(BaseModel):
    pass

class VideoScriptRequest(VideoScriptParams, BaseModel):
    pass

class VideoTermsRequest(VideoTermsParams, BaseModel):
    pass

class TaskResponse(BaseResponse):
    class TaskResponseData(BaseModel):
        task_id: str
    data: TaskResponseData

class TaskQueryResponse(BaseResponse):
    pass

class TaskDeletionResponse(BaseResponse):
    pass

class VideoScriptResponse(BaseResponse):
    pass

class VideoTermsResponse(BaseResponse):
    pass

class PodcastGenerateResponse(BaseResponse):
    """播客生成响应"""
    pass

class BgmRetrieveResponse(BaseResponse):
    pass

class BgmUploadResponse(BaseResponse):
    pass
