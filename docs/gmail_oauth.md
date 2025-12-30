# Gmail OAuth Integration Design Document

## 1. Overview

### 1.1 Purpose
Design and implement a locally-running Python application to authenticate with Gmail API using OAuth 2.0 flow and extract newsletter subscriptions from a user's Gmail account.

### 1.2 Scope
- OAuth 2.0 authentication flow implementation
- Token management and refresh logic
- Gmail API integration for message retrieval
- Newsletter identification and extraction

### 1.3 Goals
- Secure authentication without storing passwords
- Persistent token management for repeated access
- Efficient message retrieval with minimal API calls
- Robust error handling and retry logic

## 2. System Architecture

### 2.1 Component Overview
```
┌─────────────────┐     ┌──────────────┐     ┌─────────────┐
│                 │────▶│   OAuth      │────▶│   Google    │
│  Python App     │     │   Module     │     │   Auth      │
│                 │◀────│              │◀────│   Server    │
└────────┬────────┘     └──────────────┘     └─────────────┘
         │
         │              ┌──────────────┐     ┌─────────────┐
         └─────────────▶│   Gmail      │────▶│  Gmail API  │
                        │   Client     │◀────│             │
                        └──────────────┘     └─────────────┘
```

### 2.2 Data Flow
1. Application checks for existing authentication token
2. If no valid token, initiates OAuth flow via browser
3. User authenticates and grants permissions
4. Application receives and stores tokens
5. Application uses token to access Gmail API
6. Tokens are refreshed automatically when expired

## 3. Technical Specification

### 3.1 Authentication Flow

#### 3.1.1 Initial Setup (One-time)
1. Create Google Cloud Project
2. Enable Gmail API
3. Create OAuth 2.0 credentials (Desktop application type)
4. Download credentials as `credentials.json`

#### 3.1.2 OAuth 2.0 Flow
```
User                    Application              Google
 │                          │                      │
 │   Start Application      │                      │
 ├─────────────────────────▶│                      │
 │                          │  Check token.json    │
 │                          ├──────────┐           │
 │                          │          │           │
 │                          │◀─────────┘           │
 │                          │  (No valid token)    │
 │                          │                      │
 │                          │  Load credentials    │
 │                          ├──────────┐           │
 │                          │          │           │
 │                          │◀─────────┘           │
 │                          │                      │
 │  Browser Opens           │  Start OAuth Flow    │
 │◀─────────────────────────┤─────────────────────▶│
 │                          │                      │
 │     Authenticate         │                      │
 ├──────────────────────────┼─────────────────────▶│
 │                          │                      │
 │                          │   Receive Code       │
 │                          │◀─────────────────────┤
 │                          │                      │
 │                          │  Exchange for Token  │
 │                          ├─────────────────────▶│
 │                          │                      │
 │                          │   Access Token       │
 │                          │◀─────────────────────┤
 │                          │                      │
 │                          │  Save token.json     │
 │                          ├──────────┐           │
 │                          │          │           │
 │                          │◀─────────┘           │
 │   Ready                  │                      │
 │◀─────────────────────────┤                      │
```

### 3.2 Directory Structure
```
project/
├── config/
│   └── credentials.json    # OAuth client credentials (git-ignored)
├── tokens/
│   └── token.json         # User tokens (git-ignored)
├── src/
│   ├── __init__.py
│   ├── gmail_auth.py      # Authentication module
│   ├── gmail_client.py    # Gmail API client
│   └── newsletter_detector.py  # Newsletter identification
├── data/
│   └── newsletters.json   # Extracted newsletter data
├── main.py               # Entry point
├── requirements.txt
└── .gitignore
```

### 3.3 Dependencies
```
google-auth==2.23.0
google-auth-oauthlib==1.1.0
google-auth-httplib2==0.1.1
google-api-python-client==2.100.0
```

## 4. Implementation Details

### 4.1 GmailAuthenticator Class

**Purpose**: Handle OAuth authentication and token management

**Responsibilities**:
- Load credentials from file
- Execute OAuth flow if needed
- Refresh expired tokens
- Persist tokens for future use

**Key Methods**:
- `authenticate()`: Main authentication entry point
- `_load_token()`: Load existing token from disk
- `_save_token()`: Persist token to disk
- `_refresh_token()`: Refresh expired access token

### 4.2 GmailClient Class

**Purpose**: Interface with Gmail API

**Responsibilities**:
- Search for messages matching criteria
- Retrieve full message content
- Parse MIME structure
- Extract relevant headers and body

**Key Methods**:
- `get_newsletters(days_back)`: Search for newsletter emails
- `get_message_details(msg_id)`: Fetch full message
- `_extract_body(payload)`: Parse MIME parts
- `batch_get_messages(msg_ids)`: Batch retrieval

### 4.3 Newsletter Detection

**Heuristics for identifying newsletters**:
1. Presence of `List-Unsubscribe` header
2. Sender patterns (no-reply@, newsletter@, digest@)
3. HTML content with specific structures
4. Tracking pixels presence
5. Bulk precedence headers

**Query Construction**:
```
after:{date} AND (
  list:* OR 
  unsubscribe OR 
  "view in browser" OR
  "email preferences"
)
```

## 5. Security Considerations

### 5.1 Token Storage
- Store tokens in user home directory or app-specific location
- Set file permissions to 600 (owner read/write only)
- Never commit tokens to version control

### 5.2 Scope Limitation
- Request minimal required scope: `gmail.readonly`
- Avoid modify or send permissions unless necessary

### 5.3 Credential Management
```python
# Example .gitignore
tokens/
config/credentials.json
*.json
__pycache__/
```

### 5.4 Error Handling
- Implement exponential backoff for rate limits
- Handle network failures gracefully
- Log authentication errors without exposing tokens

## 6. Configuration

### 6.1 Environment Variables
```bash
GMAIL_CREDS_PATH=./config/credentials.json
GMAIL_TOKEN_PATH=./tokens/token.json
GMAIL_SCOPES=https://www.googleapis.com/auth/gmail.readonly
GMAIL_MAX_RESULTS=100
GMAIL_DAYS_BACK=7
```

### 6.2 Application Settings
```python
# config.py
class Config:
    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
    TOKEN_FILE = 'token.json'
    CREDS_FILE = 'credentials.json'
    
    # API Settings
    MAX_RESULTS_PER_PAGE = 100
    MAX_BATCH_SIZE = 50
    
    # Newsletter Detection
    NEWSLETTER_INDICATORS = [
        'List-Unsubscribe',
        'Precedence: bulk',
        'X-Campaign-ID'
    ]
    
    # Retry Logic
    MAX_RETRIES = 3
    BACKOFF_FACTOR = 2
```

## 7. API Usage Patterns

### 7.1 Efficient Message Retrieval
```python
# Use fields parameter to limit response size
service.users().messages().list(
    userId='me',
    q=query,
    fields='messages(id,threadId),nextPageToken'
).execute()

# Batch requests for multiple messages
batch = service.new_batch_http_request()
for msg_id in message_ids:
    batch.add(service.users().messages().get(
        userId='me',
        id=msg_id,
        format='metadata',
        metadataHeaders=['From', 'Subject', 'List-Unsubscribe']
    ))
batch.execute()
```

### 7.2 Rate Limit Handling
```python
def execute_with_retry(request, max_retries=3):
    for attempt in range(max_retries):
        try:
            return request.execute()
        except HttpError as e:
            if e.resp.status == 429:
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                time.sleep(wait_time)
            elif e.resp.status >= 500:
                wait_time = (2 ** attempt)
                time.sleep(wait_time)
            else:
                raise
    raise MaxRetriesExceeded()
```

## 8. Testing Strategy

### 8.1 Unit Tests
- Mock OAuth flow
- Mock Gmail API responses
- Test token refresh logic
- Test newsletter detection heuristics

### 8.2 Integration Tests
- Test with real Gmail API (test account)
- Verify token persistence
- Test error recovery

### 8.3 Test Data
```python
# test_fixtures.py
MOCK_MESSAGE = {
    'id': 'msg123',
    'threadId': 'thread123',
    'payload': {
        'headers': [
            {'name': 'From', 'value': 'newsletter@example.com'},
            {'name': 'Subject', 'value': 'Weekly Digest'},
            {'name': 'List-Unsubscribe', 'value': '<http://example.com/unsub>'}
        ]
    }
}
```

## 9. Monitoring and Logging

### 9.1 Logging Strategy
```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('gmail_app.log'),
        logging.StreamHandler()
    ]
)

# Log key events
logger.info("Starting OAuth flow")
logger.info(f"Retrieved {len(messages)} messages")
logger.warning(f"Rate limit hit, backing off {wait_time}s")
logger.error(f"Authentication failed: {error}", exc_info=False)
```

### 9.2 Metrics to Track
- Number of API calls per session
- Token refresh frequency
- Newsletter detection accuracy
- API error rates
- Processing time per message

## 10. Future Enhancements

### 10.1 Short Term
- Add SQLite cache for processed messages
- Implement incremental sync using History API
- Add configuration UI

### 10.2 Medium Term
- ML-based newsletter classification
- Parallel message processing
- Export to multiple formats (CSV, JSON, Parquet)

### 10.3 Long Term
- Multi-account support
- Web interface
- Newsletter content extraction and analysis
- Integration with knowledge graph system

## 11. Appendices

### 11.1 Google Cloud Console Setup Steps
1. Go to https://console.cloud.google.com
2. Create new project: "Newsletter Extractor"
3. Navigate to "APIs & Services" → "Library"
4. Search for "Gmail API" and click Enable
5. Go to "APIs & Services" → "Credentials"
6. Click "Create Credentials" → "OAuth client ID"
7. Application type: "Desktop app"
8. Name: "Newsletter Extractor Local"
9. Download JSON file as `credentials.json`

### 11.2 Required Permissions
- `https://www.googleapis.com/auth/gmail.readonly` - Read all resources and metadata

### 11.3 API Quotas
- Daily quota: 1,000,000,000 quota units
- Per-user rate limit: 250 quota units/user/second
- `messages.list`: 5 quota units
- `messages.get`: 5 quota units

### 11.4 References
- [Gmail API Documentation](https://developers.google.com/gmail/api/guides)
- [OAuth 2.0 for Desktop Apps](https://developers.google.com/identity/protocols/oauth2/native-app)
- [Google API Python Client](https://github.com/googleapis/google-api-python-client)