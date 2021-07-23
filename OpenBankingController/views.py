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

def main(request):

    '''
    # card
     - 은행명, 계좌번호, 잔액 등
    '''
    accountInfoList = []

    userAccountInfo = getUserAccountInfo()
    userAccountBalance = getAccountBalanceAmt()
    for accountInfo in userAccountInfo['res_list']:
        accountDic = {}
        accountDic['bank_name'] = accountInfo['bank_name']
        accountDic['account_num_masked'] = accountInfo['account_num_masked']

        for accountBalance in userAccountBalance:
            if accountInfo['bank_name'] == accountBalance['bank_name']:
                accountDic['balance_amt'] = format(int(accountBalance['balance_amt']), ',')
                break
        accountInfoList.append(accountDic)

    '''
    accountInfoList값 확인
    for accountInfo in accountInfoList:
        print(accountInfo['bank_name'])
        print(accountInfo['account_num_masked'])
        print(accountInfo['balance_amt'])
    '''


    '''
    # table
     - 각 은행별 입출금 상세 내역
    '''
    accountTransList = getAccountTrans()

    for accountTrans in accountTransList:
        print(accountTrans["bank_name"])
        #idx = 0

        accountTrans = sorted(accountTrans["res_list"]["tran_date"])
        print(accountTrans)

        for res in accountTrans["res_list"]:
            # res["idx"] = idx
            # idx += 1

            dateandtime = res["tran_date"] + res["tran_time"]
            dateandtime = datetime.datetime.strptime(dateandtime, '%Y%m%d%H%M%S')
            res["tran_date"] = res["tran_time"] = dateandtime

            res["tran_amt"] = format(int(res["tran_amt"]), ',')
            res["after_balance_amt"] = format(int(res["after_balance_amt"]), ',')

        print(accountTrans)

    return render(request, 'main.html', {'accountInfoList':accountInfoList, 'accountTransList':accountTransList})

def detail(request, bank_name):
    '''
    # table
     - 은행별 입출금 상세 내역
    '''
    accountTransList = getAccountTrans()
    accountDetailTransList = []

    minDate = datetime.datetime.strptime('99991231000000', '%Y%m%d%H%M%S')
    maxDate = datetime.datetime.strptime('00010101000000', '%Y%m%d%H%M%S')

    for accountTrans in accountTransList:
        if accountTrans["bank_name"] == bank_name:
            for res in accountTrans["res_list"]:
                dateandtime = res["tran_date"] + res["tran_time"]
                dateandtime = datetime.datetime.strptime(dateandtime, '%Y%m%d%H%M%S')
                res["tran_date"] = res["tran_time"] = dateandtime

                if minDate > dateandtime:
                    minDate = dateandtime
                elif maxDate < dateandtime:
                    maxDate = dateandtime

                res["tran_amt"] = format(int(res["tran_amt"]), ',')
                res["after_balance_amt"] = format(int(res["after_balance_amt"]), ',')
            accountDetailTransList = accountTrans
            break

    return render(request, 'detail.html', {'bankName': bank_name,'minDate': minDate, 'maxDate': maxDate, 'accountDetailTransList': accountDetailTransList})

def login(request):
    return render(request, 'login.html')
