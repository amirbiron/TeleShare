"""
מערכת לוגים מתקדמת לבוט הפרסום
"""
import logging
import os
from datetime import datetime
from functools import wraps
import coloredlogs
import json

from config import Config

class CustomFormatter(logging.Formatter):
    """פורמט מותאם עם צבעים ומידע נוסף"""
    
    def __init__(self):
        super().__init__()
        
        # פורמט בסיסי
        self.base_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
        
        # פורמט עם פרטים נוסף לדיבוגינג
        self.detailed_format = (
            "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | "
            "%(funcName)s() | %(message)s"
        )
    
    def format(self, record):
        # בחירת פורמט לפי רמת הלוג
        if record.levelno >= logging.ERROR:
            formatter = logging.Formatter(self.detailed_format)
        else:
            formatter = logging.Formatter(self.base_format)
        
        return formatter.format(record)

def setup_logger(name=None):
    """מקים logger עם הגדרות מותאמות"""
    logger_name = name or __name__
    logger = logging.getLogger(logger_name)
    
    # מניעת כפילות handlers
    if logger.handlers:
        return logger
    
    # קביעת רמת לוג
    log_level = getattr(logging, Config.LOG_LEVEL.upper(), logging.INFO)
    logger.setLevel(log_level)
    
    # יצירת תיקיית לוגים
    log_dir = os.path.dirname(Config.LOG_FILE) if '/' in Config.LOG_FILE else '.'
    os.makedirs(log_dir, exist_ok=True)
    
    # Handler לקובץ
    file_handler = logging.FileHandler(Config.LOG_FILE, encoding='utf-8')
    file_handler.setLevel(log_level)
    file_handler.setFormatter(CustomFormatter())
    
    # Handler לקונסול עם צבעים
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    
    # התקנת coloredlogs לקונסול
    coloredlogs.install(
        level=log_level,
        logger=logger,
        format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        field_styles={
            'asctime': {'color': 'cyan'},
            'levelname': {'bold': True},
            'name': {'color': 'blue'},
        },
        level_styles={
            'debug': {'color': 'white'},
            'info': {'color': 'green'},
            'warning': {'color': 'yellow'},
            'error': {'color': 'red', 'bold': True},
            'critical': {'color': 'red', 'bold': True, 'background': 'white'},
        }
    )
    
    # הוספת file handler
    logger.addHandler(file_handler)
    
    return logger

class BotLogger:
    """מחלקת לוגים מיוחדת לבוט"""
    
    def __init__(self, name="SocialMediaBot"):
        self.logger = setup_logger(name)
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def info(self, message, user_id=None, context=None):
        """לוג רגיל עם פרטים נוספים"""
        self._log_with_context(self.logger.info, message, user_id, context)
    
    def warning(self, message, user_id=None, context=None):
        """לוג אזהרה"""
        self._log_with_context(self.logger.warning, message, user_id, context)
    
    def error(self, message, user_id=None, context=None, error=None):
        """לוג שגיאה עם פרטים מלאים"""
        if error:
            message = f"{message} | שגיאה: {str(error)}"
        self._log_with_context(self.logger.error, message, user_id, context)
    
    def debug(self, message, user_id=None, context=None):
        """לוג דיבוגינג"""
        self._log_with_context(self.logger.debug, message, user_id, context)
    
    def critical(self, message, user_id=None, context=None):
        """לוג קריטי"""
        self._log_with_context(self.logger.critical, message, user_id, context)
    
    def _log_with_context(self, log_func, message, user_id=None, context=None):
        """הוספת הקשר ללוג"""
        log_parts = [f"[{self.session_id}]"]
        
        if user_id:
            log_parts.append(f"[User:{user_id}]")
        
        if context:
            log_parts.append(f"[{context}]")
        
        log_parts.append(message)
        
        log_func(" ".join(log_parts))
    
    def log_user_action(self, user_id, action, details=None):
        """לוג פעולת משתמש"""
        message = f"פעולת משתמש: {action}"
        if details:
            message += f" | פרטים: {details}"
        self.info(message, user_id=user_id, context="USER_ACTION")
    
    def log_post_attempt(self, user_id, platforms, filename, text_preview):
        """לוג ניסיון פרסום"""
        text_short = text_preview[:50] + "..." if len(text_preview) > 50 else text_preview
        message = f"ניסיון פרסום | קובץ: {filename} | פלטפורמות: {', '.join(platforms)} | טקסט: {text_short}"
        self.info(message, user_id=user_id, context="POST_ATTEMPT")
    
    def log_post_result(self, user_id, platform, success, error_msg=None):
        """לוג תוצאת פרסום לפלטפורמה"""
        if success:
            message = f"פרסום הצליח ב-{platform} ✅"
            self.info(message, user_id=user_id, context="POST_SUCCESS")
        else:
            message = f"פרסום נכשל ב-{platform} ❌"
            if error_msg:
                message += f" | שגיאה: {error_msg}"
            self.error(message, user_id=user_id, context="POST_FAILURE")
    
    def log_mock_mode(self, user_id, filename, platforms):
        """לוג מצב בדיקה"""
        message = f"מצב בדיקה - פרסום מדומה | קובץ: {filename} | פלטפורמות: {', '.join(platforms)}"
        self.info(message, user_id=user_id, context="MOCK_MODE")

def log_function_call(func):
    """דקורטור ללוגינג כניסה ויציאה מפונקציות"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = setup_logger()
        logger.debug(f"כניסה לפונקציה: {func.__name__}")
        
        try:
            result = func(*args, **kwargs)
            logger.debug(f"יציאה מפונקציה: {func.__name__} (הצלחה)")
            return result
        except Exception as e:
            logger.error(f"שגיאה בפונקציה: {func.__name__} | {str(e)}")
            raise
    
    return wrapper

def log_async_function_call(func):
    """דקורטור ללוגינג פונקציות אסינכרוניות"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        logger = setup_logger()
        logger.debug(f"כניסה לפונקציה אסינכרונית: {func.__name__}")
        
        try:
            result = await func(*args, **kwargs)
            logger.debug(f"יציאה מפונקציה אסינכרונית: {func.__name__} (הצלחה)")
            return result
        except Exception as e:
            logger.error(f"שגיאה בפונקציה אסינכרונית: {func.__name__} | {str(e)}")
            raise
    
    return wrapper

class DatabaseLogger:
    """לוגר מיוחד לפעולות מסד נתונים"""
    
    def __init__(self):
        self.logger = setup_logger("DatabaseLogger")
    
    def log_save_post(self, user_id, post_data):
        """לוג שמירת פוסט"""
        self.logger.info(f"שמירת פוסט במסד נתונים | משתמש: {user_id} | קובץ: {post_data.get('filename', 'N/A')}")
    
    def log_query(self, collection, query_type, filters=None):
        """לוג שאילתת מסד נתונים"""
        message = f"שאילתה: {query_type} בקולקשן: {collection}"
        if filters:
            message += f" | פילטרים: {json.dumps(filters, ensure_ascii=False)}"
        self.logger.debug(message)
    
    def log_connection_status(self, success, error=None):
        """לוג סטטוס חיבור למסד נתונים"""
        if success:
            self.logger.info("חיבור למסד נתונים הצליח ✅")
        else:
            self.logger.error(f"חיבור למסד נתונים נכשל ❌ | {error}")

# יצירת instance גלובלי
bot_logger = BotLogger()
db_logger = DatabaseLogger()

# פונקציית עזר לקבלת logger
def get_logger(name=None):
    """מחזיר logger מוכן לשימוש"""
    return setup_logger(name)
