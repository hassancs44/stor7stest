from flask import Blueprint, jsonify, request

from utils.excel import load

api = Blueprint("finance", __name__)

@api.get("/executed")
def executed():
    df = load("requests")
    df = df[df["الحالة"].str.contains("تم")]
    return jsonify(df.to_dict("records"))

@api.get("/purchases")
def purchases():
    purchases = load("purchase")
    requests  = load("requests")

    # ربط الشراء بالطلب
    merged = purchases.merge(
        requests,
        on="رقم_الطلب",
        how="left"
    )

    return jsonify(merged.to_dict("records"))

@api.get("/attachments/<req_id>")
def attachments(req_id):
    df = load("attachments")
    r = df[df["رقم_الطلب"] == str(req_id)]
    return jsonify(r.to_dict("records"))

from datetime import datetime
from utils.excel import append

@api.post("/create-request")
def create_request():
    data = request.get_json()

    req_id = str(int(datetime.now().timestamp()))
    desc   = data.get("الوصف","")
    company= data.get("الشركة","")
    branch = data.get("الفرع","")
    dept   = data.get("القسم","المالية")

    append("requests",[
        req_id,
        "المالية",
        "المالية",
        dept,
        company,
        branch,
        "طلب مالي",
        "بانتظار المشتريات",
        desc
    ])

    append("logs",[
        req_id,
        "إنشاء طلب مالي",
        "المالية",
        "إنشاء",
        datetime.now().date(),
        datetime.now().time(),
        "اعتماد تلقائي"
    ])

    return jsonify({
        "ok": True,
        "msg": "✔️ تم إنشاء الطلب وتحويله مباشرة للمشتريات",
        "رقم_الطلب": req_id
    })
