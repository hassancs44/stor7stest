from flask import Blueprint, request, jsonify
from utils.excel import load, save
from utils.workflow import purchasing_action
from utils.excel import load, save, append
from datetime import datetime
from utils.id import generate_custody_id

api = Blueprint("purchasing", __name__)

@api.get("/approved")
def approved():
    df = load("requests")

    df = df[
        df["الحالة"].isin([
            "بانتظار المشتريات",
            "أعيد من IT"
        ])
    ]

    return jsonify(df.to_dict("records"))



@api.post("/issue")
def issue():
    data   = request.get_json()
    req_id = str(data.get("رقم_الطلب"))
    code   = data.get("كود","").strip()
    qty    = int(data.get("كمية", 1))

    # 1️⃣ تحقق أن الصنف موجود ضمن عناصر الطلب
    items = load("items")
    valid = items[
        (items["رقم_الطلب"].astype(str) == req_id) &
        (items["كود"].astype(str) == code)
    ]

    if valid.empty:
        return jsonify({
            "ok": False,
            "msg": "❌ لا يمكن الصرف، الصنف غير موجود ضمن عناصر الطلب"
        }), 400

    # 2️⃣ تحقق من توفر الكمية في المستودع
    wh = load("warehouse")
    row = wh[wh["كود"].astype(str) == code]

    if row.empty:
        return jsonify({"ok":False,"msg":"❌ الصنف غير موجود في المستودع"}), 404

    old_qty = int(row.iloc[0]["كمية_حالياً"])
    if old_qty < qty:
        return jsonify({"ok":False,"msg":"❌ الكمية غير كافية في المستودع"}), 400

    new_qty = old_qty - qty

    # 3️⃣ تحديث حالة الطلب
    # 🔹 جلب بيانات الطلب (لربط العهدة صح)
    reqs = load("requests")
    req = reqs[reqs["رقم_الطلب"] == req_id].iloc[0]

    custody_id = generate_custody_id()

    append("custody", [
        custody_id,
        req_id,
        code,
        valid.iloc[0]["اسم"],
        "صرف من المستودع",
        "",
        req["الرافع"],
        req["القسم"],
        qty,
        datetime.now().strftime("%Y-%m-%d"),
        "",
        "نشطة",
        "",
        valid.iloc[0]["اسم"]
    ])

    # 5️⃣ تسجيل العهدة
    from utils.id import generate_custody_id


    # 6️⃣ تسجيل حركة المستودع (قبل / بعد)
    append("logs", [
        req_id,
        "صرف من المستودع",
        "المشتريات",
        "تنفيذ",
        datetime.now().date(),
        datetime.now().time(),
        f"الصنف {code} | قبل: {old_qty} | بعد: {new_qty} | كمية: {qty}"
    ])

    return jsonify({"ok":True,"msg":"✔️ تم الصرف وتحديث المخزون بنجاح"})

@api.post("/buy")  # 🧾 تسجيل شراء + بيانات مورد + فاتورة + Log
def buy():
    data   = request.get_json()
    req_id = str(data.get("رقم_الطلب"))
    vendor = data.get("المورد","غير محدد")
    price  = data.get("السعر","0")
    invoice= data.get("الفاتورة","-")

    # تحديث حالة الطلب
    df = load("requests")
    df.loc[df["رقم_الطلب"] == req_id, "الحالة"] = "تم الشراء - بانتظار الاستلام"
    save("requests", df)

    # سجل شراء
    append("purchase",[
        req_id, vendor, price, invoice, datetime.now().date(), "قيد التنفيذ"
    ])

    # Log
    append("logs",[
        req_id, "عملية شراء", "المشتريات", "تنفيذ",
        datetime.now().date(), datetime.now().time(), vendor
    ])

    return jsonify({"ok":True,"msg":"🧾 تم تسجيل عملية الشراء بنجاح"})



@api.post("/it")
def it_forward():
    data   = request.get_json()
    req_id = str(data.get("رقم_الطلب"))

    df = load("requests")
    df.loc[df["رقم_الطلب"] == req_id, "الحالة"] = "محول لقسم IT"
    save("requests", df)

    append("logs", [
        req_id,
        "تحويل إلى تقنية المعلومات",
        "المشتريات",
        "تحويل",
        datetime.now().date(),
        datetime.now().time(),
        "بانتظار التقييم الفني"
    ])

    return jsonify({"ok": True, "msg": "💻 تم تحويل الطلب إلى تقنية المعلومات"})

# =============================
# 🟦 API | المستودع الكامل
# =============================

@api.get("/warehouse")
def warehouse_list():
    wh = load("warehouse")
    return jsonify(wh.to_dict("records"))

@api.post("/warehouse/add")
def warehouse_add():
    data = request.get_json()

    required = ["كود","اسم"]
    for f in required:
        if not data.get(f,"").strip():
            return jsonify({"ok":False,"msg":"⚠️ يجب إدخال الكود والاسم"}), 400

    wh = load("warehouse")

    if data["كود"] in wh["كود"].astype(str).values:
        return jsonify({"ok":False,"msg":"❌ الكود موجود مسبقاً"}), 409

    append("warehouse",[
        data.get("كود"),
        data.get("اسم"),
        data.get("فئة"),
        data.get("كمية_حالياً"),
        data.get("حد_إعادة_الطلب"),
        data.get("الموقع"),
        data.get("الحالة")
    ])

    return jsonify({"ok":True,"msg":"✔️ تم حفظ الصنف في المستودع بنجاح"})


@api.post("/warehouse/update")
def warehouse_update():
    data = request.get_json()
    code = data.get("كود","")
    qty  = int(data.get("كمية",0))

    wh = load("warehouse")
    if code not in wh["كود"].astype(str).values:
        return jsonify({"ok":False,"msg":"❌ الصنف غير موجود"}), 404

    wh.loc[wh["كود"] == code, "كمية_حالياً"] = qty
    save("warehouse", wh)

    return jsonify({"ok":True,"msg":"✔️ تم التحديث بنجاح"})

@api.get("/it-report/<req_id>")
def it_report(req_id):
    df = load("it_reports")
    r = df[df["رقم_الطلب"] == str(req_id)]
    return jsonify(r.to_dict("records"))


@api.get("/items/<req_id>")
def request_items(req_id):
    df = load("items")
    items = df[df["رقم_الطلب"].astype(str) == str(req_id)]
    return jsonify(items.to_dict("records"))

