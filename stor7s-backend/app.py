import sys, os
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from flask import Flask, send_from_directory, request, jsonify
from flask_cors import CORS
from utils.excel import ensure_files, load, save
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__, static_folder=".", static_url_path="")
CORS(app)

# 📄 إنشاء + إصلاح ملفات Excel
ensure_files()

# ==============================
#  🏠 صفحة البداية
# ==============================
@app.route("/")
def home():
    return send_from_directory(".", "login.html")

@app.route("/<page>")
def pages(page):
    return send_from_directory(".", page)


# ===========📌 مسار مرفقات ثابت 100% ===========
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

@app.route("/uploads/<path:filename>")
def uploaded_files(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


# ==============================
# 🔐 تسجيل الدخول
# ==============================
@app.post("/api/login")
def login_check():
    data = request.get_json()
    name = data.get("name","").strip()
    df = load("users").fillna("")

    if "اسم_المستخدم" not in df.columns:
        return jsonify({"ok": False, "msg": "❌ ملف المستخدمين لا يحتوي على عمود اسم_المستخدم"}), 400

    user = df[df["اسم_المستخدم"].str.strip() == name]
    if user.empty:
        return jsonify({"ok": False, "msg": "❌ المستخدم غير موجود"}), 404

    row = user.iloc[0]
    page_map = {
        "موظف": "employee.html",
        "مدير القسم": "manager.html",
        "المشتريات": "purchasing.html",
        "تقنية المعلومات": "it.html",
        "الموارد البشرية": "hr.html",
        "المالية": "finance.html",
        "الإدارة العامة": "admin.html"
    }

    return jsonify({
        "ok": True,
        "user": {
            "name": row["اسم_المستخدم"],
            "role": row["الدور"],
            "department": row["القسم"],
            "company": row["الشركة"],
            "branch": row["الفرع"]
        },
        "page": page_map.get(row["الدور"], "login.html")
    })

# ==============================
# 📡 تسجيل مسارات البلوبرنت
# ==============================
from modules.employee import api as employee_api
from modules.manager import api as manager_api
from modules.purchasing import api as purchasing_api
from modules.it import api as it_api
from modules.hr import api as hr_api
from modules.finance import api as finance_api
from modules.admin import api as admin_api

app.register_blueprint(employee_api, url_prefix="/api/employee")
app.register_blueprint(manager_api, url_prefix="/api/manager")
app.register_blueprint(purchasing_api, url_prefix="/api/purchasing")
app.register_blueprint(it_api, url_prefix="/api/it")
app.register_blueprint(hr_api, url_prefix="/api/hr")
app.register_blueprint(finance_api, url_prefix="/api/finance")
app.register_blueprint(admin_api, url_prefix="/api/admin")

if __name__ == "__main__":
    print("🚀 STOR7S Backend Running: http://127.0.0.1:5000")
    app.run(debug=True, host="0.0.0.0", port=5000, use_reloader=False)
