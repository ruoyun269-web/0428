import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template, request,make_response, jsonify
from datetime import datetime
import os
import json
import firebase_admin
from firebase_admin import credentials, firestore
import urllib3
import time  # <--- 確保這行一定要有！


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
    link = "<h1>歡迎進入鍾若筠的網站0514</h1>"
    link += "<a href=/mis>課程</a><hr>"
    link += "<a href=/today>現在日期時間</a><hr>"
    link += "<a href=/me>關於我</a><hr>"
    link += "<a href=/welcome?u=411312537&d=靜宜資管&c=資訊管理導論>Get傳值</a><hr>"
    link += "<a href=/account>POST傳值</a><hr>"
    link += "<a href=/math>數學運算(次方/根號)</a><hr>"
    link += "<br><a href=/read>讀取Firestore資料</a><br>"
    link += "<br><a href=/read2>讀取Firestore資料(根據姓名關鍵字'楊')</a><br>"
    link += "<br><a href='/search'>搜尋老師資料(輸入關鍵字)</a><br>"
    link += "<br><a href=/read2>讀取Firestore資料(根據姓名關鍵字'楊')</a><br>"
    link += "<br><a href='/search'>搜尋老師資料(輸入關鍵字)</a><br>"
    link += "<br><a href=/movie1>爬取電影資料 (即時爬取展示)</a><hr>"
    link += "<a href='/spiderMovie'>爬取並更新電影資料到資料庫</a><br>"
    link += "<br><a href='/searchMovie'>搜尋資料庫中的電影</a><hr>"
    link += "<br><a href='/road'>台中市十大肇事路口</a><br>"
    link += "<br><a href='/road1'>肇事路口查詢 (進階表單版)</a><br>"
    link += "<br><a href='/weather'>天氣預報查詢</a><hr>"
    link += "<br><a href='/rate'>本週新片DB</a><br>"
    link += "<br><a href='/webdamo'>聊天機器人</a><br>"
    return link


@app.route("/webdamo")
def webdamo():
    return render_template("webdamo.html")





@app.route("/webhook", methods=["POST"])
def webhook():
    req = request.get_json(force=True)
    action = req["queryResult"]["action"]
   
    if action == "rateChoice":
        rate = req["queryResult"]["parameters"]["rate"]
       
        db = firestore.client()
        collection_ref = db.collection("本週新片含分級")
        docs = collection_ref.where("rate", "==", rate).get()
       
        res = f"我是鍾若筠設計的機器人，找出的本週 {rate} 電影有：\n"
        found = False
        for doc in docs:
            found = True
            m = doc.to_dict()
            res += f"- {m.get('title')} (片長：{m.get('showLength')} 分)\n"
       
        if not found:
            res = f"抱歉，本週資料庫中沒有標記為 {rate} 的電影喔！"
           
        return make_response(jsonify({"fulfillmentText": res}))

    return make_response(jsonify({"fulfillmentText": "Webhook 運作正常，但未觸發特定動作。"}))




@app.route("/rate")
def rate():
    #本週新片
    url = "https://www.atmovies.com.tw/movie/new/"
    Data = requests.get(url)
    Data.encoding = "utf-8"
    sp = BeautifulSoup(Data.text, "html.parser")
    lastUpdate = sp.find(class_="smaller09").text[5:]
    print(lastUpdate)
    print()

    result=sp.select(".filmList")

    for x in result:
        title = x.find("a").text
        introduce = x.find("p").text

        movie_id = x.find("a").get("href").replace("/", "").replace("movie", "")
        hyperlink = "http://www.atmovies.com.tw/movie/" + movie_id
        picture = "https://www.atmovies.com.tw/photo101/" + movie_id + "/pm_" + movie_id + ".jpg"

        r = x.find(class_="runtime").find("img")
        rate = ""
        if r != None:
            rr = r.get("src").replace("/images/cer_", "").replace(".gif", "")
            if rr == "G":
                rate = "普遍級"
            elif rr == "P":
                rate = "保護級"
            elif rr == "F2":
                rate = "輔12級"
            elif rr == "F5":
                rate = "輔15級"
            else:
                rate = "限制級"

        t = x.find(class_="runtime").text

        t1 = t.find("片長")
        t2 = t.find("分")
        showLength = t[t1+3:t2]

        t1 = t.find("上映日期")
        t2 = t.find("上映廳數")
        showDate = t[t1+5:t2-8]

        doc = {
            "title": title,
            "introduce": introduce,
            "picture": picture,
            "hyperlink": hyperlink,
            "showDate": showDate,
            "showLength": int(showLength),
            "rate": rate,
            "lastUpdate": lastUpdate
        }

        db = firestore.client()
        doc_ref = db.collection("本週新片含分級").document(movie_id)
        doc_ref.set(doc)
    return "本週新片已爬蟲及存檔完畢，網站最近更新日期為：" + lastUpdate





@app.route("/weather", methods=["GET", "POST"])
def weather():
    result = ""
    city = request.values.get("city", "臺中市")
    city = city.replace("台", "臺")
   
    if request.method == "POST" or request.values.get("city"):
        token = "rdec-key-123-45678-011121314" # 請確保 token 正確
        url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001?Authorization={token}&format=JSON&locationName={city}"
       
        try:
            data = requests.get(url, timeout=10)
            json_data = data.json()
            loc_data = json_data["records"]["location"][0]
            weather_state = loc_data["weatherElement"][0]["time"][0]["parameter"]["parameterName"]
            rain_rate = loc_data["weatherElement"][1]["time"][0]["parameter"]["parameterName"]
            result = f"<h3>{city} 目前天氣：{weather_state}，降雨機率：{rain_rate}%</h3>"
        except:
            result = "<p style='color:red;'>查無此縣市資料或 API Token 失效。</p>"

    html = f"""
    <h2>縣市天氣查詢</h2>
    <form action="/weather" method="get">
        請輸入縣市名稱：<input type="text" name="city" placeholder="例如：臺中市">
        <button type="submit">查詢</button>
    </form>
    {result}
    <br><a href="/">返回首頁</a>
    """
    return html


@app.route("/road", methods=["GET", "POST"])
def road():
    # 加上你的名字
    R = "<h1>十大肇事路口(113年10月)鍾若筠</h1><br>"
    url = "https://datacenter.taichung.gov.tw/swagger/OpenData/a1b899c0-511f-4e3d-b22b-814982a97e41"
    headers = {'User-Agent': 'Mozilla/5.0'}
   
    try:
        # verify=False 解決憑證問題, timeout=10 防止卡死
        response = requests.get(url, headers=headers, verify=False, timeout=10)
        JsonData = response.json()
       
        # 取得網址參數 q
        Road_query = request.args.get("q", "")
        found = False
       
        for item in JsonData:
            if Road_query and Road_query in item.get("路口名稱", ""):
                R += f"📍 <b>{item['路口名稱']}</b>，原因：{item['主要肇因']} <br>"
                found = True
       
        if not found:
            if Road_query == "":
                R += "<i>請在網址後加上 ?q=路名 來搜尋，或查看下方前 10 筆列表：</i><br><br>"
                for item in JsonData[:10]:
                    R += f"• {item['路口名稱']} <br>"
            else:
                R += f"抱歉，查無關於「{Road_query}」的相關資料！<br>"
    except Exception as e:
        R += f"<div style='color:red;'>連線錯誤：{str(e)}</div>"

    R += "<br><hr><a href='/'>回首頁</a>"
    return R

# --- (2) 肇事路口：進階表單版 (表格美化) ---
@app.route("/road1", methods=["GET", "POST"])
def road1():
    # 使用 request.values 可以同時接收 GET 和 POST 的 q
    q = request.values.get("q", "")
    results = ""
   
    if q:
        url = "https://datacenter.taichung.gov.tw/swagger/OpenData/a1b899c0-511f-4e3d-b22b-814982a97e41"
        headers = {'User-Agent': 'Mozilla/5.0'}
       
        # 重試機制
        for i in range(3):
            try:
                res = requests.get(url, headers=headers, timeout=15, verify=False)
                json_data = res.json()
                found = False
               
                # 建立表格 HTML
                results = "<h3>查詢結果：</h3><table border='1' style='border-collapse:collapse; width:100%; text-align:left;'>"
                results += "<tr style='background-color:#f2f2f2;'><th>路口名稱</th><th>件數</th><th>原因</th></tr>"
               
                for item in json_data:
                    if q in item.get("路口名稱", ""):
                        found = True
                        results += f"<tr><td>{item['路口名稱']}</td><td>{item.get('總件數', 'N/A')}</td><td>{item.get('主要肇因', 'N/A')}</td></tr>"
                results += "</table>"
               
                if not found:
                    results = f"<p style='color:orange;'>查無關於「{q}」的資料。</p>"
                break # 成功則跳出迴圈
               
            except Exception as e:
                if i < 2: # 還有重試機會
                    time.sleep(1)
                else:
                    results = f"<div style='color:red;'>連線失敗：{str(e)}</div>"

    html = f"""
    <h1>台中市易肇事路口查詢 (鍾若筠)</h1>
    <form action="/road1" method="get">
        請輸入路名：<input type="text" name="q" value="{q}">
        <button type="submit">查詢</button>
    </form>
    <hr>
    {results}
    <br><a href="/">回首頁</a>
    """
    return html




# --- (1) spiderMovie: 爬取並存到資料庫 ---
@app.route("/spiderMovie")
def spiderMovie():
    url = "https://www.atmovies.com.tw/movie/next/"
    data = requests.get(url)
    data.encoding = "utf-8"
    sp = BeautifulSoup(data.text, "html.parser")
    result = sp.select(".filmListAllX li")
    
    count = 0
    for item in result:
        img_tag = item.find("img")
        link_tag = item.find("a")
        
        if img_tag and link_tag:
            name = img_tag.get("alt")
            link = "https://www.atmovies.com.tw" + link_tag.get("href")
            raw_img = img_tag.get("src")
            # 處理相對路徑圖片
            img_src = raw_img if raw_img.startswith("http") else "https://www.atmovies.com.tw" + raw_img
            
            # --- 強化日期抓取邏輯 ---
            item_text = item.get_text()
            if "上映日期：" in item_text:
                # 取得「上映日期：」之後的內容，並取第一段連續字元(即日期)
                release_date = item_text.split("上映日期：")[1].strip().split()[0]
            else:
                release_date = "暫無資料"

            doc_data = {
                "title": name,
                "poster": img_src,
                "link": link,
                "releaseDate": release_date,
                "updateTime": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            # 寫入 Firestore，以片名為 ID 可避免重複爬取產生多筆相同資料
            db.collection("UpcomingMovies").document(name).set(doc_data)
            count += 1
            
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    R = f"<h2>爬取完成！</h2>"
    R += f"最近更新日期：{now}<br>"
    R += f"本次共爬取並成功存儲：{count} 部電影資料到資料庫。<br><br>"
    R += "<a href='/'>返回首頁</a>"
    return R


# --- (2) searchMovie: 搜尋資料庫中的電影 ---
@app.route("/searchMovie", methods=["GET", "POST"])
def searchMovie():
    if request.method == "POST":
        keyword = request.form.get("keyword")
        # 從 Firestore 的 "UpcomingMovies" 集合取得所有文件
        collection_ref = db.collection("UpcomingMovies")
        docs = collection_ref.get()
        
        # 建立結果頁面的 HTML
        Result = f"<h2>關鍵字「{keyword}」的查詢結果：</h2><hr>"
        index_num = 1
        found = False
        
        for doc in docs:
            movie = doc.to_dict()
            # 模糊搜尋：檢查關鍵字是否在電影標題中
            if keyword in movie.get("title", ""):
                found = True
                Result += f"<b>編號：{index_num}</b><br>"
                Result += f"片名：<strong>{movie.get('title')}</strong><br>"
                
                # 海報顯示 (固定寬度以便排版)
                poster_url = movie.get('poster')
                Result += f"海報：<br><img src='{poster_url}' width='150' style='margin: 10px 0;'><br>"
                
                # 上映日期
                Result += f"上映日期：{movie.get('releaseDate')}<br>"
                
                # 介紹頁連結 (另開視窗)
                Result += f"介紹頁：<a href='{movie.get('link')}' target='_blank'>點我觀看電影詳細資訊</a><hr>"
                
                index_num += 1
        
        if not found:
            Result += f"<p>抱歉，資料庫中找不到包含「{keyword}」的電影。</p>"
            
        return Result + "<br><a href='/searchMovie'>重新搜尋</a> | <a href='/'>返回首頁</a>"
    else:
        # GET 請求時顯示搜尋表單
        html = """
        <h2>搜尋資料庫電影</h2>
        <form method="post">
            請輸入片名關鍵字：<input type="text" name="keyword" placeholder="例如：復仇者" required>
            <button type="submit">開始查詢</button>
        </form><br>
        <a href='/'>返回首頁</a>
        """
        return html



@app.route("/movie1", methods=["GET", "POST"])  # 記得加入 methods
def movie1():
    # 1. 取得使用者搜尋的關鍵字
    query = request.values.get("query", "")
    
    # 2. 在頁面最上方加入搜尋表單 HTML
    R = "<h2>即將上映電影搜尋</h2>"
    R += f"""
    <form action="/movie1" method="get">
        <input type="text" name="query" value="{query}" placeholder="輸入電影關鍵字...">
        <button type="submit">搜尋</button>
    </form><br><hr>
    """
    
    url = "https://www.atmovies.com.tw/movie/next/"
    
    try:
        data = requests.get(url)
        data.encoding = "utf-8"
        sp = BeautifulSoup(data.text, "html.parser")
        result = sp.select(".filmListAllX li")
        
        for item in result:
            img_tag = item.find("img")
            link_tag = item.find("a")
            
            if img_tag and link_tag:
                name = img_tag.get("alt")
                
                # --- 篩選邏輯：如果使用者有輸入關鍵字，只顯示符合的電影 ---
                if query and query not in name:
                    continue 
                
                link = "https://www.atmovies.com.tw" + link_tag.get("href")
                raw_img = img_tag.get("src")
                img_src = raw_img if raw_img.startswith("http") else "https://www.atmovies.com.tw" + raw_img
                
                R += f"<img src='{img_src}' width='150' style='display:block; margin-bottom:10px;'>"
                R += f"電影名稱：<strong>{name}</strong><br>"
                R += f"介紹連結：<a href='{link}' target='_blank'>點我觀看</a><hr>"
        
        if not result:
            R += "暫時抓不到電影資料。"
            
    except Exception as e:
        R = f"發生錯誤：{e}"

    return R + "<br><a href='/'>返回首頁</a>"





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