"""
תצורת הבוט - כל ההגדרות והקונפיגורציה
"""
import os
from dotenv import load_dotenv

# טוען משתני סביבה מקובץ .env
load_dotenv()

class Config:
    """הגדרות כלליות של הבוט"""
    
    # Telegram Bot
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    TELEGRAM_CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID')  # לפרסום בערוץ טלגרם
    
    # MongoDB
    MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
    DATABASE_NAME = os.getenv('DATABASE_NAME', 'social_media_bot')
    
    # מצב הרצה
    MOCK_MODE = os.getenv('MOCK_MODE', 'True').lower() == 'true'  # מצב בדיקה
    AUTO_POST_MODE = os.getenv('AUTO_POST_MODE', 'False').lower() == 'true'  # פרסום אוטומטי
    
    # הגדרות קבצים
    MAX_FILE_SIZE_MB = int(os.getenv('MAX_FILE_SIZE_MB', '50'))
    SUPPORTED_VIDEO_FORMATS = ['mp4', 'mov', 'avi', 'mkv']
    TEMP_FOLDER = os.getenv('TEMP_FOLDER', './temp')
    
    # הגדרות לוגים
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'bot.log')

class SocialMediaTokens:
    """טוקנים לרשתות חברתיות"""
    
    # TikTok
    TIKTOK_CLIENT_KEY = os.getenv('TIKTOK_CLIENT_KEY')
    TIKTOK_CLIENT_SECRET = os.getenv('TIKTOK_CLIENT_SECRET')
    TIKTOK_ACCESS_TOKEN = os.getenv('TIKTOK_ACCESS_TOKEN')
    
    # Twitter/X
    TWITTER_API_KEY = os.getenv('TWITTER_API_KEY')
    TWITTER_API_SECRET = os.getenv('TWITTER_API_SECRET')
    TWITTER_ACCESS_TOKEN = os.getenv('TWITTER_ACCESS_TOKEN')
    TWITTER_ACCESS_TOKEN_SECRET = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
    
    # Facebook & Instagram
    FACEBOOK_ACCESS_TOKEN = os.getenv('FACEBOOK_ACCESS_TOKEN')
    FACEBOOK_PAGE_ID = os.getenv('FACEBOOK_PAGE_ID')
    INSTAGRAM_BUSINESS_ACCOUNT_ID = os.getenv('INSTAGRAM_BUSINESS_ACCOUNT_ID')
    
    # LinkedIn
    LINKEDIN_CLIENT_ID = os.getenv('LINKEDIN_CLIENT_ID')
    LINKEDIN_CLIENT_SECRET = os.getenv('LINKEDIN_CLIENT_SECRET')
    LINKEDIN_ACCESS_TOKEN = os.getenv('LINKEDIN_ACCESS_TOKEN')
    
    # YouTube
    YOUTUBE_CLIENT_ID = os.getenv('YOUTUBE_CLIENT_ID')
    YOUTUBE_CLIENT_SECRET = os.getenv('YOUTUBE_CLIENT_SECRET')
    YOUTUBE_REFRESH_TOKEN = os.getenv('YOUTUBE_REFRESH_TOKEN')
    
    # Tumblr
    TUMBLR_CONSUMER_KEY = os.getenv('TUMBLR_CONSUMER_KEY')
    TUMBLR_CONSUMER_SECRET = os.getenv('TUMBLR_CONSUMER_SECRET')
    TUMBLR_OAUTH_TOKEN = os.getenv('TUMBLR_OAUTH_TOKEN')
    TUMBLR_OAUTH_SECRET = os.getenv('TUMBLR_OAUTH_SECRET')
    TUMBLR_BLOG_NAME = os.getenv('TUMBLR_BLOG_NAME')
    
    # Threads (Meta) - בשלב מאוחר
    THREADS_ACCESS_TOKEN = os.getenv('THREADS_ACCESS_TOKEN')

class Messages:
    """הודעות קבועות בעברית"""
    
    # הודעות בוט
    WELCOME_MESSAGE = """
🤖 ברוכים הבאים לבוט הפרסום האוטומטי!

שלחו לי סרטון עם טקסט ואני אפרסם אותו באוטומטי ב-8 רשתות חברתיות:
• TikTok
• Twitter/X  
• Facebook
• Instagram
• LinkedIn
• YouTube Shorts
• Tumblr
• ערוץ טלגרם

📤 פשוט שלחו סרטון + טקסט ונתחיל!
    """
    
    HELP_MESSAGE = """
ℹ️ איך זה עובד:

1️⃣ שלחו סרטון (mp4) עם טקסט
2️⃣ אני אציג לכם תצוגה מקדימה
3️⃣ תאשרו פרסום
4️⃣ הסרטון יופץ לכל הרשתות!

⚙️ הגדרות:
/mock - מצב בדיקה (ללא פרסום אמיתי)
/auto - מצב פרסום אוטומטי
/status - מצב נוכחי
/help - עזרה זו
    """
    
    # הודעות שגיאה
    ERROR_NO_VIDEO = "❌ אנא שלחו סרטון עם טקסט"
    ERROR_FILE_TOO_LARGE = "❌ הקובץ גדול מדי (מקסימום {max_size}MB)"
    ERROR_UNSUPPORTED_FORMAT = "❌ פורמט לא נתמך. בחרו: {formats}"
    ERROR_NO_TEXT = "❌ אנא הוסיפו טקסט לסרטון"
    ERROR_POSTING_FAILED = "❌ שגיאה בפרסום: {error}"
    
    # הודעות הצלחה
    SUCCESS_MOCK_MODE = "📢 [בדיקה] הסרטון לא נשלח באמת – רק מדומה ✅"
    SUCCESS_POSTED = "✅ הסרטון פורסם בהצלחה לכל הרשתות!"
    SUCCESS_POSTED_PARTIAL = "⚠️ הסרטון פורסם ב-{count} מתוך {total} רשתות"
    
    # כפתורים
    BUTTON_CONFIRM = "✅ אישור פרסום"
    BUTTON_CANCEL = "❌ ביטול"
    BUTTON_MOCK_ON = "🧪 מצב בדיקה: פעיל"
    BUTTON_MOCK_OFF = "🧪 מצב בדיקה: כבוי"
    BUTTON_AUTO_ON = "🤖 פרסום אוטומטי: פעיל"
    BUTTON_AUTO_OFF = "🤖 פרסום אוטומטי: כבוי"

# בדיקת הגדרות חובה
def validate_config():
    """בודק שכל ההגדרות החיוניות קיימות"""
    errors = []
    
    if not Config.TELEGRAM_BOT_TOKEN:
        errors.append("TELEGRAM_BOT_TOKEN חסר")
    
    if not Config.MONGODB_URI:
        errors.append("MONGODB_URI חסר")
    
    if errors:
        raise ValueError(f"שגיאות קונפיגורציה: {', '.join(errors)}")
    
    return True
