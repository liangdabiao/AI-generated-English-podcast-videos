# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MoneyPrinterTurbo is an AI-powered video generation system that creates short videos from text input. The project follows an MVC architecture with both FastAPI backend and Streamlit frontend interfaces. The system is currently being transformed from a single-topic video generator to a podcast-video generation system where users can input articles and generate dual-speaker podcast conversations with accompanying videos.

## Common Development Commands

### Starting the Applications

**Web UI (Streamlit):**
```bash
# Windows
webui.bat

# Linux/MacOS
sh webui.sh

# Manual command
streamlit run ./webui/Main.py --browser.gatherUsageStats=False --server.enableCORS=True
```

**API Server (FastAPI):**
```bash
python main.py
# Access docs at http://127.0.0.1:8080/docs
```

**Docker:**
```bash
docker-compose up
# Web UI: http://0.0.0.0:8501
# API: http://0.0.0.0:8080/docs
```

### Testing

**Run Phase Tests (Current Development):**
```bash
# Phase 1 - Data model tests
python test_phase1.py

# Phase 2 - Podcast audio tests
python test_podcast_audio.py

# Service tests
python -m pytest test/services/
```

**Environment Validation:**
```bash
# Check Python environment
python -c "import sys; print(sys.path)"

# Validate dependencies
python -c "import moviepy, streamlit, fastapi, edge_tts"
```

## Architecture Overview

### Core Components

**MVC Structure:**
- `app/controllers/` - API endpoints and request handling
- `app/models/` - Pydantic data models and validation
- `app/services/` - Business logic and processing engines
- `app/utils/` - Utility functions and helpers
- `app/config/` - Configuration management

**Key Services:**
- `llm.py` - AI model integration (OpenAI, Moonshot, Azure, etc.)
- `voice.py` - TTS synthesis (Edge TTS, Azure, SiliconFlow)
- `video.py` - Video composition and rendering
- `material.py` - Video素材获取 from Pexels/Pixabay
- `subtitle.py` - 字幕生成 (Edge/Whisper)
- `podcast_audio.py` - **NEW**: Podcast audio generation
- `task.py` - Task management and state tracking

### Data Flow Architecture

**Original Video Generation:**
```
Video Topic → LLM Script Generation → TTS Audio → Material Matching → Video Composition
```

**NEW Podcast Video Generation (Current Transformation):**
```
Article Text → LLM Dialogue Generation → Dual-Speaker TTS → Audio Merging → Video Composition
```

**Key Data Models:**
```python
# Core podcast model (NEW)
class PodcastScript(BaseModel):
    speaker_1: str      # 说话人1的内容
    speaker_2: str      # 说话人2的内容
    speaker_1_voice: str # 说话人1的音色
    speaker_2_voice: str # 说话人2的音色

# Main video parameters (MODIFIED)
class VideoParams(BaseModel):
    article_text: str = ""           # NEW: 用户输入的文章
    podcast_script: Optional[List[PodcastScript]] = None  # NEW: 生成的播客脚本
    video_terms: Optional[str | list] = None  # Legacy: 视频关键词
    # ... other video parameters
```

### Configuration System

**Configuration File:** `config.toml` (copy from `config.example.toml`)

**Critical Settings:**
- `llm_provider` - AI model provider (openai, moonshot, deepseek, etc.)
- `pexels_api_keys` - Video素材 API keys
- `subtitle_provider` - 字幕生成方式 (edge/whisper)
- `[app.podcast]` - **NEW**: Podcast-specific configuration

**Podcast Configuration:**
```toml
[app.podcast]
default_speaker_1_voice = "zh-CN-XiaoxiaoNeural-Female"
default_speaker_2_voice = "zh-CN-YunxiNeural-Male"
podcast_dialogue_style = "conversational"
max_dialogue_turns = 10
enable_podcast_mode = true
```

## Current Development Status

### Phase 1 Completed: Data Model Transformation ✅
- Added `PodcastScript` model for dual-speaker dialogues
- Modified `VideoParams` to use `article_text` instead of `video_subject`
- Extended LLM service with podcast generation functions
- Added podcast configuration section

### Phase 2 Completed: Podcast Audio Generation ✅
- Created `podcast_audio.py` with dual-speaker audio generation
- Implemented audio merging with proper pause timing
- Added voice validation and recommended voice pairs
- Created comprehensive test scripts

### Next Phases (Pending)
- **Phase 3**: UI改造 - Convert Streamlit interface to article input + podcast generation
- **Phase 4**: Video Generation Logic - Adapt video generation for podcast audio timing

## External Dependencies

### Core Dependencies
- **moviepy** - Video composition and rendering
- **streamlit** - Web interface
- **fastapi** - API backend
- **edge_tts** - Text-to-speech synthesis
- **loguru** - Logging

### Optional Dependencies
- **ffmpeg** - Audio/video processing (auto-downloaded with fallbacks)
- **ImageMagick** - Image processing for subtitles
- **whisper** - High-quality subtitle generation (3GB model download)

### Voice Providers
- **Edge TTS** - Free, basic voices
- **Azure Speech** - Premium voices (requires API key)
- **SiliconFlow** - Advanced voice synthesis

## Development Guidelines

### Voice Integration
The system supports multiple TTS providers. When adding new voice support:
1. Update `voice.py` with new provider logic
2. Add configuration options in `config.example.toml`
3. Update `podcast_audio.py` voice validation methods
4. Test with `test_podcast_audio.py`

### Audio Processing Architecture
- Use `ffmpeg` as primary audio processing tool
- Implement fallback mechanisms for missing dependencies
- Handle temporary file management automatically
- Support both file-level and memory-level audio operations

### Error Handling Strategy
- Implement graceful degradation for missing dependencies
- Provide meaningful error messages for configuration issues
- Use multiple retry attempts for external API calls
- Log detailed debugging information for troubleshooting

### Configuration Management
- Never commit API keys or sensitive configuration
- Use `config.example.toml` as template
- Support environment variables for deployment
- Validate configuration at startup

## Testing Strategy

### Test Files Structure
- `test_phase1.py` - Phase 1 functionality validation
- `test_podcast_audio.py` - Podcast audio generation tests
- `test/services/` - Individual service unit tests

### Running Tests
```bash
# Validate podcast audio generation
python test_podcast_audio.py

# Test voice synthesis
python -c "from app.services.voice import tts; print('Voice service OK')"

# Check configuration
python -c "from app.config import config; print('Config loaded')"
```

## Important Notes

### Chinese Language Support
- Primary development language is Chinese
- Default voices are Chinese (zh-CN)
- All documentation and comments should include Chinese
- Support both Chinese and English video generation

### External API Keys
Required for full functionality:
- **LLM Provider**: OpenAI, Moonshot, DeepSeek, or Azure API key
- **Video Materials**: Pexels API keys
- **Premium Voices**: Azure Speech API key

### File Paths and Storage
- Avoid Chinese characters in file paths
- Use `utils.storage_dir()` for consistent storage paths
- Implement proper cleanup of temporary files
- Support both local and cloud storage options