import logging
from googleapiclient.errors import HttpError
from datetime import date

class PlaylistManager:
    def __init__(self, youtube_service):
        self.youtube = youtube_service
        self.logger = logging.getLogger(__name__)
    
    @staticmethod
    def _get_playlist_url(playlist_id):
        """Generate YouTube playlist URL"""
        return f"https://www.youtube.com/playlist?list={playlist_id}"
    
    def find_existing_playlist(self, title):
        """Find existing playlist by title"""
        try:
            request = self.youtube.playlists().list(
                part='snippet',
                mine=True,
                maxResults=50
            )
            
            response = request.execute()
            
            for item in response['items']:
                if item['snippet']['title'] == title:
                    playlist_id = item['id']
                    playlist_url = self._get_playlist_url(playlist_id)
                    self.logger.info(f"Found existing playlist: {title} (ID: {playlist_id})")
                    return playlist_id, playlist_url
            
            return None, None
            
        except HttpError as e:
            self.logger.error(f"Error searching for existing playlist: {e}")
            return None, None
    
    def get_playlist_video_ids(self, playlist_id):
        """Get all video IDs currently in the playlist"""
        try:
            video_ids = set()
            next_page_token = None
            
            while True:
                request = self.youtube.playlistItems().list(
                    part='contentDetails',
                    playlistId=playlist_id,
                    maxResults=50,
                    pageToken=next_page_token
                )
                
                response = request.execute()
                
                for item in response['items']:
                    video_ids.add(item['contentDetails']['videoId'])
                
                next_page_token = response.get('nextPageToken')
                if not next_page_token:
                    break
            
            self.logger.debug(f"Found {len(video_ids)} existing videos in playlist")
            return video_ids
            
        except HttpError as e:
            self.logger.error(f"Error getting playlist videos: {e}")
            return set()
    
    def create_playlist(self, title, description, privacy_status='public'):
        """Create a new YouTube playlist"""
        try:
            playlist_body = {
                'snippet': {
                    'title': title,
                    'description': description
                },
                'status': {
                    'privacyStatus': privacy_status
                }
            }
            
            request = self.youtube.playlists().insert(
                part='snippet,status',
                body=playlist_body
            )
            
            response = request.execute()
            playlist_id = response['id']
            playlist_url = self._get_playlist_url(playlist_id)
            
            self.logger.info(f"Created playlist: {title} (ID: {playlist_id})")
            return playlist_id, playlist_url
            
        except HttpError as e:
            self.logger.error(f"Error creating playlist: {e}")
            return None, None
    
    def get_or_create_playlist(self, title, description, privacy_status='public'):
        """Get existing playlist or create new one"""
        # Try to find existing playlist first
        playlist_id, playlist_url = self.find_existing_playlist(title)
        
        if playlist_id:
            return playlist_id, playlist_url, True  # True = existing
        
        # Create new playlist if not found
        playlist_id, playlist_url = self.create_playlist(title, description, privacy_status)
        return playlist_id, playlist_url, False  # False = new
    
    def add_video_to_playlist(self, playlist_id, video_id):
        """Add a video to the specified playlist"""
        try:
            playlist_item_body = {
                'snippet': {
                    'playlistId': playlist_id,
                    'resourceId': {
                        'kind': 'youtube#video',
                        'videoId': video_id
                    }
                }
            }
            
            request = self.youtube.playlistItems().insert(
                part='snippet',
                body=playlist_item_body
            )
            
            request.execute()
            self.logger.debug(f"Added video {video_id} to playlist {playlist_id}")
            return True
            
        except HttpError as e:
            self.logger.error(f"Error adding video {video_id} to playlist: {e}")
            return False
    
    def add_videos_to_playlist(self, playlist_id, videos, skip_duplicates=True):
        """Add multiple videos to playlist in order"""
        successful_adds = 0
        failed_adds = 0
        skipped_duplicates = 0
        
        # Get existing video IDs if skip_duplicates is enabled
        existing_video_ids = set()
        if skip_duplicates:
            existing_video_ids = self.get_playlist_video_ids(playlist_id)
        
        for video in videos:
            video_id = video['video_id']
            
            # Skip if video already exists in playlist
            if skip_duplicates and video_id in existing_video_ids:
                skipped_duplicates += 1
                self.logger.debug(f"Skipped duplicate: {video['title']}")
                continue
            
            if self.add_video_to_playlist(playlist_id, video_id):
                successful_adds += 1
                self.logger.info(f"Added: {video['title']} ({video['source_channel']})")
            else:
                failed_adds += 1
                self.logger.warning(f"Failed to add: {video['title']}")
        
        self.logger.info(f"Playlist update complete: {successful_adds} added, {failed_adds} failed, {skipped_duplicates} duplicates skipped")
        return successful_adds, failed_adds, skipped_duplicates
    
    def generate_playlist_title(self, category, channels, target_date, template='{category}_{date}'):
        """Generate playlist title based on template"""
        date_str = target_date.strftime('%Y%m%d')
        channel_names = ', '.join([ch['name'] for ch in channels])
        
        title = template.format(
            category=category,
            date=date_str,
            channels=channel_names
        )
        
        return title
    
    def generate_playlist_description(self, category, channels, target_date, video_count, template='{category} videos from {channels} uploaded on {date}'):
        """Generate playlist description"""
        date_str = target_date.strftime('%Y-%m-%d')
        channel_names = ', '.join([ch['name'] for ch in channels])
        
        description = template.format(
            category=category,
            date=date_str,
            channels=channel_names,
            count=video_count
        )
        
        description += f"\n\nTotal videos: {video_count}"
        description += f"\nGenerated automatically on {date.today().strftime('%Y-%m-%d')}"
        
        return description