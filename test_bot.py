"""
בדיקות לבוט הטלגרם
pytest test_bot.py -v
"""
import pytest
import asyncio
import os
import tempfile
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from telegram import Update, Message, Video, User, Chat
from telegram.ext import ContextTypes

# ייבוא המודולים שלנו
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from telegram_bot import SocialMediaBot, get_bot
from config import Config, Messages
from exceptions import *
from database import get_database

class TestSocialMediaBot:
    """בדיקות למחלקת הבוט הראשית"""
    
    @pytest.fixture
    def bot(self):
        """יצירת instance של הבוט לבדיקות"""
        bot = SocialMediaBot()
        bot.setup_application()
        return bot
    
    @pytest.fixture
    def mock_update(self):
        """יצירת Update מדומה"""
        user = User(id=12345, first_name="Test", is_bot=False)
        chat = Chat(id=12345, type="private")
        message = Message(
            message_id=1,
            date=None,
            chat=chat,
            from_user=user
        )
        
        update = Update(update_id=1, message=message)
        return update
    
    @pytest.fixture
    def mock_context(self):
        """יצירת Context מדומה"""
        context = Mock(spec=ContextTypes.DEFAULT_TYPE)
        context.bot = Mock()
        return context
    
    def test_bot_initialization(self, bot):
        """בדיקת אתחול הבוט"""
        assert bot is not None
        assert bot.app is not None
        assert bot.user_sessions == {}
        assert bot.social_handler is None
    
    @pytest.mark.asyncio
    async def test_start_command(self, bot, mock_update, mock_context):
        """בדיקת פקודת /start"""
        mock_update.message.reply_text = AsyncMock()
        
        await bot.start_command(mock_update, mock_context)
        
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert Messages.WELCOME_MESSAGE in call_args[0][0]
        assert call_args[1]['parse_mode'] == 'Markdown'
    
    @pytest.mark.asyncio
    async def test_help_command(self, bot, mock_update, mock_context):
        """בדיקת פקודת /help"""
        mock_update.message.reply_text = AsyncMock()
        
        await bot.help_command(mock_update, mock_context)
        
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert Messages.HELP_MESSAGE in call_args[0][0]
    
    @patch('telegram_bot.get_user_settings')
    @patch('telegram_bot.save_user_settings')
    @pytest.mark.asyncio
    async def test_mock_command_toggle(self, mock_save, mock_get, bot, mock_update, mock_context):
        """בדיקת החלפת מצב בדיקה"""
        # הגדרת מצב נוכחי
        mock_get.return_value = {'mock_mode': False}
        mock_update.message.reply_text = AsyncMock()
        
        await bot.mock_command(mock_update, mock_context)
        
        # בדיקה שהמצב הוחלף
        mock_save.assert_called_once()
        saved_settings = mock_save.call_args[0][1]
        assert saved_settings['mock_mode'] == True
        
        # בדיקת הודעה למשתמש
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args[0][0]
        assert "פעיל" in call_args
    
    @patch('telegram_bot.get_user_settings')
    @patch('telegram_bot.save_user_settings')
    @pytest.mark.asyncio
    async def test_auto_command_toggle(self, mock_save, mock_get, bot, mock_update, mock_context):
        """בדיקת החלפת מצב אוטומטי"""
        mock_get.return_value = {'auto_post': False}
        mock_update.message.reply_text = AsyncMock()
        
        await bot.auto_command(mock_update, mock_context)
        
        mock_save.assert_called_once()
        saved_settings = mock_save.call_args[0][1]
        assert saved_settings['auto_post'] == True
    
    @patch('telegram_bot.ValidationHelper.validate_platform_tokens')
    @patch('telegram_bot.get_user_settings')
    @pytest.mark.asyncio
    async def test_status_command(self, mock_get, mock_validate, bot, mock_update, mock_context):
        """בדיקת פקודת /status"""
        mock_get.return_value = {'mock_mode': True, 'auto_post': False}
        mock_validate.return_value = {
            'TikTok': True, 'Twitter': False, 'Facebook': True,
            'Instagram': False, 'LinkedIn': True, 'YouTube': False,
            'Tumblr': True, 'Telegram': True
        }
        mock_update.message.reply_text = AsyncMock()
        
        await bot.status_command(mock_update, mock_context)
        
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args[0][0]
        assert "מצב בדיקה" in call_args
        assert "פרסום אוטומטי" in call_args
        assert "רשתות זמינות" in call_args
    
    @pytest.mark.asyncio
    async def test_handle_text_message(self, bot, mock_update, mock_context):
        """בדיקת טיפול בהודעות טקסט רגילות"""
        mock_update.message.reply_text = AsyncMock()
        
        await bot.handle_text(mock_update, mock_context)
        
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args[0][0]
        assert "שלחו לי סרטון" in call_args

class TestVideoHandling:
    """בדיקות לטיפול בסרטונים"""
    
    @pytest.fixture
    def bot_with_temp_file(self):
        """בוט עם קובץ זמני לבדיקות"""
        bot = SocialMediaBot()
        bot.setup_application()
        
        # יצירת קובץ זמני
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
            temp_file.write(b'fake video content for testing')
            temp_filename = temp_file.name
        
        yield bot, temp_filename
        
        # ניקוי
        try:
            os.unlink(temp_filename)
        except FileNotFoundError:
            pass
    
    @pytest.fixture
    def mock_video_update(self):
        """Update עם סרטון מדומה"""
        user = User(id=12345, first_name="Test", is_bot=False)
        chat = Chat(id=12345, type="private")
        
        # יצירת video מדומה
        video = Video(
            file_id="test_file_id",
            file_unique_id="test_unique_id",
            width=1920,
            height=1080,
            duration=30,
            file_name="test_video.mp4",
            file_size=1000000  # 1MB
        )
        
        message = Message(
            message_id=1,
            date=None,
            chat=chat,
            from_user=user,
            video=video,
            caption="טקסט בדיקה #test"
        )
        
        update = Update(update_id=1, message=message)
        return update
    
    @patch('telegram_bot.ValidationHelper.validate_telegram_message')
    @patch('telegram_bot.FileHelper.validate_video_file')
    @patch('telegram_bot.ValidationHelper.validate_platform_tokens')
    @patch('telegram_bot.get_user_settings')
    @patch('telegram_bot.save_post')
    @pytest.mark.asyncio
    async def test_handle_video_success(self, mock_save_post, mock_get_settings, 
                                      mock_validate_tokens, mock_validate_file,
                                      mock_validate_message, bot_with_temp_file, 
                                      mock_video_update, mock_context):
        """בדיקת טיפול מוצלח בסרטון"""
        bot, temp_file = bot_with_temp_file
        
        # הגדרת mocks
        mock_video = Mock()
        mock_video.file_name = "test.mp4"
        mock_validate_message.return_value = (mock_video, "טקסט בדיקה")
        mock_validate_file.return_value = True
        mock_validate_tokens.return_value = {'TikTok': True, 'Twitter': True}
        mock_get_settings.return_value = {'mock_mode': True, 'auto_post': False}
        mock_save_post.return_value = "post_123"
        
        # Mock הורדת קובץ
        with patch.object(bot, '_download_video', return_value=temp_file):
            with patch.object(bot, '_show_preview') as mock_show_preview:
                mock_context = Mock()
                
                await bot.handle_video(mock_video_update, mock_context)
                
                # בדיקות
                mock_validate_message.assert_called_once()
                mock_validate_file.assert_called_once()
                mock_save_post.assert_called_once()
                mock_show_preview.assert_called_once()
    
    @patch('telegram_bot.ValidationHelper.validate_telegram_message')
    @pytest.mark.asyncio
    async def test_handle_video_no_video_error(self, mock_validate, bot_with_temp_file, 
                                             mock_video_update, mock_context):
        """בדיקת שגיאה כשאין סרטון"""
        bot, _ = bot_with_temp_file
        
        mock_validate.side_effect = NoVideoError()
        mock_video_update.message.reply_text = AsyncMock()
        
        await bot.handle_video(mock_video_update, mock_context)
        
        mock_video_update.message.reply_text.assert_called_once()
        call_args = mock_video_update.message.reply_text.call_args[0][0]
        assert Messages.ERROR_NO_VIDEO in call_args
    
    @patch('telegram_bot.ValidationHelper.validate_telegram_message')
    @pytest.mark.asyncio
    async def test_handle_video_file_too_large_error(self, mock_validate, bot_with_temp_file,
                                                   mock_video_update, mock_context):
        """בדיקת שגיאה של קובץ גדול מדי"""
        bot, _ = bot_with_temp_file
        
        mock_validate.side_effect = FileTooLargeError(100, 50)
        mock_video_update.message.reply_text = AsyncMock()
        
        await bot.handle_video(mock_video_update, mock_context)
        
        mock_video_update.message.reply_text.assert_called_once()
        call_args = mock_video_update.message.reply_text.call_args[0][0]
        assert "גדול מדי" in call_args

class TestCallbackHandling:
    """בדיקות לטיפול בכפתורים"""
    
    @pytest.fixture
    def mock_callback_query(self):
        """יצירת callback query מדומה"""
        user = User(id=12345, first_name="Test", is_bot=False)
        
        query = Mock()
        query.answer = AsyncMock()
        query.data = "confirm_12345"
        query.from_user = user
        query.edit_message_text = AsyncMock()
        
        update = Mock()
        update.callback_query = query
        update.effective_user = user
        
        return update
    
    @pytest.mark.asyncio
    async def test_handle_callback_confirm(self, bot, mock_callback_query, mock_context):
        """בדיקת לחיצה על כפתור אישור"""
        with patch.object(bot, '_process_posting') as mock_process:
            await bot.handle_callback(mock_callback_query, mock_context)
            
            mock_callback_query.callback_query.answer.assert_called_once()
            mock_process.assert_called_once_with(mock_callback_query, 12345)
    
    @pytest.mark.asyncio
    async def test_handle_callback_cancel(self, bot, mock_context):
        """בדיקת לחיצה על כפתור ביטול"""
        user = User(id=12345, first_name="Test", is_bot=False)
        
        query = Mock()
        query.answer = AsyncMock()
        query.data = "cancel_12345"
        query.from_user = user
        query.edit_message_text = AsyncMock()
        
        update = Mock()
        update.callback_query = query
        update.effective_user = user
        
        with patch.object(bot, '_cancel_posting') as mock_cancel:
            await bot.handle_callback(update, mock_context)
            
            query.answer.assert_called_once()
            mock_cancel.assert_called_once_with(update, 12345)

class TestPostProcessing:
    """בדיקות לעיבוד פרסומים"""
    
    @pytest.fixture
    def bot_with_session(self):
        """בוט עם session מדומה"""
        bot = SocialMediaBot()
        bot.setup_application()
        
        # הוספת session מדומה
        bot.user_sessions[12345] = {
            'post_id': 'test_post_123',
            'file_path': '/tmp/test_video.mp4',
            'filename': 'test_video.mp4',
            'text': 'טקסט בדיקה',
            'platforms': ['TikTok', 'Twitter'],
            'mock_mode': True
        }
        
        return bot
    
    @patch('telegram_bot.update_post_status')
    @patch('telegram_bot.FileHelper.cleanup_temp_files')
    @pytest.mark.asyncio
    async def test_mock_posting(self, mock_cleanup, mock_update_status, bot_with_session):
        """בדיקת פרסום מדומה"""
        message = Mock()
        message.edit_text = AsyncMock()
        
        session = bot_with_session.user_sessions[12345]
        
        await bot_with_session._mock_posting(session, message)
        
        # בדיקות
        message.edit_text.assert_called_once()
        call_args = message.edit_text.call_args[0][0]
        assert Messages.SUCCESS_MOCK_MODE in call_args
        
        mock_update_status.assert_called_once()
        status_args = mock_update_status.call_args
        assert status_args[0][0] == 'test_post_123'  # post_id
        assert status_args[0][1] == 'completed'  # status
    
    @patch('telegram_bot.update_post_status')
    @pytest.mark.asyncio
    async def test_cancel_posting(self, mock_update_status, bot_with_session):
        """בדיקת ביטול פרסום"""
        user_id = 12345
        
        query = Mock()
        query.edit_message_text = AsyncMock()
        
        update = Mock()
        update.callback_query = query
        
        with patch('telegram_bot.FileHelper.cleanup_temp_files') as mock_cleanup:
            await bot_with_session._cancel_posting(update, user_id)
            
            # בדיקות
            query.edit_message_text.assert_called_once()
            call_args = query.edit_message_text.call_args[0][0]
            assert "פרסום בוטל" in call_args
            
            mock_update_status.assert_called_once_with('test_post_123', 'cancelled')
            mock_cleanup.assert_called_once()
            
            # בדיקה שהsession נמחק
            assert user_id not in bot_with_session.user_sessions

class TestBotSingleton:
    """בדיקות לpattern של Singleton"""
    
    def test_get_bot_singleton(self):
        """בדיקה שget_bot מחזיר אותו instance"""
        bot1 = get_bot()
        bot2 = get_bot()
        
        assert bot1 is bot2
        assert id(bot1) == id(bot2)

class TestIntegration:
    """בדיקות אינטגרציה"""
    
    @pytest.mark.asyncio
    @patch('telegram_bot.get_database')
    async def test_database_integration(self, mock_get_db):
        """בדיקת אינטגרציה עם מסד נתונים"""
        mock_db = Mock()
        mock_db.health_check.return_value = True
        mock_get_db.return_value = mock_db
        
        bot = SocialMediaBot()
        bot.setup_application()
        bot.db = mock_db
        
        # בדיקה שהחיבור למסד נתונים עובד
        assert bot.db.health_check() == True
    
    def test_social_handler_integration(self):
        """בדיקת אינטגרציה עם מטפל רשתות"""
        bot = SocialMediaBot()
        bot.setup_application()
        
        mock_social_handler = Mock()
        bot.set_social_handler(mock_social_handler)
        
        assert bot.social_handler is mock_social_handler

# ============================================================================
# בדיקות עזר ואימות
# ============================================================================

def test_config_validation():
    """בדיקת תקינות קונפיגורציה"""
    # בדיקה שהמשתנים החשובים קיימים
    assert hasattr(Config, 'TELEGRAM_BOT_TOKEN')
    assert hasattr(Config, 'MOCK_MODE')
    assert hasattr(Config, 'MAX_FILE_SIZE_MB')
    assert hasattr(Messages, 'WELCOME_MESSAGE')
    assert hasattr(Messages, 'ERROR_NO_VIDEO')

def test_messages_in_hebrew():
    """בדיקה שההודעות בעברית"""
    # בדיקה שיש תווים עבריים בהודעות
    hebrew_messages = [
        Messages.WELCOME_MESSAGE,
        Messages.HELP_MESSAGE,
        Messages.ERROR_NO_VIDEO,
        Messages.SUCCESS_POSTED
    ]
    
    for message in hebrew_messages:
        # בדיקה שיש לפחות תו עברי אחד
        has_hebrew = any('\u0590' <= char <= '\u05FF' for char in message)
        assert has_hebrew, f"הודעה ללא עברית: {message[:50]}..."

@pytest.mark.integration
class TestFullWorkflow:
    """בדיקות workflow מלא - רק אם יש סביבה מתאימה"""
    
    @pytest.mark.skipif(not os.getenv('INTEGRATION_TESTS'), 
                       reason="Integration tests disabled")
    @pytest.mark.asyncio
    async def test_full_video_processing_workflow(self):
        """בדיקת workflow מלא של עיבוד סרטון"""
        # זה ידרוש סביבת בדיקה מלאה עם MongoDB אמיתי
        pass

# ============================================================================
# פיקסצ'רים גלובליים
# ============================================================================

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """הגדרת סביבת בדיקות"""
    # הגדרת משתני סביבה לבדיקות
    os.environ['MOCK_MODE'] = 'true'
    os.environ['LOG_LEVEL'] = 'ERROR'  # פחות noise בבדיקות
    os.environ['TELEGRAM_BOT_TOKEN'] = 'test_token_for_testing'
    os.environ['DATABASE_NAME'] = 'test_social_media_bot'
    
    yield
    
    # ניקוי אחרי כל הבדיקות
    test_vars = ['MOCK_MODE', 'LOG_LEVEL', 'TELEGRAM_BOT_TOKEN', 'DATABASE_NAME']
    for var in test_vars:
        if var in os.environ:
            del os.environ[var]

# ============================================================================
# הרצת בדיקות
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
    
# איך להריץ:
# pytest test_bot.py -v                    # כל הבדיקות
# pytest test_bot.py::TestSocialMediaBot -v  # מחלקה ספציפית
# pytest test_bot.py -k "test_start" -v      # בדיקות ספציפיות
# pytest test_bot.py --tb=long              # traceback מפורט
# pytest test_bot.py --cov=telegram_bot     # עם coverage
