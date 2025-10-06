#!/usr/bin/env python3
"""
Phase 3 UI改造测试脚本
测试Streamlit界面的播客视频生成功能
"""

import asyncio
import os
import sys
import subprocess
import time
import requests
from typing import Dict, Any

# 添加项目根目录到Python路径
root_dir = os.path.dirname(os.path.abspath(__file__))
if root_dir not in sys.path:
    sys.path.append(root_dir)

def test_streamlit_import():
    """测试Streamlit导入"""
    print("🔍 测试Streamlit导入...")
    try:
        import streamlit as st
        print("✅ Streamlit导入成功")
        return True
    except ImportError as e:
        print(f"❌ Streamlit导入失败: {e}")
        return False

def test_config_loading():
    """测试配置加载"""
    print("🔍 测试配置加载...")
    try:
        from app.config import config
        print(f"✅ 配置加载成功")
        print(f"   - 项目版本: {config.project_version}")
        print(f"   - 播客模式: {config.app.get('podcast', {}).get('enable_podcast_mode', False)}")
        return True
    except Exception as e:
        print(f"❌ 配置加载失败: {e}")
        return False

def test_podcast_models():
    """测试播客数据模型"""
    print("🔍 测试播客数据模型...")
    try:
        from app.models.schema import PodcastScript, VideoParams
        from app.services.podcast_audio import podcast_audio_generator

        # 测试PodcastScript模型
        test_script = PodcastScript(
            speaker_1="测试说话人1内容",
            speaker_2="测试说话人2内容",
            speaker_1_voice="zh-CN-XiaoxiaoNeural-Female",
            speaker_2_voice="zh-CN-YunxiNeural-Male"
        )
        print("✅ PodcastScript模型创建成功")

        # 测试VideoParams模型
        test_params = VideoParams(
            article_text="测试文章内容",
            podcast_script=[test_script]
        )
        print("✅ VideoParams模型创建成功")

        # 测试播客音频生成器
        voice_pairs = podcast_audio_generator.get_recommended_voice_pairs()
        print(f"✅ 推荐音色配对数量: {len(voice_pairs)}")

        return True
    except Exception as e:
        print(f"❌ 播客模型测试失败: {e}")
        return False

def test_llm_service():
    """测试LLM服务"""
    print("🔍 测试LLM服务...")
    try:
        from app.services import llm

        # 检查播客相关函数是否存在
        if hasattr(llm, 'generate_podcast_script'):
            print("✅ generate_podcast_script函数存在")
        else:
            print("❌ generate_podcast_script函数不存在")
            return False

        if hasattr(llm, 'generate_terms_from_podcast'):
            print("✅ generate_terms_from_podcast函数存在")
        else:
            print("❌ generate_terms_from_podcast函数不存在")
            return False

        return True
    except Exception as e:
        print(f"❌ LLM服务测试失败: {e}")
        return False

def test_webui_syntax():
    """测试WebUI语法"""
    print("🔍 测试WebUI语法...")
    try:
        # 检查Main.py文件语法
        import ast
        with open(os.path.join(root_dir, 'webui', 'Main.py'), 'r', encoding='utf-8') as f:
            code = f.read()

        try:
            ast.parse(code)
            print("✅ Main.py语法正确")
        except SyntaxError as e:
            print(f"❌ Main.py语法错误: {e}")
            return False

        # 检查关键函数是否存在
        if '_format_podcast_to_script' in code:
            print("✅ _format_podcast_to_script函数存在")
        else:
            print("❌ _format_podcast_to_script函数不存在")
            return False

        if 'article_text_input' in code:
            print("✅ 文章输入框存在")
        else:
            print("❌ 文章输入框不存在")
            return False

        if 'generate_podcast_script' in code:
            print("✅ 播客生成按钮存在")
        else:
            print("❌ 播客生成按钮不存在")
            return False

        return True
    except Exception as e:
        print(f"❌ WebUI语法测试失败: {e}")
        return False

def test_virtual_environment():
    """测试虚拟环境"""
    print("🔍 测试虚拟环境...")
    try:
        import sys
        venv_path = os.path.join(root_dir, '.venv')
        if os.path.exists(venv_path):
            print(f"✅ 虚拟环境存在: {venv_path}")
            print(f"   - 当前Python: {sys.executable}")
            print(f"   - 虚拟环境Python: {os.path.join(venv_path, 'Scripts', 'python.exe')}")
        else:
            print("❌ 虚拟环境不存在")
            return False

        # 检查关键依赖
        dependencies = ['streamlit', 'fastapi', 'loguru', 'pydantic']
        for dep in dependencies:
            try:
                __import__(dep)
                print(f"✅ {dep} 已安装")
            except ImportError:
                print(f"❌ {dep} 未安装")
                return False

        return True
    except Exception as e:
        print(f"❌ 虚拟环境测试失败: {e}")
        return False

def start_streamlit_test():
    """启动Streamlit进行界面测试"""
    print("🚀 启动Streamlit界面测试...")
    print("注意：这将启动一个Streamlit服务器进程")
    print("请在浏览器中访问 http://localhost:8501 进行测试")
    print("按 Ctrl+C 停止服务器")

    try:
        # 切换到项目目录
        os.chdir(root_dir)

        # 启动Streamlit
        cmd = [
            sys.executable, '-m', 'streamlit', 'run', 'webui/Main.py',
            '--server.port=8501',
            '--server.headless=true',
            '--browser.gatherUsageStats=False',
            '--server.enableCORS=True'
        ]

        print(f"执行命令: {' '.join(cmd)}")
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        # 等待服务器启动
        time.sleep(5)

        # 检查服务器是否启动成功
        try:
            response = requests.get('http://localhost:8501', timeout=5)
            if response.status_code == 200:
                print("✅ Streamlit服务器启动成功")
                print("🌐 请在浏览器中访问: http://localhost:8501")
                print("💡 测试步骤:")
                print("   1. 粘贴一段文章到文本区域")
                print("   2. 选择说话人音色")
                print("   3. 点击'生成播客对话'按钮")
                print("   4. 查看生成的对话内容")
                print("   5. 点击'生成播客视频'按钮")
                print("   6. 检查视频生成进度")

                # 等待用户手动停止
                process.wait()
            else:
                print(f"❌ 服务器响应异常: {response.status_code}")
                process.terminate()
        except requests.exceptions.RequestException:
            print("❌ 无法连接到Streamlit服务器")
            process.terminate()

    except KeyboardInterrupt:
        print("\n⏹️  用户停止测试")
    except Exception as e:
        print(f"❌ Streamlit启动失败: {e}")
    finally:
        if 'process' in locals():
            process.terminate()

async def main():
    """主测试函数"""
    print("🎙️  Phase 3 UI改造测试")
    print("=" * 60)

    tests = [
        ("虚拟环境测试", test_virtual_environment),
        ("配置加载测试", test_config_loading),
        ("播客模型测试", test_podcast_models),
        ("LLM服务测试", test_llm_service),
        ("WebUI语法测试", test_webui_syntax),
        ("Streamlit导入测试", test_streamlit_import),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 40)
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} 失败")

    print(f"\n📊 测试结果: {passed}/{total} 通过")

    if passed == total:
        print("🎉 所有基础测试通过！")
        print("\n🚀 是否启动Streamlit界面进行手动测试？(y/n)")
        choice = input("> ").strip().lower()
        if choice in ['y', 'yes', '是']:
            start_streamlit_test()
    else:
        print("❌ 部分测试失败，请先修复问题")
        return False

    return passed == total

if __name__ == "__main__":
    # 运行异步测试
    result = asyncio.run(main())
    if result:
        print("\n✅ Phase 3 UI改造测试完成")
    else:
        print("\n❌ Phase 3 UI改造测试失败")
        sys.exit(1)