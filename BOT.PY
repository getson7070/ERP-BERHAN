diff --git a/BOT.PY b/BOT.PY
index 69caa0793bc6cde32944137753b314f6ac90d50b..0e7b9506217282fed93b149f2604beda252f9d81 100644
--- a/BOT.PY
+++ b/BOT.PY
@@ -1,49 +1,67 @@
 import sqlite3
 from enum import IntEnum
 from telegram import (
     Update,
     InlineKeyboardButton,
     InlineKeyboardMarkup,
     ReplyKeyboardMarkup,
     KeyboardButton,
 )
 from telegram.ext import (
     Application,
     CommandHandler,
     MessageHandler,
     filters,
     ConversationHandler,
     ContextTypes,
     CallbackQueryHandler,
 )
 import bcrypt
+from argon2 import PasswordHasher
+from argon2.exceptions import VerifyMismatchError
 import logging
 from datetime import datetime
 import csv  # For client list integration
 
 
+ph = PasswordHasher()
+
+
+def hash_password(password: str) -> str:
+    return ph.hash(password)
+
+
+def verify_password(password: str, password_hash: str) -> bool:
+    if password_hash.startswith("$argon2"):
+        try:
+            return ph.verify(password_hash, password)
+        except VerifyMismatchError:
+            return False
+    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
+
+
 logging.basicConfig(level=logging.INFO)
 logger = logging.getLogger(__name__)
 
 
 def get_db():
     conn = sqlite3.connect("erp.db")
     conn.row_factory = sqlite3.Row
     return conn
 
 
 def check_client_list(tin: str):
     try:
         with open("client_list.csv", newline="") as csvfile:
             reader = csv.DictReader(csvfile)
             for row in reader:
                 if row.get("tin") == tin:
                     return row
     except FileNotFoundError:
         logger.error("client_list.csv not found.")
     return None
 
 
 class BotState(IntEnum):
     EMPLOYEE_LOGIN_USERNAME = 0
     EMPLOYEE_LOGIN_PASSWORD = 1
diff --git a/BOT.PY b/BOT.PY
index 69caa0793bc6cde32944137753b314f6ac90d50b..0e7b9506217282fed93b149f2604beda252f9d81 100644
--- a/BOT.PY
+++ b/BOT.PY
@@ -108,86 +126,86 @@ class BotState(IntEnum):
     MAINTENANCE_FOLLOWUP = 60
     MAINTENANCE_ID = 61
     MAINTENANCE_REPORT = 62
 
 async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
     user_id = str(update.effective_user.id)
     conn = get_db()
     user = conn.execute('SELECT * FROM users WHERE (tin = ? OR username = ?) AND user_type = ? AND approved_by_ceo = TRUE', (user_id, user_id, 'employee')).fetchone()
     conn.close()
     if user:
         await update.message.reply_text('You are pre-registered. Use /employee_login to log in.')
     else:
         await update.message.reply_text('Use /client_login to log in, /client_registration to register as client, or /employee_registration (for management) to register as employee.')
     logger.info("User started the bot: %s", user_id)
 
 async def employee_login(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
     await update.message.reply_text('Enter your username (phone number):')
     return BotState.EMPLOYEE_LOGIN_USERNAME
 
 async def get_employee_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
     context.user_data['username'] = update.message.text
     await update.message.reply_text('Enter your password:')
     return BotState.EMPLOYEE_LOGIN_PASSWORD
 
 async def get_employee_password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
-    password = update.message.text.encode('utf-8')
+    password = update.message.text
     conn = get_db()
     user = conn.execute('SELECT * FROM users WHERE user_type = ? AND username = ? AND approved_by_ceo = TRUE', ('employee', context.user_data['username'])).fetchone()
     conn.close()
-    if user and bcrypt.checkpw(password, user['password_hash'].encode('utf-8')):
+    if user and verify_password(password, user['password_hash']):
         context.user_data['logged_in'] = True
         context.user_data['role'] = 'employee'
         context.user_data['tin'] = user['tin'] if user['tin'] else None
         context.user_data['username'] = context.user_data['username']
         context.user_data['permissions'] = user['permissions'].split(',') if user['permissions'] else []
         conn = get_db()
         conn.execute('UPDATE users SET last_login = ? WHERE username = ?', (datetime.now(), context.user_data['username']))
         conn.commit()
         conn.close()
         await update.message.reply_text('Logged in successfully. Use /dashboard to see menu.')
         logger.info("Employee logged in: %s", context.user_data['username'])
     else:
         await update.message.reply_text('Invalid username/password or account not approved. Try /employee_login again.')
         logger.warning("Failed employee login attempt for username: %s", context.user_data['username'])
     return ConversationHandler.END
 
 async def client_login(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
     await update.message.reply_text('Enter your email:')
     return BotState.CLIENT_LOGIN_EMAIL
 
 async def get_client_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
     context.user_data['email'] = update.message.text
     await update.message.reply_text('Enter your password:')
     return BotState.CLIENT_LOGIN_PASSWORD
 
 async def get_client_password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
-    password = update.message.text.encode('utf-8')
+    password = update.message.text
     conn = get_db()
     user = conn.execute('SELECT * FROM users WHERE user_type = ? AND email = ? AND approved_by_ceo = TRUE', ('client', context.user_data['email'])).fetchone()
     conn.close()
-    if user and bcrypt.checkpw(password, user['password_hash'].encode('utf-8')):
+    if user and verify_password(password, user['password_hash']):
         context.user_data['logged_in'] = True
         context.user_data['role'] = 'client'
         context.user_data['tin'] = user['tin']
         context.user_data['username'] = context.user_data['email']
         context.user_data['permissions'] = user['permissions'].split(',') if user['permissions'] else []
         conn = get_db()
         conn.execute('UPDATE users SET last_login = ? WHERE email = ?', (datetime.now(), context.user_data['email']))
         conn.commit()
         conn.close()
         await update.message.reply_text('Logged in successfully. Use /dashboard to see menu.')
         logger.info("Client logged in: %s", context.user_data['email'])
     else:
         await update.message.reply_text('Invalid email/password or account not approved. Try /client_login again.')
         logger.warning("Failed client login attempt for email: %s", context.user_data['email'])
     return ConversationHandler.END
 
 async def client_registration(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
     await update.message.reply_text('Enter your 10-digit TIN (e.g., 0052225274):')
     return BotState.CLIENT_REG_TIN
 
 async def get_client_reg_tin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
     tin = update.message.text
     if not tin.isdigit() or len(tin) != 10:
         await update.message.reply_text('TIN must be a 10-digit number. Try /client_registration again.')
         return ConversationHandler.END
diff --git a/BOT.PY b/BOT.PY
index 69caa0793bc6cde32944137753b314f6ac90d50b..0e7b9506217282fed93b149f2604beda252f9d81 100644
--- a/BOT.PY
+++ b/BOT.PY
@@ -229,111 +247,111 @@ async def get_client_reg_phone(update: Update, context: ContextTypes.DEFAULT_TYP
     reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
     await update.message.reply_text('Select region:', reply_markup=reply_markup)
     return BotState.CLIENT_REG_REGION
 
 async def get_client_reg_region(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
     context.user_data['region'] = update.message.text
     conn = get_db()
     cities = [row['city'] for row in conn.execute('SELECT city FROM regions_cities WHERE region = ?', (context.user_data['region'],)).fetchall()]
     conn.close()
     keyboard = [[KeyboardButton(city) for city in cities[i:i+2]] for i in range(0, len(cities), 2)]
     reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
     await update.message.reply_text('Select city:', reply_markup=reply_markup)
     return BotState.CLIENT_REG_CITY
 
 async def get_client_reg_city(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
     context.user_data['city'] = update.message.text
     await update.message.reply_text('Enter email:')
     return BotState.CLIENT_REG_EMAIL
 
 async def get_client_reg_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
     context.user_data['email'] = update.message.text
     await update.message.reply_text('Enter password:')
     return BotState.CLIENT_REG_PASS
 
 async def get_client_reg_pass(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
-    password = update.message.text.encode('utf-8')
+    password = update.message.text
     conn = get_db()
-    password_hash = bcrypt.hashpw(password, bcrypt.gensalt()).decode('utf-8')
+    password_hash = hash_password(password)
     try:
         conn.execute('''
             INSERT INTO users (user_type, tin, institution_name, address, phone, region, city, email, password_hash, permissions, approved_by_ceo)
             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
         ''', ('client', context.user_data['tin'], context.user_data['institution_name'], context.user_data['address'],
               context.user_data['phone'], context.user_data['region'], context.user_data['city'], context.user_data['email'],
               password_hash, 'put_order,my_approved_orders,order_status,maintenance_request,maintenance_status,message', False))
         conn.commit()
         await update.message.reply_text('Registration submitted. Awaiting management approval.')
         logger.info("Client registration submitted: %s", context.user_data['tin'])
     except sqlite3.IntegrityError:
         await update.message.reply_text('TIN or email already registered. Try /client_registration again.')
     conn.close()
     return ConversationHandler.END
 
 async def employee_registration(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
     conn = get_db()
     user = conn.execute('SELECT permissions FROM users WHERE username = ?', (context.user_data.get('username', ''),)).fetchone()
     conn.close()
     if not user or 'user_management' not in user['permissions'].split(','):
         await update.message.reply_text('Access denied. Only management can register employees.')
         return ConversationHandler.END
     await update.message.reply_text('Enter employee username (phone number):')
     return BotState.EMPLOYEE_REG_USERNAME
 
 async def get_employee_reg_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
     context.user_data['username'] = update.message.text
     await update.message.reply_text('Enter password:')
     return BotState.EMPLOYEE_REG_PASSWORD
 
 async def get_employee_reg_password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
-    context.user_data['password'] = update.message.text.encode('utf-8')
+    context.user_data['password'] = update.message.text
     await update.message.reply_text('Enter permissions (comma-separated, e.g., add_report,view_orders):')
     return BotState.EMPLOYEE_REG_PERMISSIONS
 
 async def get_employee_reg_permissions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
     context.user_data['permissions'] = update.message.text.split(',')
     await update.message.reply_text('Enter position:')
     return BotState.EMPLOYEE_REG_POSITION
 
 async def get_employee_reg_position(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
     context.user_data['position'] = update.message.text
     await update.message.reply_text('Enter hire date (YYYY-MM-DD):')
     return BotState.EMPLOYEE_REG_HIRE_DATE
 
 async def get_employee_reg_hire_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
     context.user_data['hire_date'] = update.message.text
     await update.message.reply_text('Enter salary (ETB):')
     return BotState.EMPLOYEE_REG_SALARY
 
 async def get_employee_reg_salary(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
     try:
         context.user_data['salary'] = float(update.message.text)
     except ValueError:
         await update.message.reply_text('Please enter a valid number for salary.')
         return BotState.EMPLOYEE_REG_SALARY
     conn = get_db()
-    password_hash = bcrypt.hashpw(context.user_data['password'], bcrypt.gensalt()).decode('utf-8')
+    password_hash = hash_password(context.user_data['password'])
     try:
         conn.execute('''
             INSERT INTO users (user_type, username, password_hash, permissions, approved_by_ceo, position, hire_date, salary)
             VALUES (?, ?, ?, ?, ?, ?, ?, ?)
         ''', ('employee', context.user_data['username'], password_hash, ','.join(context.user_data['permissions']),
               False, context.user_data['position'], context.user_data['hire_date'], context.user_data['salary']))
         conn.commit()
         await update.message.reply_text('Employee registration submitted. Awaiting approval.')
         logger.info("Employee registration submitted: %s", context.user_data['username'])
     except sqlite3.IntegrityError:
         await update.message.reply_text('Username already registered. Try /employee_registration again.')
     conn.close()
     return ConversationHandler.END
 
 async def message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
     await update.message.reply_text('Enter your message to support:')
     return BotState.MESSAGE
 
 async def get_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
     message = update.message.text
     conn = get_db()
     user = conn.execute('SELECT tin FROM users WHERE email = ?', (context.user_data.get('email', ''),)).fetchone()
     if user:
         conn.execute('INSERT INTO messages (tin, message, date) VALUES (?, ?, ?)', (user['tin'], message, datetime.now()))
         conn.commit()
