#!/usr/bin/env python3
"""
YouTube Playlist Creator
Creates playlists from videos uploaded by specified channels within a date range.
"""

import argparse
import logging
import sys
import webbrowser
from datetime import date, datetime
from auth import get_authenticated_service
from config import CHANNELS, CATEGORIES, DateConfig, PLAYLIST_CONFIG
from video_search import VideoSearcher
from playlist_manager import PlaylistManager

def setup_logging():
    """Set up logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('youtube_playlist.log')
        ]
    )

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Create YouTube playlists from channel videos by category and date'
    )
    
    parser.add_argument(
        '--category', '-c',
        default='news',
        choices=list(CATEGORIES.keys()),
        help='Category of channels to search (default: news)'
    )
    
    parser.add_argument(
        '--date', '-d',
        type=str,
        help='Target date in YYYY-MM-DD format (default: today)'
    )
    
    return parser.parse_args()

def main():
    """Main function to create YouTube playlist"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Parse command line arguments
        args = parse_arguments()
        
        # Parse target date
        target_date = date.today()
        if args.date:
            try:
                target_date = datetime.strptime(args.date, '%Y-%m-%d').date()
            except ValueError:
                logger.error(f"Invalid date format: {args.date}. Use YYYY-MM-DD")
                sys.exit(1)
        
        # Get category configuration
        category_config = CATEGORIES.get(args.category, {})
        if not category_config:
            logger.error(f"No configuration found for category: {args.category}")
            sys.exit(1)
            
        category_channel_names = category_config.get('channels', [])
        hours_back = category_config.get('hours_back')
        
        if not category_channel_names:
            logger.error(f"No channels configured for category: {args.category}")
            sys.exit(1)
        
        # Get channel configurations
        channel_configs = [
            CHANNELS[name] for name in category_channel_names 
            if name in CHANNELS
        ]
        
        # Warn about missing channels
        missing_channels = [name for name in category_channel_names if name not in CHANNELS]
        for missing in missing_channels:
            logger.warning(f"Channel '{missing}' not found in CHANNELS config")
        
        if not channel_configs:
            logger.error(f"No valid channels found for category: {args.category}")
            sys.exit(1)
        
        # Initialize date configuration with category-specific hours_back
        date_config = DateConfig(target_date, hours_back)
        published_after, published_before = date_config.get_iso_format()
        
        logger.info(f"Category: {args.category}")
        logger.info(f"Channels: {[ch['name'] for ch in channel_configs]}")
        if hours_back:
            logger.info(f"Searching for videos from last {hours_back} hours")
        else:
            logger.info(f"Searching for videos from {target_date}")
        logger.info(f"Time range: {published_after} to {published_before}")
        
        # Get authenticated YouTube service
        logger.info("Authenticating with YouTube API...")
        youtube = get_authenticated_service()
        
        # Initialize searcher and playlist manager
        searcher = VideoSearcher(youtube)
        playlist_manager = PlaylistManager(youtube)
        
        # Search for videos from configured channels
        logger.info(f"Searching videos from {len(channel_configs)} channel(s)...")
        videos = searcher.search_multiple_channels(
            channel_configs, 
            published_after, 
            published_before,
            max_results_per_channel=50
        )
        
        if not videos:
            logger.warning("No videos found for the specified criteria")
            print("📭 No videos found matching your criteria")
            return
        
        logger.info(f"Found {len(videos)} total videos")
        
        # Display video summary
        for video in videos:
            logger.info(f"  {video['published_at'][:16]} | {video['source_channel']} | {video['title']}")
        
        # Generate playlist title and description
        title = playlist_manager.generate_playlist_title(
            args.category,
            channel_configs, 
            target_date, 
            PLAYLIST_CONFIG['name_template']
        )
        
        description = playlist_manager.generate_playlist_description(
            args.category,
            channel_configs, 
            target_date, 
            len(videos),
            PLAYLIST_CONFIG['description_template']
        )
        
        # Get or create playlist (reuse existing if found)
        logger.info(f"Looking for existing playlist: {title}")
        playlist_id, playlist_url, is_existing = playlist_manager.get_or_create_playlist(
            title, 
            description, 
            PLAYLIST_CONFIG['privacy_status']
        )
        
        if not playlist_id:
            logger.error("Failed to create or find playlist")
            print("❌ Failed to create or find playlist")
            return
        
        if is_existing:
            logger.info(f"Using existing playlist: {title}")
        else:
            logger.info(f"Created new playlist: {title}")
        
        # Add videos to playlist (skip duplicates)
        logger.info("Adding videos to playlist...")
        successful, failed, skipped = playlist_manager.add_videos_to_playlist(
            playlist_id, videos, skip_duplicates=True
        )
        
        # Final summary
        logger.info("=" * 50)
        logger.info("PLAYLIST UPDATE SUMMARY")
        logger.info("=" * 50)
        logger.info(f"Category: {args.category}")
        logger.info(f"Date: {target_date}")
        logger.info(f"Playlist: {title}")
        logger.info(f"URL: {playlist_url}")
        logger.info(f"Videos added: {successful}")
        logger.info(f"Videos failed: {failed}")
        logger.info(f"Duplicates skipped: {skipped}")
        logger.info(f"Total videos found: {len(videos)}")
        logger.info("=" * 50)
        
        if successful > 0:
            print(f"\n✅ Added {successful} new videos to playlist!")
        elif skipped > 0:
            print(f"\n📋 No new videos found (skipped {skipped} duplicates)")
        else:
            print(f"\n❓ No videos added")
            
        print(f"🔗 {playlist_url}")
        
        # Open playlist in default browser
        try:
            webbrowser.open(playlist_url)
            print("🌐 Opening playlist in your default browser...")
        except Exception as e:
            logger.debug(f"Could not open browser: {e}")
            # Don't show error to user, they still have the URL
        
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()