#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
第一阶段数据模型改造测试
"""

import sys
import os

# 添加项目根目录到路径
root_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(root_dir)

def test_data_models():
    """测试数据模型"""
    print("=== 测试数据模型 ===")
    
    try:
        from app.models.schema import PodcastScript, VideoParams, PodcastGenerateRequest
        
        # 测试PodcastScript
        print("1. 测试PodcastScript模型...")
        podcast_script = PodcastScript(
            speaker_1="今天我们来讨论人工智能的发展",
            speaker_2="是的，这是一个很有意思的话题",
            speaker_1_voice="zh-CN-XiaoxiaoNeural-Female",
            speaker_2_voice="zh-CN-YunxiNeural-Male"
        )
        print(f"   ✓ PodcastScript创建成功: {podcast_script.speaker_1[:20]}...")
        
        # 测试VideoParams
        print("2. 测试VideoParams模型...")
        video_params = VideoParams(
            article_text="这是一篇关于人工智能发展的文章...",
            speaker_1_voice="zh-CN-XiaoxiaoNeural-Female",
            speaker_2_voice="zh-CN-YunxiNeural-Male"
        )
        print(f"   ✓ VideoParams创建成功，article_text长度: {len(video_params.article_text)}")
        
        # 测试PodcastGenerateRequest
        print("3. 测试PodcastGenerateRequest模型...")
        request = PodcastGenerateRequest(
            article_text="这是一篇测试文章...",
            language="zh-CN"
        )
        print(f"   ✓ PodcastGenerateRequest创建成功: {request.article_text[:20]}...")
        
        print("✅ 所有数据模型测试通过！")
        return True
        
    except Exception as e:
        print(f"❌ 数据模型测试失败: {e}")
        return False

def test_config():
    """测试配置文件"""
    print("\n=== 测试配置文件 ===")
    
    try:
        from app.config import config
        
        # 测试播客配置
        print("1. 测试播客配置...")
        podcast_config = config.app.get("podcast", {})
        if podcast_config:
            print(f"   ✓ 播客配置加载成功: {list(podcast_config.keys())}")
        else:
            print("   ⚠️  播客配置为空，使用默认值")
        
        print("✅ 配置文件测试通过！")
        return True
        
    except Exception as e:
        print(f"❌ 配置文件测试失败: {e}")
        return False

def test_llm_service():
    """测试LLM服务"""
    print("\n=== 测试LLM服务 ===")
    
    try:
        from app.services import llm
        
        # 检查是否有新的播客相关函数
        print("1. 检查播客相关函数...")
        if hasattr(llm, 'generate_podcast_script'):
            print("   ✓ generate_podcast_script函数存在")
        else:
            print("   ❌ generate_podcast_script函数不存在")
            return False
            
        if hasattr(llm, 'parse_podcast_response'):
            print("   ✓ parse_podcast_response函数存在")
        else:
            print("   ❌ parse_podcast_response函数不存在")
            return False
            
        if hasattr(llm, 'generate_terms_from_podcast'):
            print("   ✓ generate_terms_from_podcast函数存在")
        else:
            print("   ❌ generate_terms_from_podcast函数不存在")
            return False
        
        print("✅ LLM服务测试通过！")
        return True
        
    except Exception as e:
        print(f"❌ LLM服务测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("开始第一阶段数据模型改造测试...\n")
    
    results = []
    results.append(test_data_models())
    results.append(test_config())
    results.append(test_llm_service())
    
    print(f"\n=== 测试结果 ===")
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"🎉 所有测试通过！({passed}/{total})")
        print("✅ 第一阶段数据模型改造完成！")
        return True
    else:
        print(f"❌ 部分测试失败！({passed}/{total})")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
