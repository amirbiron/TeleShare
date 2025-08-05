"""
בוט טלגרם לפרסום אוטומטי לרשתות חברתיות
"""
import os
import asyncio
from typing import Dict, List
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    filters, ContextTypes
)

from config import Config, Messages
from exceptions import *
from logger import bot_logger, get_logger
from utils import *
from database import get_database, save_post, update_post_status, get_user_settings, save_user_settings

logger = get_logger(__name__)

class SocialMediaBot:
    """הבוט הראשי לפרסום ברשתות חברתיות"""
    
    def __init__(self):
        self.app = None
        self.social_handler = None  # יחובר בהמשך
        self.db = get_database()
        
        # מצבי משתמשים (זמני - במקום DB לנתונים קטנים)
        self.user_sessions = {}
    
    def setup_application(self):
        """הגדרת האפליקציה"""
        if not Config.TELEGRAM_BOT_TOKEN:
            raise MissingConfigError("TELEGRAM_BOT_TOKEN")
        
        # יצירת אפליקציית הבוט
        self.app = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
        
        # הוספת handlers
        self._add_handlers()
        
        logger.info("בוט טלגרם הוגדר בהצלחה")
    
    def _add_handlers(self):
        """הוספת כל ה-handlers"""
        
        # פקודות
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(CommandHandler("mock", self.mock_command))
        self.app.add_handler(CommandHandler("auto", self.auto_command))
        self.app.add_handler(CommandHandler("status", self.status_command))
        
        # הודעות וידאו
        self.app.add_handler(MessageHandler(filters.VIDEO, self.handle_video))
        
        # כפתורים (callbacks)
        self.app.add_handler(CallbackQueryHandler(self.handle_callback))
        
        # הודעות טקסט רגילות
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """פקודת /start"""
        user_id = update.effective_user.id
        
        bot_logger.log_user_action(user_id, "start_command")
        
        await update.message.reply_text(
            Messages.WELCOME_MESSAGE,
            parse_mode='Markdown'
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """פקודת /help"""
        user_id = update.effective_user.id
        
        bot_logger.log_user_action(user_id, "help_command")
        
        await update.message.reply_text(
            Messages.HELP_MESSAGE,
            parse_mode='Markdown'
        )
    
    async def mock_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """פקודת /mock - החלפת מצב בדיקה"""
        user_id = update.effective_user.id
        
        # קבלת הגדרות נוכחיות
        settings = get_user_settings(user_id)
        current_mock = settings.get('mock_mode', Config.MOCK_MODE)
        
        # החלפת מצב
        new_mock = not current_mock
        settings['mock_mode'] = new_mock
        save_user_settings(user_id, settings)
        
        # הודעה למשתמש
        status = "פעיל" if new_mock else "כבוי"
        emoji = "🧪" if new_mock else "🚀"
        
        message = f"{emoji} מצב בדיקה: **{status}**"
        if new_mock:
            message += "\n\n⚠️ פרסומים יהיו מדומים (לא אמיתיים)"
        else:
            message += "\n\n✅ פרסומים יהיו אמיתיים!"
        
        bot_logger.log_user_action(user_id, "mock_mode_toggle", {"new_mode": new_mock})
        
        await update.message.reply_text(message, parse_mode='Markdown')
    
    async def auto_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """פקודת /auto - החלפת מצב פרסום אוטומטי"""
        user_id = update.effective_user.id
        
        # קבלת הגדרות נוכחיות
        settings = get_user_settings(user_id)
        current_auto = settings.get('auto_post', Config.AUTO_POST_MODE)
        
        # החלפת מצב
        new_auto = not current_auto
        settings['auto_post'] = new_auto
        save_user_settings(user_id, settings)
        
        # הודעה למשתמש
        status = "פעיל" if new_auto else "כבוי"
        emoji = "🤖" if new_auto else "👤"
        
        message = f"{emoji} פרסום אוטומטי: **{status}**"
        if new_auto:
            message += "\n\n⚡ פרסומים יתבצעו ישירות ללא אישור"
        else:
            message += "\n\n✋ פרסומים יצריכו אישור ידני"
        
        bot_logger.log_user_action(user_id, "auto_mode_toggle", {"new_mode": new_auto})
        
        await update.message.reply_text(message, parse_mode='Markdown')
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """פקודת /status - הצגת מצב נוכחי"""
        user_id = update.effective_user.id
        
        settings = get_user_settings(user_id)
        mock_mode = settings.get('mock_mode', Config.MOCK_MODE)
        auto_post = settings.get('auto_post', Config.AUTO_POST_MODE)
        
        # בדיקת זמינות פלטפורמות
        all_platforms = ['TikTok', 'Twitter', 'Facebook', 'Instagram', 'LinkedIn', 'YouTube', 'Tumblr', 'Telegram']
        platform_status = ValidationHelper.validate_platform_tokens(all_platforms)
        available_platforms = [p for p, available in platform_status.items() if available]
        
        status_message = f"""
📊 **מצב הבוט**

🧪 **מצב בדיקה:** {'פעיל' if mock_mode else 'כבוי'}
🤖 **פרסום אוטומטי:** {'פעיל' if auto_post else 'כבוי'}

🌐 **רשתות זמינות:** {len(available_platforms)}/8
{chr(10).join([f"{'✅' if platform_status.get(p) else '❌'} {p}" for p in all_platforms])}

📈 **סטטיסטיקות:**
• פוסטים אישיים: {len(self.db.get_user_posts(user_id, 100))}
• הגדרות: /mock /auto
        """
        
        bot_logger.log_user_action(user_id, "status_command")
        
        await update.message.reply_text(status_message.strip(), parse_mode='Markdown')
    
    async def handle_video(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """טיפול בהודעות וידאו"""
        user_id = update.effective_user.id
        
        try:
            # בדיקת הודעה
            video_file, text = ValidationHelper.validate_telegram_message(update.message)
            
            # הורדת הקובץ
            file_path = await self._download_video(video_file, user_id)
            
            # בדיקת תקינות הקובץ
            FileHelper.validate_video_file(file_path)
            
            # יצירת שם קובץ ייחודי
            unique_filename = FileHelper.generate_unique_filename(
                video_file.file_name or "video.mp4", 
                user_id
            )
            
            # קבלת הגדרות משתמש
            settings = get_user_settings(user_id)
            mock_mode = settings.get('mock_mode', Config.MOCK_MODE)
            auto_post = settings.get('auto_post', Config.AUTO_POST_MODE)
            
            # רשתות זמינות
            all_platforms = ['TikTok', 'Twitter', 'Facebook', 'Instagram', 'LinkedIn', 'YouTube', 'Tumblr', 'Telegram']
            platform_status = ValidationHelper.validate_platform_tokens(all_platforms)
            available_platforms = [p for p, available in platform_status.items() if available]
            
            if not available_platforms:
                await update.message.reply_text("❌ אין רשתות זמינות. אנא בדקו הגדרות הטוקנים.")
                return
            
            # שמירת הפוסט במסד נתונים
            file_size = FileHelper.get_file_size_mb(file_path)
            post_id = save_post(user_id, unique_filename, text, available_platforms, file_size)
            
            # שמירת נתוני הסשן
            self.user_sessions[user_id] = {
                'post_id': post_id,
                'file_path': file_path,
                'filename': unique_filename,
                'text': text,
                'platforms': available_platforms,
                'mock_mode': mock_mode
            }
            
            bot_logger.log_post_attempt(user_id, available_platforms, unique_filename, text)
            
            # פרסום אוטומטי או תצוגה מקדימה
            if auto_post:
                await self._process_posting(update, user_id, skip_confirmation=True)
            else:
                await self._show_preview(update, user_id)
        
        except (NoVideoError, NoTextError, FileTooLargeError, UnsupportedFileFormatError) as e:
            error_msg = MessageHelper.get_error_message(e)
            await update.message.reply_text(error_msg)
            bot_logger.error("שגיאת ולידציה", user_id=user_id, error=e)
        
        except Exception as e:
            await update.message.reply_text("❌ שגיאה בעיבוד הסרטון. אנא נסו שוב.")
            bot_logger.error("שגיאה בטיפול בוידאו", user_id=user_id, error=e)
    
    async def _download_video(self, video_file, user_id: int) -> str:
        """הורדת קובץ וידאו"""
        try:
            # יצירת תיקיית temp
            temp_dir = FileHelper.create_temp_directory()
            
            # הורדת הקובץ
            file = await video_file.get_file()
            
            # יצירת נתיב זמני
            temp_filename = f"temp_{user_id}_{TimeHelper.get_filename_timestamp()}.mp4"
            file_path = os.path.join(temp_dir, temp_filename)
            
            await file.download_to_drive(file_path)
            
            logger.debug(f"קובץ הורד: {file_path}")
            return file_path
            
        except Exception as e:
            raise FileValidationError(f"שגיאה בהורדת קובץ: {e}")
    
    async def _show_preview(self, update: Update, user_id: int):
        """הצגת תצוגה מקדימה עם כפתורי אישור"""
        session = self.user_sessions.get(user_id)
        if not session:
            await update.message.reply_text("❌ שגיאה: נתוני הסשן אבדו. אנא שלחו את הסרטון שוב.")
            return
        
        # יצירת הודעת תצוגה מקדימה
        preview_text = MessageHelper.create_preview_message(
            session['filename'],
            session['text'],
            session['platforms']
        )
        
        # יצירת כפתורים
        keyboard = [
            [
                InlineKeyboardButton(Messages.BUTTON_CONFIRM, callback_data=f"confirm_{user_id}"),
                InlineKeyboardButton(Messages.BUTTON_CANCEL, callback_data=f"cancel_{user_id}")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            preview_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """טיפול בלחיצות על כפתורים"""
        query = update.callback_query
        user_id = update.effective_user.id
        
        try:
            await query.answer()
            
            if query.data.startswith("confirm_"):
                await self._process_posting(update, user_id)
            
            elif query.data.startswith("cancel_"):
                await self._cancel_posting(update, user_id)
            
            else:
                logger.warning(f"callback לא מוכר: {query.data}")
        
        except Exception as e:
            bot_logger.error("שגיאה בטיפול בכפתור", user_id=user_id, error=e)
            await query.edit_message_text("❌ שגיאה בעיבוד הבקשה")
    
    async def _process_posting(self, update: Update, user_id: int, skip_confirmation: bool = False):
        """עיבוד ופרסום הסרטון"""
        session = self.user_sessions.get(user_id)
        if not session:
            message = "❌ שגיאה: נתוני הסשן אבדו. אנא שלחו את הסרטון שוב."
            if skip_confirmation:
                await update.message.reply_text(message)
            else:
                await update.callback_query.edit_message_text(message)
            return
        
        post_id = session['post_id']
        
        try:
            # עדכון סטטוס לעיבוד
            update_post_status(post_id, 'processing')
            
            # הודעת התחלה
            processing_msg = "🔄 מעבד ומפרסם את הסרטון..."
            if skip_confirmation:
                processing_message = await update.message.reply_text(processing_msg)
            else:
                processing_message = await update.callback_query.edit_message_text(processing_msg)
            
            # מצב בדיקה
            if session['mock_mode']:
                await self._mock_posting(session, processing_message)
                bot_logger.log_mock_mode(user_id, session['filename'], session['platforms'])
            else:
                await self._real_posting(session, processing_message)
            
            # ניקוי קבצים זמניים
            FileHelper.cleanup_temp_files([session['file_path']])
            
            # ניקוי סשן
            del self.user_sessions[user_id]
        
        except Exception as e:
            # עדכון סטטוס לכישלון
            update_post_status(post_id, 'failed', {'error': str(e)})
            
            error_msg = f"❌ שגיאה בפרסום: {str(e)}"
            try:
                await processing_message.edit_text(error_msg)
            except:
                pass
            
            bot_logger.error("שגיאה בפרסום", user_id=user_id, error=e)
    
    async def _mock_posting(self, session: Dict, message):
        """פרסום מדומה (מצב בדיקה)"""
        # המתנה קצרה לסימולציה
        await asyncio.sleep(2)
        
        # עדכון הודעה
        success_msg = Messages.SUCCESS_MOCK_MODE + f"\n\n📁 {session['filename']}\n🌐 {len(session['platforms'])} רשתות"
        await message.edit_text(success_msg)
        
        # עדכון במסד נתונים
        mock_results = {platform: {'status': 'mock_success', 'posted_at': TimeHelper.get_timestamp()} 
                       for platform in session['platforms']}
        
        update_post_status(session['post_id'], 'completed', mock_results)
    
    async def _real_posting(self, session: Dict, message):
        """פרסום אמיתי לרשתות"""
        if not self.social_handler:
            # טעינת social_media_handler (יחובר בהמשך)
            await message.edit_text("❌ שגיאה: מודול הפרסום לא זמין")
            return
        
        results = {}
        successful_platforms = []
        failed_platforms = []
        
        # פרסום לכל פלטפורמה
        for platform in session['platforms']:
            try:
                await message.edit_text(f"🔄 מפרסם ב-{platform}...")
                
                # פרסום (זה יחובר ל-social_media_handler)
                success = await self.social_handler.post_to_platform(
                    platform, 
                    session['file_path'], 
                    session['text']
                )
                
                if success:
                    successful_platforms.append(platform)
                    results[platform] = {'status': 'success', 'posted_at': TimeHelper.get_timestamp()}
                    bot_logger.log_post_result(session.get('user_id'), platform, True)
                else:
                    failed_platforms.append(platform)
                    results[platform] = {'status': 'failed', 'error': 'Unknown error'}
                    bot_logger.log_post_result(session.get('user_id'), platform, False, "Unknown error")
                
            except Exception as e:
                failed_platforms.append(platform)
                results[platform] = {'status': 'failed', 'error': str(e)}
                bot_logger.log_post_result(session.get('user_id'), platform, False, str(e))
        
        # הודעת סיכום
        final_message = MessageHelper.create_success_message(successful_platforms, failed_platforms)
        await message.edit_text(final_message, parse_mode='Markdown')
        
        # עדכון במסד נתונים
        final_status = 'completed' if len(failed_platforms) == 0 else 'partial'
        update_post_status(session['post_id'], final_status, results)
    
    async def _cancel_posting(self, update: Update, user_id: int):
        """ביטול פרסום"""
        session = self.user_sessions.get(user_id)
        if session:
            # ניקוי קבצים
            FileHelper.cleanup_temp_files([session['file_path']])
            
            # עדכון סטטוס במסד נתונים
            update_post_status(session['post_id'], 'cancelled')
            
            # ניקוי סשן
            del self.user_sessions[user_id]
        
        await update.callback_query.edit_message_text("❌ פרסום בוטל")
        bot_logger.log_user_action(user_id, "posting_cancelled")
    
    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """טיפול בהודעות טקסט רגילות"""
        await update.message.reply_text(
            "💡 שלחו לי סרטון עם טקסט כדי להתחיל!\n\n"
            "או השתמשו ב-/help לעזרה נוספת."
        )
    
    def set_social_handler(self, social_handler):
        """הגדרת מטפל הרשתות החברתיות"""
        self.social_handler = social_handler
        logger.info("מטפל רשתות חברתיות חובר לבוט")
    
    async def run(self):
        """הרצת הבוט"""
        try:
            logger.info("מתחיל את בוט הטלגרם...")
            await self.app.run_polling(drop_pending_updates=True)
        except Exception as e:
            logger.critical(f"שגיאה קריטית בהרצת הבוט: {e}")
            raise
    
    def stop(self):
        """עצירת הבוט"""
        if self.app:
            logger.info("עוצר את בוט הטלגרם...")
            # ניקוי קבצים זמניים
            for session in self.user_sessions.values():
                if 'file_path' in session:
                    FileHelper.cleanup_temp_files([session['file_path']])
            
            self.user_sessions.clear()

# יצירת instance גלובלי
_bot_instance = None

def get_bot() -> SocialMediaBot:
    """מחזיר instance של הבוט (Singleton pattern)"""
    global _bot_instance
    
    if _bot_instance is None:
        _bot_instance = SocialMediaBot()
        _bot_instance.setup_application()
    
    return _bot_instance
