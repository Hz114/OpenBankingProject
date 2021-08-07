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
        #print(accountList)

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

# Create your views here.


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

        idx = 0
        allBalanceAmt = 0
        for accountInfo in userAccountInfo['res_list']:
            accountDic = {}
            accountDic['bank_idx'] = idx
            accountDic['bank_name'] = accountInfo['bank_name']
            accountDic['account_num_masked'] = accountInfo['account_num_masked']

            for accountBalance in userAccountBalance:
                if accountInfo['bank_name'] == accountBalance['bank_name']:
                    accountDic['balance_amt'] = format(int(accountBalance['balance_amt']), ',')
                    allBalanceAmt += int(accountBalance['balance_amt'])
                    break
            accountInfoList.append(accountDic)
            idx += 1
        allBalanceAmt = format(allBalanceAmt, ',')

        '''
        # table
         - 각 은행별 입출금 상세 내역
        '''
        idx = 0

        # 모든 카드의 내역을 확인
        # http://127.0.0.1:8000/open/allAccountTransList
        accountTransList = getAccountTrans()
        allMonthBalanceAmt = []
        allMonthUseBalanceAmt = []

        for m in range(0, 12):
            allMonthBalanceAmt.append(0)
            allMonthUseBalanceAmt.append(0)

        for accountTrans in accountTransList:
            # print(accountTrans["bank_name"])
            accountTrans["bank_idx"] = idx
            accountTrans["res_list"].reverse()

            monthBalanceAmt = []
            monthUseBalanceAmt = []

            for m in range(0, 12):
                monthBalanceAmt.append(0)
                monthUseBalanceAmt.append(0)

            res_idx = 0
            for res in accountTrans["res_list"]:
                res["idx"] = res_idx

                dateandtime = res["tran_date"] + res["tran_time"]
                dateandtime = datetime.datetime.strptime(dateandtime, '%Y%m%d%H%M%S')
                res["tran_date"] = dateandtime.date()
                res["tran_time"] = dateandtime.time()

                if monthBalanceAmt[int(dateandtime.date().month)-1] == 0:
                    monthBalanceAmt[int(dateandtime.date().month)-1] = int(res["after_balance_amt"])
                    allMonthBalanceAmt[int(dateandtime.date().month)-1] += int(res["after_balance_amt"])

                if res["inout_type"] == '출금':
                    monthUseBalanceAmt[int(dateandtime.date().month) - 1] += int(res["tran_amt"])
                    allMonthUseBalanceAmt[int(dateandtime.date().month) - 1] += int(res["tran_amt"])

                res["tran_amt"] = format(int(res["tran_amt"]), ',')
                res["after_balance_amt"] = format(int(res["after_balance_amt"]), ',')

                res_idx += 1
            idx += 1

            for m in range(1, 12):
                if monthBalanceAmt[m] == 0:
                    monthBalanceAmt[m] = monthBalanceAmt[m-1]
            accountTrans["month_balance_amt"] = monthBalanceAmt
            accountTrans["month_use_balance_amt"] = monthUseBalanceAmt


        for m in range(1, 12):
            if allMonthBalanceAmt[m] == 0:
                allMonthBalanceAmt[m] = allMonthBalanceAmt[m-1]

        return render(request, 'index.html',
                          {'accountInfoList': accountInfoList, 'accountTransList': accountTransList,
                           'allBalanceAmt': allBalanceAmt, 'allMonthBalanceAmt':allMonthBalanceAmt, 'allMonthUseBalanceAmt':allMonthUseBalanceAmt })
    except KeyError:
        return render(request, 'error.html')


def chart(request):
    print('OpenBankingPController view.py - def chart')
    category = {
        '카페' : ['커피','카페', '케이크', '제과','다방','케익','케잌', '빵','베이커리','스타벅스','투썸플레이스','카페베네','이디야','엔젤리너스',	'빌리앤젤','커피빈','파스꾸찌','할리스','요거프레소'],
        '식비' : ['떡볶이','한정식','주점','갈비','칵테일','막걸리','포차','삼겹','초밥','파자','곱창','닭발','돈까스','김밥',	'맘스터치','롯데리아','맥도날드','분식','우아한형제들','치킨','BHC','교촌','포장마차','식당','구내','호떡', '푸드'],
        '편의점' : ['GS25', '세븐일레븐', 'CU', '미니스톱', '이마트24','편의점'],
        '교통비' : ['택시' ,'KTX','버스', '지하철'],
        '온라인쇼핑' : ['네이버페이','카카오페이', '쿠팡', '11번가', '티몬','토스'],
        '여행/숙박' :  ['에어', '숙소', '펜션','항공', '비행', '기념', '호텔', '모텔', '해외결제'],
        '주거/생활비' : ['월세', '마트', '공과금', '오늘의집', '가구'],
        '통신비' : ['SKT','KT', 'U+'],
        '금융비' : ['주식','학자금', '수수료', '대출'],
        '경조사비' : ['혼례', '장례', '결혼', '축의금', '조의금', '꽃', '화원'],
        '교육비' :  ['등록금', '해커스', '독서실', '스터디', '시험', '원서'],
        '문화비' :  ['CGV', '메가박스', '롯데시네마', 'APPLE', 'NETFLIX', '멜론', '티빙', '왓챠', 'wave', 'VIBE', '지니뮤직', '소리바다', '연극', '뮤지컬', '콘서트', '인터파크'],
        '여가/취미/레저비' : ['합기도', '헬스', '짐', 'GYM', '골프' ,'수상','낚시', 'PC', '노래', '피아노', '펜싱', '방탈출', '보컬', '기타', '댄스', '발레', '요가', '필라테스'],
        '문구/디지털/가전' : ['다이소', '컴퓨터', '교보문고', '알라딘', '알파', '삼성', 'LG', '완구','인쇄', '소니', '아이리버', '플레이스테이션'],
        '미용/뷰티' : ['올리브영', '미용', '헤어', '랄라블라', '오렌즈', '렌즈미', '네일', '피부', '왁싱'],
        '의류/패션/잡화' : ['옷', '다비치안경', '쥬얼리', '스파오','탑텐', '유니클로','샵', '몰', '액세서리', 'OST', '백화점', '의류',  '나이키', '아디다스', '상품권', '시계'],
        '건강비' : ['병원', '의원', '치과', '약국', '의료', '건강', '마스크']
    }
    count_all_category ={
        '카페': 0,
        '식비': 0,
        '편의점': 0,
        '교통비': 0,
        '온라인쇼핑': 0,
        '여행/숙박': 0,
        '주거/생활비': 0,
        '통신비': 0,
        '금융비': 0,
        '경조사비': 0,
        '교육비': 0,
        '문화비': 0,
        '여가/취미/레저비': 0,
        '문구/디지털/가전': 0,
        '미용/뷰티': 0,
        '의류/패션/잡화': 0,
        '건강비': 0
    }
    count_all_content = {}

    # 모든 카드의 내역을 확인
    # http://127.0.0.1:8000/open/allAccountTransList
    accountTransList = getAccountTrans()
    idx = 0

    for accountTrans in accountTransList:
        print(accountTrans["bank_name"])
        accountTrans["bank_idx"] = idx

        count_account_category = {
            '카페': 0,
            '식비': 0,
            '편의점': 0,
            '교통비': 0,
            '온라인쇼핑': 0,
            '여행/숙박': 0,
            '주거/생활비': 0,
            '통신비': 0,
            '금융비': 0,
            '경조사비': 0,
            '교육비': 0,
            '문화비': 0,
            '여가/취미/레저비': 0,
            '문구/디지털/가전': 0,
            '미용/뷰티': 0,
            '의류/패션/잡화': 0,
            '건강비': 0
        }
        count_account_content = {}

        res_idx = 0
        for res in accountTrans["res_list"]:
            res["category"] = ''
            res["idx"] = res_idx

            dateandtime = res["tran_date"] + res["tran_time"]
            dateandtime = datetime.datetime.strptime(dateandtime, '%Y%m%d%H%M%S')
            res["tran_date"] = dateandtime.date()
            res["tran_time"] = dateandtime.time()

            if res["inout_type"] == '출금':
                for key in category.keys():
                    for value in category[key]:
                        if value in res["print_content"]:
                            res["category"] = key
                            count_all_category[key] += 1
                            count_account_category[key] += 1


                            try:
                                count_account_content[key + '-' + res["print_content"]] += 1
                            except:
                                count_account_content[key+'-'+res["print_content"]] = 1

                            try:
                                count_all_content[key+'-'+res["print_content"]] += 1
                            except:
                                count_all_content[key+'-'+res["print_content"]] = 1

                            break
                    if res["category"] == key:
                        break

            res_idx += 1

        accountTrans['count_account_category'] = count_account_category
        print(accountTrans['count_account_category'])
        print(count_account_content)

    print(count_all_category)
    print(count_all_content)

    return render(request, 'ui-badges.html')

def login(request):
    print('OpenBankingPController view.py - def login')
    return render(request, 'index-base.html')


