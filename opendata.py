import requests, json
url = "https://datacenter.taichung.gov.tw/swagger/OpenData/a1b899c0-511f-4e3d-b22b-814982a97e41"
Data = requests.get(url)
#print(Data.text)
JsonData = json.loads(Data.text)
Result = ""
Road = input("請輸入欲查詢的路名：")
for item in JsonData:
	if Road in item["路口名稱"]:
		Result += item["路口名稱"] + "：發生" + item["總件數"] + "件，主因是" + item["主要肇因"] + "\n\n"
if Result == "":
	Result = "抱歉，查無相關資料！"
print(Result)
