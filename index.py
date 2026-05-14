from flask import Flask, render_template, request
from datetime import datetime
import os
import json
import firebase_admin
from firebase_admin import credentials, firestore

# 判斷是在 Vercel 還是本地
if not firebase_admin._apps:  # 加入檢查避免重複啟動
    if os.path.exists('serviceAccountKey.json'):
        cred = credentials.Certificate('serviceAccountKey.json')
    else:
        firebase_config = os.getenv('FIREBASE_CONFIG')
        if firebase_config:
            cred_dict = json.loads(firebase_config)
            cred = credentials.Certificate(cred_dict)
        else:
            raise ValueError("找不到 Firebase 設定！")
    firebase_admin.initialize_app(cred)

db = firestore.client()
app = Flask(__name__)

@app.route("/")
def index():
    link = "<h1>歡迎進入林彣媞的網站20260409</h1>"
    link += "<a href=/mis>課程</a><hr>"
    link += "<a href=/today>現在日期時間</a><hr>"
    link += "<a href=/me>關於我</a><hr>"
    link += "<a href=/welcome?u=411312537&d=靜宜資管&c=資訊管理導論>Get傳值</a><hr>"
    link += "<a href=/account>POST傳值</a><hr>"
    link += "<a href=/math>數學運算(次方/根號)</a><hr>"
    link += "<br><a href=/read>讀取Firestore資料</a><br>"
    link += "<br><a href=/read2>讀取Firestore資料(根據姓名關鍵字'楊')</a><br>"
    link += "<br><a href=/search>搜尋老師資料(輸入姓名)</a><br>"
    link += "<br><a href=/spider>執行爬蟲：抓取老師課程連結</a><br>"
    return link


@app.route("/spider")
def spider():
    import requests
    from bs4 import BeautifulSoup

    url = "https://www1.pu.edu.tw/~tcyang/course.html"
    try:
        Data = requests.get(url)
        Data.encoding = "utf-8"
        sp = BeautifulSoup(Data.text, "html.parser")
        result = sp.select(".team-box a")
        
        # 建立簡單的 HTML 表格顯示結果
        info = "<h2>爬蟲結果：靜宜老師課程資料</h2>"
        info += "<table border='1' cellpadding='5' style='border-collapse: collapse;'>"
        info += "<tr><th>老師姓名</th><th>課程連結</th></tr>"
        
        for i in result:
            name = i.text.strip()
            href = i.get("href")
            # 處理相對連結，補足完整網址
            if href.startswith("http"):
                full_url = href
            else:
                full_url = "https://www1.pu.edu.tw/~tcyang/" + href
            
            info += f"<tr><td>{name}</td><td><a href='{full_url}' target='_blank'>{full_url}</a></td></tr>"
        
        info += "</table>"
    except Exception as e:
        info = f"抓取資料時發生錯誤：{e}"
    
    return info + "<br><br><a href='/'>返回首頁</a>"





@app.route("/search", methods=["GET", "POST"])
def search():
    if request.method == "POST":
        keyword = request.form.get("keyword")
        Result = f"<h3>關鍵字「{keyword}」的查詢結果：</h3><hr>"
        
        collection_ref = db.collection("靜宜資管")
        docs = collection_ref.get()
        
        found = False
        for doc in docs:
            teacher = doc.to_dict()
            # 確保 'name' 鍵值存在且包含關鍵字
            if "name" in teacher and keyword in teacher["name"]:
                found = True
                Result += f"姓名：{teacher.get('name')}<br>"
                Result += f"研究室：{teacher.get('lab')}<br>"
                Result += f"郵件：{teacher.get('mail')}<br><hr>"
        
        if not found:
            Result = f"<h3>抱歉，查無關於「{keyword}」的資料。</h3>"
            
        return Result + "<br><a href='/search'>重新搜尋</a> | <a href='/'>返回首頁</a>"
    else:
        # 如果是 GET 請求，則顯示輸入表單
        return render_template("search.html")


@app.route("/read2")
def read2():
    Result = ""
    keyword = "楊"
    collection_ref = db.collection("靜宜資管")
    docs = collection_ref.get()
    for doc in docs:        
        teacher = doc.to_dict()
        # 修正篩選邏輯：檢查姓名裡是否有關鍵字
        if "name" in teacher and keyword in teacher["name"]:
            Result += f"姓名：{teacher.get('name')}，研究室：{teacher.get('lab')}，郵件：{teacher.get('mail')}<br>"
   
    if Result == "":
        Result = "抱歉查無此關鍵字姓名之老師資料"
   
    return Result + "<br><a href=/>返回首頁</a>"

@app.route("/read")
def read():
    Result = ""
    db = firestore.client()
    collection_ref = db.collection("靜宜資管")    
    docs = collection_ref.get()    
   
    data_list = []
    for doc in docs:
        data_list.append(doc.to_dict())
   
    sorted_data = sorted(data_list, key=lambda x: x.get('lab', 0), reverse=True)
   
    for item in sorted_data:
        Result += str(item) + "<br>"
    return Result


@app.route("/mis")
def course():
    return "<h1>資訊管理導論</h1><a href=/>返回首頁</a>"

@app.route("/today")
def today():
    now = datetime.now()
    return render_template("today.html", datetime=str(now))

@app.route("/me")
def me():
    return render_template("mis2026b.html")

@app.route("/welcome", methods=["GET"])
def welcome():
    user = request.values.get("u")
    d = request.values.get("d")
    c = request.values.get("c")
    return render_template("welcome.html", name = user,dep = d,course=c)

@app.route("/account", methods=["GET", "POST"])
def account():
    if request.method == "POST":
        user = request.form["user"]
        pwd = request.form["pwd"]
        result = "您輸入的帳號是：" + user + "; 密碼為：" + pwd
        return result
    else:
        return render_template("account.html")

@app.route("/math", methods=["GET", "POST"])
def math_calc():
    if request.method == "POST":
        try:
            x = float(request.form["x"])
            y = float(request.form["y"])
            opt = request.form["opt"]
            if opt == "∧":
                result = x ** y
            elif opt == "√":
                result = "錯誤：數學上不能開 0 次方根" if y == 0 else x ** (1/y)
            return f"<h1>計算結果：{result}</h1><a href='/math'>重新計算</a> | <a href='/'>回首頁</a>"
        except Exception as e:
            return f"發生錯誤：{e} <br><a href='/math'>返回</a>"
    else:
        return render_template("math.html")

if __name__ == "__main__":
    app.run(debug=True)