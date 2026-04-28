from flask import Flask, render_template, request
from datetime import datetime
import os
import json
import firebase_admin
from firebase_admin import credentials, firestore

# 判斷是在 Vercel 還是本地
if not firebase_admin._apps:
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
    link = "<h1>歡迎進入鍾若筠的網站20260409</h1>"
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
    link += "<br><a href=/movie1>爬取電影資訊 (具備搜尋功能)</a><br>"
    return link

@app.route("/movie1", methods=["GET", "POST"])
def movie1():
    import requests
    from bs4 import BeautifulSoup
    
    url = "https://www.atmovies.com.tw/movie/next/"
    try:
        Data = requests.get(url)
        Data.encoding = "utf-8"
        sp = BeautifulSoup(Data.text, "html.parser")
        result = sp.select(".filmListAllX li")
        
        # 獲取搜尋關鍵字
        keyword = request.form.get("movie_key", "").strip()
        
        info = "<h2>近期上映電影</h2>"
        
        # 加入搜尋表單
        info += f"""
            <form action="/movie1" method="post">
                <input type="text" name="movie_key" placeholder="輸入電影名稱關鍵字" value="{keyword}">
                <button type="submit">搜尋電影</button>
            </form><br>
        """
        
        info += "<table border='1' cellpadding='10' style='border-collapse: collapse;'>"
        info += "<tr><th>電影海報</th><th>電影名稱與介紹</th></tr>"
        
        found = False
        for item in result:
            img_tag = item.find("img")
            name = img_tag.get("alt") if img_tag else "未知電影"
            
            # 如果有輸入關鍵字，就進行篩選
            if keyword and keyword not in name:
                continue
                
            found = True
            img_url = img_tag.get("src") if img_tag else ""
            if img_url and not img_url.startswith("http"):
                img_url = "https://www.atmovies.com.tw" + img_url
            
            a_tag = item.find("a")
            href = a_tag.get("href") if a_tag else "#"
            full_link = "https://www.atmovies.com.tw" + href
            
            info += "<tr>"
            info += f"<td><img src='{img_url}' width='150'></td>"
            info += f"<td><a href='{full_link}' target='_blank' style='text-decoration:none; color:blue; font-size:18px; font-weight:bold;'>{name}</a></td>"
            info += "</tr>"
        
        if not found:
            info += f"<tr><td colspan='2'>找不到包含「{keyword}」的電影。</td></tr>"
            
        info += "</table>"
    except Exception as e:
        info = f"爬取電影資料時發生錯誤：{e}"

    return info + "<br><br><a href='/'>返回首頁</a>"

@app.route("/spider")
def spider():
    import requests
    from bs4 import BeautifulSoup
    import urllib3

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    url = "https://www1.pu.edu.tw/~tcyang/course.html"
    try:
        Data = requests.get(url, verify=False)
        Data.encoding = "utf-8"
        sp = BeautifulSoup(Data.text, "html.parser")
        result = sp.select(".team-box a")
        
        info = "<h2>爬蟲結果：靜宜老師課程資料</h2>"
        info += "<table border='1' cellpadding='5' style='border-collapse: collapse;'>"
        info += "<tr><th>老師姓名</th><th>課程連結</th></tr>"
        
        for i in result:
            name = i.text.strip()
            href = i.get("href")
            if href.startswith("http"):
                full_url = href
            else:
                href_clean = href.replace("./", "")
                full_url = "https://www1.pu.edu.tw/~tcyang/" + href_clean
            
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
            if "name" in teacher and keyword in teacher["name"]:
                found = True
                Result += f"姓名：{teacher.get('name')}<br>"
                Result += f"研究室：{teacher.get('lab')}<br>"
                Result += f"郵件：{teacher.get('mail')}<br><hr>"
        if not found:
            Result = f"<h3>抱歉，查無關於「{keyword}」的資料。</h3>"
        return Result + "<br><a href='/search'>重新搜尋</a> | <a href='/'>返回首頁</a>"
    else:
        return render_template("search.html")

@app.route("/read2")
def read2():
    Result = ""
    keyword = "楊"
    collection_ref = db.collection("靜宜資管")
    docs = collection_ref.get()
    for doc in docs:        
        teacher = doc.to_dict()
        if "name" in teacher and keyword in teacher["name"]:
            Result += f"姓名：{teacher.get('name')}，研究室：{teacher.get('lab')}，郵件：{teacher.get('mail')}<br>"
    if Result == "":
        Result = "抱歉查無此關鍵字姓名之老師資料"
    return Result + "<br><a href=/>返回首頁</a>"

@app.route("/read")
def read():
    collection_ref = db.collection("靜宜資管")    
    docs = collection_ref.get()
    items = []
    for doc in docs:
        data = doc.to_dict()
        content = f"文件內容：{data}<br>"
        if data.get('mail') == 'ruoyun269@gmail.com':
            items.insert(0, content)
        else:
            items.append(content)
    return "".join(items) + "<br><a href=/>返回首頁</a>"

@app.route("/mis")
def course():
    return "<h1>資訊管理導論</h1><a href=/>返回首頁</a>"

@app.route("/today")
def today():
    now = datetime.now()
    return render_template("today.html", datetime = str(now))

@app.route("/me")
def me():
    return render_template("mis2026b.html")

@app.route("/welcome", methods=["GET"])
def welcome():
    user = request.values.get("u")
    d = request.values.get("d")
    c = request.values.get("c")
    return render_template("welcome.html", name=user, dep=d, course=c)

@app.route("/account", methods=["GET", "POST"])
def account():
    if request.method == "POST":
        user = request.form["user"]
        pwd = request.form["pwd"]
        return f"您輸入的帳號是：{user}; 密碼為：{pwd} <br><a href='/'>返回首頁</a>"
    return render_template("account.html")

@app.route("/math", methods=["GET", "POST"])
def calculate():
    if request.method == "POST":
        try:
            x = float(request.form.get("x", 0))
            y = float(request.form.get("y", 0))
            op = request.form.get("op")
            if op == "pow":
                res = x ** y
                msg = f"{x} 的 {y} 次方為 {res}"
            else:
                res = x ** (1/y)
                msg = f"{x} 的 {y} 次方根為 {res}"
            return f"<h1>計算結果</h1><p>{msg}</p><a href='/math'>重新計算</a> | <a href='/'>返回首頁</a>"
        except Exception as e:
            return f"計算出錯：{str(e)}"
    return render_template("calculator.html")

if __name__ == "__main__":
    app.run(debug=True)