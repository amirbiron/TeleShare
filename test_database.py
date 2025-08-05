"""
בדיקות למסד הנתונים MongoDB
pytest test_database.py -v
"""
import pytest
import os
import tempfile
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from pymongo.errors import ConnectionFailure, OperationFailure
from bson import ObjectId

# ייבוא המודולים שלנו
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import DatabaseManager, get_database, save_post, update_post_status
from exceptions import *
from config import Config

class TestDatabaseManager:
    """בדיקות למחלקת ניהול מסד הנתונים"""
    
    @pytest.fixture
    def mock_mongo_client(self):
        """יצירת MongoDB client מדומה"""
        mock_client = Mock()
        mock_db = Mock()
        mock_collections = {
            'posts': Mock(),
            'users': Mock(),
            'logs': Mock()
        }
        
        mock_client.admin.command.return_value = {'ok': 1}
        mock_client.__getitem__.return_value = mock_db
        mock_db.__getitem__ = lambda self, key: mock_collections[key]
        
        return mock_client, mock_db, mock_collections
    
    @patch('database.MongoClient')
    def test_database_connection_success(self, mock_mongo_client_class):
        """בדיקת חיבור מוצלח למסד נתונים"""
        mock_client, mock_db, mock_collections = self.mock_mongo_client()
        mock_mongo_client_class.return_value = mock_client
        
        db_manager = DatabaseManager()
        
        # בדיקות
        assert db_manager.client is not None
        assert db_manager.db is not None
        assert 'posts' in db_manager.collections
        assert 'users' in db_manager.collections
        assert 'logs' in db_manager.collections
        
        # בדיקה שנעשה ping
        mock_client.admin.command.assert_called_with('ping')
    
    @patch('database.MongoClient')
    def test_database_connection_failure(self, mock_mongo_client_class):
        """בדיקת כישלון חיבור למסד נתונים"""
        mock_client = Mock()
        mock_client.admin.command.side_effect = ConnectionFailure("Connection failed")
        mock_mongo_client_class.return_value = mock_client
        
        with pytest.raises(ConnectionError):
            DatabaseManager()
    
    @patch('database.MongoClient')
    def test_save_post_success(self, mock_mongo_client_class):
        """בדיקת שמירת פוסט מוצלחת"""
        mock_client, mock_db, mock_collections = self.mock_mongo_client()
        mock_mongo_client_class.return_value = mock_client
        
        # הגדרת תגובה מדומה
        mock_result = Mock()
        mock_result.inserted_id = ObjectId()
        mock_collections['posts'].insert_one.return_value = mock_result
        
        db_manager = DatabaseManager()
        
        # שמירת פוסט
        post_id = db_manager.save_post(
            user_id=12345,
            filename="test_video.mp4",
            text="טקסט בדיקה",
            platforms=["TikTok", "Twitter"],
            file_size_mb=5.2
        )
        
        # בדיקות
        assert post_id is not None
        assert isinstance(post_id, str)
        
        # בדיקה שנעשה insert_one
        mock_collections['posts'].insert_one.assert_called_once()
        
        # בדיקת נתוני הפוסט
        call_args = mock_collections['posts'].insert_one.call_args[0][0]
        assert call_args['user_id'] == 12345
        assert call_args['filename'] == "test_video.mp4"
        assert call_args['text'] == "טקסט בדיקה"
        assert call_args['platforms'] == ["TikTok", "Twitter"]
        assert call_args['file_size_mb'] == 5.2
        assert call_args['status'] == 'created'
        assert 'created_at' in call_args
        assert 'updated_at' in call_args
    
    @patch('database.MongoClient')
    def test_save_post_database_error(self, mock_mongo_client_class):
        """בדיקת שגיאה בשמירת פוסט"""
        mock_client, mock_db, mock_collections = self.mock_mongo_client()
        mock_mongo_client_class.return_value = mock_client
        
        # הגדרת שגיאה
        mock_collections['posts'].insert_one.side_effect = OperationFailure("Insert failed")
        
        db_manager = DatabaseManager()
        
        with pytest.raises(SaveError):
            db_manager.save_post(
                user_id=12345,
                filename="test.mp4",
                text="test",
                platforms=["TikTok"],
                file_size_mb=1.0
            )
    
    @patch('database.MongoClient')
    def test_update_post_status_success(self, mock_mongo_client_class):
        """בדיקת עדכון סטטוס פוסט"""
        mock_client, mock_db, mock_collections = self.mock_mongo_client()
        mock_mongo_client_class.return_value = mock_client
        
        # הגדרת תגובה מדומה
        mock_result = Mock()
        mock_result.modified_count = 1
        mock_collections['posts'].update_one.return_value = mock_result
        
        db_manager = DatabaseManager()
        
        # עדכון סטטוס
        posting_results = {"TikTok": {"status": "success"}}
        db_manager.update_post_status("507f1f77bcf86cd799439011", "completed", posting_results)
        
        # בדיקות
        mock_collections['posts'].update_one.assert_called_once()
        
        call_args = mock_collections['posts'].update_one.call_args
        filter_arg = call_args[0][0]
        update_arg = call_args[0][1]
        
        assert isinstance(filter_arg['_id'], ObjectId)
        assert update_arg['$set']['status'] == 'completed'
        assert update_arg['$set']['posting_results'] == posting_results
        assert 'updated_at' in update_arg['$set']
    
    @patch('database.MongoClient')
    def test_get_user_posts(self, mock_mongo_client_class):
        """בדיקת קבלת פוסטים של משתמש"""
        mock_client, mock_db, mock_collections = self.mock_mongo_client()
        mock_mongo_client_class.return_value = mock_client
        
        # הגדרת נתונים מדומים
        mock_posts = [
            {
                '_id': ObjectId(),
                'user_id': 12345,
                'filename': 'video1.mp4',
                'text': 'פוסט ראשון',
                'created_at': datetime.now()
            },
            {
                '_id': ObjectId(),
                'user_id': 12345,
                'filename': 'video2.mp4',
                'text': 'פוסט שני',
                'created_at': datetime.now() - timedelta(hours=1)
            }
        ]
        
        mock_cursor = Mock()
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_posts
        mock_collections['posts'].find.return_value = mock_cursor
        
        db_manager = DatabaseManager()
        
        # קבלת פוסטים
        posts = db_manager.get_user_posts(12345, limit=10)
        
        # בדיקות
        assert len(posts) == 2
        assert all(isinstance(post['_id'], str) for post in posts)
        assert posts[0]['user_id'] == 12345
        
        # בדיקת הפרמטרים של השאילתה
        mock_collections['posts'].find.assert_called_once_with({'user_id': 12345})
        mock_cursor.sort.assert_called_once_with('created_at', -1)
        mock_cursor.limit.assert_called_once_with(10)
    
    @patch('database.MongoClient')
    def test_get_post_by_id_found(self, mock_mongo_client_class):
        """בדיקת קבלת פוסט לפי ID - נמצא"""
        mock_client, mock_db, mock_collections = self.mock_mongo_client()
        mock_mongo_client_class.return_value = mock_client
        
        post_id = "507f1f77bcf86cd799439011"
        mock_post = {
            '_id': ObjectId(post_id),
            'user_id': 12345,
            'filename': 'test.mp4'
        }
        
        mock_collections['posts'].find_one.return_value = mock_post
        
        db_manager = DatabaseManager()
        
        # קבלת פוסט
        result = db_manager.get_post_by_id(post_id)
        
        # בדיקות
        assert result is not None
        assert result['_id'] == post_id
        assert result['user_id'] == 12345
        
        # בדיקת הפרמטרים
        mock_collections['posts'].find_one.assert_called_once()
        call_args = mock_collections['posts'].find_one.call_args[0][0]
        assert isinstance(call_args['_id'], ObjectId)
    
    @patch('database.MongoClient')
    def test_get_post_by_id_not_found(self, mock_mongo_client_class):
        """בדיקת קבלת פוסט לפי ID - לא נמצא"""
        mock_client, mock_db, mock_collections = self.mock_mongo_client()
        mock_mongo_client_class.return_value = mock_client
        
        mock_collections['posts'].find_one.return_value = None
        
        db_manager = DatabaseManager()
        
        # קבלת פוסט שלא קיים
        result = db_manager.get_post_by_id("507f1f77bcf86cd799439011")
        
        assert result is None
    
    @patch('database.MongoClient')
    def test_save_user_settings(self, mock_mongo_client_class):
        """בדיקת שמירת הגדרות משתמש"""
        mock_client, mock_db, mock_collections = self.mock_mongo_client()
        mock_mongo_client_class.return_value = mock_client
        
        mock_result = Mock()
        mock_result.modified_count = 1
        mock_collections['users'].update_one.return_value = mock_result
        
        db_manager = DatabaseManager()
        
        # שמירת הגדרות
        settings = {
            'mock_mode': True,
            'auto_post': False,
            'preferred_platforms': ['TikTok', 'Twitter']
        }
        
        db_manager.save_user_settings(12345, settings)
        
        # בדיקות
        mock_collections['users'].update_one.assert_called_once()
        
        call_args = mock_collections['users'].update_one.call_args
        filter_arg = call_args[0][0]
        update_arg = call_args[0][1]
        options = call_args[1]
        
        assert filter_arg == {'user_id': 12345}
        assert update_arg['$set']['settings'] == settings
        assert 'updated_at' in update_arg['$set']
        assert options['upsert'] == True
    
    @patch('database.MongoClient')
    def test_get_user_settings_existing_user(self, mock_mongo_client_class):
        """בדיקת קבלת הגדרות משתמש קיים"""
        mock_client, mock_db, mock_collections = self.mock_mongo_client()
        mock_mongo_client_class.return_value = mock_client
        
        mock_user = {
            'user_id': 12345,
            'settings': {
                'mock_mode': False,
                'auto_post': True
            }
        }
        
        mock_collections['users'].find_one.return_value = mock_user
        
        db_manager = DatabaseManager()
        
        # קבלת הגדרות
        settings = db_manager.get_user_settings(12345)
        
        # בדיקות
        assert settings == mock_user['settings']
        mock_collections['users'].find_one.assert_called_once_with({'user_id': 12345})
    
    @patch('database.MongoClient')
    def test_get_user_settings_new_user(self, mock_mongo_client_class):
        """בדיקת קבלת הגדרות למשתמש חדש"""
        mock_client, mock_db, mock_collections = self.mock_mongo_client()
        mock_mongo_client_class.return_value = mock_client
        
        # משתמש לא קיים
        mock_collections['users'].find_one.return_value = None
        
        # Mock לsave_user_settings
        mock_result = Mock()
        mock_collections['users'].update_one.return_value = mock_result
        
        db_manager = DatabaseManager()
        
        # קבלת הגדרות
        settings = db_manager.get_user_settings(12345)
        
        # בדיקות שהוחזרו הגדרות ברירת מחדל
        assert 'mock_mode' in settings
        assert 'auto_post' in settings
        assert 'preferred_platforms' in settings
        
        # בדיקה שנשמרו הגדרות ברירת מחדל
        mock_collections['users'].update_one.assert_called_once()
    
    @patch('database.MongoClient')
    def test_get_statistics(self, mock_mongo_client_class):
        """בדיקת קבלת סטטיסטיקות"""
        mock_client, mock_db, mock_collections = self.mock_mongo_client()
        mock_mongo_client_class.return_value = mock_client
        
        # הגדרת תגובות מדומות
        mock_collections['posts'].count_documents.side_effect = [100, 5, 80]  # total, today, successful
        mock_collections['users'].count_documents.return_value = 25
        
        # סטטיסטיקות פלטפורמות
        platform_stats = [
            {'_id': 'TikTok', 'count': 45},
            {'_id': 'Twitter', 'count': 30},
            {'_id': 'Instagram', 'count': 25}
        ]
        mock_collections['posts'].aggregate.return_value = platform_stats
        
        db_manager = DatabaseManager()
        
        # קבלת סטטיסטיקות
        stats = db_manager.get_statistics()
        
        # בדיקות
        assert stats['total_posts'] == 100
        assert stats['posts_today'] == 5
        assert stats['successful_posts'] == 80
        assert stats['total_users'] == 25
        assert stats['popular_platforms']['TikTok'] == 45
        assert stats['popular_platforms']['Twitter'] == 30
    
    @patch('database.MongoClient')
    def test_cleanup_old_posts(self, mock_mongo_client_class):
        """בדיקת ניקוי פוסטים ישנים"""
        mock_client, mock_db, mock_collections = self.mock_mongo_client()
        mock_mongo_client_class.return_value = mock_client
        
        mock_result = Mock()
        mock_result.deleted_count = 15
        mock_collections['posts'].delete_many.return_value = mock_result
        
        db_manager = DatabaseManager()
        
        # ניקוי פוסטים
        db_manager.cleanup_old_posts(days_old=30)
        
        # בדיקות
        mock_collections['posts'].delete_many.assert_called_once()
        
        call_args = mock_collections['posts'].delete_many.call_args[0][0]
        assert 'created_at' in call_args
        assert '$lt' in call_args['created_at']
        assert 'status' in call_args
        assert call_args['status']['$in'] == ['completed', 'failed']
    
    @patch('database.MongoClient')
    def test_cleanup_old_logs(self, mock_mongo_client_class):
        """בדיקת ניקוי לוגים ישנים"""
        mock_client, mock_db, mock_collections = self.mock_mongo_client()
        mock_mongo_client_class.return_value = mock_client
        
        mock_result = Mock()
        mock_result.deleted_count = 50
        mock_collections['logs'].delete_many.return_value = mock_result
        
        db_manager = DatabaseManager()
        
        # ניקוי לוגים
        db_manager.cleanup_old_logs(days_old=7)
        
        # בדיקות
        mock_collections['logs'].delete_many.assert_called_once()
        
        call_args = mock_collections['logs'].delete_many.call_args[0][0]
        assert 'timestamp' in call_args
        assert '$lt' in call_args['timestamp']
    
    @patch('database.MongoClient')
    def test_health_check_success(self, mock_mongo_client_class):
        """בדיקת health check מוצלח"""
        mock_client, mock_db, mock_collections = self.mock_mongo_client()
        mock_mongo_client_class.return_value = mock_client
        
        mock_client.admin.command.return_value = {'ok': 1}
        
        db_manager = DatabaseManager()
        
        # בדיקת בריאות
        result = db_manager.health_check()
        
        assert result == True
        mock_client.admin.command.assert_called_with('ping')
    
    @patch('database.MongoClient')
    def test_health_check_failure(self, mock_mongo_client_class):
        """בדיקת health check נכשל"""
        mock_client, mock_db, mock_collections = self.mock_mongo_client()
        mock_mongo_client_class.return_value = mock_client
        
        # הגדרת שגיאה בping
        mock_client.admin.command.side_effect = Exception("Connection lost")
        
        db_manager = DatabaseManager()
        
        # בדיקת בריאות
        result = db_manager.health_check()
        
        assert result == False
    
    @patch('database.MongoClient')
    def test_close_connection(self, mock_mongo_client_class):
        """בדיקת סגירת חיבור"""
        mock_client, mock_db, mock_collections = self.mock_mongo_client()
        mock_mongo_client_class.return_value = mock_client
        
        db_manager = DatabaseManager()
        
        # סגירת חיבור
        db_manager.close_connection()
        
        mock_client.close.assert_called_once()
    
    @patch('database.MongoClient')
    def test_log_action(self, mock_mongo_client_class):
        """בדיקת רישום פעולה"""
        mock_client, mock_db, mock_collections = self.mock_mongo_client()
        mock_mongo_client_class.return_value = mock_client
        
        mock_result = Mock()
        mock_collections['logs'].insert_one.return_value = mock_result
        
        db_manager = DatabaseManager()
        
        # רישום פעולה
        db_manager.log_action(
            user_id=12345,
            action="video_uploaded",
            details={"filename": "test.mp4", "size": "5MB"},
            level="info"
        )
        
        # בדיקות
        mock_collections['logs'].insert_one.assert_called_once()
        
        call_args = mock_collections['logs'].insert_one.call_args[0][0]
        assert call_args['user_id'] == 12345
        assert call_args['action'] == "video_uploaded"
        assert call_args['details']['filename'] == "test.mp4"
        assert call_args['level'] == "info"
        assert 'timestamp' in call_args

class TestDatabaseHelperFunctions:
    """בדיקות לפונקציות עזר של מסד הנתונים"""
    
    @patch('database.get_database')
    def test_save_post_helper(self, mock_get_db):
        """בדיקת פונקציית עזר לשמירת פוסט"""
        mock_db = Mock()
        mock_db.save_post.return_value = "post_123"
        mock_get_db.return_value = mock_db
        
        result = save_post(
            user_id=12345,
            filename="test.mp4",
            text="טקסט",
            platforms=["TikTok"],
            file_size_mb=1.0
        )
        
        assert result == "post_123"
        mock_db.save_post.assert_called_once_with(12345, "test.mp4", "טקסט", ["TikTok"], 1.0)
    
    @patch('database.get_database')
    def test_update_post_status_helper(self, mock_get_db):
        """בדיקת פונקציית עזר לעדכון סטטוס"""
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        
        update_post_status("post_123", "completed", {"TikTok": "success"})
        
        mock_db.update_post_status.assert_called_once_with("post_123", "completed", {"TikTok": "success"})

class TestDatabaseSingleton:
    """בדיקות לpattern של Singleton"""
    
    @patch('database.DatabaseManager')
    def test_get_database_singleton(self, mock_db_manager):
        """בדיקה שget_database מחזיר אותו instance"""
        mock_instance = Mock()
        mock_db_manager.return_value = mock_instance
        
        # איפוס singleton
        import database
        database._db_manager = None
        
        db1 = get_database()
        db2 = get_database()
        
        assert db1 is db2
        assert db1 is mock_instance
        
        # בדיקה שהconstructor נקרא רק פעם אחת
        mock_db_manager.assert_called_once()

class TestDatabaseIntegration:
    """בדיקות אינטגרציה - דורשות MongoDB אמיתי"""
    
    @pytest.mark.integration
    @pytest.mark.skipif(not os.getenv('INTEGRATION_TESTS'), 
                       reason="Integration tests disabled")
    def test_real_database_connection(self):
        """בדיקת חיבור למסד נתונים אמיתי"""
        # זה ידרוש MongoDB אמיתי
        try:
            db = DatabaseManager()
            assert db.health_check() == True
        except ConnectionError:
            pytest.skip("MongoDB not available for integration tests")
    
    @pytest.mark.integration
    @pytest.mark.skipif(not os.getenv('INTEGRATION_TESTS'), 
                       reason="Integration tests disabled")
    def test_full_post_lifecycle(self):
        """בדיקת מחזור חיים מלא של פוסט"""
        try:
            db = DatabaseManager()
            
            # שמירת פוסט
            post_id = db.save_post(
                user_id=99999,  # ID בדיקה
                filename="integration_test.mp4",
                text="בדיקת אינטגרציה",
                platforms=["TikTok", "Twitter"],
                file_size_mb=2.5
            )
            
            assert post_id is not None
            
            # עדכון סטטוס
            db.update_post_status(post_id, "completed", {"TikTok": {"status": "success"}})
            
            # קבלת הפוסט
            post = db.get_post_by_id(post_id)
            assert post is not None
            assert post['status'] == 'completed'
            
            # ניקוי
            db.collections['posts'].delete_one({'_id': ObjectId(post_id)})
            
        except ConnectionError:
            pytest.skip("MongoDB not available for integration tests")

class TestDatabaseErrorHandling:
    """בדיקות לטיפול בשגיאות"""
    
    @patch('database.MongoClient')
    def test_database_operation_with_connection_lost(self, mock_mongo_client_class):
        """בדיקת פעולה כשהחיבור אבד"""
        mock_client, mock_db, mock_collections = self.mock_mongo_client()
        mock_mongo_client_class.return_value = mock_client
        
        # שגיאה באמצע פעולה
        mock_collections['posts'].insert_one.side_effect = ConnectionFailure("Connection lost")
        
        db_manager = DatabaseManager()
        
        with pytest.raises(SaveError):
            db_manager.save_post(12345, "test.mp4", "test", ["TikTok"], 1.0)
    
    @patch('database.MongoClient')
    def test_invalid_object_id(self, mock_mongo_client_class):
        """בדיקת ObjectId לא תקין"""
        mock_client, mock_db, mock_collections = self.mock_mongo_client()
        mock_mongo_client_class.return_value = mock_client
        
        db_manager = DatabaseManager()
        
        # ID לא תקין
        result = db_manager.get_post_by_id("invalid_id")
        
        # צריך להחזיר None ולא לגרום לשגיאה
        assert result is None

class TestDatabasePerformance:
    """בדיקות ביצועים בסיסיות"""
    
    @patch('database.MongoClient')
    def test_create_indexes_called(self, mock_mongo_client_class):
        """בדיקה שנוצרים אינדקסים"""
        mock_client, mock_db, mock_collections = self.mock_mongo_client()
        mock_mongo_client_class.return_value = mock_client
        
        # Mock ליצירת אינדקסים
        for collection in mock_collections.values():
            collection.create_index = Mock()
        
        db_manager = DatabaseManager()
        
        # בדיקה שנוצרו אינדקסים
        mock_collections['posts'].create_index.assert_called()
        mock_collections['logs'].create_index.assert_called()

# ============================================================================
# פיקסצ'רים גלובליים
# ============================================================================

@pytest.fixture(scope="session", autouse=True)
def setup_test_database_environment():
    """הגדרת סביבת בדיקות למסד נתונים"""
    # הגדרת משתני סביבה
    os.environ['DATABASE_NAME'] = 'test_social_media_bot'
    os.environ['MONGODB_URI'] = 'mongodb://localhost:27017/'
    
    yield
    
    # ניקוי
    if 'DATABASE_NAME' in os.environ:
        del os.environ['DATABASE_NAME']
    if 'MONGODB_URI' in os.environ:
        del os.environ['MONGODB_URI']

# ============================================================================
# הרצת בדיקות
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

# איך להריץ:
# pytest test_database.py -v                           # כל הבדיקות
# pytest test_database.py::TestDatabaseManager -v      # מחלקה ספציפית  
# pytest test_database.py -k "test_save_post" -v       # בדיקות ספציפיות
# pytest test_database.py -m integration -v            # רק בדיקות אינטגרציה
# pytest test_database.py --cov=database               # עם coverage
# INTEGRATION_TESTS=1 pytest test_database.py -v      # עם בדיקות אינטגרציה
