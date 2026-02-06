"""Unit tests for audio serving routes.

Tests HTTP 200/206 responses, authentication, validation, and caching headers.
Per constitution: TDD required - write tests first, ensure they FAIL before implementation.
"""
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, mock_open


class TestAudioRoutes:
    """Tests for /audio/<item_id> endpoint."""

    @pytest.fixture
    def app(self):
        """Create test Flask app."""
        from src.web.app import create_app
        with patch('src.db.connection.initialize_pool'):
            app = create_app()
            app.config['TESTING'] = True
            app.config['LOGIN_DISABLED'] = True  # Disable authentication for tests
            return app

    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return app.test_client()

    @pytest.fixture
    def mock_audio_file(self, tmp_path):
        """Create mock audio file for testing."""
        audio_file = tmp_path / "test_audio.mp3"
        audio_content = b"fake mp3 content" * 1000  # ~16KB
        audio_file.write_bytes(audio_content)
        return audio_file, audio_content

    # T003: HTTP 200 full file response
    def test_serve_audio_full_file_200(self, client, mock_audio_file):
        """Test HTTP 200 response for full file request."""
        audio_file, audio_content = mock_audio_file

        with patch('src.web.audio_routes.Path') as mock_path:
            mock_path.return_value.exists.return_value = True
            mock_path.return_value.stat.return_value.st_size = len(audio_content)

            with patch('builtins.open', mock_open(read_data=audio_content)):
                # User must be authenticated - mock login
                with client.session_transaction() as sess:
                    sess['user_id'] = 'test_user'

                response = client.get('/audio/1a4f6b0976cc66ba')

                assert response.status_code == 200
                assert response.headers['Content-Type'] == 'audio/mpeg'
                assert 'Accept-Ranges' in response.headers
                assert response.headers['Accept-Ranges'] == 'bytes'

    # T004: HTTP 206 range request handling
    def test_serve_audio_range_request_206(self, client, mock_audio_file):
        """Test HTTP 206 response for byte range request."""
        audio_file, audio_content = mock_audio_file
        file_size = len(audio_content)

        with patch('src.web.audio_routes.Path') as mock_path:
            mock_path.return_value.exists.return_value = True
            mock_path.return_value.stat.return_value.st_size = file_size

            with patch('builtins.open', mock_open(read_data=audio_content)):
                with client.session_transaction() as sess:
                    sess['user_id'] = 'test_user'

                # Request first 1024 bytes
                response = client.get(
                    '/audio/1a4f6b0976cc66ba',
                    headers={'Range': 'bytes=0-1023'}
                )

                assert response.status_code == 206
                assert 'Content-Range' in response.headers
                assert response.headers['Content-Range'] == f'bytes 0-1023/{file_size}'
                assert response.headers['Content-Length'] == '1024'

    # T005: HTTP 401 authentication failure
    def test_serve_audio_unauthenticated_401(self, client):
        """Test HTTP 401 when user not authenticated."""
        response = client.get('/audio/1a4f6b0976cc66ba')

        # Should redirect to login or return 401
        assert response.status_code in [401, 302]

    # T006: HTTP 404 missing file
    def test_serve_audio_missing_file_404(self, client):
        """Test HTTP 404 when audio file doesn't exist."""
        with patch('src.web.audio_routes.Path') as mock_path:
            mock_path.return_value.exists.return_value = False

            with client.session_transaction() as sess:
                sess['user_id'] = 'test_user'

            response = client.get('/audio/nonexistent_item_id')

            assert response.status_code == 404

    # T007: HTTP 400 invalid item_id (path traversal)
    def test_serve_audio_invalid_item_id_400(self, client):
        """Test HTTP 400 for invalid item_id format (security check)."""
        with client.session_transaction() as sess:
            sess['user_id'] = 'test_user'

        # Try path traversal attack
        response = client.get('/audio/../../../etc/passwd')

        assert response.status_code == 400

    # T008: HTTP 416 out-of-range request
    def test_serve_audio_range_not_satisfiable_416(self, client, mock_audio_file):
        """Test HTTP 416 when requested range exceeds file size."""
        audio_file, audio_content = mock_audio_file
        file_size = len(audio_content)

        with patch('src.web.audio_routes.Path') as mock_path:
            mock_path.return_value.exists.return_value = True
            mock_path.return_value.stat.return_value.st_size = file_size

            with client.session_transaction() as sess:
                sess['user_id'] = 'test_user'

            # Request range beyond file size
            response = client.get(
                '/audio/1a4f6b0976cc66ba',
                headers={'Range': f'bytes={file_size + 100}-{file_size + 200}'}
            )

            assert response.status_code == 416
            assert 'Content-Range' in response.headers

    # T009: Cache headers (immutable, max-age)
    def test_serve_audio_cache_headers(self, client, mock_audio_file):
        """Test cache headers for immutable content."""
        audio_file, audio_content = mock_audio_file

        with patch('src.web.audio_routes.Path') as mock_path:
            mock_path.return_value.exists.return_value = True
            mock_path.return_value.stat.return_value.st_size = len(audio_content)

            with patch('builtins.open', mock_open(read_data=audio_content)):
                with client.session_transaction() as sess:
                    sess['user_id'] = 'test_user'

                response = client.get('/audio/1a4f6b0976cc66ba')

                assert 'Cache-Control' in response.headers
                cache_control = response.headers['Cache-Control']
                assert 'max-age=31536000' in cache_control
                assert 'immutable' in cache_control

    # T010: Accept-Ranges header
    def test_serve_audio_accept_ranges_header(self, client, mock_audio_file):
        """Test Accept-Ranges header present in all responses."""
        audio_file, audio_content = mock_audio_file

        with patch('src.web.audio_routes.Path') as mock_path:
            mock_path.return_value.exists.return_value = True
            mock_path.return_value.stat.return_value.st_size = len(audio_content)

            with patch('builtins.open', mock_open(read_data=audio_content)):
                with client.session_transaction() as sess:
                    sess['user_id'] = 'test_user'

                response = client.get('/audio/1a4f6b0976cc66ba')

                assert 'Accept-Ranges' in response.headers
                assert response.headers['Accept-Ranges'] == 'bytes'
