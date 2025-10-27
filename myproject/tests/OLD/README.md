# Obsolete Tests Archive

This folder contains tests that have been moved from the active test suite due to obsolete functionality.

## Files Moved

### `test_youtube_service.py`
- **Original Location**: `/tests/test_youtube_service.py`
- **Reason**: YouTube streaming functionality has been replaced by direct RTSP→HLS streaming
- **Date Moved**: 2025-10-27
- **Test Count**: All YouTube service tests

### `test_youtube_legacy.py`
- **Original Location**: Extracted from `/tests/test_core_views.py` and `/tests/test_integration.py`
- **Reason**: YouTube streaming functionality has been replaced by direct RTSP→HLS streaming
- **Date Moved**: 2025-10-27
- **Test Classes**:
  - `YouTubeLegacyTest` (from test_core_views.py)
  - `YouTubeIntegrationTest` (from test_integration.py)

## Architecture Change

The ClimaCocal system has migrated from YouTube-based streaming to direct camera streaming:

- **Old**: Camera → YouTube Live → User
- **New**: Camera → RTSP → HLS → User

This change provides:
- Better performance and lower latency
- Direct control over streaming quality
- No dependency on YouTube API
- Improved reliability

## Test Status

All moved tests are marked with `skipTest()` to indicate they're obsolete. The tests are preserved for historical reference and potential debugging needs.

## Current Test Statistics (27/10/2025)

**Active Test Suite**: 171 testes passando 100% ✅
- Base streaming tests: test_streaming_services.py + test_streaming_views.py
- Climber system tests: test_climber_service.py + test_climber_views.py  
- Core application tests: test_core_views.py + test_integration.py
- Additional tests: test_e2e_playwright.py + test_payment_service.py + test_weather_service.py

**Obsolete Tests Archived**: 5 testes YouTube ⚠️
- test_youtube_service.py (moved from /tests/)
- YouTubeLegacyTest + YouTubeIntegrationTest (extracted from active files)

## Running Obsolete Tests

To run these tests (they will be skipped):
```bash
python manage.py test tests.OLD.test_youtube_service
python manage.py test tests.OLD.test_youtube_legacy
```

All tests will be automatically skipped with the message: "YouTube functionality obsolete - replaced by direct streaming"

## Migration Status

✅ **COMPLETED (27/10/2025)**: Clean migration from YouTube to RTSP→HLS streaming
- Architecture modernization complete
- Test suite cleanup finalized
- Documentation updated across all files
- Production system stable with 171 active tests