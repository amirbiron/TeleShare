"""
מערכת מסד נתונים MongoDB לבוט הפרסום
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
import pymongo
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure

from config import Config
from exceptions import *
from logger import db_logger, get_logger

logger = get_logger(__name__)

class DatabaseManager:
    """מנהל מסד הנתונים"""
    
    def __init__(self):
        self.client: Optional[MongoClient] = None
        self.db = None
        self.collections = {}
        self._connect()
    
    def _connect(self):
        """יצירת חיבור למסד הנתונים"""
        try:
            self.client = MongoClient(Config.MONGODB_URI, serverSelectionTimeoutMS=5000)
            
            # בדיקת חיבור
            self.client.admin.command('ping')
            
            self.db = self.client[Config.DATABASE_NAME]
            self._setup_collections()
            
            db_logger.log_connection_status(True)
            logger.info("חיבור למסד נתונים הצליח")
            
        except ConnectionFailure as e:
            db_logger.log_connection_status(False, str(e))
            raise ConnectionError("MongoDB")
        except Exception as e:
            db_logger.log_connection_status(False, str(e))
            raise DatabaseError(f"שגיאה בחיבור למסד נתונים: {e}")
    
    def _setup_collections(self):
        """הגדרת קולקשנים"""
        # קולקשן פוסטים
        self.collections['posts'] = self.db.posts
        
        # קולקשן משתמשים
        self.collections['users'] = self.db.users
        
        # קולקשן לוגים
        self.collections['logs'] = self.db.logs
        
        # יצירת אינדקסים
        self._create_indexes()
    
    def _create_indexes(self):
        """יצירת אינדקסים לביצועים טובים יותר"""
        try:
            # אינדקס על user_id ותאריך
            self.collections['posts'].create_index([("user_id", 1), ("created_at", -1)])
            
            # אינדקס על סטטוס פרסום
            self.collections['posts'].create_index("status")
            
            # אינדקס על תאריך ברירת מחדל
            self.collections['logs'].create_index([("timestamp", -1)])
            
            logger.debug("אינדקסים נוצרו בהצלחה")
            
        except Exception as e:
            logger.warning(f"שגיאה ביצירת אינדקסים: {e}")
    
    def save_post(self, user_id: int, filename: str, text: str, 
                  platforms: List[str], file_size_mb: float) -> str:
        """שמירת פוסט חדש"""
        try:
            post_data = {
                'user_id': user_id,
                'filename': filename,
                'text': text,
                'text_preview': text[:100] + "..." if len(text) > 100 else text,
                'platforms': platforms,
                'file_size_mb': file_size_mb,
                'status': 'created',
                'created_at': datetime.now(),
                'updated_at': datetime.now(),
                'posting_results': {},
                'mock_mode': Config.MOCK_MODE
            }
            
            result = self.collections['posts'].insert_one(post_data)
            post_id = str(result.inserted_id)
            
            db_logger.log_save_post(user_id, post_data)
            logger.info(f"פוסט נשמר במסד נתונים: {post_id}")
            
            return post_id
            
        except Exception as e:
            raise SaveError(f"שמירת פוסט: {e}")
    
    def update_post_status(self, post_id: str, status: str, 
                          posting_results: Optional[Dict] = None):
        """עדכון סטטוס פוסט"""
        try:
            from bson import ObjectId
            
            update_data = {
                'status': status,
                'updated_at': datetime.now()
            }
            
            if posting_results:
                update_data['posting_results'] = posting_results
            
            result = self.collections['posts'].update_one(
                {'_id': ObjectId(post_id)},
                {'$set': update_data}
            )
            
            if result.modified_count == 0:
                logger.warning(f"לא נמצא פוסט לעדכון: {post_id}")
            else:
                logger.debug(f"סטטוס פוסט עודכן: {post_id} -> {status}")
            
        except Exception as e:
            raise SaveError(f"עדכון סטטוס פוסט: {e}")
    
    def get_user_posts(self, user_id: int, limit: int = 10) -> List[Dict]:
        """קבלת פוסטים של משתמש"""
        try:
            db_logger.log_query('posts', 'find', {'user_id': user_id})
            
            posts = list(self.collections['posts'].find(
                {'user_id': user_id}
            ).sort('created_at', -1).limit(limit))
            
            # המרת ObjectId לstring
            for post in posts:
                post['_id'] = str(post['_id'])
            
            return posts
            
        except Exception as e:
            raise DatabaseError(f"שגיאה בקבלת פוסטים: {e}")
    
    def get_post_by_id(self, post_id: str) -> Optional[Dict]:
        """קבלת פוסט לפי ID"""
        try:
            from bson import ObjectId
            
            post = self.collections['posts'].find_one({'_id': ObjectId(post_id)})
            
            if post:
                post['_id'] = str(post['_id'])
            
            return post
            
        except Exception as e:
            logger.error(f"שגיאה בקבלת פוסט {post_id}: {e}")
            return None
    
    def save_user_settings(self, user_id: int, settings: Dict):
        """שמירת הגדרות משתמש"""
        try:
            user_data = {
                'user_id': user_id,
                'settings': settings,
                'updated_at': datetime.now()
            }
            
            # upsert - עדכון או יצירה אם לא קיים
            self.collections['users'].update_one(
                {'user_id': user_id},
                {'$set': user_data, '$setOnInsert': {'created_at': datetime.now()}},
                upsert=True
            )
            
            logger.debug(f"הגדרות משתמש {user_id} נשמרו")
            
        except Exception as e:
            raise SaveError(f"שמירת הגדרות משתמש: {e}")
    
    def get_user_settings(self, user_id: int) -> Dict:
        """קבלת הגדרות משתמש"""
        try:
            user = self.collections['users'].find_one({'user_id': user_id})
            
            if user and 'settings' in user:
                return user['settings']
            else:
                # הגדרות ברירת מחדל
                default_settings = {
                    'mock_mode': Config.MOCK_MODE,
                    'auto_post': Config.AUTO_POST_MODE,
                    'preferred_platforms': ['TikTok', 'Twitter', 'Instagram', 'YouTube']
                }
                
                # שמירת הגדרות ברירת מחדל
                self.save_user_settings(user_id, default_settings)
                return default_settings
                
        except Exception as e:
            logger.error(f"שגיאה בקבלת הגדרות משתמש {user_id}: {e}")
            # החזרת הגדרות ברירת מחדל במקרה של שגיאה
            return {
                'mock_mode': Config.MOCK_MODE,
                'auto_post': Config.AUTO_POST_MODE,
                'preferred_platforms': ['TikTok', 'Twitter', 'Instagram', 'YouTube']
            }
    
    def log_action(self, user_id: int, action: str, details: Dict = None, 
                   level: str = 'info'):
        """שמירת לוג פעולה במסד נתונים"""
        try:
            log_data = {
                'user_id': user_id,
                'action': action,
                'details': details or {},
                'level': level,
                'timestamp': datetime.now()
            }
            
            self.collections['logs'].insert_one(log_data)
            
        except Exception as e:
            # אם נכשלה שמירת הלוג, רק נרשום ללוג רגיל
            logger.error(f"שגיאה בשמירת לוג במסד נתונים: {e}")
    
    def get_statistics(self) -> Dict:
        """קבלת סטטיסטיקות כלליות"""
        try:
            stats = {}
            
            # סך פוסטים
            stats['total_posts'] = self.collections['posts'].count_documents({})
            
            # פוסטים מהיום האחרון
            yesterday = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            stats['posts_today'] = self.collections['posts'].count_documents({
                'created_at': {'$gte': yesterday}
            })
            
            # פוסטים מוצלחים
            stats['successful_posts'] = self.collections['posts'].count_documents({
                'status': 'completed'
            })
            
            # סך משתמשים
            stats['total_users'] = self.collections['users'].count_documents({})
            
            # פלטפורמות פופולריות
            pipeline = [
                {'$unwind': '$platforms'},
                {'$group': {'_id': '$platforms', 'count': {'$sum': 1}}},
                {'$sort': {'count': -1}},
                {'$limit': 10}
            ]
            
            platform_stats = list(self.collections['posts'].aggregate(pipeline))
            stats['popular_platforms'] = {item['_id']: item['count'] for item in platform_stats}
            
            return stats
            
        except Exception as e:
            logger.error(f"שגיאה בקבלת סטטיסטיקות: {e}")
            return {}
    
    def cleanup_old_posts(self, days_old: int = 30):
        """ניקוי פוסטים ישנים"""
        try:
            cutoff_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            cutoff_date = cutoff_date.replace(day=cutoff_date.day - days_old)
            
            result = self.collections['posts'].delete_many({
                'created_at': {'$lt': cutoff_date},
                'status': {'$in': ['completed', 'failed']}
            })
            
            logger.info(f"נמחקו {result.deleted_count} פוסטים ישנים")
            
        except Exception as e:
            logger.error(f"שגיאה בניקוי פוסטים ישנים: {e}")
    
    def cleanup_old_logs(self, days_old: int = 7):
        """ניקוי לוגים ישנים"""
        try:
            cutoff_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            cutoff_date = cutoff_date.replace(day=cutoff_date.day - days_old)
            
            result = self.collections['logs'].delete_many({
                'timestamp': {'$lt': cutoff_date}
            })
            
            logger.info(f"נמחקו {result.deleted_count} לוגים ישנים")
            
        except Exception as e:
            logger.error(f"שגיאה בניקוי לוגים ישנים: {e}")
    
    def health_check(self) -> bool:
        """בדיקת תקינות החיבור למסד נתונים"""
        try:
            self.client.admin.command('ping')
            return True
        except Exception:
            return False
    
    def close_connection(self):
        """סגירת החיבור למסד הנתונים"""
        if self.client:
            self.client.close()
            logger.info("חיבור למסד נתונים נסגר")

# יצירת instance גלובלי
_db_manager = None

def get_database() -> DatabaseManager:
    """מחזיר instance של DatabaseManager (Singleton pattern)"""
    global _db_manager
    
    if _db_manager is None:
        _db_manager = DatabaseManager()
    
    return _db_manager

# פונקציות עזר מהירות
def save_post(user_id: int, filename: str, text: str, platforms: List[str], file_size_mb: float) -> str:
    """פונקציית עזר לשמירת פוסט"""
    db = get_database()
    return db.save_post(user_id, filename, text, platforms, file_size_mb)

def update_post_status(post_id: str, status: str, posting_results: Optional[Dict] = None):
    """פונקציית עזר לעדכון סטטוס פוסט"""
    db = get_database()
    db.update_post_status(post_id, status, posting_results)

def get_user_settings(user_id: int) -> Dict:
    """פונקציית עזר לקבלת הגדרות משתמש"""
    db = get_database()
    return db.get_user_settings(user_id)

def save_user_settings(user_id: int, settings: Dict):
    """פונקציית עזר לשמירת הגדרות משתמש"""
    db = get_database()
    db.save_user_settings(user_id, settings)
