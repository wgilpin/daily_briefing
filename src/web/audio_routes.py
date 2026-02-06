"""Audio file serving routes.

Serves MP3 files with HTTP 206 partial content support for browser seeking.
Implements security (authentication, path traversal prevention) and caching.
"""
from flask import Blueprint, send_file, request, abort, make_response
from flask_login import login_required
from pathlib import Path

audio_bp = Blueprint('audio', __name__)


@audio_bp.route('/audio/<item_id>')
@login_required
def serve_audio(item_id: str):
    """Serve MP3 file with HTTP 206 partial content support.

    Args:
        item_id: Feed item identifier (hexadecimal hash)

    Returns:
        Response: Audio file with appropriate headers (200 or 206)

    Raises:
        400: Invalid item_id format (security check)
        404: Audio file not found
        416: Range not satisfiable
    """
    # T015: Input validation - prevent path traversal attacks
    if not item_id.isalnum() or len(item_id) < 16:
        abort(400, "Invalid item ID format")

    # Map item_id to audio file (WAV format from Kokoro TTS)
    audio_path = Path('data/audio_cache') / f"{item_id}.wav"

    if not audio_path.exists():
        abort(404, "Audio not found")

    file_size = audio_path.stat().st_size
    range_header = request.headers.get('Range')

    # T016: Cache headers for immutable content
    cache_headers = {
        'Cache-Control': 'public, max-age=31536000, immutable',
        'Accept-Ranges': 'bytes'
    }

    if not range_header:
        # T012: HTTP 200 full file support
        response = send_file(
            audio_path,
            mimetype='audio/wav',
            as_attachment=False,
            conditional=True  # Enable ETag/Last-Modified
        )
        response.headers.update(cache_headers)
        return response

    # T013: HTTP 206 partial content logic (range header parsing)
    byte_range = range_header.replace('bytes=', '').split('-')
    start = int(byte_range[0]) if byte_range[0] else 0
    end = int(byte_range[1]) if byte_range[1] else file_size - 1

    # Validate range
    if start >= file_size or end >= file_size or start > end:
        response = make_response('', 416)
        response.headers['Content-Range'] = f'bytes */{file_size}'
        return response

    length = end - start + 1

    # Read partial content
    with open(audio_path, 'rb') as f:
        f.seek(start)
        data = f.read(length)

    # Build 206 response
    response = make_response(data, 206)
    response.headers['Content-Type'] = 'audio/wav'
    response.headers['Content-Range'] = f'bytes {start}-{end}/{file_size}'
    response.headers['Content-Length'] = str(length)
    response.headers.update(cache_headers)

    return response
