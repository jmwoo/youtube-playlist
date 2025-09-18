import logging
from datetime import datetime
from googleapiclient.errors import HttpError

class VideoSearcher:
    def __init__(self, youtube_service):
        self.youtube = youtube_service
        self.logger = logging.getLogger(__name__)
    
    def get_channel_id_from_handle(self, handle):
        """Get channel ID from @handle"""
        try:
            # Remove @ if present
            clean_handle = handle.lstrip('@')
            
            # Search for channel by handle
            request = self.youtube.search().list(
                part='snippet',
                type='channel',
                q=clean_handle,
                maxResults=1
            )
            response = request.execute()
            
            if response['items']:
                return response['items'][0]['snippet']['channelId']
            else:
                self.logger.error(f"Channel not found for handle: {handle}")
                return None
                
        except HttpError as e:
            self.logger.error(f"Error finding channel {handle}: {e}")
            return None
    
    def search_channel_videos(self, channel_id, published_after, published_before, max_results=50):
        """Search for videos from a specific channel within date range"""
        try:
            videos = []
            next_page_token = None
            
            while len(videos) < max_results:
                request = self.youtube.search().list(
                    part='snippet',
                    channelId=channel_id,
                    type='video',
                    publishedAfter=published_after,
                    publishedBefore=published_before,
                    order='date',
                    maxResults=min(50, max_results - len(videos)),
                    pageToken=next_page_token
                )
                
                response = request.execute()
                
                for item in response['items']:
                    description = item['snippet']['description']
                    video_data = {
                        'video_id': item['id']['videoId'],
                        'title': item['snippet']['title'],
                        'published_at': item['snippet']['publishedAt'],
                        'channel_title': item['snippet']['channelTitle'],
                        'description': description[:100] + '...' if len(description) > 100 else description
                    }
                    videos.append(video_data)
                
                next_page_token = response.get('nextPageToken')
                if not next_page_token:
                    break
            
            self.logger.info(f"Found {len(videos)} videos for channel {channel_id}")
            return videos
            
        except HttpError as e:
            self.logger.error(f"Error searching videos for channel {channel_id}: {e}")
            return []
    
    def search_multiple_channels(self, channel_configs, published_after, published_before, max_results_per_channel=50):
        """Search videos from multiple channels and combine results"""
        all_videos = []
        
        for channel_config in channel_configs:
            channel_id = channel_config.get('channel_id')
            if not channel_id:
                # Try to get channel ID from handle
                channel_id = self.get_channel_id_from_handle(channel_config['handle'])
                if not channel_id:
                    continue
            
            videos = self.search_channel_videos(
                channel_id, 
                published_after, 
                published_before, 
                max_results_per_channel
            )
            
            # Add channel name to each video
            for video in videos:
                video['source_channel'] = channel_config['name']
            
            all_videos.extend(videos)
        
        # Sort all videos by publish date
        all_videos.sort(key=lambda x: x['published_at'])
        
        self.logger.info(f"Total videos found across all channels: {len(all_videos)}")
        return all_videos