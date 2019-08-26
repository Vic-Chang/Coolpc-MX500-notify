from bs4 import BeautifulSoup
import LineConfig
import re
import requests
import sqlite3
import datetime
import traceback


def check_price():
    try:
        # 取得分析價格
        coolpc_url = 'https://www.coolpc.com.tw/evaluate.php'
        cool = requests.get(coolpc_url)
        soup = BeautifulSoup(cool.text, "lxml")  # 指定 lxml 作為解析器

        # 兩種方式都可以
        # mx_name = soup.find('option',text=re.compile('(?=.*(MX500))(?=.*(500G))',re.I)).text
        mx_name = soup.find('option', text=lambda text: text and all(x in text for x in ['MX500', '500G'])).text
        mx_name_split = mx_name[mx_name.rfind('$') + 1:]
        mx_price = int(re.match(r'\d+', mx_name_split).group(0))

        # 儲存資料
        conn = sqlite3.connect('CoolpcMX500.db')

        # 查詢db過往價格，若無資料則新增該筆資訊
        mx500_data = conn.execute("SELECT * FROM MX500;").fetchall()
        today = str(datetime.datetime.now().date())
        if len(mx500_data) == 0:
            sql = str.format('Insert into MX500 (ID,Logdate,Price) values(1,\'{0}\',{1})', today, mx_price)
            conn.execute(sql)
            conn.commit()
            conn.close()
        else:
            oldprice = int(mx500_data[0][2])
            olddate = mx500_data[0][1]
            if oldprice != mx_price:
                sql = str.format('Update MX500 set Logdate = \'{0}\', Price = {1} where ID=1', today, mx_price)
                conn.execute(sql)
                conn.commit()
                conn.close()
            send_notify(oldprice, olddate, mx_price)
    except Exception as e:
        exception_notify(str(e), traceback.format_exc())


def send_notify(oldprice, olddate, newprice):
    wave = ''
    if (newprice - oldprice) > 0:
        wave = '+$' + str(newprice - oldprice)
    elif (newprice - oldprice) < 0:
        wave = '-$' + str(abs(newprice - oldprice))

    # 若有波動，則發送lINE訊息通知
    if wave:
        notify_msg = str.format('\n\n ‼️今日價格發生波動 ({0})‼️\n', wave)
        notify_msg += str.format('\n上次價格({0}) ${1}', olddate, oldprice)
        notify_msg += str.format('\n今日價格 ${0}\n', newprice)
        headers = {"Authorization": "Bearer " + LineConfig.LINE_NOTIFY_TOKEN}
        params = {"message": notify_msg}
        requests.post(LineConfig.LINE_NOTIFY_URL, headers=headers, params=params)


def exception_notify(error_msg, detail=''):
    headers = {"Authorization": "Bearer " + LineConfig.LINE_NOTIFY_TOKEN}
    params = {"message": 'Error ! 運行失敗，原因 : ' + error_msg + '\n詳細原因:\n' + detail}
    requests.post(LineConfig.LINE_NOTIFY_URL, headers=headers, params=params)


def exception_notify(error_msg, detail=''):
    headers = {"Authorization": "Bearer " + LineConfig.LINE_NOTIFY_TOKEN}
    params = {"message": 'Error ! 運行失敗，原因 : ' + error_msg + '\n詳細原因:\n' + detail}
    requests.post(LineConfig.LINE_NOTIFY_URL, headers=headers, params=params)


if __name__ == '__main__':
    check_price()
