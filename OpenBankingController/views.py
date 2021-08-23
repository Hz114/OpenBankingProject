import django.http
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpRequest
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
import requests
import json
import pandas as pd
from collections import defaultdict
from django.http import HttpResponse
import random
import django.http.response
# hide API KEY
import os
from pathlib import Path

import datetime
from itertools import islice

from fbprophet import Prophet
import numpy as np

# hide API KEY

BASE_DIR = Path(__file__).resolve().parent.parent
secret_file = os.path.join(BASE_DIR, 'secrets.json')

with open(secret_file) as f:
    secrets = json.loads(f.read())


def get_secret(setting, secrets=secrets):
    try:
        return secrets[setting]
    except KeyError:
        error_msg = "Set the {} environment variable".format(setting)
        raise ImproperlyConfigured(error_msg)


token = get_secret("API_TOKEN")
header = "Bearer" + token
user_seq_no = get_secret("API_USER_SEQ_NO")


class OpenBankingControllerView:  # 결과값 dict로 반환
    def goconnection(apiURL):
        try:
            # print(apiURL)
            # headers =
            # params =
            httpConnection = requests.get(apiURL,
                                          headers={"Connection": "keep-alive", "Content-Type": "application/json",
                                                   "charset": "utf-8", "Authorization": header},
                                          params={"user_seq_no": user_seq_no})
            responseCode = httpConnection.status_code
            response = httpConnection.json()  # json 형태일 경우 dictionary로 변환
            # print(responseCode)
            # print(headers, params)
            # print(response)
            return response

        except Exception as e:
            print(e)
            return str(e)


class getAllAcountList:  # dict로 반환
    def getallaccountlist(self):
        apiURL = apiURL = "https://developers.kftc.or.kr/proxy/account/list"
        apiURL = apiURL + "?&include_cancel_yn=N&sort_order=D"

        result = OpenBankingControllerView.goconnection(apiURL)

        jsonResult = json.dumps(result)
        jsonObject = json.loads(jsonResult)
        jsonArray = jsonObject['res_list']

        accountList = defaultdict(list)

        for items in jsonArray:
            accountList["fintech_use_num"].append(items["fintech_use_num"])
            accountList["bank_code_std"].append(items["bank_code_std"])
            accountList["bank_name"].append(items["bank_name"])

        accountList = dict(accountList)
        # print(accountList)

        return accountList


class getAllAcountTransactionList:
    def getallaccounttransactionlist(self):

        Min = 111111111
        Max = 999999999

        from_date = "20210601"
        to_date = "20210630"

        before_inquiry_trace_info = ["333", "222", "123", "111"]
        allAccountList = getAllAcountList.getallaccountlist(self)  # dict로 불러온다

        jsonArray = allAccountList["fintech_use_num"]
        fintechUseNum = []

        for item in jsonArray:  # fintech만 추출 -> list에 담기
            fintechUseNum.append(str(item))
        # print(fintechUseNum)
        # print(len(fintechUseNum))

        totalResult = []

        for i in range(len(fintechUseNum)):

            randomNumber = str(int(random.randint(1, 10000) + (Max - Min)))

            bank_tran_id = "M202112767" + "U" + randomNumber  # 이용기관코드 -> 뒤에 9자리 난수생성으로 사용

            apiURL = "https://testapi.openbanking.or.kr/v2.0/account/transaction_list/fin_num"
            apiURL = apiURL + "?bank_tran_id=" + bank_tran_id + "&fintech_use_num=" + fintechUseNum[
                i] + "&inquiry_type=A&inquiry_base=D&from_date=" + from_date + "&to_date=" + to_date + "&sort_order=D&tran_dtime=20201001150133"

            result = OpenBankingControllerView.goconnection(apiURL)  # dict로 반환
            jsonTranObject = result
            jsonTranArray = result["res_list"]

            bankTranList = {}
            bankResList = []

            bank_name = jsonTranObject["bank_name"]
            balance_amt = jsonTranObject["balance_amt"]
            bankTranList["bank_name"] = bank_name
            bankTranList["balance_amt"] = balance_amt

            for items in jsonTranArray:
                bankResList.append(items)

            bankTranList["res_list"] = bankResList
            totalResult.append(bankTranList)

        return totalResult


@api_view(['GET'])
def getUserInfo(request):
    if request.method == 'GET':
        apiURL = "https://developers.kftc.or.kr/proxy/user/me"

        result = OpenBankingControllerView.goconnection(apiURL)

        jsonresult = json.dumps(result)
        jsonObject = json.loads(jsonresult)

        # 다음 json파일을 훔쳐서 표시하자~~
        # print(jsonObject)
        return Response(jsonObject)


@api_view(['GET'])
def getAllAccountList(request, self=None):
    if request.method == 'GET':
        result = getAllAcountList.getallaccountlist(self)

        jsonResult = json.dumps(result)
        jsonObject = json.loads(jsonResult)

        return Response(jsonObject)


@api_view(['GET'])
def getAllAcountTransList(request, self=None):
    if request.method == 'GET':
        result = getAllAcountTransactionList.getallaccounttransactionlist(self)

    return Response(result)


@api_view(['GET'])
def getBalanceAmt(request, self=None):
    if request.method == 'GET':

        result = getAllAcountTransactionList.getallaccounttransactionlist(self)

        jsonArray = result

        balanceAmtlist = []

        for items in jsonArray:
            balanceAmtdict = {}
            bankName = items["bank_name"]
            balanceAmt = items["balance_amt"]
            balanceAmtdict["bank_name"] = bankName
            balanceAmtdict["balance_amt"] = balanceAmt
            balanceAmtlist.append(balanceAmtdict)

    return Response(balanceAmtlist)


@api_view(['GET'])
def getMonthlyWithdrawl(request, self=None):
    if request.method == 'GET':
        result = getAllAcountTransactionList.getallaccounttransactionlist(self)

        jsonArray = result

        MonthlyWithdrrawlList = []
        reslistdict = {}

        for items in jsonArray:
            jsonBankArray = items["res_list"]
            for item in jsonBankArray:
                if item["inout_type"] == "출금":
                    reslistdict["tran_date"] = item["tran_date"]
                    reslistdict["tran_time"] = item["tran_time"]
                    reslistdict["tran_type"] = item["tran_type"]
                    reslistdict["print_content"] = item["print_content"]
                    reslistdict["balance_name"] = item["branch_name"]

                    MonthlyWithdrrawlList.append(reslistdict)

        print(type(MonthlyWithdrrawlList))
        return Response(MonthlyWithdrrawlList)

def getUserAccountInfo():
    apiURL = "https://developers.kftc.or.kr/proxy/user/me"
    result = OpenBankingControllerView.goconnection(apiURL)
    jsonresult = json.dumps(result)
    jsonObject = json.loads(jsonresult)
    return jsonObject

def getAccountBalanceAmt(self=None):
    result = getAllAcountTransactionList.getallaccounttransactionlist(self)
    jsonArray = result

    balanceAmtlist = []
    for items in jsonArray:
        balanceAmtdict = {}
        bankName = items["bank_name"]
        balanceAmt = items["balance_amt"]
        balanceAmtdict["bank_name"] = bankName
        balanceAmtdict["balance_amt"] = balanceAmt
        balanceAmtlist.append(balanceAmtdict)
    return balanceAmtlist


def getAccountTrans(self=None):
    result = getAllAcountTransactionList.getallaccounttransactionlist(self)
    return result


def index(request):
    print('OpenBankingPController view.py - def index')
    '''
    # card
     - 은행명, 계좌번호, 잔액 등
    '''
    try:
        accountInfoList = []

        # user의 개인정보 불러오기
        # http://127.0.0.1:8000/open/user
        userAccountInfo = getUserAccountInfo()

        # 모든 카드의 잔액을 확인
        # http://127.0.0.1:8000/open/allAccountBalanceAmt
        userAccountBalance = getAccountBalanceAmt()

        allBalanceAmt = 0
        for accountInfo in userAccountInfo['res_list']:
            accountDic = {}
            accountDic['bank_name'] = accountInfo['bank_name']
            accountDic['account_num_masked'] = accountInfo['account_num_masked']

            for accountBalance in userAccountBalance:
                if accountInfo['bank_name'] == accountBalance['bank_name']:
                    accountDic['balance_amt'] = format(int(accountBalance['balance_amt']), ',')
                    allBalanceAmt += int(accountBalance['balance_amt'])
                    break
            accountInfoList.append(accountDic)
        allBalanceAmt = format(allBalanceAmt, ',')

        '''
        # table
         - 각 은행별 입출금 상세 내역
        '''


        # 모든 카드의 내역을 확인
        # http://127.0.0.1:8000/open/allAccountTransList
        accountTransList = getAccountTrans()
        allMonthBalanceAmt = []
        allMonthUseBalanceAmt = []

        for m in range(0, 12):
            allMonthBalanceAmt.append(0)
            allMonthUseBalanceAmt.append(0)

        for accountTrans in accountTransList:
            monthBalanceAmt = []
            monthUseBalanceAmt = []

            for m in range(0, 12):
                monthBalanceAmt.append(0)
                monthUseBalanceAmt.append(0)

            accountTrans["res_list"].reverse()
            for res in accountTrans["res_list"]:
                dateandtime = res["tran_date"] + res["tran_time"]
                dateandtime = datetime.datetime.strptime(dateandtime, '%Y%m%d%H%M%S')
                res["tran_date"] = dateandtime.date()
                res["tran_time"] = dateandtime.time()

                if monthBalanceAmt[int(dateandtime.date().month) - 1] == 0:
                    monthBalanceAmt[int(dateandtime.date().month) - 1] = int(res["after_balance_amt"])
                    allMonthBalanceAmt[int(dateandtime.date().month) - 1] += int(res["after_balance_amt"])

                if res["inout_type"] == '출금':
                    monthUseBalanceAmt[int(dateandtime.date().month) - 1] += int(res["tran_amt"])
                    allMonthUseBalanceAmt[int(dateandtime.date().month) - 1] += int(res["tran_amt"])

                res["tran_amt"] = format(int(res["tran_amt"]), ',')
                res["after_balance_amt"] = format(int(res["after_balance_amt"]), ',')

            for m in range(1, 12):
                if monthBalanceAmt[m] == 0:
                    monthBalanceAmt[m] = monthBalanceAmt[m - 1]
            accountTrans["month_balance_amt"] = monthBalanceAmt
            accountTrans["month_use_balance_amt"] = monthUseBalanceAmt

        for m in range(1, 12):
            if allMonthBalanceAmt[m] == 0:
                allMonthBalanceAmt[m] = allMonthBalanceAmt[m - 1]

        return render(request, 'index.html',
                      {'accountInfoList': accountInfoList, 'accountTransList': accountTransList,
                       'allBalanceAmt': allBalanceAmt, 'allMonthBalanceAmt': allMonthBalanceAmt,
                       'allMonthUseBalanceAmt': allMonthUseBalanceAmt})
    except KeyError:
        return render(request, 'error.html')


def analysis(request):
    print('OpenBankingPController view.py - def analysis')
    category = {
        '카페': ['커피', '카페', '케이크', '제과', '다방', '케익', '케잌', '빵', '베이커리', '스타벅스', '투썸플레이스', '카페베네', '이디야', '엔젤리너스', '빌리앤젤',
               '커피빈', '파스꾸찌', '할리스', '요거프레소'],
        '식비': ['떡볶이', '한정식', '주점', '갈비', '칵테일', '막걸리', '포차', '삼겹', '초밥', '파자', '곱창', '닭발', '돈까스', '김밥', '맘스터치', '롯데리아',
               '맥도날드', '분식', '우아한형제들', '치킨', 'BHC', '교촌', '포장마차', '식당', '구내', '호떡', '푸드'],
        '편의점': ['GS25', '세븐일레븐', 'CU', '미니스톱', '이마트24', '편의점'],
        '교통비': ['택시', 'KTX', '버스', '지하철'],
        '온라인쇼핑': ['네이버페이', '카카오페이', '쿠팡', '11번가', '티몬', '토스'],
        '여행비': ['에어', '숙소', '펜션', '항공', '비행', '기념', '호텔', '모텔', '해외결제'],
        '생활비': ['월세', '마트', '공과금', '오늘의집', '가구'],
        '통신비': ['SKT', 'KT', 'U+'],
        '금융비': ['주식', '학자금', '수수료', '대출'],
        '경조사비': ['혼례', '장례', '결혼', '축의금', '조의금', '꽃', '화원'],
        '교육비': ['등록금', '해커스', '독서실', '스터디', '시험', '원서'],
        '문화비': ['CGV', '메가박스', '롯데시네마', 'APPLE', 'NETFLIX', '멜론', '티빙', '왓챠', 'wave', 'VIBE', '지니뮤직', '소리바다', '연극',
                '뮤지컬', '콘서트', '인터파크'],
        '여가비': ['합기도', '헬스', '짐', 'GYM', '골프', '수상', '낚시', 'PC', '노래', '피아노', '펜싱', '방탈출', '보컬', '기타', '댄스', '발레', '요가',
                '필라테스'],
        '문구가전제품': ['다이소', '컴퓨터', '교보문고', '알라딘', '알파', '삼성', 'LG', '완구', '인쇄', '소니', '아이리버', '플레이스테이션'],
        '뷰티미용': ['올리브영', '미용', '헤어', '랄라블라', '오렌즈', '렌즈미', '네일', '피부', '왁싱'],
        '의류잡화': ['옷', '다비치안경', '쥬얼리', '스파오', '탑텐', '유니클로', '샵', '몰', '액세서리', 'OST', '백화점', '의류', '나이키', '아디다스', '상품권',
                 '시계'],
        '건강비': ['병원', '의원', '치과', '약국', '의료', '건강', '마스크']
    }
    # count_all_content = {}

    # 모든 카드의 내역을 확인
    # http://127.0.0.1:8000/open/allAccountTransList
    accountTransList = getAccountTrans()

    all_res_list = []

    for accountTrans in accountTransList:
        print('-' + accountTrans["bank_name"])
        count_account_category = {
            '카페': 0,
            '식비': 0,
            '편의점': 0,
            '교통비': 0,
            '온라인쇼핑': 0,
            '여행비': 0,
            '생홥비': 0,
            '통신비': 0,
            '금융비': 0,
            '경조사비': 0,
            '교육비': 0,
            '문화비': 0,
            '여가비': 0,
            '문구가전제품': 0,
            '뷰티미용': 0,
            '의류잡화': 0,
            '건강비': 0
        }
        account_category_content = {}

        total_tran_amt = 0
        res_out_cnt = 0
        accountTrans["res_list"].reverse()

        all_res_list.append(accountTrans["res_list"])

        for res in accountTrans["res_list"]:
            res["category"] = ''

            dateandtime = res["tran_date"] + res["tran_time"]
            dateandtime = datetime.datetime.strptime(dateandtime, '%Y%m%d%H%M%S')
            res["tran_date"] = dateandtime.date()
            res["tran_time"] = dateandtime.time()

            if res["inout_type"] == '출금':
                total_tran_amt += int(res["tran_amt"])
                res_out_cnt += 1
                for key in category.keys():
                    for value in category[key]:
                        if value in res["print_content"]:
                            res["category"] = key
                            count_account_category[key] += 1

                            try:
                                account_category_content[key].append({"tran_date": res["tran_date"],
                                                                      "tran_time": res["tran_time"],
                                                                      "print_content": res["print_content"],
                                                                      "tran_amt": format(int(res["tran_amt"]), ',')})
                            except:
                                account_category_content[key] = []
                                account_category_content[key].append({  "tran_date" : res["tran_date"],
                                                                        "tran_time" : res["tran_time"],
                                                                        "print_content" : res["print_content"],
                                                                        "tran_amt": format(int(res["tran_amt"]), ',')})
                            break
                    if res["category"] == key:
                        break

        # 카테고리 소비 top5 찾기
        # top 5 제외한 값 정보 추가 -위에서 islice하면 없어짐해결방안 생각
        count_account_category = dict(sorted(count_account_category.items(), key=lambda x: x[1], reverse=True))
        count_account_category = dict(islice(count_account_category.items(), 5))

        top5_cnt = 0
        del_category_list = []
        for key, value in count_account_category.items():
            if count_account_category[key] == 0:
                del_category_list.append(key)
            else:
                top5_cnt += value
                count_account_category[key] = value

        if res_out_cnt > top5_cnt:
            count_account_category['기타'] = res_out_cnt - top5_cnt

        # 리스트 안의 값을 제거
        for del_category in del_category_list:
            del count_account_category[del_category]

        accountTrans['count_account_category'] = count_account_category
        accountTrans['res_out_cnt'] = res_out_cnt
        accountTrans['account_category_content'] = account_category_content
        accountTrans['total_tran_amt'] = format(total_tran_amt, ',')

    #forecast.to_csv("afterBalanceAmt_forecast_" + accountTrans["bank_name"] + "_30.csv", encoding='utf-8')
    all_res_list =  pd.DataFrame(all_res_list)
    #all_res_list.to_csv("all_res_list.csv", encoding='utf-8-sig')

    return render(request, 'analysis.html',{'accountTransList': accountTransList})


def forecast(request):
    print('OpenBankingPController view.py - def forecast')

    # 모든 카드의 내역을 확인
    # http://127.0.0.1:8000/open/allAccountTransList
    accountTransList = getAccountTrans()

    for accountTrans in accountTransList:

        print("###########"+accountTrans["bank_name"]+"###########")

        accountTrans["res_list"].reverse()
        afterBalanceAmt_bank_ls = {}

        for res in accountTrans["res_list"]:
            res["category"] = ''

            dateandtime = res["tran_date"] + res["tran_time"]
            dateandtime = datetime.datetime.strptime(dateandtime, '%Y%m%d%H%M%S')
            res["tran_date"] = dateandtime.date()
            res["tran_time"] = dateandtime.time()

            if res["tran_date"] not in afterBalanceAmt_bank_ls:
                afterBalanceAmt_bank_ls[res["tran_date"]] = int(res["after_balance_amt"])

        afterBalanceAmt_bank_df = pd.DataFrame.from_dict(afterBalanceAmt_bank_ls, orient='index')
        afterBalanceAmt_bank_df = afterBalanceAmt_bank_df.rename(columns={0: 'y'})


        afterBalanceAmt_bank_df_index = pd.to_datetime(afterBalanceAmt_bank_df.index)
        afterBalanceAmt_bank_df.set_index(afterBalanceAmt_bank_df_index, inplace=True)
        afterBalanceAmt_bank_df = afterBalanceAmt_bank_df.resample(rule="M").mean()

        afterBalanceAmt_bank_df_index = afterBalanceAmt_bank_df.index.strftime("%b")
        afterBalanceAmt_bank_df.set_index(afterBalanceAmt_bank_df_index, inplace=True)
        afterBalanceAmt_bank_df['month'] = afterBalanceAmt_bank_df.index

        afterBalanceAmt_bank_dic = afterBalanceAmt_bank_df.to_dict('index')


        for row_key, row_value in afterBalanceAmt_bank_dic.items():
            for month_key, month_value in afterBalanceAmt_bank_dic[row_key].items():
                if month_key == 'month':
                    continue
                n = int(int(month_value) / 10) * 10
                afterBalanceAmt_bank_dic[row_key][month_key] = n

        print(afterBalanceAmt_bank_dic)

        # fbprophet 적용 코드
        path = "./OpenBankingController/static/forecast/afterBalanceAmt_forecast_"+ accountTrans["bank_name"] +"_5.csv"
        bank_forecast = pd.read_csv(path, sep=',', error_bad_lines=False, warn_bad_lines=False)
        bank_forecast = pd.DataFrame(bank_forecast)

        bank_forecast['ds'] = pd.to_datetime(bank_forecast['ds'])
        bank_forecast.set_index('ds', inplace=True)
        bank_forecast = bank_forecast[['yhat', 'yhat_lower', 'yhat_upper']]


        bank_forecast = bank_forecast.resample(rule="M").mean()

        bank_forecast_index = bank_forecast.index.strftime("%b")
        bank_forecast.set_index(bank_forecast_index, inplace=True)
        bank_forecast['month'] = bank_forecast.index

        bank_forecast = bank_forecast.to_dict('index')

        for row_key, row_value in bank_forecast.items():
            for month_key, month_value in bank_forecast[row_key].items():
                if month_key == 'month':
                    continue
                n = int(int(month_value) / 10) * 10
                bank_forecast[row_key][month_key] = n

        print(bank_forecast)

        accountTrans['y'] = afterBalanceAmt_bank_dic
        accountTrans['yhat'] = bank_forecast


    return render(request, 'forecast.html', {'accountTransList': accountTransList})
    '''
    # fbprophet 적용 코드
    res_df = pd.DataFrame(res_data)

    prophet = Prophet(seasonality_mode='multiplicative',
                     yearly_seasonality=True,
                     weekly_seasonality=True, daily_seasonality=True,
                     changepoint_prior_scale=0.5)
    prophet.fit(res_df)

    future = prophet.make_future_dataframe(periods=30, freq='d')
    forecast = prophet.predict(future)

    forecast.to_csv("afterBalanceAmt_forecast_"+accountTrans["bank_name"]+"_30.csv", encoding='utf-8')
    '''

    ######################################

    '''
    #csv파일 실행코드
    path = "./OpenBankingController/static/forecast/afterBalanceAmt_forecastAll_5.csv"
    all_forecast = pd.read_csv(path, sep=',', error_bad_lines=False, warn_bad_lines=False)
    all_forecast = pd.DataFrame(all_forecast)

    all_forecast['ds'] = pd.to_datetime(all_forecast['ds'])
    all_forecast.set_index('ds',inplace = True)
    all_forecast = all_forecast[['yhat', 'yhat_lower', 'yhat_upper']]
    all_forecast = all_forecast.resample(rule="M").mean()


    all_forecast_index = all_forecast.index.strftime("%b")
    all_forecast.set_index(all_forecast_index, inplace=True)

    all_forecast = all_forecast.to_dict('index')

    for month in all_forecast:
        print(month)
        for key, value in all_forecast[month].items():
            n = int(value / 100) * 100
            all_forecast[month][key] = n

    print(all_forecast)

    return render(request, 'forecast.html',{'accountTransList': accountTransList, 'all_forecast': all_forecast})
    '''

def login(request):
    print('OpenBankingPController view.py - def login')
    return render(request, 'login.html')


def register(request):
    print('OpenBankingPController view.py - def register')
    return render(request, 'register.html')


def authResetPass(request):
    print('OpenBankingPController view.py - def authResetPass')
    return render(request, 'index-base.html')
    #return render(request, 'auth-reset-pass.html')

