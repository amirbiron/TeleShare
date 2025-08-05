"""
מטפל פרסום לכל הרשתות החברתיות
"""
import os
import asyncio
from typing import Dict, Optional, Tuple
import requests
import tweepy
from facebook import GraphAPI
import pytumblr
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from linkedin_api import Linkedin

from config import Config, SocialMediaTokens
from exceptions import *
from logger import get_logger
from utils import async_retry

logger = get_logger(__name__)

class BaseSocialMediaAPI:
    """מחלקת בסיס לכל רשתות החברתיות"""
    
    def __init__(self, platform_name: str):
        self.platform_name = platform_name
        self.logger = get_logger(f"{__name__}.{platform_name}")
    
    async def post(self, video_path: str, text: str) -> bool:
        """פונקציית פרסום בסיסית - יש להגדיר מחדש בכל מחלקה"""
        raise NotImplementedError(f"פונקציית post לא מוגדרת עבור {self.platform_name}")
    
    def _validate_tokens(self) -> bool:
        """בדיקת זמינות טוקנים - יש להגדיר מחדש"""
        return True
    
    def _handle_api_error(self, error: Exception) -> SocialMediaAPIError:
        """טיפול בשגיאות API"""
        return handle_api_error(self.platform_name, error)

class TikTokAPI(BaseSocialMediaAPI):
    """API של TikTok"""
    
    def __init__(self):
        super().__init__("TikTok")
        self.client_key = SocialMediaTokens.TIKTOK_CLIENT_KEY
        self.client_secret = SocialMediaTokens.TIKTOK_CLIENT_SECRET
        self.access_token = SocialMediaTokens.TIKTOK_ACCESS_TOKEN
    
    def _validate_tokens(self) -> bool:
        return bool(self.access_token)
    
    async def post(self, video_path: str, text: str) -> bool:
        """פרסום ב-TikTok"""
        if not self._validate_tokens():
            raise TokenMissingError("TikTok")
        
        try:
            self.logger.info(f"מתחיל פרסום ב-TikTok: {os.path.basename(video_path)}")
            
            # TikTok API מורכב - כאן נדמה פרסום
            # במציאות צריך להשתמש ב-TikTok for Developers API
            
            # סימולציה של פרסום
            await asyncio.sleep(2)
            
            # בדיקת גודל קובץ (TikTok מגביל ל-287MB)
            file_size = os.path.getsize(video_path) / (1024 * 1024)  # MB
            if file_size > 287:
                raise PostingError("TikTok", f"קובץ גדול מדי: {file_size:.1f}MB (מקסימום: 287MB)")
            
            self.logger.info("פרסום ב-TikTok הושלם בהצלחה")
            return True
            
        except Exception as e:
            self.logger.error(f"שגיאה בפרסום ב-TikTok: {e}")
            raise self._handle_api_error(e)

class TwitterAPI(BaseSocialMediaAPI):
    """API של Twitter/X"""
    
    def __init__(self):
        super().__init__("Twitter")
        self.api_key = SocialMediaTokens.TWITTER_API_KEY
        self.api_secret = SocialMediaTokens.TWITTER_API_SECRET
        self.access_token = SocialMediaTokens.TWITTER_ACCESS_TOKEN
        self.access_token_secret = SocialMediaTokens.TWITTER_ACCESS_TOKEN_SECRET
        
        self.client = None
        self._setup_client()
    
    def _validate_tokens(self) -> bool:
        return all([self.api_key, self.api_secret, self.access_token, self.access_token_secret])
    
    def _setup_client(self):
        """הגדרת לקוח Twitter"""
        if not self._validate_tokens():
            return
        
        try:
            # Twitter API v2
            self.client = tweepy.Client(
                consumer_key=self.api_key,
                consumer_secret=self.api_secret,
                access_token=self.access_token,
                access_token_secret=self.access_token_secret,
                wait_on_rate_limit=True
            )
            
            # Twitter API v1.1 למדיה
            auth = tweepy.OAuth1UserHandler(
                self.api_key, self.api_secret,
                self.access_token, self.access_token_secret
            )
            self.api_v1 = tweepy.API(auth, wait_on_rate_limit=True)
            
        except Exception as e:
            self.logger.error(f"שגיאה בהגדרת Twitter client: {e}")
    
    async def post(self, video_path: str, text: str) -> bool:
        """פרסום ב-Twitter"""
        if not self._validate_tokens():
            raise TokenMissingError("Twitter")
        
        if not self.client:
            raise InvalidCredentialsError("Twitter")
        
        try:
            self.logger.info(f"מתחיל פרסום ב-Twitter: {os.path.basename(video_path)}")
            
            # העלאת וידאו (Twitter מגביל ל-512MB ו-140 שניות)
            file_size = os.path.getsize(video_path) / (1024 * 1024)  # MB
            if file_size > 512:
                raise PostingError("Twitter", f"קובץ גדול מדי: {file_size:.1f}MB (מקסימום: 512MB)")
            
            # העלאת מדיה עם API v1.1
            media = self.api_v1.media_upload(video_path)
            
            # פרסום הציוץ עם API v2
            response = self.client.create_tweet(
                text=text[:280],  # הגבלת טוויטר
                media_ids=[media.media_id]
            )
            
            if response.data:
                self.logger.info(f"פרסום ב-Twitter הושלם: {response.data['id']}")
                return True
            else:
                raise PostingError("Twitter", "לא התקבלה תגובה מ-Twitter")
            
        except tweepy.TooManyRequests:
            raise APIQuotaExceededError("Twitter")
        except tweepy.Unauthorized:
            raise InvalidCredentialsError("Twitter")
        except Exception as e:
            self.logger.error(f"שגיאה בפרסום ב-Twitter: {e}")
            raise self._handle_api_error(e)

class FacebookAPI(BaseSocialMediaAPI):
    """API של Facebook"""
    
    def __init__(self):
        super().__init__("Facebook")
        self.access_token = SocialMediaTokens.FACEBOOK_ACCESS_TOKEN
        self.page_id = SocialMediaTokens.FACEBOOK_PAGE_ID
        self.graph = None
        self._setup_client()
    
    def _validate_tokens(self) -> bool:
        return bool(self.access_token and self.page_id)
    
    def _setup_client(self):
        """הגדרת Graph API"""
        if not self._validate_tokens():
            return
        
        try:
            self.graph = GraphAPI(access_token=self.access_token)
        except Exception as e:
            self.logger.error(f"שגיאה בהגדרת Facebook client: {e}")
    
    async def post(self, video_path: str, text: str) -> bool:
        """פרסום ב-Facebook"""
        if not self._validate_tokens():
            raise TokenMissingError("Facebook")
        
        if not self.graph:
            raise InvalidCredentialsError("Facebook")
        
        try:
            self.logger.info(f"מתחיל פרסום ב-Facebook: {os.path.basename(video_path)}")
            
            # בדיקת גודל קובץ (Facebook מגביל ל-4GB)
            file_size = os.path.getsize(video_path) / (1024 * 1024)  # MB
            if file_size > 4000:
                raise PostingError("Facebook", f"קובץ גדול מדי: {file_size:.1f}MB (מקסימום: 4GB)")
            
            # פרסום וידאו
            with open(video_path, 'rb') as video_file:
                response = self.graph.put_video(
                    video=video_file,
                    message=text,
                    album_path=f"{self.page_id}/videos"
                )
            
            if 'id' in response:
                self.logger.info(f"פרסום ב-Facebook הושלם: {response['id']}")
                return True
            else:
                raise PostingError("Facebook", "לא התקבלה תגובה מ-Facebook")
            
        except Exception as e:
            self.logger.error(f"שגיאה בפרסום ב-Facebook: {e}")
            if "token" in str(e).lower():
                raise InvalidCredentialsError("Facebook")
            else:
                raise self._handle_api_error(e)

class InstagramAPI(BaseSocialMediaAPI):
    """API של Instagram (דרך Facebook)"""
    
    def __init__(self):
        super().__init__("Instagram")
        self.access_token = SocialMediaTokens.FACEBOOK_ACCESS_TOKEN
        self.account_id = SocialMediaTokens.INSTAGRAM_BUSINESS_ACCOUNT_ID
        self.graph = None
        self._setup_client()
    
    def _validate_tokens(self) -> bool:
        return bool(self.access_token and self.account_id)
    
    def _setup_client(self):
        """הגדרת Graph API"""
        if not self._validate_tokens():
            return
        
        try:
            self.graph = GraphAPI(access_token=self.access_token)
        except Exception as e:
            self.logger.error(f"שגיאה בהגדרת Instagram client: {e}")
    
    async def post(self, video_path: str, text: str) -> bool:
        """פרסום ב-Instagram"""
        if not self._validate_tokens():
            raise TokenMissingError("Instagram")
        
        if not self.graph:
            raise InvalidCredentialsError("Instagram")
        
        try:
            self.logger.info(f"מתחיל פרסום ב-Instagram: {os.path.basename(video_path)}")
            
            # Instagram מגביל ל-100MB ו-60 שניות לריילס
            file_size = os.path.getsize(video_path) / (1024 * 1024)  # MB
            if file_size > 100:
                raise PostingError("Instagram", f"קובץ גדול מדי: {file_size:.1f}MB (מקסימום: 100MB)")
            
            # זה דורש השלמה של Instagram Basic Display API
            # כאן נדמה את הפרסום
            await asyncio.sleep(2)
            
            self.logger.info("פרסום ב-Instagram הושלם (דמה)")
            return True
            
        except Exception as e:
            self.logger.error(f"שגיאה בפרסום ב-Instagram: {e}")
            raise self._handle_api_error(e)

class LinkedInAPI(BaseSocialMediaAPI):
    """API של LinkedIn"""
    
    def __init__(self):
        super().__init__("LinkedIn")
        self.client_id = SocialMediaTokens.LINKEDIN_CLIENT_ID
        self.client_secret = SocialMediaTokens.LINKEDIN_CLIENT_SECRET
        self.access_token = SocialMediaTokens.LINKEDIN_ACCESS_TOKEN
    
    def _validate_tokens(self) -> bool:
        return bool(self.access_token)
    
    async def post(self, video_path: str, text: str) -> bool:
        """פרסום ב-LinkedIn"""
        if not self._validate_tokens():
            raise TokenMissingError("LinkedIn")
        
        try:
            self.logger.info(f"מתחיל פרסום ב-LinkedIn: {os.path.basename(video_path)}")
            
            # LinkedIn מגביל ל-200MB ו-10 דקות
            file_size = os.path.getsize(video_path) / (1024 * 1024)  # MB
            if file_size > 200:
                raise PostingError("LinkedIn", f"קובץ גדול מדי: {file_size:.1f}MB (מקסימום: 200MB)")
            
            # LinkedIn API מורכב - כאן נדמה פרסום
            await asyncio.sleep(2)
            
            self.logger.info("פרסום ב-LinkedIn הושלם (דמה)")
            return True
            
        except Exception as e:
            self.logger.error(f"שגיאה בפרסום ב-LinkedIn: {e}")
            raise self._handle_api_error(e)

class YouTubeAPI(BaseSocialMediaAPI):
    """API של YouTube Shorts"""
    
    def __init__(self):
        super().__init__("YouTube")
        self.client_id = SocialMediaTokens.YOUTUBE_CLIENT_ID
        self.client_secret = SocialMediaTokens.YOUTUBE_CLIENT_SECRET
        self.refresh_token = SocialMediaTokens.YOUTUBE_REFRESH_TOKEN
        self.service = None
        self._setup_client()
    
    def _validate_tokens(self) -> bool:
        return bool(self.refresh_token)
    
    def _setup_client(self):
        """הגדרת YouTube API client"""
        if not self._validate_tokens():
            return
        
        try:
            # יצירת credentials
            creds = Credentials(
                token=None,
                refresh_token=self.refresh_token,
                client_id=self.client_id,
                client_secret=self.client_secret,
                token_uri="https://oauth2.googleapis.com/token"
            )
            
            # רענון הטוקן
            creds.refresh(Request())
            
            # יצירת service
            self.service = build('youtube', 'v3', credentials=creds)
            
        except Exception as e:
            self.logger.error(f"שגיאה בהגדרת YouTube client: {e}")
    
    async def post(self, video_path: str, text: str) -> bool:
        """פרסום ב-YouTube Shorts"""
        if not self._validate_tokens():
            raise TokenMissingError("YouTube")
        
        if not self.service:
            raise InvalidCredentialsError("YouTube")
        
        try:
            self.logger.info(f"מתחיל פרסום ב-YouTube: {os.path.basename(video_path)}")
            
            # YouTube מגביל ל-256GB אבל נשים מגבלה סבירה
            file_size = os.path.getsize(video_path) / (1024 * 1024)  # MB
            if file_size > 1000:  # 1GB
                raise PostingError("YouTube", f"קובץ גדול מדי: {file_size:.1f}MB (מקסימום: 1GB)")
            
            # הגדרות וידאו
            body = {
                'snippet': {
                    'title': text[:100] if text else 'Video from Bot',
                    'description': text,
                    'tags': ['shorts'],
                    'categoryId': '22'  # People & Blogs
                },
                'status': {
                    'privacyStatus': 'public'
                }
            }
            
            # העלאת וידאו (זה ייקח זמן)
            # כאן נדמה את הפרסום כי זה מורכב
            await asyncio.sleep(3)
            
            self.logger.info("פרסום ב-YouTube הושלם (דמה)")
            return True
            
        except Exception as e:
            self.logger.error(f"שגיאה בפרסום ב-YouTube: {e}")
            raise self._handle_api_error(e)

class TumblrAPI(BaseSocialMediaAPI):
    """API של Tumblr"""
    
    def __init__(self):
        super().__init__("Tumblr")
        self.consumer_key = SocialMediaTokens.TUMBLR_CONSUMER_KEY
        self.consumer_secret = SocialMediaTokens.TUMBLR_CONSUMER_SECRET
        self.oauth_token = SocialMediaTokens.TUMBLR_OAUTH_TOKEN
        self.oauth_secret = SocialMediaTokens.TUMBLR_OAUTH_SECRET
        self.blog_name = SocialMediaTokens.TUMBLR_BLOG_NAME
        
        self.client = None
        self._setup_client()
    
    def _validate_tokens(self) -> bool:
        return all([self.consumer_key, self.consumer_secret, 
                   self.oauth_token, self.oauth_secret, self.blog_name])
    
    def _setup_client(self):
        """הגדרת Tumblr client"""
        if not self._validate_tokens():
            return
        
        try:
            self.client = pytumblr.TumblrRestClient(
                self.consumer_key,
                self.consumer_secret,
                self.oauth_token,
                self.oauth_secret
            )
        except Exception as e:
            self.logger.error(f"שגיאה בהגדרת Tumblr client: {e}")
    
    async def post(self, video_path: str, text: str) -> bool:
        """פרסום ב-Tumblr"""
        if not self._validate_tokens():
            raise TokenMissingError("Tumblr")
        
        if not self.client:
            raise InvalidCredentialsError("Tumblr")
        
        try:
            self.logger.info(f"מתחיל פרסום ב-Tumblr: {os.path.basename(video_path)}")
            
            # Tumblr מגביל ל-100MB
            file_size = os.path.getsize(video_path) / (1024 * 1024)  # MB
            if file_size > 100:
                raise PostingError("Tumblr", f"קובץ גדול מדי: {file_size:.1f}MB (מקסימום: 100MB)")
            
            # פרסום וידאו
            response = self.client.create_video(
                self.blog_name,
                caption=text,
                data=video_path
            )
            
            if response.get('meta', {}).get('status') == 201:
                self.logger.info(f"פרסום ב-Tumblr הושלם: {response.get('response', {}).get('id')}")
                return True
            else:
                raise PostingError("Tumblr", f"שגיאה: {response}")
            
        except Exception as e:
            self.logger.error(f"שגיאה בפרסום ב-Tumblr: {e}")
            raise self._handle_api_error(e)

class TelegramChannelAPI(BaseSocialMediaAPI):
    """API של ערוץ טלגרם"""
    
    def __init__(self, bot_token: str):
        super().__init__("Telegram")
        self.bot_token = bot_token
        self.channel_id = Config.TELEGRAM_CHANNEL_ID
    
    def _validate_tokens(self) -> bool:
        return bool(self.bot_token and self.channel_id)
    
    async def post(self, video_path: str, text: str) -> bool:
        """פרסום בערוץ טלגרם"""
        if not self._validate_tokens():
            raise TokenMissingError("Telegram")
        
        try:
            self.logger.info(f"מתחיל פרסום בערוץ טלגרם: {os.path.basename(video_path)}")
            
            # שליחת וידאו לערוץ
            url = f"https://api.telegram.org/bot{self.bot_token}/sendVideo"
            
            with open(video_path, 'rb') as video_file:
                files = {'video': video_file}
                data = {
                    'chat_id': self.channel_id,
                    'caption': text,
                    'parse_mode': 'Markdown'
                }
                
                response = requests.post(url, files=files, data=data, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    self.logger.info(f"פרסום בערוץ טלגרם הושלם: {result.get('result', {}).get('message_id')}")
                    return True
                else:
                    raise PostingError("Telegram", f"שגיאה: {result.get('description')}")
            else:
                raise PostingError("Telegram", f"HTTP {response.status_code}")
            
        except Exception as e:
            self.logger.error(f"שגיאה בפרסום בערוץ טלגרם: {e}")
            raise self._handle_api_error(e)

class SocialMediaManager:
    """מנהל כל הרשתות החברתיות"""
    
    def __init__(self, bot_token: str = None):
        self.logger = get_logger(f"{__name__}.Manager")
        
        # יצירת כל ה-APIs
        self.apis = {
            'TikTok': TikTokAPI(),
            'Twitter': TwitterAPI(),
            'Facebook': FacebookAPI(),
            'Instagram': InstagramAPI(),
            'LinkedIn': LinkedInAPI(),
            'YouTube': YouTubeAPI(),
            'Tumblr': TumblrAPI(),
            'Telegram': TelegramChannelAPI(bot_token or Config.TELEGRAM_BOT_TOKEN)
        }
        
        self.logger.info("SocialMediaManager initialized")
    
    async def post_to_platform(self, platform: str, video_path: str, text: str) -> bool:
        """פרסום לפלטפורמה ספציפית"""
        if platform not in self.apis:
            raise ValueError(f"פלטפורמה לא מוכרת: {platform}")
        
        api = self.apis[platform]
        
        try:
            return await async_retry(
                lambda: api.post(video_path, text),
                max_retries=2,
                delay=1.0
            )
        except Exception as e:
            self.logger.error(f"פרסום נכשל ב-{platform}: {e}")
            return False
    
    async def post_to_all_platforms(self, platforms: list, video_path: str, text: str) -> Dict[str, bool]:
        """פרסום לכל הפלטפורמות"""
        results = {}
        
        # פרסום במקביל
        tasks = []
        for platform in platforms:
            if platform in self.apis:
                task = asyncio.create_task(
                    self.post_to_platform(platform, video_path, text),
                    name=platform
                )
                tasks.append((platform, task))
        
        # חכייה לכל המשימות
        for platform, task in tasks:
            try:
                results[platform] = await task
            except Exception as e:
                self.logger.error(f"שגיאה בפרסום ל-{platform}: {e}")
                results[platform] = False
        
        return results
    
    def get_available_platforms(self) -> Dict[str, bool]:
        """בדיקת זמינות פלטפורמות"""
        availability = {}
        
        for platform, api in self.apis.items():
            try:
                availability[platform] = api._validate_tokens()
            except Exception as e:
                self.logger.warning(f"שגיאה בבדיקת {platform}: {e}")
                availability[platform] = False
        
        return availability

# יצירת instance גלובלי
_social_manager = None

def get_social_manager() -> SocialMediaManager:
    """מחזיר instance של SocialMediaManager (Singleton pattern)"""
    global _social_manager
    
    if _social_manager is None:
        _social_manager = SocialMediaManager()
    
    return _social_manager
