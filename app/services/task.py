import asyncio
import math
import os
import os.path
import re
from os import path

from loguru import logger

from app.config import config
from app.models import const
from app.models.schema import VideoConcatMode, VideoParams
from app.services import llm, material, subtitle, video, voice
from app.services import podcast_audio
from app.services import state as sm
from app.utils import utils


def generate_script(task_id, params):
    logger.info("\n\n## generating video script")

    # 检查是否是播客模式
    if hasattr(params, 'podcast_mode') and params.podcast_mode:
        logger.info("Using podcast mode for script generation")
        podcast_script = generate_podcast_script(task_id, params)
        if podcast_script:
            # 将播客脚本转换为字符串格式，保持向后兼容
            return podcast_script
        return None

    # 传统模式
    video_script = getattr(params, 'video_script', '').strip()
    if not video_script:
        video_script = llm.generate_script(
            video_subject=getattr(params, 'video_subject', ''),
            language=params.video_language,
            paragraph_number=params.paragraph_number,
        )
    else:
        logger.debug(f"video script: \n{video_script}")

    if not video_script:
        sm.state.update_task(task_id, state=const.TASK_STATE_FAILED)
        logger.error("failed to generate video script.")
        return None

    return video_script


def generate_podcast_script(task_id, params):
    """生成播客脚本"""
    logger.info("\n\n## generating podcast script")

    # 检查是否有播客脚本
    if params.podcast_script:
        logger.debug(f"using existing podcast script: {len(params.podcast_script)} turns")
        return params.podcast_script

    # 从文章生成播客脚本
    if params.article_text:
        podcast_script = llm.generate_podcast_script(
            article_text=params.article_text,
            language=params.video_language
        )

        if not podcast_script:
            sm.state.update_task(task_id, state=const.TASK_STATE_FAILED)
            logger.error("failed to generate podcast script.")
            return None

        logger.debug(f"generated podcast script: {len(podcast_script)} turns")
        return podcast_script

    sm.state.update_task(task_id, state=const.TASK_STATE_FAILED)
    logger.error("no article text provided for podcast mode.")
    return None


def generate_terms(task_id, params, video_script):
    logger.info("\n\n## generating video terms")

    # 检查是否是播客模式
    if hasattr(params, 'podcast_mode') and params.podcast_mode:
        logger.info("Using podcast mode for terms generation")
        return generate_podcast_terms(task_id, params, video_script)

    # 传统模式
    video_terms = params.video_terms
    if not video_terms:
        video_terms = llm.generate_terms(
            video_subject=params.video_subject, video_script=video_script, amount=5
        )
    else:
        if isinstance(video_terms, str):
            video_terms = [term.strip() for term in re.split(r"[,，]", video_terms)]
        elif isinstance(video_terms, list):
            video_terms = [term.strip() for term in video_terms]
        else:
            raise ValueError("video_terms must be a string or a list of strings.")

        logger.debug(f"video terms: {utils.to_json(video_terms)}")

    if not video_terms:
        sm.state.update_task(task_id, state=const.TASK_STATE_FAILED)
        logger.error("failed to generate video terms.")
        return None

    return video_terms


def generate_podcast_terms(task_id, params, podcast_script):
    """从播客脚本生成搜索词"""
    logger.info("\n\n## generating podcast search terms")

    # 使用播客脚本生成搜索词
    video_terms = llm.generate_terms_from_podcast(
        podcast_script=podcast_script,
        amount=5
    )

    if not video_terms:
        sm.state.update_task(task_id, state=const.TASK_STATE_FAILED)
        logger.error("failed to generate podcast search terms.")
        return None

    logger.debug(f"podcast search terms: {utils.to_json(video_terms)}")
    return video_terms


def save_script_data(task_id, video_script, video_terms, params):
    script_file = path.join(utils.task_dir(task_id), "script.json")

    # 检查是否是播客模式
    if hasattr(params, 'podcast_mode') and params.podcast_mode:
        script_data = {
            "podcast_script": video_script,  # 在播客模式下，video_script其实是podcast_script
            "search_terms": video_terms,
            "params": params,
            "mode": "podcast"
        }
    else:
        script_data = {
            "script": video_script,
            "search_terms": video_terms,
            "params": params,
            "mode": "traditional"
        }

    with open(script_file, "w", encoding="utf-8") as f:
        f.write(utils.to_json(script_data))


def generate_audio(task_id, params, video_script):
    logger.info("\n\n## generating audio")

    # 检查是否是播客模式
    if hasattr(params, 'podcast_mode') and params.podcast_mode:
        logger.info("Using podcast mode for audio generation")
        return generate_podcast_audio(task_id, params, video_script)

    # 传统模式
    audio_file = path.join(utils.task_dir(task_id), "audio.mp3")
    sub_maker = voice.tts(
        text=video_script,
        voice_name=voice.parse_voice_name(params.voice_name),
        voice_rate=params.voice_rate,
        voice_file=audio_file,
    )
    if sub_maker is None:
        sm.state.update_task(task_id, state=const.TASK_STATE_FAILED)
        logger.error(
            """failed to generate audio:
1. check if the language of the voice matches the language of the video script.
2. check if the network is available. If you are in China, it is recommended to use a VPN and enable the global traffic mode.
        """.strip()
        )
        return None, None, None

    audio_duration = math.ceil(voice.get_audio_duration(sub_maker))
    return audio_file, audio_duration, sub_maker


def generate_podcast_audio(task_id, params, podcast_script):
    """生成播客音频"""
    logger.info("\n\n## generating podcast audio")

    audio_file = path.join(utils.task_dir(task_id), "audio.mp3")

    try:
        # 使用播客音频生成器
        audio_path, audio_duration = asyncio.run(podcast_audio.podcast_audio_generator.generate_podcast_audio(
            podcast_script=podcast_script,
            output_path=audio_file,
            voice_rate=getattr(params, 'voice_rate', 1.0),
            voice_volume=getattr(params, 'voice_volume', 1.0)
        ))

        if not audio_path or not os.path.exists(audio_path):
            sm.state.update_task(task_id, state=const.TASK_STATE_FAILED)
            logger.error("failed to generate podcast audio file.")
            return None, None, None

        logger.info(f"podcast audio generated: {audio_path}, duration: {audio_duration}s")
        return audio_path, audio_duration, None  # 播客模式不需要sub_maker

    except Exception as e:
        sm.state.update_task(task_id, state=const.TASK_STATE_FAILED)
        logger.error(f"failed to generate podcast audio: {str(e)}")
        return None, None, None


def generate_subtitle(task_id, params, video_script, sub_maker, audio_file):
    if not params.subtitle_enabled:
        return ""

    subtitle_path = path.join(utils.task_dir(task_id), "subtitle.srt")
    subtitle_provider = config.app.get("subtitle_provider", "edge").strip().lower()
    logger.info(f"\n\n## generating subtitle, provider: {subtitle_provider}")

    # 检查是否是播客模式
    if hasattr(params, 'podcast_mode') and params.podcast_mode:
        logger.info("Using podcast mode for subtitle generation")
        return generate_podcast_subtitle(task_id, params, video_script, audio_file, subtitle_path)

    # 传统模式
    subtitle_fallback = False
    if subtitle_provider == "edge":
        voice.create_subtitle(
            text=video_script, sub_maker=sub_maker, subtitle_file=subtitle_path
        )
        if not os.path.exists(subtitle_path):
            subtitle_fallback = True
            logger.warning("subtitle file not found, fallback to whisper")

    if subtitle_provider == "whisper" or subtitle_fallback:
        subtitle.create(audio_file=audio_file, subtitle_file=subtitle_path)
        logger.info("\n\n## correcting subtitle")
        subtitle.correct(subtitle_file=subtitle_path, video_script=video_script)

    subtitle_lines = subtitle.file_to_subtitles(subtitle_path)
    if not subtitle_lines:
        logger.warning(f"subtitle file is invalid: {subtitle_path}")
        return ""

    return subtitle_path


def generate_podcast_subtitle(task_id, params, podcast_script, audio_file, subtitle_path):
    """生成播客字幕"""
    logger.info("\n\n## generating podcast subtitle")

    try:
        # 获取字幕提供者配置
        subtitle_provider = config.app.get("subtitle_provider", "edge").strip().lower()
        logger.info(f"podcast subtitle provider: {subtitle_provider}")

        # 根据配置选择字幕生成方式
        subtitle_fallback = False
        if subtitle_provider == "edge":
            # 为播客创建简单字幕文件
            logger.info("generating podcast subtitle from script")
            try:
                # 创建基本字幕文件，将对话按行分配时间
                with open(subtitle_path, "w", encoding="utf-8") as f:
                    idx = 1
                    current_time = 0.0

                    for i, turn in enumerate(podcast_script):
                        logger.info(f"processing dialogue turn {i+1}")

                        # 处理说话人1
                        if turn.speaker_1.strip():
                            speaker1_text = turn.speaker_1.strip()
                            duration = max(len(speaker1_text) * 0.1, 2.0)  # 估算每个字符0.1秒，最少2秒
                            start_time = current_time
                            end_time = current_time + duration

                            # 格式化为SRT时间格式
                            start_str = utils.time_convert_seconds_to_hmsm(start_time).replace(".", ",")
                            end_str = utils.time_convert_seconds_to_hmsm(end_time).replace(".", ",")

                            logger.debug(f"Speaker 1: {start_str} --> {end_str}, text: {speaker1_text[:50]}...")

                            f.write(f"{idx}\n")
                            f.write(f"{start_str} --> {end_str}\n")
                            f.write(f"[说话人1] {speaker1_text}\n\n")

                            idx += 1
                            current_time = end_time + 1.0  # 添加1秒停顿

                        # 处理说话人2
                        if turn.speaker_2.strip():
                            speaker2_text = turn.speaker_2.strip()
                            duration = max(len(speaker2_text) * 0.1, 2.0)
                            start_time = current_time
                            end_time = current_time + duration

                            start_str = utils.time_convert_seconds_to_hmsm(start_time).replace(".", ",")
                            end_str = utils.time_convert_seconds_to_hmsm(end_time).replace(".", ",")

                            logger.debug(f"Speaker 2: {start_str} --> {end_str}, text: {speaker2_text[:50]}...")

                            f.write(f"{idx}\n")
                            f.write(f"{start_str} --> {end_str}\n")
                            f.write(f"[说话人2] {speaker2_text}\n\n")

                            idx += 1
                            current_time = end_time + 1.0

                logger.info(f"basic podcast subtitle created successfully: {subtitle_path} with {idx-1} entries")

                # 验证文件是否创建成功
                if os.path.exists(subtitle_path) and os.path.getsize(subtitle_path) > 0:
                    logger.info("subtitle file validation passed")
                    subtitle_fallback = False  # 确保不回退到Whisper
                else:
                    logger.warning("subtitle file validation failed, will fallback to whisper")
                    subtitle_fallback = True

            except Exception as e:
                logger.error(f"failed to create basic subtitle: {str(e)}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                subtitle_fallback = True

        if subtitle_provider == "whisper" or subtitle_fallback:
            # 使用Whisper从音频生成字幕
            logger.info("generating podcast subtitle from audio using Whisper")
            subtitle.create(audio_file=audio_file, subtitle_file=subtitle_path)
            if not os.path.exists(subtitle_path):
                logger.error("failed to generate subtitle with whisper")
                return ""

        # 如果使用Edge TTS生成的字幕，跳过校正步骤，因为字幕已经从脚本生成
        if subtitle_provider == "edge" and not subtitle_fallback:
            logger.info("skipping subtitle correction for edge-generated subtitles")
            enhanced_subtitle_path = subtitle_path
        else:
            # 生成完整的播客文本用于字幕校正
            full_podcast_text = ""
            for i, turn in enumerate(podcast_script):
                full_podcast_text += f"说话人1: {turn.speaker_1}\n"
                full_podcast_text += f"说话人2: {turn.speaker_2}\n"

            # 校正字幕
            logger.info("\n\n## correcting podcast subtitle")
            subtitle.correct(subtitle_file=subtitle_path, video_script=full_podcast_text)

            # 增强播客字幕：添加说话人标识
            enhanced_subtitle_path = enhance_podcast_subtitle(
                subtitle_path, podcast_script, task_id
            )

        subtitle_lines = subtitle.file_to_subtitles(enhanced_subtitle_path)
        if not subtitle_lines:
            logger.warning(f"podcast subtitle file is invalid: {enhanced_subtitle_path}")
            return ""

        logger.info(f"podcast subtitle generated: {len(subtitle_lines)} lines")
        return enhanced_subtitle_path

    except Exception as e:
        logger.error(f"failed to generate podcast subtitle: {str(e)}")
        return ""


def enhance_podcast_subtitle(original_subtitle_path, podcast_script, task_id):
    """增强播客字幕，添加说话人标识"""
    logger.info("\n\n## enhancing podcast subtitle with speaker labels")

    try:
        # 读取原始字幕
        subtitle_lines = subtitle.file_to_subtitles(original_subtitle_path)
        if not subtitle_lines:
            return original_subtitle_path

        enhanced_lines = []
        current_speaker = None
        script_index = 0

        for idx, (line_num, time_range, text) in enumerate(subtitle_lines):
            enhanced_text = text

            # 基于文本内容推断说话人
            detected_speaker = detect_speaker_from_text(text, podcast_script, script_index)

            if detected_speaker and detected_speaker != current_speaker:
                enhanced_text = f"[{detected_speaker}] {text}"
                current_speaker = detected_speaker

            enhanced_lines.append((line_num, time_range, enhanced_text))

        # 保存增强的字幕
        enhanced_subtitle_path = path.join(utils.task_dir(task_id), "subtitle_enhanced.srt")

        with open(enhanced_subtitle_path, "w", encoding="utf-8") as f:
            for line_num, time_range, text in enhanced_lines:
                f.write(f"{line_num}\n{time_range}\n{text}\n\n")

        logger.info(f"enhanced subtitle saved: {enhanced_subtitle_path}")
        return enhanced_subtitle_path

    except Exception as e:
        logger.error(f"failed to enhance podcast subtitle: {str(e)}")
        return original_subtitle_path


def detect_speaker_from_text(text, podcast_script, current_script_index):
    """基于文本内容和播客脚本推断说话人"""
    try:
        if not podcast_script or current_script_index >= len(podcast_script):
            return None

        current_turn = podcast_script[current_script_index]
        text_lower = text.lower().strip()

        # 简单的关键词匹配来推断说话人
        speaker1_text = current_turn.speaker_1.lower()
        speaker2_text = current_turn.speaker_2.lower()

        # 计算文本相似度
        words_text = set(text_lower.split())
        words_s1 = set(speaker1_text.split())
        words_s2 = set(speaker2_text.split())

        similarity_s1 = len(words_text.intersection(words_s1)) / max(len(words_text), 1)
        similarity_s2 = len(words_text.intersection(words_s2)) / max(len(words_text), 1)

        if similarity_s1 > similarity_s2 and similarity_s1 > 0.3:
            return "说话人1"
        elif similarity_s2 > similarity_s1 and similarity_s2 > 0.3:
            return "说话人2"

        return None

    except Exception as e:
        logger.warning(f"failed to detect speaker: {str(e)}")
        return None


def get_video_materials(task_id, params, video_terms, audio_duration):
    if params.video_source == "local":
        logger.info("\n\n## preprocess local materials")
        materials = video.preprocess_video(
            materials=params.video_materials, clip_duration=params.video_clip_duration
        )
        if not materials:
            sm.state.update_task(task_id, state=const.TASK_STATE_FAILED)
            logger.error(
                "no valid materials found, please check the materials and try again."
            )
            return None
        return [material_info.url for material_info in materials]
    else:
        logger.info(f"\n\n## downloading videos from {params.video_source}")

        # 检查是否是播客模式
        is_podcast_mode = hasattr(params, 'podcast_mode') and params.podcast_mode

        downloaded_videos = material.download_videos(
            task_id=task_id,
            search_terms=video_terms,
            source=params.video_source,
            video_aspect=params.video_aspect,
            video_contact_mode=params.video_concat_mode,
            audio_duration=audio_duration * params.video_count,
            max_clip_duration=params.video_clip_duration,
            is_podcast_mode=is_podcast_mode,
        )
        if not downloaded_videos:
            sm.state.update_task(task_id, state=const.TASK_STATE_FAILED)
            logger.error(
                "failed to download videos, maybe the network is not available. if you are in China, please use a VPN."
            )
            return None
        return downloaded_videos


def generate_final_videos(
    task_id, params, downloaded_videos, audio_file, subtitle_path
):
    final_video_paths = []
    combined_video_paths = []
    video_concat_mode = (
        params.video_concat_mode if params.video_count == 1 else VideoConcatMode.random
    )
    video_transition_mode = params.video_transition_mode

    _progress = 50
    for i in range(params.video_count):
        index = i + 1
        combined_video_path = path.join(
            utils.task_dir(task_id), f"combined-{index}.mp4"
        )
        logger.info(f"\n\n## combining video: {index} => {combined_video_path}")
        video.combine_videos(
            combined_video_path=combined_video_path,
            video_paths=downloaded_videos,
            audio_file=audio_file,
            video_aspect=params.video_aspect,
            video_concat_mode=video_concat_mode,
            video_transition_mode=video_transition_mode,
            max_clip_duration=params.video_clip_duration,
            threads=params.n_threads,
        )

        _progress += 50 / params.video_count / 2
        sm.state.update_task(task_id, progress=_progress)

        final_video_path = path.join(utils.task_dir(task_id), f"final-{index}.mp4")

        logger.info(f"\n\n## generating video: {index} => {final_video_path}")
        video.generate_video(
            video_path=combined_video_path,
            audio_path=audio_file,
            subtitle_path=subtitle_path,
            output_file=final_video_path,
            params=params,
        )

        _progress += 50 / params.video_count / 2
        sm.state.update_task(task_id, progress=_progress)

        final_video_paths.append(final_video_path)
        combined_video_paths.append(combined_video_path)

    return final_video_paths, combined_video_paths


def start(task_id, params: VideoParams, stop_at: str = "video"):
    logger.info(f"start task: {task_id}, stop_at: {stop_at}")
    sm.state.update_task(task_id, state=const.TASK_STATE_PROCESSING, progress=5)

    if type(params.video_concat_mode) is str:
        params.video_concat_mode = VideoConcatMode(params.video_concat_mode)

    # 检查是否是播客模式
    is_podcast_mode = hasattr(params, 'podcast_mode') and params.podcast_mode
    if is_podcast_mode:
        logger.info("Starting task in PODCAST mode")
        params.podcast_mode = True
    else:
        logger.info("Starting task in TRADITIONAL mode")

    # 1. Generate script
    video_script = generate_script(task_id, params)
    if not video_script or (isinstance(video_script, str) and "Error: " in video_script):
        sm.state.update_task(task_id, state=const.TASK_STATE_FAILED)
        return

    sm.state.update_task(task_id, state=const.TASK_STATE_PROCESSING, progress=10)

    if stop_at == "script":
        script_data = {"podcast_script": video_script} if is_podcast_mode else {"script": video_script}
        sm.state.update_task(
            task_id, state=const.TASK_STATE_COMPLETE, progress=100, **script_data
        )
        return script_data

    # 2. Generate terms
    video_terms = ""
    if params.video_source != "local":
        video_terms = generate_terms(task_id, params, video_script)
        if not video_terms:
            sm.state.update_task(task_id, state=const.TASK_STATE_FAILED)
            return

    save_script_data(task_id, video_script, video_terms, params)

    if stop_at == "terms":
        sm.state.update_task(
            task_id, state=const.TASK_STATE_COMPLETE, progress=100, terms=video_terms
        )
        return {"podcast_script" if is_podcast_mode else "script": video_script, "terms": video_terms}

    sm.state.update_task(task_id, state=const.TASK_STATE_PROCESSING, progress=20)

    # 3. Generate audio
    audio_file, audio_duration, sub_maker = generate_audio(
        task_id, params, video_script
    )
    if not audio_file:
        sm.state.update_task(task_id, state=const.TASK_STATE_FAILED)
        return

    sm.state.update_task(task_id, state=const.TASK_STATE_PROCESSING, progress=30)

    if stop_at == "audio":
        sm.state.update_task(
            task_id,
            state=const.TASK_STATE_COMPLETE,
            progress=100,
            audio_file=audio_file,
            audio_duration=audio_duration,
        )
        return {"audio_file": audio_file, "audio_duration": audio_duration}

    # 4. Generate subtitle
    subtitle_path = generate_subtitle(
        task_id, params, video_script, sub_maker, audio_file
    )

    if stop_at == "subtitle":
        sm.state.update_task(
            task_id,
            state=const.TASK_STATE_COMPLETE,
            progress=100,
            subtitle_path=subtitle_path,
        )
        return {"subtitle_path": subtitle_path}

    sm.state.update_task(task_id, state=const.TASK_STATE_PROCESSING, progress=40)

    # 5. Get video materials
    downloaded_videos = get_video_materials(
        task_id, params, video_terms, audio_duration
    )
    if not downloaded_videos:
        sm.state.update_task(task_id, state=const.TASK_STATE_FAILED)
        return

    if stop_at == "materials":
        sm.state.update_task(
            task_id,
            state=const.TASK_STATE_COMPLETE,
            progress=100,
            materials=downloaded_videos,
        )
        return {"materials": downloaded_videos}

    sm.state.update_task(task_id, state=const.TASK_STATE_PROCESSING, progress=50)

    # 6. Generate final videos
    final_video_paths, combined_video_paths = generate_final_videos(
        task_id, params, downloaded_videos, audio_file, subtitle_path
    )

    if not final_video_paths:
        sm.state.update_task(task_id, state=const.TASK_STATE_FAILED)
        return

    logger.success(
        f"task {task_id} finished, generated {len(final_video_paths)} videos."
    )

    # 构建返回数据，适配播客模式
    kwargs = {
        "videos": final_video_paths,
        "combined_videos": combined_video_paths,
        "audio_file": audio_file,
        "audio_duration": audio_duration,
        "subtitle_path": subtitle_path,
        "materials": downloaded_videos,
    }

    if is_podcast_mode:
        kwargs["podcast_script"] = video_script
    else:
        kwargs["script"] = video_script

    kwargs["terms"] = video_terms

    sm.state.update_task(
        task_id, state=const.TASK_STATE_COMPLETE, progress=100, **kwargs
    )
    return kwargs


if __name__ == "__main__":
    task_id = "task_id"
    params = VideoParams(
        video_subject="金钱的作用",
        voice_name="zh-CN-XiaoyiNeural-Female",
        voice_rate=1.0,
    )
    start(task_id, params, stop_at="video")
