import asyncio
import os
import tempfile
import subprocess
from typing import List, Optional, Tuple
from loguru import logger
from app.models.schema import PodcastScript
from app.services.voice import tts, get_audio_duration
from app.config import config
from app.utils import utils


class PodcastAudioGenerator:
    """播客音频生成器"""

    def __init__(self):
        self.temp_dir = utils.storage_dir("temp")
        self.silence_duration = 500  # 语音间停顿时间（毫秒）
        self.default_voice_rate = 1.0
        self.default_voice_volume = 1.0

    async def generate_podcast_audio(
        self,
        podcast_script: List[PodcastScript],
        output_path: str,
        voice_rate: float = None,
        voice_volume: float = None
    ) -> Tuple[str, float]:
        """
        生成播客音频文件

        Args:
            podcast_script: 播客脚本列表
            output_path: 输出音频文件路径
            voice_rate: 语速
            voice_volume: 音量

        Returns:
            (音频文件路径, 音频时长)
        """
        if not podcast_script:
            raise ValueError("播客脚本不能为空")

        voice_rate = voice_rate or self.default_voice_rate
        voice_volume = voice_volume or self.default_voice_volume

        logger.info(f"开始生成播客音频，共 {len(podcast_script)} 轮对话")

        # 生成临时音频文件列表
        temp_audio_files = []

        try:
            # 为每轮对话生成音频
            for i, dialogue in enumerate(podcast_script):
                logger.info(f"正在生成第 {i+1} 轮对话音频...")

                # 生成说话人1的音频
                speaker1_audio = await self._generate_speaker_audio(
                    text=dialogue.speaker_1,
                    voice_name=dialogue.speaker_1_voice,
                    output_prefix=f"speaker1_{i}",
                    voice_rate=voice_rate,
                    voice_volume=voice_volume
                )

                # 生成说话人2的音频
                speaker2_audio = await self._generate_speaker_audio(
                    text=dialogue.speaker_2,
                    voice_name=dialogue.speaker_2_voice,
                    output_prefix=f"speaker2_{i}",
                    voice_rate=voice_rate,
                    voice_volume=voice_volume
                )

                # 合并当前轮对话的音频
                dialogue_audio = self._merge_dialogue_audio(speaker1_audio, speaker2_audio)
                temp_audio_files.append(dialogue_audio)

            # 合并所有对话音频
            final_audio_path = self._concatenate_all_audio(temp_audio_files)

            # 如果合并成功且文件存在，复制到目标路径
            if final_audio_path and os.path.exists(final_audio_path):
                import shutil
                shutil.copy2(final_audio_path, output_path)
            elif temp_audio_files and os.path.exists(temp_audio_files[0]):
                # 回退方案：使用第一个音频文件
                import shutil
                shutil.copy2(temp_audio_files[0], output_path)

            # 获取音频时长
            audio_duration = self._get_audio_file_duration(output_path)

            logger.success(f"播客音频生成完成: {output_path}, 时长: {audio_duration:.2f}秒")
            return output_path, audio_duration

        except Exception as e:
            logger.error(f"生成播客音频失败: {str(e)}")
            raise
        finally:
            # 清理临时文件
            self._cleanup_temp_files(temp_audio_files)

    async def _generate_speaker_audio(
        self,
        text: str,
        voice_name: str,
        output_prefix: str,
        voice_rate: float,
        voice_volume: float
    ) -> str:
        """
        生成单个说话人的音频

        Args:
            text: 文本内容
            voice_name: 语音名称
            output_prefix: 输出文件前缀
            voice_rate: 语速
            voice_volume: 音量

        Returns:
            音频文件路径
        """
        if not text.strip():
            logger.warning(f"文本为空，跳过生成: {output_prefix}")
            return ""

        output_file = os.path.join(self.temp_dir, f"{output_prefix}.mp3")

        # 确保目录存在
        os.makedirs(self.temp_dir, exist_ok=True)

        try:
            # 使用现有的tts服务生成音频
            sub_maker = await tts(
                text=text,
                voice_name=voice_name,
                voice_rate=voice_rate,
                voice_file=output_file,
                voice_volume=voice_volume
            )

            if sub_maker and os.path.exists(output_file):
                logger.info(f"成功生成音频: {output_file}")
                return output_file
            else:
                logger.error(f"音频生成失败: {output_file}")
                return ""

        except Exception as e:
            logger.error(f"生成音频时出错 {output_prefix}: {str(e)}")
            return ""

    def _merge_dialogue_audio(self, speaker1_audio: str, speaker2_audio: str) -> str:
        """
        合并两个说话人的音频（添加停顿）

        Args:
            speaker1_audio: 说话人1音频文件路径
            speaker2_audio: 说话人2音频文件路径

        Returns:
            合并后的音频文件路径
        """
        if not speaker1_audio and not speaker2_audio:
            return ""

        try:
            # 使用ffmpeg合并音频
            output_file = os.path.join(self.temp_dir, f"dialogue_{utils.timestamp()}.mp3")

            # 构建输入文件列表
            inputs = []
            if speaker1_audio and os.path.exists(speaker1_audio):
                inputs.append(speaker1_audio)
            if speaker2_audio and os.path.exists(speaker2_audio):
                inputs.append(speaker2_audio)

            if not inputs:
                return ""

            # 使用ffmpeg concatenate demuxer合并音频
            # 首先创建文件列表
            list_file = os.path.join(self.temp_dir, f"concat_list_{utils.timestamp()}.txt")
            with open(list_file, 'w', encoding='utf-8') as f:
                for input_file in inputs:
                    f.write(f"file '{input_file}'\n")
                    # 添加静音
                    f.write(f"duration {self.silence_duration / 1000}\n")

            # 使用ffmpeg合并
            cmd = [
                'ffmpeg', '-y', '-f', 'concat', '-safe', '0',
                '-i', list_file, '-c', 'copy', output_file
            ]

            try:
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                logger.info(f"对话音频合并完成: {output_file}")
                return output_file
            except subprocess.CalledProcessError as e:
                logger.error(f"ffmpeg合并失败: {e.stderr}")
                # 回退方案：只返回第一个音频文件
                return inputs[0] if inputs else ""
            except FileNotFoundError:
                logger.warning("ffmpeg未找到，使用简单合并方式")
                # 回退方案：只返回第一个音频文件
                return inputs[0] if inputs else ""
            finally:
                # 清理临时文件
                try:
                    os.remove(list_file)
                except:
                    pass

        except Exception as e:
            logger.error(f"合并对话音频失败: {str(e)}")
            return ""

    def _concatenate_all_audio(self, audio_files: List[str]) -> str:
        """
        拼接所有音频文件

        Args:
            audio_files: 音频文件路径列表

        Returns:
            拼接后的音频文件路径
        """
        # 过滤有效的音频文件
        valid_files = [f for f in audio_files if f and os.path.exists(f)]

        if not valid_files:
            return ""

        if len(valid_files) == 1:
            return valid_files[0]

        try:
            output_file = os.path.join(self.temp_dir, f"final_audio_{utils.timestamp()}.mp3")

            # 使用ffmpeg concatenate demuxer
            list_file = os.path.join(self.temp_dir, f"final_concat_list_{utils.timestamp()}.txt")
            with open(list_file, 'w', encoding='utf-8') as f:
                for audio_file in valid_files:
                    f.write(f"file '{audio_file}'\n")
                    # 在每轮对话之间添加较长停顿
                    f.write(f"duration {self.silence_duration * 2 / 1000}\n")

            # 使用ffmpeg合并
            cmd = [
                'ffmpeg', '-y', '-f', 'concat', '-safe', '0',
                '-i', list_file, '-c', 'copy', output_file
            ]

            try:
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                logger.info(f"所有音频拼接完成: {output_file}")
                return output_file
            except subprocess.CalledProcessError as e:
                logger.error(f"ffmpeg拼接失败: {e.stderr}")
                # 回退方案：返回第一个文件
                return valid_files[0]
            except FileNotFoundError:
                logger.warning("ffmpeg未找到，返回第一个音频文件")
                return valid_files[0]
            finally:
                # 清理临时文件
                try:
                    os.remove(list_file)
                except:
                    pass

        except Exception as e:
            logger.error(f"拼接音频文件失败: {str(e)}")
            return valid_files[0] if valid_files else ""

    def _get_audio_file_duration(self, audio_file: str) -> float:
        """
        获取音频文件时长

        Args:
            audio_file: 音频文件路径

        Returns:
            音频时长（秒）
        """
        if not audio_file or not os.path.exists(audio_file):
            return 0.0

        try:
            # 使用ffprobe获取音频时长
            cmd = [
                'ffprobe', '-v', 'quiet', '-show_entries',
                'format=duration', '-of', 'csv=p=0', audio_file
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            duration = float(result.stdout.strip())
            return duration
        except (subprocess.CalledProcessError, FileNotFoundError, ValueError):
            # 如果ffprobe不可用，使用moviepy
            try:
                from moviepy import AudioFileClip
                audio_clip = AudioFileClip(audio_file)
                duration = audio_clip.duration
                audio_clip.close()
                return duration
            except Exception:
                # 如果都不可用，返回估算值
                logger.warning(f"无法获取音频时长: {audio_file}")
                return 0.0

    def _cleanup_temp_files(self, temp_files: List[str]):
        """
        清理临时文件

        Args:
            temp_files: 临时文件路径列表
        """
        for temp_file in temp_files:
            try:
                if temp_file and os.path.exists(temp_file):
                    os.remove(temp_file)
                    logger.debug(f"已删除临时文件: {temp_file}")
            except Exception as e:
                logger.warning(f"删除临时文件失败 {temp_file}: {str(e)}")

    async def generate_single_speaker_audio(
        self,
        text: str,
        voice_name: str,
        output_path: str,
        voice_rate: float = None,
        voice_volume: float = None
    ) -> Tuple[str, float]:
        """
        生成单说话人音频（用于兼容性）

        Args:
            text: 文本内容
            voice_name: 语音名称
            output_path: 输出文件路径
            voice_rate: 语速
            voice_volume: 音量

        Returns:
            (音频文件路径, 音频时长)
        """
        voice_rate = voice_rate or self.default_voice_rate
        voice_volume = voice_volume or self.default_voice_volume

        logger.info(f"生成单说话人音频: {output_path}")

        # 确保输出目录存在
        output_dir = os.path.dirname(output_path)
        os.makedirs(output_dir, exist_ok=True)

        try:
            sub_maker = await tts(
                text=text,
                voice_name=voice_name,
                voice_rate=voice_rate,
                voice_file=output_path,
                voice_volume=voice_volume
            )

            if sub_maker and os.path.exists(output_path):
                # 获取音频时长
                duration = get_audio_duration(sub_maker)
                logger.success(f"单说话人音频生成完成: {output_path}, 时长: {duration:.2f}秒")
                return output_path, duration
            else:
                raise Exception("音频生成失败")

        except Exception as e:
            logger.error(f"生成单说话人音频失败: {str(e)}")
            raise

    def get_recommended_voice_pairs(self) -> List[Tuple[str, str]]:
        """
        获取推荐的音色配对

        Returns:
            推荐的音色配对列表 [(说话人1音色, 说话人2音色), ...]
        """
        # 中文推荐音色配对
        chinese_pairs = [
            ("zh-CN-XiaoxiaoNeural-Female", "zh-CN-YunxiNeural-Male"),
            ("zh-CN-XiaoyiNeural-Female", "zh-CN-YunyangNeural-Male"),
            ("zh-CN-XiaoxiaoMultilingualNeural-V2-Female", "zh-CN-YunxiNeural-Male"),
            ("zh-CN-XiaoyiNeural-Female", "zh-CN-YunjianNeural-Male"),
        ]

        # 英文推荐音色配对
        english_pairs = [
            ("en-US-AvaMultilingualNeural-Female", "en-US-BrianMultilingualNeural-Male"),
            ("en-US-EmmaMultilingualNeural-Female", "en-US-AndrewMultilingualNeural-Male"),
            ("en-US-JennyNeural-Female", "en-US-GuyNeural-Male"),
            ("en-US-AriaNeural-Female", "en-US-ChristopherNeural-Male"),
        ]

        return chinese_pairs + english_pairs

    def validate_voice_names(self, voice1: str, voice2: str) -> bool:
        """
        验证音色名称是否有效

        Args:
            voice1: 说话人1音色
            voice2: 说话人2音色

        Returns:
            是否有效
        """
        try:
            from app.services.voice import get_all_azure_voices, get_siliconflow_voices

            # 获取所有可用音色
            azure_voices = get_all_azure_voices()
            siliconflow_voices = get_siliconflow_voices()
            all_voices = azure_voices + siliconflow_voices

            # 检查音色是否存在
            voice1_valid = any(voice1 in v for v in all_voices)
            voice2_valid = any(voice2 in v for v in all_voices)

            return voice1_valid and voice2_valid

        except Exception as e:
            logger.error(f"验证音色名称失败: {str(e)}")
            return False


# 创建全局实例
podcast_audio_generator = PodcastAudioGenerator()