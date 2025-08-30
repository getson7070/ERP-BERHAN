"""Telegram bot interface for BERHAN ERP."""

# mypy: ignore-errors

from enum import IntEnum
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
    Defaults,
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    ContextTypes,
    CallbackQueryHandler,
)
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import logging
from datetime import datetime
import csv  # For client list integration
import os
from db import get_db
import sqlite3
from sqlalchemy import text
from erp.sql_compat import execute as safe_execute


ph = PasswordHasher()
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if TOKEN is None:
    raise RuntimeError("TELEGRAM_BOT_TOKEN is not set")


def hash_password(password: str) -> str:
    return ph.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    if not password_hash.startswith("$argon2"):
        return False
    try:
        return ph.verify(password_hash, password)
    except VerifyMismatchError:
        return False


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
    CLIENT_LOGIN_EMAIL = 2
    CLIENT_LOGIN_PASSWORD = 3
    CLIENT_REG_TIN = 4
    CLIENT_REG_INST = 5
    CLIENT_REG_ADDR = 6
    CLIENT_REG_PHONE = 7
    CLIENT_REG_REGION = 8
    CLIENT_REG_CITY = 9
    CLIENT_REG_EMAIL = 10
    CLIENT_REG_PASS = 11
    EMPLOYEE_REG_USERNAME = 12
    EMPLOYEE_REG_PASSWORD = 13
    EMPLOYEE_REG_PERMISSIONS = 14
    EMPLOYEE_REG_POSITION = 15
    EMPLOYEE_REG_HIRE_DATE = 16
    EMPLOYEE_REG_SALARY = 17
    MESSAGE = 18
    INSTITUTION = 19
    LOCATION = 20
    PHONE = 21
    VISIT_DATE = 22
    INTERESTED_PRODUCTS = 23
    OUTCOME = 24
    SALE_AMOUNT = 25
    VISIT_TYPE = 26
    FOLLOW_UP_DETAILS = 27
    ADD_INVENTORY = 28
    INVENTORY_DESC = 29
    INVENTORY_PACK = 30
    INVENTORY_BRAND = 31
    INVENTORY_TYPE = 32
    INVENTORY_EXP = 33
    INVENTORY_CAT = 34
    ADD_TENDER = 35
    TENDER_TYPE = 36
    TENDER_DESC = 37
    TENDER_DUE = 38
    TENDER_INST = 39
    TENDER_ENVELOPE = 40
    TENDER_PRIVATE = 41
    TENDER_TECH = 42
    TENDER_FIN = 43
    PLACE_ORDER = 44
    ORDER_ITEM = 45
    ORDER_QTY = 46
    ORDER_CUST = 47
    ORDER_VAT_EXEMPT = 48
    RECEIVE_INVENTORY = 49
    RECEIVE_ITEM = 50
    RECEIVE_QTY = 51
    INVENTORY_OUT = 52
    OUT_ITEM = 53
    OUT_QTY = 54
    OUT_ACTION = 55
    OUT_SUBACTION = 56
    MAINTENANCE_REQUEST = 57
    MAINTENANCE_EQUIP = 58
    MAINTENANCE_TYPE = 59
    MAINTENANCE_FOLLOWUP = 60
    MAINTENANCE_ID = 61
    MAINTENANCE_REPORT = 62


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    conn = get_db()
    user = conn.execute(
        text(
            "SELECT * FROM users WHERE (tin = :identifier OR username = :identifier) "
            "AND user_type = :user_type AND approved_by_ceo = TRUE"
        ),
        {"identifier": user_id, "user_type": "employee"},
    ).fetchone()
    conn.close()
    if user:
        await update.message.reply_text(
            "You are pre-registered. Use /employee_login to log in."
        )
    else:
        await update.message.reply_text(
            "Use /client_login to log in, /client_registration to register as client, or /employee_registration (for management) to register as employee."
        )
    logger.info("User started the bot: %s", user_id)


async def employee_login(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Enter your username (phone number):")
    return BotState.EMPLOYEE_LOGIN_USERNAME


async def get_employee_username(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    context.user_data["username"] = update.message.text
    await update.message.reply_text("Enter your password:")
    return BotState.EMPLOYEE_LOGIN_PASSWORD


async def get_employee_password(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    password = update.message.text
    conn = get_db()
    user = conn.execute(
        text(
            "SELECT * FROM users WHERE user_type = :user_type "
            "AND username = :username AND approved_by_ceo = TRUE"
        ),
        {"user_type": "employee", "username": context.user_data["username"]},
    ).fetchone()
    conn.close()
    if user and verify_password(password, user["password_hash"]):
        context.user_data["logged_in"] = True
        context.user_data["role"] = "employee"
        context.user_data["tin"] = user["tin"] if user["tin"] else None
        context.user_data["username"] = context.user_data["username"]
        context.user_data["permissions"] = (
            user["permissions"].split(",") if user["permissions"] else []
        )
        conn = get_db()
        conn.execute(
            text(
                "UPDATE users SET last_login = :last_login WHERE username = :username"
            ),
            {"last_login": datetime.now(), "username": context.user_data["username"]},
        )
        conn.commit()
        conn.close()
        await update.message.reply_text(
            "Logged in successfully. Use /dashboard to see menu."
        )
        logger.info("Employee logged in: %s", context.user_data["username"])
    else:
        await update.message.reply_text(
            "Invalid username/password or account not approved. Try /employee_login again."
        )
        logger.warning(
            "Failed employee login attempt for username: %s",
            context.user_data["username"],
        )
    return ConversationHandler.END


async def client_login(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Enter your email:")
    return BotState.CLIENT_LOGIN_EMAIL


async def get_client_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["email"] = update.message.text
    await update.message.reply_text("Enter your password:")
    return BotState.CLIENT_LOGIN_PASSWORD


async def get_client_password(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    password = update.message.text
    conn = get_db()
    user = conn.execute(
        text(
            "SELECT * FROM users WHERE user_type = :user_type "
            "AND email = :email AND approved_by_ceo = TRUE"
        ),
        {"user_type": "client", "email": context.user_data["email"]},
    ).fetchone()
    conn.close()
    if user and verify_password(password, user["password_hash"]):
        context.user_data["logged_in"] = True
        context.user_data["role"] = "client"
        context.user_data["tin"] = user["tin"]
        context.user_data["username"] = context.user_data["email"]
        context.user_data["permissions"] = (
            user["permissions"].split(",") if user["permissions"] else []
        )
        conn = get_db()
        conn.execute(
            text("UPDATE users SET last_login = :last_login WHERE email = :email"),
            {"last_login": datetime.now(), "email": context.user_data["email"]},
        )
        conn.commit()
        conn.close()
        await update.message.reply_text(
            "Logged in successfully. Use /dashboard to see menu."
        )
        logger.info("Client logged in: %s", context.user_data["email"])
    else:
        await update.message.reply_text(
            "Invalid email/password or account not approved. Try /client_login again."
        )
        logger.warning(
            "Failed client login attempt for email: %s", context.user_data["email"]
        )
    return ConversationHandler.END


async def client_registration(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    await update.message.reply_text("Enter your 10-digit TIN (e.g., 0052225274):")
    return BotState.CLIENT_REG_TIN


async def get_client_reg_tin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    tin = update.message.text
    if not tin.isdigit() or len(tin) != 10:
        await update.message.reply_text(
            "TIN must be a 10-digit number. Try /client_registration again."
        )
        return ConversationHandler.END
    context.user_data["tin"] = tin
    conn = get_db()
    client_info = check_client_list(tin)
    if (
        client_info
        and not conn.execute(
            text("SELECT 1 FROM users WHERE tin = :tin"), {"tin": tin}
        ).fetchone()
    ):
        context.user_data["phone"] = client_info["phone"]
        context.user_data["email"] = client_info["email"]
        await update.message.reply_text(
            f'Client {client_info["name"]} with TIN {tin} found. Enter institution name:'
        )
        conn.close()
        return BotState.CLIENT_REG_INST
    elif conn.execute(
        text("SELECT 1 FROM users WHERE tin = :tin OR email = :email"),
        {"tin": tin, "email": client_info["email"] if client_info else ""},
    ).fetchone():
        user = conn.execute(
            text(
                "SELECT institution_name, tin FROM users WHERE tin = :tin OR email = :email"
            ),
            {"tin": tin, "email": client_info["email"] if client_info else ""},
        ).fetchone()
        if user["tin"] and user["institution_name"]:
            await update.message.reply_text(
                f'Client {user["institution_name"]} with TIN {tin} already exists. Log in or use /message to contact support.'
            )
            conn.close()
            return ConversationHandler.END
        await update.message.reply_text(
            "TIN or email already registered. Try /client_registration again."
        )
        conn.close()
        return ConversationHandler.END
    conn.close()
    await update.message.reply_text("Enter institution name:")
    return BotState.CLIENT_REG_INST


async def get_client_reg_inst(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    context.user_data["institution_name"] = update.message.text
    await update.message.reply_text("Enter address:")
    return BotState.CLIENT_REG_ADDR


async def get_client_reg_addr(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    context.user_data["address"] = update.message.text
    await update.message.reply_text("Enter phone number:")
    return BotState.CLIENT_REG_PHONE


async def get_client_reg_phone(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    context.user_data["phone"] = update.message.text
    conn = get_db()
    regions = [
        row["region"]
        for row in conn.execute(
            text("SELECT DISTINCT region FROM regions_cities")
        ).fetchall()
    ]
    conn.close()
    keyboard = [
        [KeyboardButton(region) for region in regions[i : i + 2]]
        for i in range(0, len(regions), 2)
    ]
    reply_markup = ReplyKeyboardMarkup(
        keyboard, resize_keyboard=True, one_time_keyboard=True
    )
    await update.message.reply_text("Select region:", reply_markup=reply_markup)
    return BotState.CLIENT_REG_REGION


async def get_client_reg_region(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    context.user_data["region"] = update.message.text
    conn = get_db()
    cities = [
        row["city"]
        for row in conn.execute(
            text("SELECT city FROM regions_cities WHERE region = :region"),
            {"region": context.user_data["region"]},
        ).fetchall()
    ]
    conn.close()
    keyboard = [
        [KeyboardButton(city) for city in cities[i : i + 2]]
        for i in range(0, len(cities), 2)
    ]
    reply_markup = ReplyKeyboardMarkup(
        keyboard, resize_keyboard=True, one_time_keyboard=True
    )
    await update.message.reply_text("Select city:", reply_markup=reply_markup)
    return BotState.CLIENT_REG_CITY


async def get_client_reg_city(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    context.user_data["city"] = update.message.text
    await update.message.reply_text("Enter email:")
    return BotState.CLIENT_REG_EMAIL


async def get_client_reg_email(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    context.user_data["email"] = update.message.text
    await update.message.reply_text("Enter password:")
    return BotState.CLIENT_REG_PASS


async def get_client_reg_pass(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    password = update.message.text
    conn = get_db()
    password_hash = hash_password(password)
    try:
        conn.execute(
            text(
                """
                INSERT INTO users (user_type, tin, institution_name, address, phone, region, city, email, password_hash, permissions, approved_by_ceo)
                VALUES (:user_type, :tin, :institution_name, :address, :phone, :region, :city, :email, :password_hash, :permissions, :approved)
                """
            ),
            {
                "user_type": "client",
                "tin": context.user_data["tin"],
                "institution_name": context.user_data["institution_name"],
                "address": context.user_data["address"],
                "phone": context.user_data["phone"],
                "region": context.user_data["region"],
                "city": context.user_data["city"],
                "email": context.user_data["email"],
                "password_hash": password_hash,
                "permissions": "put_order,my_approved_orders,order_status,maintenance_request,maintenance_status,message",
                "approved": False,
            },
        )
        conn.commit()
        await update.message.reply_text(
            "Registration submitted. Awaiting management approval."
        )
        logger.info("Client registration submitted: %s", context.user_data["tin"])
    except sqlite3.IntegrityError:
        await update.message.reply_text(
            "TIN or email already registered. Try /client_registration again."
        )
    conn.close()
    return ConversationHandler.END


async def employee_registration(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    conn = get_db()
    user = conn.execute(
        text("SELECT permissions FROM users WHERE username = :username"),
        {"username": context.user_data.get("username", "")},
    ).fetchone()
    conn.close()
    if not user or "user_management" not in user["permissions"].split(","):
        await update.message.reply_text(
            "Access denied. Only management can register employees."
        )
        return ConversationHandler.END
    await update.message.reply_text("Enter employee username (phone number):")
    return BotState.EMPLOYEE_REG_USERNAME


async def get_employee_reg_username(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    context.user_data["username"] = update.message.text
    await update.message.reply_text("Enter password:")
    return BotState.EMPLOYEE_REG_PASSWORD


async def get_employee_reg_password(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    context.user_data["password"] = update.message.text
    await update.message.reply_text(
        "Enter permissions (comma-separated, e.g., add_report,view_orders):"
    )
    return BotState.EMPLOYEE_REG_PERMISSIONS


async def get_employee_reg_permissions(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    context.user_data["permissions"] = update.message.text.split(",")
    await update.message.reply_text("Enter position:")
    return BotState.EMPLOYEE_REG_POSITION


async def get_employee_reg_position(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    context.user_data["position"] = update.message.text
    await update.message.reply_text("Enter hire date (YYYY-MM-DD):")
    return BotState.EMPLOYEE_REG_HIRE_DATE


async def get_employee_reg_hire_date(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    context.user_data["hire_date"] = update.message.text
    await update.message.reply_text("Enter salary (ETB):")
    return BotState.EMPLOYEE_REG_SALARY


async def get_employee_reg_salary(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    try:
        context.user_data["salary"] = float(update.message.text)
    except ValueError:
        await update.message.reply_text("Please enter a valid number for salary.")
        return BotState.EMPLOYEE_REG_SALARY
    conn = get_db()
    password_hash = hash_password(context.user_data["password"])
    try:
        conn.execute(
            text(
                """
                INSERT INTO users (user_type, username, password_hash, permissions, approved_by_ceo, position, hire_date, salary)
                VALUES (:user_type, :username, :password_hash, :permissions, :approved, :position, :hire_date, :salary)
                """
            ),
            {
                "user_type": "employee",
                "username": context.user_data["username"],
                "password_hash": password_hash,
                "permissions": ",".join(context.user_data["permissions"]),
                "approved": False,
                "position": context.user_data["position"],
                "hire_date": context.user_data["hire_date"],
                "salary": context.user_data["salary"],
            },
        )
        conn.commit()
        await update.message.reply_text(
            "Employee registration submitted. Awaiting approval."
        )
        logger.info(
            "Employee registration submitted: %s", context.user_data["username"]
        )
    except sqlite3.IntegrityError:
        await update.message.reply_text(
            "Username already registered. Try /employee_registration again."
        )
    conn.close()
    return ConversationHandler.END


async def message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Enter your message to support:")
    return BotState.MESSAGE


async def get_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    message = update.message.text
    conn = get_db()
    user = conn.execute(
        text("SELECT tin FROM users WHERE email = :email"),
        {"email": context.user_data.get("email", "")},
    ).fetchone()
    if user:
        conn.execute(
            text(
                "INSERT INTO messages (tin, message, date) VALUES (:tin, :message, :date)"
            ),
            {"tin": user["tin"], "message": message, "date": datetime.now()},
        )
        conn.commit()
        await update.message.reply_text("Message sent to support successfully.")
    else:
        await update.message.reply_text("Please log in to send a message.")
    conn.close()
    return ConversationHandler.END


async def dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if "logged_in" not in context.user_data or not context.user_data["logged_in"]:
        await update.message.reply_text(
            "Please log in first with /employee_login or /client_login."
        )
        return ConversationHandler.END
    if "client" in context.user_data["role"]:
        keyboard = [
            [KeyboardButton("Put Order"), KeyboardButton("My Approved Orders")],
            [KeyboardButton("Order Status"), KeyboardButton("Maintenance Request")],
            [KeyboardButton("Maintenance Status"), KeyboardButton("Message")],
            [KeyboardButton("Logout")],
        ]
    else:
        keyboard = [
            [KeyboardButton("Marketing"), KeyboardButton("Inventory")],
            [KeyboardButton("Tenders"), KeyboardButton("Reports")],
            [KeyboardButton("Orders"), KeyboardButton("Maintenance")],
            [KeyboardButton("Logout")],
        ]
    reply_markup = ReplyKeyboardMarkup(
        keyboard, resize_keyboard=True, one_time_keyboard=True
    )
    await update.message.reply_text(
        "Welcome to BERHAN ERP Dashboard. Choose an option:", reply_markup=reply_markup
    )
    return ConversationHandler.END


async def logout(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text(
        "Logged out. Use /employee_login or /client_login to log in again."
    )
    logger.info("User logged out: %s", update.effective_user.id)
    return ConversationHandler.END


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    if "logged_in" not in context.user_data or not context.user_data["logged_in"]:
        await update.message.reply_text(
            "Please log in first with /employee_login or /client_login."
        )
        return ConversationHandler.END
    if text == "Put Order" and "put_order" in context.user_data["permissions"]:
        return await place_order(update, context)
    elif (
        text == "My Approved Orders"
        and "my_approved_orders" in context.user_data["permissions"]
    ):
        return await my_approved_orders(update, context)
    elif text == "Order Status" and "order_status" in context.user_data["permissions"]:
        return await order_status(update, context)
    elif (
        text == "Maintenance Request"
        and "maintenance_request" in context.user_data["permissions"]
    ):
        return await maintenance_request(update, context)
    elif (
        text == "Maintenance Status"
        and "maintenance_status" in context.user_data["permissions"]
    ):
        return await maintenance_status(update, context)
    elif text == "Message" and "message" in context.user_data["permissions"]:
        return await message(update, context)
    elif text == "Marketing" and any(
        p in context.user_data["permissions"]
        for p in ["add_report", "my_report", "marketing_report", "promotion_report"]
    ):
        keyboard = [
            [KeyboardButton("Add Report"), KeyboardButton("My Report")],
            [KeyboardButton("Back")],
        ]
        reply_markup = ReplyKeyboardMarkup(
            keyboard, resize_keyboard=True, one_time_keyboard=True
        )
        await update.message.reply_text("Marketing Section:", reply_markup=reply_markup)
        return ConversationHandler.END
    elif text == "Inventory" and any(
        p in context.user_data["permissions"]
        for p in [
            "add_inventory",
            "receive_inventory",
            "inventory_out",
            "inventory_report",
        ]
    ):
        keyboard = [
            [KeyboardButton("Add Inventory"), KeyboardButton("Receive Inventory")],
            [KeyboardButton("Inventory Out"), KeyboardButton("Inventory Report")],
            [KeyboardButton("Back")],
        ]
        reply_markup = ReplyKeyboardMarkup(
            keyboard, resize_keyboard=True, one_time_keyboard=True
        )
        await update.message.reply_text("Inventory Section:", reply_markup=reply_markup)
        return ConversationHandler.END
    elif text == "Tenders" and any(
        p in context.user_data["permissions"]
        for p in ["add_tender", "tenders_list", "tenders_report"]
    ):
        keyboard = [
            [KeyboardButton("Add Tender"), KeyboardButton("Tenders List")],
            [KeyboardButton("Back")],
        ]
        reply_markup = ReplyKeyboardMarkup(
            keyboard, resize_keyboard=True, one_time_keyboard=True
        )
        await update.message.reply_text("Tenders Section:", reply_markup=reply_markup)
        return ConversationHandler.END
    elif text == "Reports" and any(
        p in context.user_data["permissions"]
        for p in ["tenders_report", "inventory_report", "marketing_report"]
    ):
        keyboard = [
            [KeyboardButton("Tenders Report"), KeyboardButton("Inventory Report")],
            [KeyboardButton("Marketing Report"), KeyboardButton("Back")],
        ]
        reply_markup = ReplyKeyboardMarkup(
            keyboard, resize_keyboard=True, one_time_keyboard=True
        )
        await update.message.reply_text("Reports Section:", reply_markup=reply_markup)
        return ConversationHandler.END
    elif text == "Orders" and "view_orders" in context.user_data["permissions"]:
        keyboard = [
            [KeyboardButton("Place Order"), KeyboardButton("View Orders")],
            [KeyboardButton("Back")],
        ]
        reply_markup = ReplyKeyboardMarkup(
            keyboard, resize_keyboard=True, one_time_keyboard=True
        )
        await update.message.reply_text("Orders Section:", reply_markup=reply_markup)
        return ConversationHandler.END
    elif text == "Maintenance" and any(
        p in context.user_data["permissions"]
        for p in ["maintenance_request", "maintenance_report", "maintenance_followup"]
    ):
        keyboard = [
            [KeyboardButton("Request Maintenance"), KeyboardButton("View Maintenance")],
            [KeyboardButton("Back")],
        ]
        reply_markup = ReplyKeyboardMarkup(
            keyboard, resize_keyboard=True, one_time_keyboard=True
        )
        await update.message.reply_text(
            "Maintenance Section:", reply_markup=reply_markup
        )
        return ConversationHandler.END
    elif text == "Logout":
        await logout(update, context)
        return ConversationHandler.END
    elif text == "Back":
        await dashboard(update, context)
        return ConversationHandler.END
    elif text == "Add Report" and "add_report" in context.user_data["permissions"]:
        return await add_report(update, context)
    elif text == "My Report" and "add_report" in context.user_data["permissions"]:
        return await my_report(update, context)
    elif (
        text == "Add Inventory" and "add_inventory" in context.user_data["permissions"]
    ):
        return await add_inventory(update, context)
    elif (
        text == "Receive Inventory"
        and "receive_inventory" in context.user_data["permissions"]
    ):
        return await receive_inventory(update, context)
    elif (
        text == "Inventory Out" and "inventory_out" in context.user_data["permissions"]
    ):
        return await inventory_out(update, context)
    elif (
        text == "Inventory Report"
        and "inventory_report" in context.user_data["permissions"]
    ):
        return await inventory_report(update, context)
    elif text == "Add Tender" and "add_tender" in context.user_data["permissions"]:
        return await add_tender(update, context)
    elif text == "Tenders List" and "tenders_list" in context.user_data["permissions"]:
        return await tenders_list(update, context)
    elif (
        text == "Tenders Report"
        and "tenders_report" in context.user_data["permissions"]
    ):
        return await tenders_report(update, context)
    elif text == "Marketing Report" in context.user_data["permissions"]:
        return await marketing_report(update, context)
    elif text == "Place Order" and "put_order" in context.user_data["permissions"]:
        return await place_order(update, context)
    elif text == "View Orders" and "view_orders" in context.user_data["permissions"]:
        return await view_orders(update, context)
    elif (
        text == "Request Maintenance"
        and "maintenance_request" in context.user_data["permissions"]
    ):
        return await maintenance_request(update, context)
    elif (
        text == "View Maintenance"
        and "maintenance_report" in context.user_data["permissions"]
    ):
        return await maintenance_view(update, context)
    else:
        await update.message.reply_text(
            "Invalid option or insufficient permissions. Please choose from the menu."
        )
        return ConversationHandler.END


async def add_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if "logged_in" not in context.user_data or not context.user_data["logged_in"]:
        await update.message.reply_text(
            "Please log in first with /employee_login or /client_login."
        )
        return ConversationHandler.END
    if "add_report" not in context.user_data["permissions"]:
        await update.message.reply_text("Access denied. Missing add_report permission.")
        return ConversationHandler.END
    await update.message.reply_text("Enter institution:")
    return BotState.INSTITUTION


async def get_institution(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["institution"] = update.message.text
    await update.message.reply_text("Enter location (e.g., Location 1):")
    return BotState.LOCATION


async def get_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["location"] = update.message.text
    await update.message.reply_text("Enter phone (internal, not visible to reps):")
    return BotState.PHONE


async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["phone"] = update.message.text
    await update.message.reply_text("Enter visit date (YYYY-MM-DD):")
    return BotState.VISIT_DATE


async def get_visit_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["visit_date"] = update.message.text
    keyboard = [
        [InlineKeyboardButton("CLIA", callback_data="clia")],
        [InlineKeyboardButton("Chemistry", callback_data="chemistry")],
        [InlineKeyboardButton("POCT", callback_data="poct")],
        [InlineKeyboardButton("Hematology", callback_data="hematology")],
        [InlineKeyboardButton("Microbiology", callback_data="microbiology")],
        [InlineKeyboardButton("Ultrasound", callback_data="ultrasound")],
        [InlineKeyboardButton("Other", callback_data="other")],
    ]
    reply_markup = InlineKeyboardMarkup(
        [keyboard[i : i + 2] for i in range(0, len(keyboard), 2)]
    )
    await update.message.reply_text(
        "Select product category:", reply_markup=reply_markup
    )
    context.user_data["selected_products"] = []
    context.user_data["current_category"] = None
    return BotState.INTERESTED_PRODUCTS


def build_menu(buttons, n_cols):
    return [buttons[i : i + n_cols] for i in range(0, len(buttons), n_cols)]


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    data = query.data
    if data in [
        "clia",
        "chemistry",
        "poct",
        "hematology",
        "microbiology",
        "ultrasound",
        "other",
    ]:
        context.user_data["current_category"] = data
        categories = {
            "clia": ["EXI1800", "EXI1820", "EXI2400"],
            "chemistry": ["EXC200", "EXC420"],
            "poct": ["EXR110", "EXR120", "Q8 PRO"],
            "hematology": ["EXC8000", "EXC6000", "Z50", "Z3", "Z3 CRP"],
            "microbiology": ["EXS2600", "EXB120"],
            "ultrasound": [
                "DW-350",
                "DW-360",
                "DW-370",
                "DW-580",
                "DW-CE540",
                "DW-CE780",
                "DW-CT520",
                "DW-PE522",
                "DW-PE542",
                "DW-PE512",
            ],
            "other": ["OTHERS"],
        }
        items = categories[data]
        keyboard = [
            [
                InlineKeyboardButton(item, callback_data=f"select_{item}")
                for item in items
            ]
        ]
        keyboard.append(
            [
                InlineKeyboardButton("Back to Categories", callback_data="back"),
                InlineKeyboardButton("Done", callback_data="done"),
            ]
        )
        reply_markup = InlineKeyboardMarkup(build_menu(keyboard, 2))
        await query.edit_message_text(
            text=f"Select products from {data.upper()}:",  # nosec B608
            reply_markup=reply_markup,
        )
        return BotState.INTERESTED_PRODUCTS
    elif data.startswith("select_"):
        product = data.replace("select_", "")
        if product not in context.user_data["selected_products"]:
            context.user_data["selected_products"].append(product)
        await query.edit_message_text(
            text=f"Selected products: {', '.join(context.user_data['selected_products'])}\nSelect more or use 'Back'/'Done'."
        )
        return BotState.INTERESTED_PRODUCTS
    elif data == "back":
        keyboard = [
            [InlineKeyboardButton("CLIA", callback_data="clia")],
            [InlineKeyboardButton("Chemistry", callback_data="chemistry")],
            [InlineKeyboardButton("POCT", callback_data="poct")],
            [InlineKeyboardButton("Hematology", callback_data="hematology")],
            [InlineKeyboardButton("Microbiology", callback_data="microbiology")],
            [InlineKeyboardButton("Ultrasound", callback_data="ultrasound")],
            [InlineKeyboardButton("Other", callback_data="other")],
        ]
        reply_markup = InlineKeyboardMarkup(build_menu(keyboard, 2))
        await query.edit_message_text(
            text="Select product category:", reply_markup=reply_markup
        )
        context.user_data["current_category"] = None
        return BotState.INTERESTED_PRODUCTS
    elif data == "done":
        await query.edit_message_text(
            text=f"Selected products: {', '.join(context.user_data['selected_products'])}"
        )
        context.user_data["interested_products"] = ", ".join(
            context.user_data["selected_products"]
        )
        keyboard = [
            [KeyboardButton("Sale"), KeyboardButton("Contract")],
            [KeyboardButton("Negotiation"), KeyboardButton("No Interest")],
        ]
        reply_markup = ReplyKeyboardMarkup(
            keyboard, resize_keyboard=True, one_time_keyboard=True
        )
        await query.message.reply_text("Enter outcome:", reply_markup=reply_markup)
        return BotState.OUTCOME


async def get_outcome(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["outcome"] = update.message.text
    if context.user_data["outcome"] == "Sale":
        await update.message.reply_text("Enter sale amount (ETB):")
        return BotState.SALE_AMOUNT
    else:
        keyboard = [[KeyboardButton("First Visit"), KeyboardButton("Follow-up")]]
        reply_markup = ReplyKeyboardMarkup(
            keyboard, resize_keyboard=True, one_time_keyboard=True
        )
        await update.message.reply_text("Enter visit type:", reply_markup=reply_markup)
        return BotState.VISIT_TYPE


async def get_sale_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data["sale_amount"] = float(update.message.text)
    except ValueError:
        await update.message.reply_text("Please enter a valid number for sale amount.")
        return BotState.SALE_AMOUNT
    keyboard = [[KeyboardButton("First Visit"), KeyboardButton("Follow-up")]]
    reply_markup = ReplyKeyboardMarkup(
        keyboard, resize_keyboard=True, one_time_keyboard=True
    )
    await update.message.reply_text("Enter visit type:", reply_markup=reply_markup)
    return BotState.VISIT_TYPE


async def get_visit_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["visit_type"] = update.message.text
    if context.user_data["visit_type"] == "Follow-up":
        await update.message.reply_text("Enter follow-up details:")
        return BotState.FOLLOW_UP_DETAILS
    else:
        await save_report(update, context)
        return ConversationHandler.END


async def get_follow_up_details(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    context.user_data["follow_up_details"] = update.message.text
    await save_report(update, context)
    return ConversationHandler.END


async def save_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    conn = get_db()
    sales_rep = (
        context.user_data["username"]
        if context.user_data["tin"] is None
        else context.user_data["tin"]
    )
    conn.execute(
        text(
            """
            INSERT INTO reports (institution, location, owner, phone, visit_date, interested_products, outcome, sale_amount, visit_type, follow_up_details, sales_rep)
            VALUES (:institution, :location, :owner, :phone, :visit_date, :interested_products, :outcome, :sale_amount, :visit_type, :follow_up_details, :sales_rep)
            """
        ),
        {
            "institution": context.user_data["institution"],
            "location": context.user_data["location"],
            "owner": "",
            "phone": context.user_data["phone"],
            "visit_date": context.user_data["visit_date"],
            "interested_products": context.user_data["interested_products"],
            "outcome": context.user_data["outcome"],
            "sale_amount": context.user_data.get("sale_amount"),
            "visit_type": context.user_data["visit_type"],
            "follow_up_details": context.user_data.get("follow_up_details"),
            "sales_rep": sales_rep,
        },
    )
    conn.commit()
    await update.message.reply_text("Report submitted successfully.")
    logger.info("Report submitted by %s", sales_rep)
    conn.close()


async def my_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if "add_report" not in context.user_data["permissions"]:
        await update.message.reply_text("Access denied. Missing add_report permission.")
        return ConversationHandler.END
    conn = get_db()
    sales_rep = (
        context.user_data["username"]
        if context.user_data["tin"] is None
        else context.user_data["tin"]
    )
    reports = conn.execute(
        text(
            "SELECT institution, visit_date, outcome, visit_type FROM reports WHERE sales_rep = :sales_rep ORDER BY id DESC LIMIT 5"
        ),
        {"sales_rep": sales_rep},
    ).fetchall()
    conn.close()
    if not reports:
        await update.message.reply_text("No reports found.")
        return ConversationHandler.END
    message = "My Reports:\n"
    for report in reports:
        message += f"Institution: {report['institution']}, Date: {report['visit_date']}, Outcome: {report['outcome']}, Type: {report['visit_type']}\n"
    await update.message.reply_text(message)
    return ConversationHandler.END


async def add_inventory(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if "add_inventory" not in context.user_data["permissions"]:
        await update.message.reply_text(
            "Access denied. Missing add_inventory permission."
        )
        return ConversationHandler.END
    await update.message.reply_text("Enter description:")
    return BotState.ADD_INVENTORY


async def get_inventory_desc(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["description"] = update.message.text
    await update.message.reply_text("Enter pack size:")
    return BotState.INVENTORY_PACK


async def get_inventory_pack(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["pack_size"] = update.message.text
    await update.message.reply_text("Enter brand:")
    return BotState.INVENTORY_BRAND


async def get_inventory_brand(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    context.user_data["brand"] = update.message.text
    keyboard = [[KeyboardButton("Device"), KeyboardButton("Reagent")]]
    reply_markup = ReplyKeyboardMarkup(
        keyboard, resize_keyboard=True, one_time_keyboard=True
    )
    await update.message.reply_text("Enter type:", reply_markup=reply_markup)
    return BotState.INVENTORY_TYPE


async def get_inventory_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["type"] = update.message.text
    if context.user_data["type"] == "Reagent":
        await update.message.reply_text("Enter expiration date (YYYY-MM-DD):")
        return BotState.INVENTORY_EXP
    else:
        await update.message.reply_text("Enter category (e.g., CLIA, Chemistry):")
        return BotState.INVENTORY_CAT


async def get_inventory_exp(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["exp_date"] = update.message.text
    await update.message.reply_text("Enter category (e.g., CLIA, Chemistry):")
    return BotState.INVENTORY_CAT


async def get_inventory_cat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["category"] = update.message.text
    await save_inventory(update, context)
    return ConversationHandler.END


async def save_inventory(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    conn = get_db()
    initials = "".join(word[0].upper() for word in context.user_data["brand"].split())
    seq = conn.execute(text("SELECT COUNT(*) FROM inventory")).fetchone()[0] + 1
    item_code = f"{context.user_data['category'][:3].upper()}-{initials}-{context.user_data['pack_size']}-{seq:04d}"
    user = (
        context.user_data["username"]
        if context.user_data["tin"] is None
        else context.user_data["tin"]
    )
    conn.execute(
        text(
            """
            INSERT INTO inventory (item_code, description, pack_size, brand, type, exp_date, category, stock)
            VALUES (:item_code, :description, :pack_size, :brand, :type, :exp_date, :category, :stock)
            """
        ),
        {
            "item_code": item_code,
            "description": context.user_data["description"],
            "pack_size": context.user_data["pack_size"],
            "brand": context.user_data["brand"],
            "type": context.user_data["type"],
            "exp_date": context.user_data.get("exp_date"),
            "category": context.user_data["category"],
            "stock": 0,
        },
    )
    conn.commit()
    await update.message.reply_text("Inventory item added successfully.")
    logger.info("Inventory added by %s", user)
    conn.close()


async def receive_inventory(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if "receive_inventory" not in context.user_data["permissions"]:
        await update.message.reply_text(
            "Access denied. Missing receive_inventory permission."
        )
        return ConversationHandler.END
    conn = get_db()
    items = conn.execute("SELECT id, item_code FROM inventory").fetchall()
    conn.close()
    if not items:
        await update.message.reply_text("No items available in inventory.")
        return ConversationHandler.END
    keyboard = [
        [KeyboardButton(item["item_code"]) for item in items[i : i + 2]]
        for i in range(0, len(items), 2)
    ]
    reply_markup = ReplyKeyboardMarkup(
        keyboard, resize_keyboard=True, one_time_keyboard=True
    )
    await update.message.reply_text(
        "Select item to receive:", reply_markup=reply_markup
    )
    return BotState.RECEIVE_INVENTORY


async def get_receive_item(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    conn = get_db()
    context.user_data["item_id"] = conn.execute(
        text("SELECT id FROM inventory WHERE item_code = :code"),
        {"code": update.message.text},
    ).fetchone()["id"]
    conn.close()
    await update.message.reply_text("Enter quantity to receive:")
    return BotState.RECEIVE_QTY


async def get_receive_qty(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data["quantity"] = int(update.message.text)
    except ValueError:
        await update.message.reply_text("Please enter a valid number for quantity.")
        return BotState.RECEIVE_QTY
    conn = get_db()
    conn.execute(
        text("UPDATE inventory SET stock = stock + :qty WHERE id = :id"),
        {"qty": context.user_data["quantity"], "id": context.user_data["item_id"]},
    )
    user = (
        context.user_data["username"]
        if context.user_data["tin"] is None
        else context.user_data["tin"]
    )
    conn.execute(
        text(
            """
            INSERT INTO inventory_movements (item_id, quantity, action, date, user)
            VALUES (:item_id, :quantity, 'Receive', :date, :user)
            """
        ),
        {
            "item_id": context.user_data["item_id"],
            "quantity": context.user_data["quantity"],
            "date": datetime.now(),
            "user": user,
        },
    )
    conn.commit()
    await update.message.reply_text("Inventory received successfully.")
    conn.close()
    return ConversationHandler.END


async def inventory_out(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if "inventory_out" not in context.user_data["permissions"]:
        await update.message.reply_text(
            "Access denied. Missing inventory_out permission."
        )
        return ConversationHandler.END
    conn = get_db()
    items = conn.execute(
        "SELECT id, item_code, stock FROM inventory WHERE stock > 0"
    ).fetchall()
    conn.close()
    if not items:
        await update.message.reply_text("No items available for out.")
        return ConversationHandler.END
    keyboard = [
        [KeyboardButton(item["item_code"]) for item in items[i : i + 2]]
        for i in range(0, len(items), 2)
    ]
    reply_markup = ReplyKeyboardMarkup(
        keyboard, resize_keyboard=True, one_time_keyboard=True
    )
    await update.message.reply_text(
        "Select item to move out:", reply_markup=reply_markup
    )
    return BotState.INVENTORY_OUT


async def get_out_item(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    conn = get_db()
    context.user_data["item_id"] = conn.execute(
        text("SELECT id FROM inventory WHERE item_code = :code"),
        {"code": update.message.text},
    ).fetchone()["id"]
    conn.close()
    await update.message.reply_text("Enter quantity to move out:")
    return BotState.OUT_QTY


async def get_out_qty(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data["quantity"] = int(update.message.text)
    except ValueError:
        await update.message.reply_text("Please enter a valid number for quantity.")
        return BotState.OUT_QTY
    conn = get_db()
    stock = conn.execute(
        text("SELECT stock FROM inventory WHERE id = :id"),
        {"id": context.user_data["item_id"]},
    ).fetchone()["stock"]
    conn.close()
    if stock < context.user_data["quantity"]:
        await update.message.reply_text("Insufficient stock.")
        return BotState.OUT_QTY
    keyboard = [[KeyboardButton("Sales"), KeyboardButton("Delivery")]]
    reply_markup = ReplyKeyboardMarkup(
        keyboard, resize_keyboard=True, one_time_keyboard=True
    )
    await update.message.reply_text("Enter action:", reply_markup=reply_markup)
    return BotState.OUT_ACTION


async def get_out_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["action"] = update.message.text
    if context.user_data["action"] == "Sales":
        keyboard = [[KeyboardButton("Credit"), KeyboardButton("Cash")]]
    else:
        keyboard = [
            [KeyboardButton("Sample"), KeyboardButton("Pre-qualification")],
            [KeyboardButton("Quality Test"), KeyboardButton("Donation")],
        ]
    reply_markup = ReplyKeyboardMarkup(
        keyboard, resize_keyboard=True, one_time_keyboard=True
    )
    await update.message.reply_text("Enter sub-action:", reply_markup=reply_markup)
    return BotState.OUT_SUBACTION


async def get_out_subaction(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["sub_action"] = update.message.text
    conn = get_db()
    conn.execute(
        text("UPDATE inventory SET stock = stock - :qty WHERE id = :id"),
        {"qty": context.user_data["quantity"], "id": context.user_data["item_id"]},
    )
    user = (
        context.user_data["username"]
        if context.user_data["tin"] is None
        else context.user_data["tin"]
    )
    conn.execute(
        text(
            """
            INSERT INTO inventory_movements (item_id, quantity, action, sub_action, date, user)
            VALUES (:item_id, :quantity, :action, :sub_action, :date, :user)
            """
        ),
        {
            "item_id": context.user_data["item_id"],
            "quantity": context.user_data["quantity"],
            "action": context.user_data["action"],
            "sub_action": context.user_data["sub_action"],
            "date": datetime.now(),
            "user": user,
        },
    )
    conn.commit()
    await update.message.reply_text("Inventory out recorded successfully.")
    conn.close()
    return ConversationHandler.END


async def inventory_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if "inventory_report" not in context.user_data["permissions"]:
        await update.message.reply_text(
            "Access denied. Missing inventory_report permission."
        )
        return ConversationHandler.END
    conn = get_db()
    inventory = conn.execute(
        "SELECT * FROM inventory ORDER BY id DESC LIMIT 5"
    ).fetchall()
    movements = conn.execute(
        "SELECT * FROM inventory_movements ORDER BY date DESC LIMIT 5"
    ).fetchall()
    conn.close()
    message = "Inventory Report:\n\nItems:\n"
    for item in inventory:
        message += (
            f"ID: {item['id']}, Code: {item['item_code']}, Stock: {item['stock']}\n"
        )
    message += "\nMovements:\n"
    for move in movements:
        message += f"ID: {move['id']}, Item ID: {move['item_id']}, Qty: {move['quantity']}, Date: {move['date']}\n"
    await update.message.reply_text(message)
    return ConversationHandler.END


async def add_tender(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if "add_tender" not in context.user_data["permissions"]:
        await update.message.reply_text("Access denied. Missing add_tender permission.")
        return ConversationHandler.END
    conn = get_db()
    tender_types = conn.execute("SELECT id, type_name FROM tender_types").fetchall()
    conn.close()
    keyboard = [[KeyboardButton(t["type_name"]) for t in tender_types]]
    reply_markup = ReplyKeyboardMarkup(
        keyboard, resize_keyboard=True, one_time_keyboard=True
    )
    await update.message.reply_text("Select tender type:", reply_markup=reply_markup)
    return BotState.TENDER_TYPE


async def get_tender_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    conn = get_db()
    context.user_data["tender_type_id"] = conn.execute(
        text("SELECT id FROM tender_types WHERE type_name = :name"),
        {"name": update.message.text},
    ).fetchone()["id"]
    conn.close()
    await update.message.reply_text("Enter description:")
    return BotState.TENDER_DESC


async def get_tender_desc(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["description"] = update.message.text
    await update.message.reply_text("Enter due date (YYYY-MM-DD):")
    return BotState.TENDER_DUE


async def get_tender_due(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["due_date"] = update.message.text
    await update.message.reply_text("Enter institution (optional):")
    return BotState.TENDER_INST


async def get_tender_inst(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["institution"] = update.message.text
    keyboard = [[KeyboardButton("One Envelope"), KeyboardButton("Two Envelope")]]
    reply_markup = ReplyKeyboardMarkup(
        keyboard, resize_keyboard=True, one_time_keyboard=True
    )
    await update.message.reply_text("Enter envelope type:", reply_markup=reply_markup)
    return BotState.TENDER_ENVELOPE


async def get_tender_envelope(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    context.user_data["envelope_type"] = update.message.text
    if context.user_data["envelope_type"] == "One Envelope":
        await update.message.reply_text("Enter private key:")
        return BotState.TENDER_PRIVATE
    else:
        await update.message.reply_text("Enter technical key:")
        return BotState.TENDER_TECH


async def get_tender_private(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["private_key"] = update.message.text
    await save_tender(update, context)
    return ConversationHandler.END


async def get_tender_tech(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["tech_key"] = update.message.text
    await update.message.reply_text("Enter financial key:")
    return BotState.TENDER_FIN


async def get_tender_fin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["fin_key"] = update.message.text
    await save_tender(update, context)
    return ConversationHandler.END


async def save_tender(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    conn = get_db()
    user = (
        context.user_data["username"]
        if context.user_data["tin"] is None
        else context.user_data["tin"]
    )
    conn.execute(
        text(
            """
            INSERT INTO tenders (tender_type_id, description, due_date, status, user, institution, envelope_type, private_key, tech_key, fin_key)
            VALUES (:tender_type_id, :description, :due_date, :status, :user, :institution, :envelope_type, :private_key, :tech_key, :fin_key)
            """
        ),
        {
            "tender_type_id": context.user_data["tender_type_id"],
            "description": context.user_data["description"],
            "due_date": context.user_data["due_date"],
            "status": "Open",
            "user": user,
            "institution": context.user_data.get("institution"),
            "envelope_type": context.user_data["envelope_type"],
            "private_key": context.user_data.get("private_key"),
            "tech_key": context.user_data.get("tech_key"),
            "fin_key": context.user_data.get("fin_key"),
        },
    )
    conn.commit()
    await update.message.reply_text("Tender added successfully.")
    logger.info("Tender added by %s", user)
    conn.close()


async def tenders_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if "tenders_list" not in context.user_data["permissions"]:
        await update.message.reply_text(
            "Access denied. Missing tenders_list permission."
        )
        return ConversationHandler.END
    conn = get_db()
    tenders = conn.execute(
        "SELECT t.id, tt.type_name, t.description, t.due_date, t.status, t.user, t.institution, t.envelope_type FROM tenders t JOIN tender_types tt ON t.tender_type_id = tt.id ORDER BY t.due_date ASC LIMIT 5"
    ).fetchall()
    conn.close()
    if not tenders:
        await update.message.reply_text("No tenders found.")
        return ConversationHandler.END
    message = "Tenders List:\n"
    for tender in tenders:
        message += f"ID: {tender['id']}, Type: {tender['type_name']}, Due: {tender['due_date']}, Status: {tender['status']}\n"
    await update.message.reply_text(message)
    return ConversationHandler.END


async def tenders_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if "tenders_report" not in context.user_data["permissions"]:
        await update.message.reply_text(
            "Access denied. Missing tenders_report permission."
        )
        return ConversationHandler.END
    conn = get_db()
    tenders = conn.execute(
        "SELECT t.id, tt.type_name, t.description, t.due_date, t.status, t.user, t.institution, t.envelope_type FROM tenders t JOIN tender_types tt ON t.tender_type_id = tt.id ORDER BY t.due_date ASC LIMIT 5"
    ).fetchall()
    conn.close()
    if not tenders:
        await update.message.reply_text("No tenders found.")
        return ConversationHandler.END
    message = "Tenders Report:\n"
    for tender in tenders:
        message += f"ID: {tender['id']}, Type: {tender['type_name']}, Due: {tender['due_date']}, Status: {tender['status']}\n"
    await update.message.reply_text(message)
    return ConversationHandler.END


async def marketing_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if "marketing_report" not in context.user_data["permissions"]:
        await update.message.reply_text(
            "Access denied. Missing marketing_report permission."
        )
        return ConversationHandler.END
    conn = get_db()
    reports = conn.execute(
        "SELECT institution, visit_date, outcome, visit_type FROM reports ORDER BY visit_date DESC LIMIT 5"
    ).fetchall()
    conn.close()
    if not reports:
        await update.message.reply_text("No reports found.")
        return ConversationHandler.END
    message = "Marketing Report:\n"
    for report in reports:
        message += f"Institution: {report['institution']}, Date: {report['visit_date']}, Outcome: {report['outcome']}, Type: {report['visit_type']}\n"
    await update.message.reply_text(message)
    return ConversationHandler.END


async def place_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if "put_order" not in context.user_data["permissions"]:
        await update.message.reply_text("Access denied. Missing put_order permission.")
        return ConversationHandler.END
    conn = get_db()
    items = conn.execute("SELECT id, item_code FROM inventory").fetchall()
    conn.close()
    if not items:
        await update.message.reply_text("No items available in inventory.")
        return ConversationHandler.END
    keyboard = [
        [KeyboardButton(item["item_code"]) for item in items[i : i + 2]]
        for i in range(0, len(items), 2)
    ]
    reply_markup = ReplyKeyboardMarkup(
        keyboard, resize_keyboard=True, one_time_keyboard=True
    )
    await update.message.reply_text("Select item to order:", reply_markup=reply_markup)
    return BotState.ORDER_ITEM


async def get_order_item(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    conn = get_db()
    context.user_data["item_id"] = conn.execute(
        text("SELECT id FROM inventory WHERE item_code = :code"),
        {"code": update.message.text},
    ).fetchone()["id"]
    conn.close()
    await update.message.reply_text("Enter quantity:")
    return BotState.ORDER_QTY


async def get_order_qty(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data["quantity"] = int(update.message.text)
    except ValueError:
        await update.message.reply_text("Please enter a valid number for quantity.")
        return BotState.ORDER_QTY
    await update.message.reply_text("Enter customer name:")
    return BotState.ORDER_CUST


async def get_order_cust(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["customer"] = update.message.text
    keyboard = [[KeyboardButton("Yes"), KeyboardButton("No")]]
    reply_markup = ReplyKeyboardMarkup(
        keyboard, resize_keyboard=True, one_time_keyboard=True
    )
    await update.message.reply_text(
        "Is this order VAT exempt? (Yes/No):", reply_markup=reply_markup
    )
    return BotState.ORDER_VAT_EXEMPT


async def get_order_vat_exempt(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    context.user_data["vat_exempt"] = update.message.text.lower() == "yes"
    conn = get_db()
    sales_rep = context.user_data["tin"]
    conn.execute(
        text(
            """
            INSERT INTO orders (item_id, quantity, customer, sales_rep, vat_exempt)
            VALUES (:item_id, :quantity, :customer, :sales_rep, :vat_exempt)
            """
        ),
        {
            "item_id": context.user_data["item_id"],
            "quantity": context.user_data["quantity"],
            "customer": context.user_data["customer"],
            "sales_rep": sales_rep,
            "vat_exempt": context.user_data["vat_exempt"],
        },
    )
    conn.commit()
    await update.message.reply_text("Order placed successfully, pending approval.")
    conn.close()
    return ConversationHandler.END


async def my_approved_orders(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if "my_approved_orders" not in context.user_data["permissions"]:
        await update.message.reply_text(
            "Access denied. Missing my_approved_orders permission."
        )
        return ConversationHandler.END
    conn = get_db()
    sales_rep = context.user_data["tin"]
    cur = conn.cursor()
    safe_execute(
        cur,
        "SELECT * FROM orders WHERE sales_rep = ? AND status = ? ORDER BY id DESC LIMIT 5",
        (sales_rep, "approved"),
    )
    orders = cur.fetchall()
    conn.close()
    if not orders:
        await update.message.reply_text("No approved orders found.")
        return ConversationHandler.END
    message = "My Approved Orders:\n"
    for order in orders:
        message += f"ID: {order['id']}, Item ID: {order['item_id']}, Qty: {order['quantity']}, Status: {order['status']}\n"
    await update.message.reply_text(message)
    return ConversationHandler.END


async def order_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if "order_status" not in context.user_data["permissions"]:
        await update.message.reply_text(
            "Access denied. Missing order_status permission."
        )
        return ConversationHandler.END
    conn = get_db()
    sales_rep = context.user_data["tin"]
    orders = conn.execute(
        text(
            "SELECT * FROM orders WHERE sales_rep = :sales_rep ORDER BY id DESC LIMIT 5"
        ),
        {"sales_rep": sales_rep},
    ).fetchall()
    conn.close()
    if not orders:
        await update.message.reply_text("No orders found.")
        return ConversationHandler.END
    message = "Order Status:\n"
    for order in orders:
        message += f"ID: {order['id']}, Item ID: {order['item_id']}, Qty: {order['quantity']}, Status: {order['status']}, Delivery Status: {order['delivery_status']}\n"
    await update.message.reply_text(message)
    return ConversationHandler.END


async def maintenance_request(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    if "maintenance_request" not in context.user_data["permissions"]:
        await update.message.reply_text(
            "Access denied. Missing maintenance_request permission."
        )
        return ConversationHandler.END
    await update.message.reply_text("Enter equipment ID:")
    return BotState.MAINTENANCE_EQUIP


async def get_maintenance_equip(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    try:
        context.user_data["equipment_id"] = int(update.message.text)
    except ValueError:
        await update.message.reply_text("Please enter a valid number for equipment ID.")
        return BotState.MAINTENANCE_EQUIP
    await update.message.reply_text("Enter maintenance type:")
    return BotState.MAINTENANCE_TYPE


async def get_maintenance_type(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    context.user_data["type"] = update.message.text
    conn = get_db()
    user = context.user_data["tin"]
    conn.execute(
        text(
            """
            INSERT INTO maintenance (equipment_id, request_date, type, status, user)
            VALUES (:equipment_id, :request_date, :type, :status, :user)
            """
        ),
        {
            "equipment_id": context.user_data["equipment_id"],
            "request_date": datetime.now(),
            "type": context.user_data["type"],
            "status": "pending",
            "user": user,
        },
    )
    conn.commit()
    await update.message.reply_text("Maintenance request submitted.")
    conn.close()
    return ConversationHandler.END


async def maintenance_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if "maintenance_status" not in context.user_data["permissions"]:
        await update.message.reply_text(
            "Access denied. Missing maintenance_status permission."
        )
        return ConversationHandler.END
    conn = get_db()
    user = context.user_data["tin"]
    maintenance = conn.execute(
        text(
            "SELECT * FROM maintenance WHERE user = :user ORDER BY request_date DESC LIMIT 5"
        ),
        {"user": user},
    ).fetchall()
    conn.close()
    if not maintenance:
        await update.message.reply_text("No maintenance requests found.")
        return ConversationHandler.END
    message = "Maintenance Status:\n"
    for maint in maintenance:
        message += f"ID: {maint['id']}, Equip ID: {maint['equipment_id']}, Type: {maint['type']}, Status: {maint['status']}\n"
    await update.message.reply_text(message)
    return ConversationHandler.END


async def maintenance_followup(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    if "maintenance_followup" not in context.user_data["permissions"]:
        await update.message.reply_text(
            "Access denied. Missing maintenance_followup permission."
        )
        return ConversationHandler.END
    conn = get_db()
    cur = conn.cursor()
    safe_execute(
        cur, "SELECT * FROM maintenance WHERE status = ? LIMIT 5", ("pending",)
    )
    maintenance = cur.fetchall()
    conn.close()
    if not maintenance:
        await update.message.reply_text("No pending maintenance requests.")
        return ConversationHandler.END
    keyboard = [
        [KeyboardButton(str(m["id"])) for m in maintenance[i : i + 2]]
        for i in range(0, len(maintenance), 2)
    ]
    reply_markup = ReplyKeyboardMarkup(
        keyboard, resize_keyboard=True, one_time_keyboard=True
    )
    await update.message.reply_text(
        "Select maintenance ID to follow up:", reply_markup=reply_markup
    )
    return BotState.MAINTENANCE_ID


async def get_maintenance_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data["maintenance_id"] = int(update.message.text)
    except ValueError:
        await update.message.reply_text("Please enter a valid maintenance ID.")
        return BotState.MAINTENANCE_ID
    await update.message.reply_text("Enter report details:")
    return BotState.MAINTENANCE_REPORT


async def get_maintenance_report(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    context.user_data["report"] = update.message.text
    conn = get_db()
    user_val = (
        context.user_data["username"]
        if context.user_data["tin"] is None
        else context.user_data["tin"]
    )
    cur = conn.cursor()
    safe_execute(
        cur,
        "UPDATE maintenance SET status = ?, report = ?, user = ? WHERE id = ?",
        (
            "completed",
            context.user_data["report"],
            user_val,
            context.user_data["maintenance_id"],
        ),
    )
    conn.commit()
    await update.message.reply_text("Maintenance followed up successfully.")
    conn.close()
    return ConversationHandler.END


async def view_orders(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if "view_orders" not in context.user_data["permissions"]:
        await update.message.reply_text(
            "Access denied. Missing view_orders permission."
        )
        return ConversationHandler.END
    conn = get_db()
    if context.user_data["tin"] is None:  # Management
        orders = conn.execute(
            text("SELECT * FROM orders ORDER BY id DESC LIMIT 10")
        ).fetchall()
    else:
        orders = conn.execute(
            text(
                "SELECT * FROM orders WHERE sales_rep = :sales_rep ORDER BY id DESC LIMIT 10"
            ),
            {"sales_rep": context.user_data["tin"]},
        ).fetchall()
    conn.close()
    if not orders:
        await update.message.reply_text("No orders found.")
        return ConversationHandler.END
    message = "Orders:\n"
    for order in orders:
        message += f"ID: {order['id']}, Item ID: {order['item_id']}, Qty: {order['quantity']}, Status: {order['status']}\n"
    await update.message.reply_text(message)
    return ConversationHandler.END


async def maintenance_view(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if "maintenance_report" not in context.user_data["permissions"]:
        await update.message.reply_text(
            "Access denied. Missing maintenance_report permission."
        )
        return ConversationHandler.END
    conn = get_db()
    maintenance = conn.execute(
        "SELECT * FROM maintenance ORDER BY request_date DESC LIMIT 10"
    ).fetchall()
    conn.close()
    if not maintenance:
        await update.message.reply_text("No maintenance requests found.")
        return ConversationHandler.END
    message = "Maintenance Requests:\n"
    for maint in maintenance:
        message += f"ID: {maint['id']}, Equip ID: {maint['equipment_id']}, Type: {maint['type']}, Status: {maint['status']}\n"
    await update.message.reply_text(message)
    return ConversationHandler.END


def main() -> None:
    application = (
        Application.builder()
        .token(TOKEN)
        .defaults(Defaults(parse_mode=ParseMode.HTML))
        .proxy_url("socks5://123.141.181.7:5031")
        .build()  # Replace with a valid proxy
    )

    employee_login_conv = ConversationHandler(
        entry_points=[CommandHandler("employee_login", employee_login)],
        states={
            BotState.EMPLOYEE_LOGIN_USERNAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_employee_username)
            ],
            BotState.EMPLOYEE_LOGIN_PASSWORD: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_employee_password)
            ],
        },
        fallbacks=[],
        per_message=True,  # Added to fix PTBUserWarning
    )

    client_login_conv = ConversationHandler(
        entry_points=[CommandHandler("client_login", client_login)],
        states={
            BotState.CLIENT_LOGIN_EMAIL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_client_email)
            ],
            BotState.CLIENT_LOGIN_PASSWORD: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_client_password)
            ],
        },
        fallbacks=[],
        per_message=True,
    )

    client_reg_conv = ConversationHandler(
        entry_points=[CommandHandler("client_registration", client_registration)],
        states={
            BotState.CLIENT_REG_TIN: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_client_reg_tin)
            ],
            BotState.CLIENT_REG_INST: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_client_reg_inst)
            ],
            BotState.CLIENT_REG_ADDR: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_client_reg_addr)
            ],
            BotState.CLIENT_REG_PHONE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_client_reg_phone)
            ],
            BotState.CLIENT_REG_REGION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_client_reg_region)
            ],
            BotState.CLIENT_REG_CITY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_client_reg_city)
            ],
            BotState.CLIENT_REG_EMAIL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_client_reg_email)
            ],
            BotState.CLIENT_REG_PASS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_client_reg_pass)
            ],
        },
        fallbacks=[],
        per_message=True,
    )

    employee_reg_conv = ConversationHandler(
        entry_points=[CommandHandler("employee_registration", employee_registration)],
        states={
            BotState.EMPLOYEE_REG_USERNAME: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, get_employee_reg_username
                )
            ],
            BotState.EMPLOYEE_REG_PASSWORD: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, get_employee_reg_password
                )
            ],
            BotState.EMPLOYEE_REG_PERMISSIONS: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, get_employee_reg_permissions
                )
            ],
            BotState.EMPLOYEE_REG_POSITION: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, get_employee_reg_position
                )
            ],
            BotState.EMPLOYEE_REG_HIRE_DATE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, get_employee_reg_hire_date
                )
            ],
            BotState.EMPLOYEE_REG_SALARY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_employee_reg_salary)
            ],
        },
        fallbacks=[],
        per_message=True,
    )

    report_conv = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^Add Report$") & ~filters.COMMAND, add_report)
        ],
        states={
            BotState.INSTITUTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_institution)
            ],
            BotState.LOCATION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_location)
            ],
            BotState.PHONE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)
            ],
            BotState.VISIT_DATE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_visit_date)
            ],
            BotState.INTERESTED_PRODUCTS: [CallbackQueryHandler(button)],
            BotState.OUTCOME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_outcome)
            ],
            BotState.SALE_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_sale_amount)
            ],
            BotState.VISIT_TYPE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_visit_type)
            ],
            BotState.FOLLOW_UP_DETAILS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_follow_up_details)
            ],
        },
        fallbacks=[],
        per_message=True,
    )

    inventory_conv = ConversationHandler(
        entry_points=[
            MessageHandler(
                filters.Regex("^Add Inventory$") & ~filters.COMMAND, add_inventory
            )
        ],
        states={
            BotState.ADD_INVENTORY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_inventory_desc)
            ],
            BotState.INVENTORY_DESC: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_inventory_desc)
            ],
            BotState.INVENTORY_PACK: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_inventory_pack)
            ],
            BotState.INVENTORY_BRAND: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_inventory_brand)
            ],
            BotState.INVENTORY_TYPE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_inventory_type)
            ],
            BotState.INVENTORY_EXP: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_inventory_exp)
            ],
            BotState.INVENTORY_CAT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_inventory_cat)
            ],
        },
        fallbacks=[],
        per_message=True,
    )

    receive_conv = ConversationHandler(
        entry_points=[
            MessageHandler(
                filters.Regex("^Receive Inventory$") & ~filters.COMMAND,
                receive_inventory,
            )
        ],
        states={
            BotState.RECEIVE_INVENTORY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_receive_item)
            ],
            BotState.RECEIVE_ITEM: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_receive_item)
            ],
            BotState.RECEIVE_QTY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_receive_qty)
            ],
        },
        fallbacks=[],
        per_message=True,
    )

    out_conv = ConversationHandler(
        entry_points=[
            MessageHandler(
                filters.Regex("^Inventory Out$") & ~filters.COMMAND, inventory_out
            )
        ],
        states={
            BotState.INVENTORY_OUT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_out_item)
            ],
            BotState.OUT_ITEM: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_out_item)
            ],
            BotState.OUT_QTY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_out_qty)
            ],
            BotState.OUT_ACTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_out_action)
            ],
            BotState.OUT_SUBACTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_out_subaction)
            ],
        },
        fallbacks=[],
        per_message=True,
    )

    tender_conv = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^Add Tender$") & ~filters.COMMAND, add_tender)
        ],
        states={
            BotState.TENDER_TYPE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_tender_type)
            ],
            BotState.TENDER_DESC: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_tender_desc)
            ],
            BotState.TENDER_DUE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_tender_due)
            ],
            BotState.TENDER_INST: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_tender_inst)
            ],
            BotState.TENDER_ENVELOPE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_tender_envelope)
            ],
            BotState.TENDER_PRIVATE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_tender_private)
            ],
            BotState.TENDER_TECH: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_tender_tech)
            ],
            BotState.TENDER_FIN: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_tender_fin)
            ],
        },
        fallbacks=[],
        per_message=True,
    )

    order_conv = ConversationHandler(
        entry_points=[
            MessageHandler(
                filters.Regex("^Place Order$") & ~filters.COMMAND, place_order
            )
        ],
        states={
            BotState.ORDER_ITEM: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_order_item)
            ],
            BotState.ORDER_QTY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_order_qty)
            ],
            BotState.ORDER_CUST: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_order_cust)
            ],
            BotState.ORDER_VAT_EXEMPT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_order_vat_exempt)
            ],
        },
        fallbacks=[],
        per_message=True,
    )

    maintenance_request_conv = ConversationHandler(
        entry_points=[
            MessageHandler(
                filters.Regex("^Request Maintenance$") & ~filters.COMMAND,
                maintenance_request,
            )
        ],
        states={
            BotState.MAINTENANCE_EQUIP: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_maintenance_equip)
            ],
            BotState.MAINTENANCE_TYPE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_maintenance_type)
            ],
        },
        fallbacks=[],
        per_message=True,
    )

    maintenance_followup_conv = ConversationHandler(
        entry_points=[
            MessageHandler(
                filters.Regex("^View Maintenance$") & ~filters.COMMAND,
                maintenance_followup,
            )
        ],
        states={
            BotState.MAINTENANCE_ID: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_maintenance_id)
            ],
            BotState.MAINTENANCE_REPORT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_maintenance_report)
            ],
        },
        fallbacks=[],
        per_message=True,
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(employee_login_conv)
    application.add_handler(client_login_conv)
    application.add_handler(client_reg_conv)
    application.add_handler(employee_reg_conv)
    application.add_handler(report_conv)
    application.add_handler(inventory_conv)
    application.add_handler(receive_conv)
    application.add_handler(out_conv)
    application.add_handler(tender_conv)
    application.add_handler(order_conv)
    application.add_handler(maintenance_request_conv)
    application.add_handler(maintenance_followup_conv)
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    application.run_polling(
        timeout=120, allowed_updates=Update.ALL_TYPES
    )  # Increased timeout to 120 seconds


if __name__ == "__main__":
    main()
