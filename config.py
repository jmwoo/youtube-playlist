from datetime import datetime, date, timezone, timedelta

CHANNELS = {
    'CNBC': {
        'name': 'CNBC',
        'channel_id': 'UCrp_UI8XtuYfpiqluWLD7Lw',
        'handle': '@CNBCtelevision'
    }
    # Add more channels here as needed
}

# Category definitions - which channels belong to which categories, hours_back to adjust recency
CATEGORIES = {
    'news': {
        'channels': ['CNBC'],
        'hours_back': 7 
    },
    'dev': {
        'channels': [],
        'hours_back': 24
    }
}

# Date range configuration
class DateConfig:
    def __init__(self, target_date=None, hours_back=None):
        self.target_date = target_date or date.today()
        self.hours_back = hours_back
    
    def get_date_range(self):
        """Get date range - either full day or last N hours"""
        end_time = datetime.now(timezone.utc)
        
        # If not today, use end of that day
        if self.target_date != date.today():
            end_time = datetime.combine(self.target_date, datetime.max.time()).replace(tzinfo=timezone.utc)
        
        # If hours_back is specified, use that instead of full day
        if self.hours_back:
            start_time = end_time - timedelta(hours=self.hours_back)
        else:
            # Default: from midnight of target date
            start_time = datetime.combine(self.target_date, datetime.min.time()).replace(tzinfo=timezone.utc)
        
        return start_time, end_time
    
    def get_iso_format(self):
        """Get ISO format strings for YouTube API"""
        start_time, end_time = self.get_date_range()
        return start_time.isoformat().replace('+00:00', 'Z'), end_time.isoformat().replace('+00:00', 'Z')

# Playlist configuration
PLAYLIST_CONFIG = {
    'privacy_status': 'unlisted',  # 'public', 'private', or 'unlisted'
    'name_template': '{category}_{date}',  # Use {category}, {date} for YYYYMMDD format
    'description_template': '{category} videos from {channels} uploaded on {date}'
}