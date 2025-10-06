#!/usr/bin/env python3
"""
播客音频生成测试脚本
"""

import asyncio
import os
import sys
sys.path.append('.')

from app.services.podcast_audio import podcast_audio_generator
from app.models.schema import PodcastScript
from app.utils import utils


async def test_podcast_audio_generation():
    """测试播客音频生成"""
    print("=== 播客音频生成测试 ===")

    # 创建测试用的播客脚本
    test_script = [
        PodcastScript(
            speaker_1="大家好，欢迎收听今天的科技播客。我是主持人小雪。",
            speaker_2="你好，我是小云。今天我们要讨论人工智能的最新发展。",
            speaker_1_voice="zh-CN-XiaoxiaoNeural-Female",
            speaker_2_voice="zh-CN-YunxiNeural-Male"
        ),
        PodcastScript(
            speaker_1="确实，AI技术最近发展非常迅速。特别是大型语言模型的应用。",
            speaker_2="是的，从ChatGPT到各种专业领域的AI应用，正在改变我们的生活方式。",
            speaker_1_voice="zh-CN-XiaoxiaoNeural-Female",
            speaker_2_voice="zh-CN-YunxiNeural-Male"
        ),
        PodcastScript(
            speaker_1="你认为AI在未来五年会有什么样的发展？",
            speaker_2="我觉得AI会更加普及化，同时也会更加专业化和个性化。",
            speaker_1_voice="zh-CN-XiaoxiaoNeural-Female",
            speaker_2_voice="zh-CN-YunxiNeural-Male"
        )
    ]

    print(f"测试脚本包含 {len(test_script)} 轮对话")

    # 创建输出目录
    output_dir = utils.storage_dir("test_output")
    os.makedirs(output_dir, exist_ok=True)

    output_file = os.path.join(output_dir, "test_podcast.mp3")

    try:
        # 生成播客音频
        print(f"开始生成播客音频...")
        audio_path, duration = await podcast_audio_generator.generate_podcast_audio(
            podcast_script=test_script,
            output_path=output_file,
            voice_rate=1.0,
            voice_volume=1.0
        )

        print(f"✅ 播客音频生成成功！")
        print(f"📁 文件路径: {audio_path}")
        print(f"⏱️  音频时长: {duration:.2f}秒")
        print(f"📏 文件大小: {os.path.getsize(audio_path) / 1024:.2f}KB")

        # 检查文件是否存在
        if os.path.exists(audio_path):
            print("✅ 音频文件已成功创建")
        else:
            print("❌ 音频文件未找到")

    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()


async def test_single_speaker_audio():
    """测试单说话人音频生成"""
    print("\n=== 单说话人音频生成测试 ===")

    text = "这是一个单说话人音频测试，用于验证系统的基本功能。"
    voice_name = "zh-CN-XiaoxiaoNeural-Female"

    output_dir = utils.storage_dir("test_output")
    os.makedirs(output_dir, exist_ok=True)

    output_file = os.path.join(output_dir, "test_single_speaker.mp3")

    try:
        print(f"开始生成单说话人音频...")
        audio_path, duration = await podcast_audio_generator.generate_single_speaker_audio(
            text=text,
            voice_name=voice_name,
            output_path=output_file,
            voice_rate=1.0,
            voice_volume=1.0
        )

        print(f"✅ 单说话人音频生成成功！")
        print(f"📁 文件路径: {audio_path}")
        print(f"⏱️  音频时长: {duration:.2f}秒")
        print(f"📏 文件大小: {os.path.getsize(audio_path) / 1024:.2f}KB")

    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()


async def test_voice_validation():
    """测试音色验证功能"""
    print("\n=== 音色验证测试 ===")

    # 测试推荐的音色配对
    recommended_pairs = podcast_audio_generator.get_recommended_voice_pairs()
    print(f"推荐的音色配对数量: {len(recommended_pairs)}")

    for i, (voice1, voice2) in enumerate(recommended_pairs[:3]):  # 只显示前3个
        is_valid = podcast_audio_generator.validate_voice_names(voice1, voice2)
        print(f"配对 {i+1}: {voice1} + {voice2} -> {'✅ 有效' if is_valid else '❌ 无效'}")

    # 测试无效音色
    invalid_pair = ("invalid_voice_1", "invalid_voice_2")
    is_valid = podcast_audio_generator.validate_voice_names(*invalid_pair)
    print(f"无效配对: {invalid_pair} -> {'✅ 有效' if is_valid else '❌ 无效'}")


async def main():
    """主测试函数"""
    print("🎙️  播客音频生成系统测试")
    print("=" * 50)

    # 创建必要的目录
    temp_dir = utils.storage_dir("temp")
    os.makedirs(temp_dir, exist_ok=True)

    # 运行测试
    await test_voice_validation()
    await test_single_speaker_audio()
    await test_podcast_audio_generation()

    print("\n" + "=" * 50)
    print("🏁 测试完成")


if __name__ == "__main__":
    # 运行测试
    asyncio.run(main())