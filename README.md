# YouTube Playlist Creator

Creates YouTube playlists from videos uploaded by specified channels within a date range.
Great for consuming new content from your favorite channels during your daily routine.

## Setup

1. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up Google Cloud API credentials (see setup instructions below)

4. Run the script:
```bash
# Default: news category, today's date
python main.py

# Specify category and date
python main.py --category news --date 2025-09-16

# Short form
python main.py -c news -d 2025-09-16
```

## Google Cloud Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable YouTube Data API v3
4. Create OAuth 2.0 credentials
5. Download credentials as `credentials.json`
6. Place `credentials.json` in the project root

## Features

- **Category-based organization** - Group channels by category (news, dev, etc.)
- **Playlist reuse** - Finds existing playlists or creates new ones
- **Duplicate detection** - Skips videos already in playlist
- **Flexible date ranges** - Search any date (defaults to today)
- **Command-line interface** - Easy to use and automate
- **OAuth 2.0 authentication** - One-time setup with token persistence
- **Multi-channel support** - Add multiple channels per category

## Usage Examples

**Morning routine** (6am):
```bash
python main.py  # Creates "news_20250917" with today's videos
```

**Later in the day** (8am):
```bash
python main.py  # Adds NEW videos to existing "news_20250917" playlist
```

**Catch up on yesterday**:
```bash
python main.py --date 2025-09-16  # Creates/updates "news_20250916"
```