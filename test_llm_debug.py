#!/usr/bin/env python3
"""
LLM播客脚本生成调试脚本
"""

import os
import sys
import json
from typing import List

# 添加项目根目录到Python路径
root_dir = os.path.dirname(os.path.abspath(__file__))
if root_dir not in sys.path:
    sys.path.append(root_dir)

def test_openai_config():
    """测试OpenAI配置"""
    print("🔍 测试OpenAI配置...")
    try:
        from app.config import config

        llm_provider = config.app.get("llm_provider", "openai")
        print(f"✅ LLM提供商: {llm_provider}")

        if llm_provider == "openai":
            api_key = config.app.get("openai_api_key")
            model_name = config.app.get("openai_model_name")
            base_url = config.app.get("openai_base_url", "")

            print(f"✅ API Key: {'已设置' if api_key else '未设置'}")
            print(f"✅ Model: {model_name}")
            print(f"✅ Base URL: {base_url}")

            if not api_key:
                print("❌ OpenAI API Key未设置")
                return False
            if not model_name:
                print("❌ OpenAI Model未设置")
                return False

        return True
    except Exception as e:
        print(f"❌ 配置测试失败: {e}")
        return False

def test_llm_response():
    """测试LLM响应"""
    print("\n🔍 测试LLM响应...")
    try:
        from app.services.llm import _generate_response

        # 简单的测试prompt
        test_prompt = """
请返回一个简单的JSON数组，包含两个对象：
[
  {
    "speaker_1": "你好",
    "speaker_2": "世界"
  }
]
"""

        print("发送测试请求...")
        response = _generate_response(test_prompt)
        print(f"✅ 原始响应: {repr(response)}")

        if not response or response.strip() == "":
            print("❌ LLM返回空响应")
            return False

        if response.startswith("Error:"):
            print(f"❌ LLM调用失败: {response}")
            return False

        # 尝试解析JSON
        try:
            data = json.loads(response)
            print(f"✅ JSON解析成功: {data}")
            return True
        except json.JSONDecodeError as e:
            print(f"❌ JSON解析失败: {e}")
            print(f"❌ 响应内容: {response}")
            return False

    except Exception as e:
        print(f"❌ LLM响应测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_podcast_script_generation():
    """测试播客脚本生成"""
    print("\n🔍 测试播客脚本生成...")
    try:
        from app.services.llm import generate_podcast_script

        # 简单的测试文章
        test_article = "人工智能是计算机科学的一个分支，它试图创建能够执行通常需要人类智能的任务的机器。"

        print("生成播客脚本...")
        podcast_script = generate_podcast_script(test_article, "zh-CN")

        if podcast_script:
            print(f"✅ 生成成功，共 {len(podcast_script)} 轮对话")
            for i, script in enumerate(podcast_script):
                print(f"  轮次 {i+1}:")
                print(f"    说话人1: {script.speaker_1}")
                print(f"    说话人2: {script.speaker_2}")
            return True
        else:
            print("❌ 播客脚本生成失败")
            return False

    except Exception as e:
        print(f"❌ 播客脚本生成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("🤖 LLM播客脚本生成调试测试")
    print("=" * 50)

    tests = [
        ("OpenAI配置测试", test_openai_config),
        ("LLM响应测试", test_llm_response),
        ("播客脚本生成测试", test_podcast_script_generation),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 30)

        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} 失败")

    print(f"\n📊 测试结果: {passed}/{total} 通过")

    if passed == total:
        print("🎉 所有测试通过！")
    else:
        print("❌ 部分测试失败，请检查配置")

if __name__ == "__main__":
    main()