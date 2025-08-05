"""
שגיאות מותאמות אישית לבוט הפרסום
"""

class SocialMediaBotException(Exception):
    """שגיאה בסיסית של הבוט"""
    def __init__(self, message, error_code=None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)

class FileValidationError(SocialMediaBotException):
    """שגיאות קשורות לבדיקת קבצים"""
    pass

class FileTooLargeError(FileValidationError):
    """קובץ גדול מדי"""
    def __init__(self, file_size_mb, max_size_mb):
        self.file_size_mb = file_size_mb
        self.max_size_mb = max_size_mb
        message = f"קובץ גדול מדי: {file_size_mb}MB (מקסימום: {max_size_mb}MB)"
        super().__init__(message, "FILE_TOO_LARGE")

class UnsupportedFileFormatError(FileValidationError):
    """פורמט קובץ לא נתמך"""
    def __init__(self, file_format, supported_formats):
        self.file_format = file_format
        self.supported_formats = supported_formats
        message = f"פורמט '{file_format}' לא נתמך. פורמטים נתמכים: {', '.join(supported_formats)}"
        super().__init__(message, "UNSUPPORTED_FORMAT")

class MissingContentError(SocialMediaBotException):
    """תוכן חסר"""
    pass

class NoVideoError(MissingContentError):
    """אין סרטון בהודעה"""
    def __init__(self):
        super().__init__("לא נמצא סרטון בהודעה", "NO_VIDEO")

class NoTextError(MissingContentError):
    """אין טקסט בהודעה"""
    def __init__(self):
        super().__init__("לא נמצא טקסט בהודעה", "NO_TEXT")

class DatabaseError(SocialMediaBotException):
    """שגיאות מסד נתונים"""
    pass

class ConnectionError(DatabaseError):
    """שגיאת חיבור למסד נתונים"""
    def __init__(self, db_type="MongoDB"):
        super().__init__(f"לא ניתן להתחבר ל-{db_type}", "DB_CONNECTION_ERROR")

class SaveError(DatabaseError):
    """שגיאת שמירה במסד נתונים"""
    def __init__(self, operation="save"):
        super().__init__(f"שגיאה בביצוע פעולה: {operation}", "DB_SAVE_ERROR")

class SocialMediaAPIError(SocialMediaBotException):
    """שגיאות API של רשתות חברתיות"""
    def __init__(self, platform, message, error_code=None):
        self.platform = platform
        full_message = f"שגיאה ב-{platform}: {message}"
        super().__init__(full_message, error_code)

class TokenMissingError(SocialMediaAPIError):
    """טוקן חסר לרשת חברתית"""
    def __init__(self, platform):
        super().__init__(platform, f"טוקן חסר עבור {platform}", "TOKEN_MISSING")

class APIQuotaExceededError(SocialMediaAPIError):
    """חריגה ממכסת API"""
    def __init__(self, platform):
        super().__init__(platform, f"חרגת ממכסת ה-API של {platform}", "QUOTA_EXCEEDED")

class InvalidCredentialsError(SocialMediaAPIError):
    """פרטי גישה לא תקינים"""
    def __init__(self, platform):
        super().__init__(platform, f"פרטי גישה לא תקינים עבור {platform}", "INVALID_CREDENTIALS")

class PostingError(SocialMediaAPIError):
    """שגיאה כללית בפרסום"""
    def __init__(self, platform, details=""):
        message = f"שגיאה בפרסום"
        if details:
            message += f": {details}"
        super().__init__(platform, message, "POSTING_ERROR")

class ConfigurationError(SocialMediaBotException):
    """שגיאות הגדרה"""
    pass

class MissingConfigError(ConfigurationError):
    """הגדרה חסרה"""
    def __init__(self, config_name):
        super().__init__(f"הגדרה חסרה: {config_name}", "MISSING_CONFIG")

class InvalidConfigError(ConfigurationError):
    """הגדרה לא תקינה"""
    def __init__(self, config_name, expected_format=""):
        message = f"הגדרה לא תקינה: {config_name}"
        if expected_format:
            message += f" (צפוי: {expected_format})"
        super().__init__(message, "INVALID_CONFIG")

class TelegramBotError(SocialMediaBotException):
    """שגיאות בוט טלגרם"""
    pass

class MessageHandlingError(TelegramBotError):
    """שגיאה בטיפול בהודעה"""
    def __init__(self, details=""):
        message = f"שגיאה בטיפול בהודעה"
        if details:
            message += f": {details}"
        super().__init__(message, "MESSAGE_HANDLING_ERROR")

class CallbackError(TelegramBotError):
    """שגיאה בטיפול בכפתור"""
    def __init__(self, callback_data=""):
        message = f"שגיאה בטיפול בכפתור"
        if callback_data:
            message += f" ({callback_data})"
        super().__init__(message, "CALLBACK_ERROR")

# פונקציות עזר לטיפול בשגיאות
def handle_api_error(platform, error):
    """ממיר שגיאות API כלליות לשגיאות מותאמות"""
    error_str = str(error).lower()
    
    if "token" in error_str or "auth" in error_str:
        return InvalidCredentialsError(platform)
    elif "quota" in error_str or "limit" in error_str:
        return APIQuotaExceededError(platform)
    elif "forbidden" in error_str or "unauthorized" in error_str:
        return InvalidCredentialsError(platform)
    else:
        return PostingError(platform, str(error))

def log_error(logger, error, context=""):
    """רושם שגיאה עם הקשר נוסף"""
    error_type = type(error).__name__
    error_code = getattr(error, 'error_code', 'UNKNOWN')
    
    log_message = f"[{error_type}] {error}"
    if context:
        log_message = f"{context} - {log_message}"
    if error_code != 'UNKNOWN':
        log_message += f" (קוד: {error_code})"
    
    logger.error(log_message)
    
    return {
        'error_type': error_type,
        'error_code': error_code,
        'message': str(error),
        'context': context
    }
