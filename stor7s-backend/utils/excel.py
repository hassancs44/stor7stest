import os
import pandas as pd
from config import DATA, EXCEL, COLUMNS


# ===== تحديد المسار =====
def file_path(key):
    return os.path.join(DATA, EXCEL[key])


# ===== تصحيح الملفات مرة واحدة فقط =====
def ensure_files():
    """✨ تصحيح Excel بدون حذف بيانات وبدون تكرار أعمدة نهائياً"""

    for key, fname in EXCEL.items():
        path = file_path(key)

        # إنشاء الملف إن لم يوجد
        if not os.path.exists(path):
            pd.DataFrame(columns=COLUMNS[key]).to_excel(path, index=False)
            print(f"📄 تم إنشاء ملف جديد: {fname}")
            continue

        # قراءة البيانات بدون تعديل على المحتوى
        df = pd.read_excel(path, dtype=str).fillna("")

        # إزالة الأعمدة المكررة
        df = df.loc[:, ~df.columns.duplicated()].copy()

        # ✨ معالجة اسم_المستخدم في users فقط
        if key == "users":
            rename_map = {
                "الاسم": "اسم_المستخدم",
                "اسم المستخدم": "اسم_المستخدم",
                "اسم المستخدم ": "اسم_المستخدم",
                "اسم_المستخدم ": "اسم_المستخدم",
                " اسم_المستخدم": "اسم_المستخدم"
            }
            df.rename(columns=rename_map, inplace=True)

        # ✨ تصحيح المرفقات فقط + إزالة المسار من اسم الملف
        if key == "attachments" and "اسم_الملف" in df.columns:
            df["اسم_الملف"] = df["اسم_الملف"].astype(str).apply(
                lambda x: os.path.basename(x) if x else ""
            )

        # إضافة أي عمود ناقص بدون حذف الموجود
        for col in COLUMNS[key]:
            if col not in df.columns:
                df[col] = ""

        # ترتيب الأعمدة
        base_cols = [c for c in COLUMNS[key] if c in df.columns]
        extra_cols = [c for c in df.columns if c not in base_cols]
        df = df[base_cols + extra_cols]

        # حفظ
        df.to_excel(path, index=False)
        print(f"✔️ تمت معالجة: {fname} بدون فقد بيانات أو تكرار")

    print("\n🎯 انتهى — لا أعمدة مكررة ولا مسح بيانات\n")


# ===== قراءة بدون لمس ensure_files (المشكلة كانت هنا) =====
def load(key):
    path = file_path(key)
    if not os.path.exists(path):
        pd.DataFrame(columns=COLUMNS[key]).to_excel(path, index=False)
    return pd.read_excel(path, dtype=str).fillna("")


# ===== حفظ مباشر =====
def save(key, df):
    df.to_excel(file_path(key), index=False)


# ===== إضافة صف بدون تخريب الجدول =====
def append(key, row, cols=None):
    df = load(key)

    # إضافة الأعمدة الناقصة فقط
    if cols:
        for c in cols:
            if c not in df.columns:
                df[c] = ""

    df.loc[len(df)] = row
    save(key, df)
    return True
