# 🤖 בוט פרסום אוטומטי לרשתות חברתיות

> **בוט טלגרם חכם שמפרסם סרטונים אוטומטית ב-8 רשתות חברתיות בו זמנית!**

## 📋 תיאור

בוט זה מאפשר לכם לשלוח סרטון אחד בטלגרם ולפרסם אותו אוטומטית בכל הרשתות החברתיות הפופולריות:

- 🎵 **TikTok**
- 🐦 **Twitter/X**  
- 👥 **Facebook**
- 📸 **Instagram** 
- 💼 **LinkedIn**
- 📺 **YouTube Shorts**
- 📝 **Tumblr**
- 📨 **ערוץ טלגרם**

## ✨ תכונות עיקריות

### 🚀 פרסום מהיר ונוח
- שליחת סרטון + טקסט בטלגרם = פרסום בכל הרשתות
- תצוגה מקדימה עם אפשרות אישור
- מצב פרסום אוטומטי (ללא אישור)

### 🧪 מצב בדיקה (Mock Mode)
- פרסומים מדומים לבדיקות
- בטוח לפיתוח ולימוד
- מציג את כל התהליך ללא פרסום אמיתי

### 📊 מערכת לוגים מתקדמת
- מעקב אחר כל פרסום
- שמירת נתונים במסד נתונים
- לוגים צבעוניים ומפורטים

### 🔒 אבטחה ובטיחות
- ולידציה מלאה של קבצים
- הגנה מפני קבצים גדולים מדי
- ניהול בטוח של טוקנים

## 🛠️ התקנה

### דרישות מערכת
- **Python 3.8+**
- **MongoDB** (מקומי או בענן)
- **חשבונות ברשתות החברתיות** + טוקני API

### שלב 1: הורדה והתקנה

```bash
# שכפול הפרויקט
git clone https://github.com/your-username/social-media-bot.git
cd social-media-bot

# יצירת סביבה וירטואלית
python -m venv venv

# הפעלת הסביבה
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# התקנת תלויות
pip install -r requirements.txt
```

### שלב 2: הגדרת המשתנים

```bash
# העתקת קובץ הסביבה
cp .env.template .env

# עריכת הקובץ עם הטוקנים שלכם
nano .env  # או עורך אחר
```

### שלב 3: הפעלה

```bash
# הפעלת הבוט
python main.py
```

## ⚙️ הגדרה מפורטת

### 🔑 קבלת טוקנים

#### טלגרם (חובה)
1. פתחו צ'אט עם [@BotFather](https://t.me/BotFather)
2. שלחו `/newbot`
3. בחרו שם לבוט
4. העתיקו את הטוקן ל-`TELEGRAM_BOT_TOKEN`

#### Twitter/X
1. התחברו ל-[Twitter Developer](https://developer.twitter.com)
2. צרו אפליקציה חדשה
3. קבלו API Keys והעתיקו:
   - `TWITTER_API_KEY`
   - `TWITTER_API_SECRET` 
   - `TWITTER_ACCESS_TOKEN`
   - `TWITTER_ACCESS_TOKEN_SECRET`

#### Facebook + Instagram
1. התחברו ל-[Facebook Developers](https://developers.facebook.com)
2. צרו אפליקציה
3. הוסיפו **Facebook Login** ו-**Instagram Basic Display**
4. קבלו:
   - `FACEBOOK_ACCESS_TOKEN`
   - `FACEBOOK_PAGE_ID`
   - `INSTAGRAM_BUSINESS_ACCOUNT_ID`

#### שאר הרשתות
ראו הוראות מפורטות בקובץ `.env.template`

### 🗄️ הגדרת MongoDB

#### מקומי (מומלץ לפיתוח)
```bash
# התקנת MongoDB
# Ubuntu/Debian:
sudo apt install mongodb

# macOS:
brew install mongodb-community

# הפעלה:
sudo systemctl start mongodb
```

#### בענן (מומלץ לפרודקשן)
1. צרו חשבון ב-[MongoDB Atlas](https://www.mongodb.com/atlas)
2. צרו Cluster חדש (חינם)
3. קבלו את ה-Connection String
4. הכניסו ל-`MONGODB_URI`

## 🎯 איך זה עובד?

### תרחיש שימוש בסיסי

1. **שליחת סרטון**: שלחוו סרטון עם טקסט לבוט בטלגרם
2. **תצוגה מקדימה**: הבוט יציג תצוגה מקדימה עם כפתורי אישור
3. **פרסום**: לחיצה על "אישור" תפרסם בכל הרשתות הזמינות
4. **מעקב**: הבוט ידווח על הצלחה/כישלון בכל רשת

### פקודות זמינות

| פקודה | תיאור |
|-------|--------|
| `/start` | הפעלת הבוט והודעת ברוכים הבאים |
| `/help` | הוראות שימוש |
| `/mock` | החלפת מצב בדיקה (דמה/אמיתי) |
| `/auto` | החלפת מצב פרסום (אוטומטי/ידני) |
| `/status` | הצגת מצב הבוט והרשתות הזמינות |

### מצבי פעולה

#### 🧪 מצב בדיקה (Mock Mode)
```bash
/mock  # החלפת מצב
```
- פרסומים מדומים (לא אמיתיים)
- בטוח לבדיקות
- רושם לוגים רגילים

#### 🤖 מצב אוטומטי
```bash
/auto  # החלפת מצב
```
- פרסום ישיר ללא אישור
- מהיר יותר
- מתאים למשתמשים מנוסים

## 📁 מבנה הפרויקט

```
social-media-bot/
├── 📄 main.py              # נקודת כניסה ראשית
├── 🤖 telegram_bot.py      # לוגיקת בוט הטלגרם
├── 🌐 social_media_handler.py  # פרסום לרשתות
├── 🗄️ database.py          # ניהול מסד נתונים
├── ⚙️ config.py            # הגדרות וקונפיגורציה
├── 🚨 exceptions.py        # שגיאות מותאמות
├── 📝 logger.py            # מערכת לוגים
├── 🔧 utils.py             # פונקציות עזר
├── 📦 requirements.txt     # תלויות Python
├── 🔒 .env.template        # תבנית משתני סביבה
├── 📋 .gitignore          # קבצים להתעלמות
└── 📖 README.md           # התיעוד הזה
```

## 🔧 פתרון בעיות נפוצות

### ❌ שגיאת חיבור למסד נתונים
```bash
# בדיקת MongoDB
sudo systemctl status mongodb

# הפעלה מחדש
sudo systemctl restart mongodb
```

### ❌ שגיאת טוקן טלגרם
- בדקו שהטוקן נכון ב-`.env`
- וודאו שלא העתקתם רווחים מיותרים

### ❌ רשת לא זמינה
- בדקו שהטוקנים נכונים
- השתמשו ב-`/status` לבדיקת זמינות

### ❌ קובץ גדול מדי
- הגדירו `MAX_FILE_SIZE_MB` גדול יותר
- או דחסו את הסרטון

## 🚀 פריסה (Deployment)

### Render (מומלץ)
1. העתיקו את הפרויקט ל-GitHub
2. התחברו ל-[Render](https://render.com)
3. צרו **Web Service** חדש
4. חברו לרפוזיטורי
5. הגדירו משתני סביבה
6. פרסו!

### Docker
```bash
# בניית הקונטיינר
docker build -t social-media-bot .

# הרצה
docker run -d --env-file .env social-media-bot
```

### VPS מסורתי
```bash
# על השרת
git clone your-repo
cd social-media-bot
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# הרצה ברקע
nohup python main.py &
```

## 📊 לוגים וניטור

### קבצי לוג
- `bot.log` - לוג ראשי
- הלוגים נשמרים גם במסד הנתונים

### צפייה בלוגים בזמן אמת
```bash
tail -f bot.log
```

### לוגים צבעוניים
הבוט כולל לוגים צבעוניים שמקלים על המעקב:
- 🟢 **ירוק**: הצלחה
- 🟡 **צהוב**: אזהרה  
- 🔴 **אדום**: שגיאה
- 🔵 **כחול**: מידע

## 🛡️ אבטחה

### מידע רגיש
- **אל תשתפו את קובץ `.env`**
- הקובץ מכיל טוקנים רגישים
- השתמשו ב-`.env.template` לשיתוף

### הרשאות
- רצו הבוט עם משתמש נפרד (לא root)
- הגדירו firewall מתאים
- עדכנו תלויות באופן קבוע

## 🤝 תרומה לפרויקט

מוזמנים לתרום! אנחנו מחפשים:
- 🐛 דיווח על באגים
- ✨ רעיונות לתכונות חדשות  
- 📖 שיפורי תיעוד
- 🌐 תמיכה ברשתות נוספות

### איך לתרום
1. Fork את הפרויקט
2. צרו branch חדש: `git checkout -b feature/amazing-feature`
3. Commit השינויים: `git commit -m 'Add amazing feature'`
4. Push ל-branch: `git push origin feature/amazing-feature`
5. פתחו Pull Request

## 📄 רישיון

הפרויקט מוגש תחת רישיון MIT - ראו [LICENSE](LICENSE) לפרטים נוספים.

## 💬 תמיכה

### צריכים עזרה?
- 📧 **אימייל**: your-email@example.com
- 💬 **טלגרם**: [@your_username](https://t.me/your_username)
- 🐛 **Issues**: [GitHub Issues](https://github.com/your-username/social-media-bot/issues)

### שאלות נפוצות

**ש: האם הבוט חינמי?**
ת: כן! הקוד חינמי לחלוטין. רק השירותים החיצוניים עלולים לעלות כסף.

**ש: כמה רשתות אפשר לחבר?**
ת: כרגע 8 רשתות, אבל אפשר להוסיף עוד.

**ש: האם זה בטוח?**
ת: כן, הטוקנים נשמרים מקומית ולא נשלחים לשום מקום.

**ש: האם יש הגבלת גודל קבצים?**
ת: כן, ברירת מחדל 50MB אבל אפשר לשנות.

---

<div align="center">

### 🌟 אם הפרויקט עזר לכם - תנו כוכב! ⭐

**נבנה בעם ❤️ בישראל 🇮🇱**

</div>
