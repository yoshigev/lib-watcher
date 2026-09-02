# 📚 מערכת התראות זמינות ספרים (Library Catalog Watcher)

אפליקציית Web גנרית לניטור קטלוגי ספריות ציבוריות מבוססות מערכת BuildaGate, המאפשרת חיפוש ספרים, מעקב אחר עותקים מושאלים וקבלת התראות מייל (Brevo) ברגע שספר הופך לזמין להשאלה.

האפליקציה פועלת במודל **Wake-on-Cron** חינמי לחלוטין (מבוסס **Render**, **MongoDB Atlas** ו-**GitHub Actions**).

---

## 🚀 הרצה מקומית עם קובץ `.env` (Quick Start)

קובץ ההגדרות **`.env`** מכיל את כל משתני הסביבה הדרושים להרצה, והוא מוגדר ב-**`.gitignore`** כך שלעולם לא יעלה ל-Git.

### שלבי הרצה:

1. **התקנת התלויות (חד-פעמי):**
   ```bash
   pip install -r requirements.txt
   ```

2. **הפעלת השרת המקומי:**
   הפעל את השרת באמצעות `python -m uvicorn` (הקורא אוטומטית את קובץ ה-`.env` שבתיקייה):
   ```bash
   python -m uvicorn app.main:app --reload --port 8000
   ```

3. **כניסה למערכת בדפדפן:**
   גש אל: **http://localhost:8000**  
   - **שם משתמש:** `admin`
   - **סיסמה:** `password123`  
   *(המשתמש והסיסמה מוגדרים במשתנה `SEED_USERS` שבקובץ `.env` וניתנים לשינוי בכל עת)*.

> [!NOTE]
> **אין צורך בהתקנת MongoDB מקומי:** אם אין שרת MongoDB דולק במחשב שלך, האפליקציה מזהה זאת ומשתמשת אוטומטית במסד נתונים בזיכרון (`mongomock`) לצורכי פיתוח ובדיקות.

---

## 🔒 שמירה על סודיות ופרטיות ב-Git

- כל שמות הספריות, מזהי ה-URL, הסיסמאות ומפתחות ה-API מוגדרים **אך ורק בקובץ `.env`**.
- הקובץ **`.gitignore`** מונע העלאה של `.env`, `.env.*` או קובצי מידע סודיים ל-GitHub.
- הקובץ **`.env.example`** כולל תבנית נקייה לשימוש ציבורי ב-Repository.

---

## ⚙️ הגדרת שליחת מיילים (Brevo) — שלב אחר שלב

כדי לקבל מיילים אמיתיים לתיבה שלך (300 מיילים חינם ביום ללא כרטיס אשראי):

1. **הרשמה:** פתח חשבון חינם ב-[brevo.com](https://www.brevo.com).
2. **אימות כתובת שולח (Sender Email) — חובה:**
   - בתפריט Brevo גש אל: **Senders, Domains & Dedicated IPs** ➜ **Senders**.
   - לחץ על **Add a sender**, הזן את השם ואת כתובת המייל שלך (למשל: `your_email@gmail.com`).
   - תקבל מייל אימות לתיבה ➜ אשר את הקישור.
3. **יצירת API Key:**
   - לחץ על שם החשבון (בפינה) ➜ **SMTP & API** ➜ לשונית **API Keys**.
   - לחץ על **Generate a new API key** והעתק את המחרוזת (`xkeysib-...`).
4. **הזנת המשתנים בקובץ `.env`:**
   ```env
   BREVO_API_KEY=xkeysib-your-api-key-here
   BREVO_SENDER_EMAIL=your_email@gmail.com   # המייל שאימתת ב-Brevo
   BREVO_SENDER_NAME=התראות ספרייה
   ```

---

## ☁️ פריסה מרכזית וחינמית בענן (Deployment)

הארכיטקטורה מנוהלת מתוך ה-Repository באמצעות **Render Blueprint** ו-**GitHub Actions**.

### 1. יצירת מסד נתונים חינמי ב-MongoDB Atlas:
1. פתח חשבון ב-[mongodb.com/atlas](https://www.mongodb.com/atlas) (חינם, ללא כרטיס אשראי).
2. צור Cluster מסוג **M0 (Free)**.
3. ב-**Database Access** צור משתמש וסיסמה, וב-**Network Access** אפשר גישה מכל מקום (`0.0.0.0/0`).
4. העתק את ה-Connection String (`mongodb+srv://...`).

### 2. פריסה ב-Render באמצעות Blueprint (`render.yaml`):
1. חבר את ה-GitHub repository שלך ב-[render.com](https://render.com).
2. לחץ **New** ➜ **Blueprint**, בחר ב-Repo ואשר.
3. בלוח הניהול ב-Render הזן את ה-Environment Variables מתוך ה-`.env` שלך:
   - `MONGODB_URI`: מחרוזת החיבור של MongoDB Atlas.
   - `LIBRARY_BASE_URL`: כתובת שרת הקטלוג.
   - `LIBRARY_SITE_NAME`: מזהה האתר בקטלוג.
   - `LIBRARY_NEW_NAME_MADE`: מזהה הקטגוריה בקטלוג.
   - `LIBRARY_BUYER_ID`: מזהה הקונה בקטלוג.
   - `LIBRARY_DISPLAY_NAME`: שם התצוגה של הספרייה.
   - `BREVO_API_KEY`, `BREVO_SENDER_EMAIL`: הגדרות המייל מ-Brevo.
   - `SEED_USERS`: משתמש מורשה (JSON).
   - `CRON_SECRET`: מחרוזת סודית לבדיקות ה-Cron.

### 3. הפעלת ה-Cron דרך GitHub Actions:
קובץ ה-Workflow נמצא ב-`.github/workflows/cron.yml`.  
בהגדרות ה-Repository ב-GitHub (Settings ➜ Secrets and variables ➜ Actions), הוסף 2 Secrets:
- `APP_URL`: כתובת האפליקציה ב-Render (למשל: `https://your-app.onrender.com`).
- `CRON_SECRET`: המחרוזת שהגדרת ב-Render.

*GitHub Actions יפעיל בדיקת זמינות כל 15 דקות ויעיר את השרת אוטומטית בעת הצורך.*
