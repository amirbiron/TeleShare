"""
פונקציות עזר כלליות לבוט הפרסום
"""
import os
import magic
import hashlib
from datetime import datetime
from typing import Optional, Tuple, Dict, List
from PIL import Image
import tempfile
import asyncio

from config import Config, Messages
from exceptions import *
from logger import get_logger

logger = get_logger(__name__)

class FileHelper:
    """עזרים לטיפול בקבצים"""
    
    @staticmethod
    def get_file_size_mb(file_path: str) -> float:
        """מחזיר גודל קובץ במגה-בייט"""
        try:
            size_bytes = os.path.getsize(file_path)
            return round(size_bytes / (1024 * 1024), 2)
        except OSError as e:
            raise FileValidationError(f"לא ניתן לקרוא גודל קובץ: {e}")
    
    @staticmethod
    def get_file_format(file_path: str) -> str:
        """מחזיר פורמט הקובץ"""
        try:
            mime = magic.Magic(mime=True)
            mime_type = mime.from_file(file_path)
            
            # המרת MIME type לסיומת
            format_map = {
                'video/mp4': 'mp4',
                'video/quicktime': 'mov',
                'video/x-msvideo': 'avi',
                'video/x-matroska': 'mkv'
            }
            
            return format_map.get(mime_type, 'unknown')
        except Exception as e:
            # fallback - לקיחת סיומת מהשם
            return file_path.split('.')[-1].lower() if '.' in file_path else 'unknown'
    
    @staticmethod
    def validate_video_file(file_path: str) -> bool:
        """בודק תקינות קובץ וידאו"""
        try:
            # בדיקת גודל
            file_size = FileHelper.get_file_size_mb(file_path)
            if file_size > Config.MAX_FILE_SIZE_MB:
                raise FileTooLargeError(file_size, Config.MAX_FILE_SIZE_MB)
            
            # בדיקת פורמט
            file_format = FileHelper.get_file_format(file_path)
            if file_format not in Config.SUPPORTED_VIDEO_FORMATS:
                raise UnsupportedFileFormatError(file_format, Config.SUPPORTED_VIDEO_FORMATS)
            
            logger.debug(f"קובץ תקין: {file_path} ({file_size}MB, {file_format})")
            return True
            
        except (FileTooLargeError, UnsupportedFileFormatError):
            raise
        except Exception as e:
            raise FileValidationError(f"שגיאה בבדיקת קובץ: {e}")
    
    @staticmethod
    def generate_unique_filename(original_name: str, user_id: int) -> str:
        """יוצר שם קובץ ייחודי"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_ext = original_name.split('.')[-1] if '.' in original_name else 'mp4'
        
        # יצירת hash קצר מה-user_id והזמן
        hash_input = f"{user_id}_{timestamp}_{original_name}"
        short_hash = hashlib.md5(hash_input.encode()).hexdigest()[:8]
        
        return f"{timestamp}_{short_hash}.{file_ext}"
    
    @staticmethod
    def create_temp_directory() -> str:
        """יוצר תיקיית temp ומחזיר את הנתיב"""
        temp_dir = Config.TEMP_FOLDER
        os.makedirs(temp_dir, exist_ok=True)
        return temp_dir
    
    @staticmethod
    def cleanup_temp_files(file_paths: List[str]):
        """מנקה קבצים זמניים"""
        for file_path in file_paths:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.debug(f"קובץ זמני נמחק: {file_path}")
            except Exception as e:
                logger.warning(f"לא ניתן למחוק קובץ זמני {file_path}: {e}")

class TextHelper:
    """עזרים לטיפול בטקסט"""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """מנקה טקסט מתווים מיותרים"""
        if not text:
            return ""
        
        # הסרת רווחים מיותרים
        cleaned = text.strip()
        
        # הסרת שורות ריקות כפולות
        cleaned = '\n'.join(line.strip() for line in cleaned.split('\n') if line.strip())
        
        return cleaned
    
    @staticmethod
    def validate_text(text: str) -> bool:
        """בודק תקינות טקסט"""
        cleaned_text = TextHelper.clean_text(text)
        
        if not cleaned_text:
            raise NoTextError()
        
        if len(cleaned_text) < 3:
            raise MissingContentError("הטקסט קצר מדי (מינימום 3 תווים)")
        
        return True
    
    @staticmethod
    def truncate_text(text: str, max_length: int) -> str:
        """מקצר טקסט לאורך מקסימלי"""
        if len(text) <= max_length:
            return text
        
        return text[:max_length-3] + "..."
    
    @staticmethod
    def extract_hashtags(text: str) -> List[str]:
        """מחלץ האשטגים מטקסט"""
        import re
        hashtags = re.findall(r'#[\w\u0590-\u05FF]+', text)
        return hashtags
    
    @staticmethod
    def get_text_preview(text: str, max_chars: int = 100) -> str:
        """מחזיר תצוגה מקדימה של הטקסט"""
        cleaned = TextHelper.clean_text(text)
        return TextHelper.truncate_text(cleaned, max_chars)

class TimeHelper:
    """עזרים לזמן ותאריכים"""
    
    @staticmethod
    def get_timestamp() -> str:
        """מחזיר חתימת זמן נוכחית"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    @staticmethod
    def get_filename_timestamp() -> str:
        """מחזיר חתימת זמן לשמות קבצים"""
        return datetime.now().strftime("%Y%m%d_%H%M%S")
    
    @staticmethod
    def format_duration(seconds: int) -> str:
        """מעצב משך זמן לפורמט קריא"""
        if seconds < 60:
            return f"{seconds} שניות"
        elif seconds < 3600:
            minutes = seconds // 60
            return f"{minutes} דקות"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours} שעות ו-{minutes} דקות"

class MessageHelper:
    """עזרים להודעות וטקסטים"""
    
    @staticmethod
    def get_error_message(error: Exception) -> str:
        """מחזיר הודעת שגיאה מתאימה למשתמש"""
        if isinstance(error, FileTooLargeError):
            return Messages.ERROR_FILE_TOO_LARGE.format(max_size=Config.MAX_FILE_SIZE_MB)
        elif isinstance(error, UnsupportedFileFormatError):
            return Messages.ERROR_UNSUPPORTED_FORMAT.format(formats=', '.join(Config.SUPPORTED_VIDEO_FORMATS))
        elif isinstance(error, NoVideoError):
            return Messages.ERROR_NO_VIDEO
        elif isinstance(error, NoTextError):
            return Messages.ERROR_NO_TEXT
        elif isinstance(error, SocialMediaAPIError):
            return Messages.ERROR_POSTING_FAILED.format(error=str(error))
        else:
            return f"❌ שגיאה: {str(error)}"
    
    @staticmethod
    def create_preview_message(filename: str, text: str, platforms: List[str]) -> str:
        """יוצר הודעת תצוגה מקדימה"""
        text_preview = TextHelper.get_text_preview(text, 200)
        
        preview = f"""
📹 **תצוגה מקדימה**

📁 **קובץ:** {filename}
📝 **טקסט:** {text_preview}

🌐 **רשתות לפרסום:**
{chr(10).join([f"• {platform}" for platform in platforms])}

האם לפרסם?
        """
        
        return preview.strip()
    
    @staticmethod
    def create_success_message(successful_platforms: List[str], failed_platforms: List[str]) -> str:
        """יוצר הודעת הצלחה/כישלון"""
        total = len(successful_platforms) + len(failed_platforms)
        success_count = len(successful_platforms)
        
        if success_count == total:
            return Messages.SUCCESS_POSTED
        elif success_count == 0:
            return "❌ הפרסום נכשל בכל הרשתות"
        else:
            message = Messages.SUCCESS_POSTED_PARTIAL.format(count=success_count, total=total)
            
            if successful_platforms:
                message += f"\n\n✅ **הצלחות:** {', '.join(successful_platforms)}"
            
            if failed_platforms:
                message += f"\n\n❌ **כישלונות:** {', '.join(failed_platforms)}"
            
            return message

class ValidationHelper:
    """עזרים לבדיקות שונות"""
    
    @staticmethod
    def validate_telegram_message(message) -> Tuple[str, str]:
        """בודק הודעת טלגרם ומחזיר נתיב קובץ וטקסט"""
        # בדיקת וידאו
        if not message.video:
            raise NoVideoError()
        
        # בדיקת טקסט
        text = message.caption or ""
        TextHelper.validate_text(text)
        
        return message.video, TextHelper.clean_text(text)
    
    @staticmethod
    def validate_platform_tokens(platforms: List[str]) -> Dict[str, bool]:
        """בודק אילו פלטפורמות זמינות (יש להן טוקנים)"""
        from config import SocialMediaTokens
        
        availability = {}
        
        token_mapping = {
            'TikTok': SocialMediaTokens.TIKTOK_ACCESS_TOKEN,
            'Twitter': SocialMediaTokens.TWITTER_ACCESS_TOKEN,
            'Facebook': SocialMediaTokens.FACEBOOK_ACCESS_TOKEN,
            'Instagram': SocialMediaTokens.INSTAGRAM_BUSINESS_ACCOUNT_ID,
            'LinkedIn': SocialMediaTokens.LINKEDIN_ACCESS_TOKEN,
            'YouTube': SocialMediaTokens.YOUTUBE_REFRESH_TOKEN,
            'Tumblr': SocialMediaTokens.TUMBLR_OAUTH_TOKEN,
            'Telegram': Config.TELEGRAM_CHANNEL_ID
        }
        
        for platform in platforms:
            token = token_mapping.get(platform)
            availability[platform] = bool(token and token.strip())
        
        return availability

async def async_retry(func, max_retries: int = 3, delay: float = 1.0):
    """מנסה שוב פונקציה אסינכרונית עם השהיה"""
    last_error = None
    
    for attempt in range(max_retries):
        try:
            if asyncio.iscoroutinefunction(func):
                return await func()
            else:
                return func()
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                logger.warning(f"ניסיון {attempt + 1} נכשל, מנסה שוב בעוד {delay} שניות...")
                await asyncio.sleep(delay)
                delay *= 2  # exponential backoff
            else:
                logger.error(f"כל הניסיונות נכשלו")
    
    raise last_error

def format_file_size(size_bytes: int) -> str:
    """מעצב גודל קובץ לפורמט קריא"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"

def safe_filename(filename: str) -> str:
    """מנקה שם קובץ מתווים לא חוקיים"""
    import re
    # הסרת תווים לא חוקיים
    safe_name = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # הגבלת אורך
    if len(safe_name) > 100:
        name_part = safe_name[:90]
        ext_part = safe_name[-10:] if '.' in safe_name[-10:] else ''
        safe_name = name_part + ext_part
    
    return safe_name
