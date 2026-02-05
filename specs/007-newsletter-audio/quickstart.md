# Quickstart: Newsletter Audio Generation

**Date**: 2026-02-05
**Feature**: [spec.md](spec.md)
**For**: Developers implementing or testing this feature

## Overview

This guide walks you through setting up, implementing, and testing the newsletter audio generation feature using ElevenLabs text-to-speech.

## Prerequisites

- Python 3.13+ installed
- `uv` package manager configured
- ElevenLabs account with API key (free tier sufficient for testing)
- Existing daily_briefing project running locally

## Setup

### 1. Install Dependencies

```bash
# Add ElevenLabs SDK
uv add elevenlabs

# Verify installation
uv run python -c "import elevenlabs; print('ElevenLabs SDK installed')"
```

### 2. Get ElevenLabs API Key

1. Sign up at [ElevenLabs](https://elevenlabs.io/)
2. Navigate to [Profile Settings](https://elevenlabs.io/app/settings/api-keys)
3. Generate a new API key
4. Copy the key (starts with `sk_`)

### 3. Configure Environment

Add to your `.env` file:

```bash
# Required
ELEVENLABS_API_KEY=sk_your_api_key_here

# Optional (these are the defaults)
ELEVENLABS_MALE_VOICE_ID=ErXwobaYiN019PkySvjV
ELEVENLABS_FEMALE_VOICE_ID=21m00Tcm4TlvDq8ikWAM
ELEVENLABS_MODEL=eleven_monolingual_v1
ELEVENLABS_TIMEOUT=30
```

### 4. Verify Configuration

```bash
# Test API connectivity
uv run python -c "
from elevenlabs import ElevenLabs
import os

client = ElevenLabs(api_key=os.getenv('ELEVENLABS_API_KEY'))
voices = client.voices.get_all()
print(f'✓ Connected! Found {len(voices.voices)} voices')
"
```

## Development Workflow

### Phase 1: Implement Models

**File**: `src/models/audio_models.py`

```bash
# Create the file (refer to data-model.md for full content)
touch src/models/audio_models.py
```

Key models to implement:
- `AudioConfig` - Configuration from environment
- `NewsletterItem` - Parsed markdown item
- `AudioSegment` - Generated audio for one item
- `AudioGenerationResult` - Overall result summary
- `TTSRequest` - API request payload

### Phase 2: Implement Services (TDD)

#### 2a. Markdown Parser

**Test First**: `tests/unit/services/audio/test_markdown_parser.py`

```python
def test_parse_newsletter_items():
    """Test parsing markdown into structured items."""
    markdown = """
# Newsletter Digest

## Technology

#### First Article
Content for first article.

#### Second Article
Content for second article.
*Source: https://example.com*
    """

    items = parse_newsletter_items(markdown)

    assert len(items) == 2
    assert items[0].title == "First Article"
    assert items[0].item_number == 1
    assert items[0].voice_gender == "male"  # Odd
    assert items[1].voice_gender == "female"  # Even
```

**Then Implement**: `src/services/audio/markdown_parser.py`

#### 2b. TTS Service

**Test First**: `tests/unit/services/audio/test_tts_service.py`

```python
@pytest.fixture
def mock_elevenlabs_client(mocker):
    """Mock ElevenLabs client."""
    mock = mocker.Mock()
    mock.generate.return_value = b'\xff\xfb\x90\x00...'  # Fake MP3
    return mock

def test_convert_to_speech_success(mock_elevenlabs_client):
    """Test successful TTS conversion."""
    service = ElevenLabsTTSService(api_key="test", config=AudioConfig())
    service._client = mock_elevenlabs_client

    request = TTSRequest(text="Test content", voice_id="test_voice")
    result = service.convert_to_speech(request)

    assert isinstance(result, AudioSegment)
    assert len(result.audio_bytes) > 0
    mock_elevenlabs_client.generate.assert_called_once()
```

**Then Implement**: `src/services/audio/tts_service.py`

#### 2c. Audio Generator Orchestrator

**Test First**: `tests/unit/services/audio/test_audio_generator.py`

```python
def test_generate_audio_for_newsletter(tmp_path, mocker):
    """Test end-to-end audio generation."""
    # Create test markdown
    markdown_path = tmp_path / "test_digest.md"
    markdown_path.write_text("# Newsletter\n\n#### Item 1\nContent")

    # Mock TTS service
    mock_tts = mocker.Mock()
    mock_tts.convert_to_speech.return_value = AudioSegment(
        item_number=1,
        audio_bytes=b'\xff\xfb...',
        voice_id="test",
        voice_gender="male"
    )

    result = generate_audio_for_newsletter(markdown_path, tts_service=mock_tts)

    assert result.success is True
    assert result.output_path.exists()
    assert result.output_path.suffix == ".mp3"
```

**Then Implement**: `src/services/audio/audio_generator.py`

### Phase 3: Integration

**Modify**: `src/newsletter/storage.py`

Add audio generation hook after line ~205:

```python
def save_consolidated_digest(markdown_content: str, timestamp: str) -> Path:
    """Save consolidated digest and generate audio."""
    # Existing code...
    output_path = Path(f"data/output/digest_{timestamp}.md")
    output_path.write_text(markdown_content)

    # NEW: Generate audio
    try:
        from src.services.audio.audio_generator import generate_audio_for_newsletter
        audio_result = generate_audio_for_newsletter(output_path)
        if audio_result.success:
            logger.info(f"Audio generated: {audio_result.output_path}")
        else:
            logger.warning(f"Audio generation partial: {audio_result.items_processed}/{audio_result.total_items}")
    except Exception as e:
        logger.error(f"Audio generation failed: {e}")
        # Don't re-raise - audio is optional

    return output_path
```

## Testing

### Run Unit Tests

```bash
# All audio service tests
uv run pytest tests/unit/services/audio/ -v

# Specific test file
uv run pytest tests/unit/services/audio/test_tts_service.py -v

# With coverage
uv run pytest tests/unit/services/audio/ --cov=src/services/audio --cov-report=term-missing
```

### Run Integration Tests

```bash
# Full workflow test (mocked API)
uv run pytest tests/integration/test_newsletter_audio_workflow.py -v
```

### Manual Testing

```bash
# Generate newsletter with audio
uv run python -m src.web.app

# Then in browser, trigger newsletter refresh via:
# POST http://localhost:5000/api/refresh

# Check output directory
ls -lh data/output/
# Should see both .md and .mp3 files with matching timestamps
```

### Test with Real API

```bash
# Create test script
cat > test_real_audio.py << 'EOF'
from src.services.audio.audio_generator import generate_audio_for_newsletter
from pathlib import Path

# Use existing newsletter
markdown_path = Path("data/output/digest_20260205_135306_678384.md")
result = generate_audio_for_newsletter(markdown_path)

print(f"Success: {result.success}")
print(f"Output: {result.output_path}")
print(f"Items: {result.items_processed}/{result.total_items}")
EOF

uv run python test_real_audio.py
```

## Troubleshooting

### Error: "ELEVENLABS_API_KEY not found"

**Solution**: Ensure `.env` file exists and contains the API key:

```bash
echo "ELEVENLABS_API_KEY=sk_your_key" >> .env
```

### Error: "401 Unauthorized"

**Cause**: Invalid or expired API key

**Solution**:
1. Verify API key in ElevenLabs dashboard
2. Regenerate key if needed
3. Update `.env` file

### Error: "429 Rate Limit Exceeded"

**Cause**: Exceeded free tier limit (10k characters/month)

**Solution**:
- Wait until next month (free tier)
- Upgrade to paid plan ($5/month for 30k characters)
- Reduce newsletter frequency for testing

### Audio File Not Generated

**Debug steps**:

```bash
# Check logs
tail -f logs/app.log | grep -i audio

# Verify markdown file exists
ls -l data/output/digest_*.md

# Test parser independently
uv run python -c "
from src.services.audio.markdown_parser import parse_newsletter_items
from pathlib import Path
items = parse_newsletter_items(Path('data/output/digest_20260205_135306_678384.md'))
print(f'Parsed {len(items)} items')
"
```

### Audio Quality Issues

**Adjust voice settings** in `.env`:

```bash
# More stable (less varied)
ELEVENLABS_STABILITY=0.8

# More expressive (more varied)
ELEVENLABS_STABILITY=0.3

# Note: These require extending AudioConfig model to support custom settings
```

## Voice Customization

### List Available Voices

```python
from elevenlabs import ElevenLabs
import os

client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))
voices = client.voices.get_all()

for voice in voices.voices:
    print(f"{voice.name}: {voice.voice_id}")
```

### Change Default Voices

Update `.env`:

```bash
# Use different male voice (Adam instead of Antoni)
ELEVENLABS_MALE_VOICE_ID=pNInz6obpgDQGcFmaJgB

# Use different female voice (Domi instead of Rachel)
ELEVENLABS_FEMALE_VOICE_ID=AZnzlk1XvdvUeBnXmlld
```

## Performance Optimization

### Monitor API Usage

```python
# Add to audio_generator.py
import time

start_time = time.time()
# ... generate audio ...
duration = time.time() - start_time

logger.info(f"Audio generation took {duration:.2f}s for {len(items)} items")
logger.info(f"Average: {duration/len(items):.2f}s per item")
```

### Estimate Costs

```bash
# Calculate character count for a newsletter
uv run python -c "
from pathlib import Path
content = Path('data/output/digest_20260205_135306_678384.md').read_text()
# Rough estimate: strip markdown, count characters
text = content.replace('#', '').replace('*', '')
print(f'Approx {len(text)} characters')
print(f'Free tier: {10000 - len(text)} characters remaining this month')
"
```

## Code Quality

### Run Linter

```bash
# Check code style
uv run ruff check src/services/audio/ src/models/audio_models.py

# Auto-fix issues
uv run ruff check --fix src/services/audio/
```

### Run Type Checker

```bash
# Check type annotations
uv run mypy src/services/audio/ src/models/audio_models.py

# Strict mode
uv run mypy --strict src/services/audio/
```

## Next Steps

1. **Implement models** (`src/models/audio_models.py`)
2. **Write tests first** (TDD approach)
3. **Implement services** (markdown parser, TTS service, audio generator)
4. **Integrate into pipeline** (`storage.py` hook)
5. **Test end-to-end** (real newsletter generation)
6. **Deploy** (verify .env on server, test in production)

## Resources

- [ElevenLabs API Docs](https://elevenlabs.io/docs/api-reference/overview)
- [ElevenLabs Python SDK](https://github.com/elevenlabs/elevenlabs-python)
- [Voice Library](https://elevenlabs.io/voice-library)
- [Data Model Reference](data-model.md)
- [Integration Contract](contracts/elevenlabs-tts-integration.md)

## Support

If issues persist:
1. Check [ElevenLabs Status](https://status.elevenlabs.io/)
2. Review [API Changelog](https://elevenlabs.io/docs/changelog)
3. Contact ElevenLabs support (for API issues)
4. Open project issue (for integration bugs)
