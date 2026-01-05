from flask import Blueprint, request, jsonify
from utils.excel import load, save
from utils.workflow import after_manager

api = Blueprint("manager", __name__)
COLS=["رقم_الطلب","الحالة"]

@api.get("/pending/<dept>")
def pending(dept):
    df = load("requests")
    df = df[
        (df["القسم"] == dept) &
        (df["الحالة"] == "بانتظار مدير القسم")
    ]
    return jsonify(df.to_dict("records"))




@api.post("/approve")
def approve():
    data = request.get_json()
    num = data.get("رقم_الطلب")

    df = load("requests")
    df.loc[df["رقم_الطلب"] == str(num), "الحالة"] = "بانتظار المشتريات"
    save("requests", df)

    from utils.workflow import to_purchasing
    to_purchasing(num)

    return jsonify({"ok": True, "msg": f"✔️ تم اعتماد الطلب وتحويله للمشتريات"})




