"""
נקודת כניסה ראשית לבוט הפרסום האוטומטי
🤖 Social Media Auto-Posting Bot
"""
import asyncio
import signal
import sys
import os
from typing import Optional

# הוספת נתיב הפרויקט לPython path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config, validate_config
from exceptions import *
from logger import bot_logger, get_logger
from database import get_database
from telegram_bot import get_bot
from social_media_handler import get_social_manager
from utils import FileHelper

logger = get_logger(__name__)

class BotApplication:
    """מחלקה ראשית להרצת הבוט"""
    
    def __init__(self):
        self.bot = None
        self.social_manager = None
        self.database = None
        self.running = False
        
        # הגדרת signal handlers לכיבוי נקי
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    async def initialize(self):
        """אתחול כל הרכיבים"""
        try:
            logger.info("🚀 מתחיל אתחול בוט הפרסום האוטומטי...")
            
            # 1. בדיקת קונפיגורציה
            self._validate_configuration()
            
            # 2. אתחול מסד נתונים
            await self._initialize_database()
            
            # 3. אתחול מטפל רשתות חברתיות
            await self._initialize_social_manager()
            
            # 4. אתחול בוט טלגרם
            await self._initialize_telegram_bot()
            
            # 5. יצירת תיקיות נדרשות
            self._create_directories()
            
            # 6. הצגת מידע על הבוט
            self._show_startup_info()
            
            logger.info("✅ אתחול הושלם בהצלחה!")
            
        except Exception as e:
            logger.critical(f"❌ שגיאה קריטית באתחול: {e}")
            raise
    
    def _validate_configuration(self):
        """בדיקת קונפיגורציה"""
        try:
            validate_config()
            logger.info("✅ קונפיגורציה תקינה")
        except ValueError as e:
            raise ConfigurationError(f"קונפיגורציה לא תקינה: {e}")
    
    async def _initialize_database(self):
        """אתחול מסד נתונים"""
        try:
            self.database = get_database()
            
            # בדיקת חיבור
            if not self.database.health_check():
                raise ConnectionError("MongoDB")
            
            logger.info("✅ חיבור למסד נתונים הצליח")
            
            # ניקוי קבצים ישנים (אופציונלי)
            if Config.LOG_LEVEL.upper() == 'DEBUG':
                self.database.cleanup_old_logs(days_old=3)
                self.database.cleanup_old_posts(days_old=14)
            
        except Exception as e:
            logger.error(f"❌ שגיאה באתחול מסד נתונים: {e}")
            raise
    
    async def _initialize_social_manager(self):
        """אתחול מטפל רשתות חברתיות"""
        try:
            self.social_manager = get_social_manager()
            
            # בדיקת זמינות פלטפורמות
            available_platforms = self.social_manager.get_available_platforms()
            available_count = sum(available_platforms.values())
            
            logger.info(f"📱 רשתות זמינות: {available_count}/8")
            
            for platform, available in available_platforms.items():
                status = "✅" if available else "❌"
                logger.info(f"  {status} {platform}")
            
            if available_count == 0:
                logger.warning("⚠️ אין רשתות זמינות! בדקו הגדרות הטוקנים")
            
        except Exception as e:
            logger.error(f"❌ שגיאה באתחול מטפל רשתות: {e}")
            raise
    
    async def _initialize_telegram_bot(self):
        """אתחול בוט טלגרם"""
        try:
            self.bot = get_bot()
            
            # חיבור מטפל הרשתות לבוט
            self.bot.set_social_handler(self.social_manager)
            
            logger.info("🤖 בוט טלגרם מוכן לפעולה")
            
        except Exception as e:
            logger.error(f"❌ שגיאה באתחול בוט טלגרם: {e}")
            raise
    
    def _create_directories(self):
        """יצירת תיקיות נדרשות"""
        try:
            # תיקיית קבצים זמניים
            temp_dir = FileHelper.create_temp_directory()
            logger.debug(f"תיקיית temp: {temp_dir}")
            
            # תיקיית לוגים
            log_dir = os.path.dirname(Config.LOG_FILE) if '/' in Config.LOG_FILE else '.'
            os.makedirs(log_dir, exist_ok=True)
            
        except Exception as e:
            logger.warning(f"שגיאה ביצירת תיקיות: {e}")
    
    def _show_startup_info(self):
        """הצגת מידע על הבוט"""
        info = f"""
╔══════════════════════════════════════╗
║      🤖 בוט פרסום אוטומטי             ║
╠══════════════════════════════════════╣
║ מצב בדיקה: {'פעיל' if Config.MOCK_MODE else 'כבוי'}    ║
║ פרסום אוטומטי: {'פעיל' if Config.AUTO_POST_MODE else 'כבוי'} ║
║ מסד נתונים: {Config.DATABASE_NAME}        ║
║ גודל מקס: {Config.MAX_FILE_SIZE_MB}MB           ║
╚══════════════════════════════════════╝
        """
        
        logger.info(info.strip())
        
        # הודעות חשובות
        if Config.MOCK_MODE:
            logger.warning("🧪 מצב בדיקה פעיל - פרסומים יהיו מדומים!")
        
        if not Config.TELEGRAM_CHANNEL_ID:
            logger.warning("⚠️ לא הוגדר ערוץ טלגרם לפרסום")
    
    async def run(self):
        """הרצת הבוט"""
        if not self.bot:
            raise RuntimeError("הבוט לא אותחל")
        
        try:
            self.running = True
            logger.info("🚀 מתחיל הרצת הבוט...")
            
            # רישום התחלת הפעלה
            bot_logger.info("בוט הופעל", context="STARTUP")
            
            # הרצת הבוט
            await self.bot.run()
            
        except Exception as e:
            logger.critical(f"❌ שגיאה קריטית: {e}")
            raise
        finally:
            await self.cleanup()
    
    async def cleanup(self):
        """ניקוי ויציאה נקייה"""
        if not self.running:
            return
        
        logger.info("🧹 מתחיל ניקוי...")
        
        try:
            # עצירת הבוט
            if self.bot:
                self.bot.stop()
                logger.info("✅ בוט טלגרם נעצר")
            
            # סגירת חיבור למסד נתונים
            if self.database:
                self.database.close_connection()
                logger.info("✅ חיבור מסד נתונים נסגר")
            
            # ניקוי קבצים זמניים
            temp_files = []
            temp_dir = Config.TEMP_FOLDER
            if os.path.exists(temp_dir):
                for file in os.listdir(temp_dir):
                    if file.startswith('temp_'):
                        temp_files.append(os.path.join(temp_dir, file))
                
                if temp_files:
                    FileHelper.cleanup_temp_files(temp_files)
                    logger.info(f"✅ נוקו {len(temp_files)} קבצים זמניים")
            
            # רישום סיום
            bot_logger.info("בוט נכבה", context="SHUTDOWN")
            logger.info("👋 ניקוי הושלם - להתראות!")
            
        except Exception as e:
            logger.error(f"שגיאה בניקוי: {e}")
        finally:
            self.running = False
    
    def _signal_handler(self, signum, frame):
        """טיפול בסיגנלי כיבוי"""
        signal_name = signal.Signals(signum).name
        logger.info(f"🛑 התקבל סיגנל כיבוי: {signal_name}")
        
        # יציאה חדה במקרה של סיגנל שני
        if not self.running:
            logger.warning("🚨 סיגנל כיבוי שני - יציאה מיידית!")
            sys.exit(1)
        
        # יצירת task לניקוי
        asyncio.create_task(self._graceful_shutdown())
    
    async def _graceful_shutdown(self):
        """כיבוי הדרגתי"""
        logger.info("⏳ מתחיל כיבוי הדרגתי...")
        await self.cleanup()
        
        # יציאה מהלולאה הראשית
        loop = asyncio.get_running_loop()
        loop.stop()

async def main():
    """פונקציה ראשית"""
    app = BotApplication()
    
    try:
        # אתחול
        await app.initialize()
        
        # הרצה
        await app.run()
        
    except KeyboardInterrupt:
        logger.info("🛑 הבוט נעצר על ידי המשתמש")
    except Exception as e:
        logger.critical(f"💥 שגיאה קטלנית: {e}")
        sys.exit(1)
    finally:
        # ניקוי סופי
        await app.cleanup()

def run_bot():
    """פונקציית עזר להרצת הבוט"""
    try:
        # הרצה עם asyncio
        if sys.platform == 'win32':
            # תמיכה ב-Windows
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        
        asyncio.run(main())
        
    except KeyboardInterrupt:
        pass  # כבר טופל
    except Exception as e:
        logger.critical(f"💥 שגיאה לא צפויה: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # בדיקת Python version
    if sys.version_info < (3, 8):
        print("❌ נדרש Python 3.8 או חדש יותר")
        sys.exit(1)
    
    # הרצת הבוט
    run_bot()
