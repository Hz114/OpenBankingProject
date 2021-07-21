# OpenBankingController / views.py

import django.http
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

# Create your views here.


token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOiIxMTAwOTk1NDEzIiwic2NvcGUiOlsiaW5xdWlyeSIsImxvZ2luIiwidHJhbnNmZXIiXSwiaXNzIjoiaHR0cHM6Ly93d3cub3BlbmJhbmtpbmcub3Iua3IiLCJleHAiOjE2MzQ0NzQ5NDQsImp0aSI6ImE3N2VmZjVlLWQxZTktNDE3Ni1iNDljLWJhNDBlOTZmYjUyZSJ9.a_OiYfRaei-qCRbZtnpi2LOmma2hVjt5qR5h_7Ilu78"
header = "Bearer" + token
user_seq_no = "1100995413"


class OpenBankingControllerView: #결과값 dict로 반환

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
            response = httpConnection.json() #json 형태일 경우 dictionary로 변환
            # print(responseCode)
            # print(headers, params)
            # print(response)
            return response

        except Exception as e:
            print(e)

            return str(e)


class getAllAcountList: #dict로 반환

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
        print(accountList)

        return accountList


class getAllAcountTransactionList:

    def getallaccounttransactionlist(self):

        Min = 111111111
        Max = 999999999

        from_date = "20210601"
        to_date = "20210630"
        
        before_inquiry_trace_info = ["333","222","123","111"]
        allAccountList = getAllAcountList.getallaccountlist(self) #dict로 불러온다

        jsonArray = allAccountList["fintech_use_num"]
        fintechUseNum = []

        for item in jsonArray: #fintech만 추출 -> list에 담기
            fintechUseNum.append(str(item))
        # print(fintechUseNum)
        # print(len(fintechUseNum))

        totalResult = []


        for i in range(len(fintechUseNum)):

            randomNumber = str(int(random.randint(1,10000) + (Max-Min)))

            bank_tran_id =  "M202112767" + "U" + randomNumber  # 이용기관코드 -> 뒤에 9자리 난수생성으로 사용

            apiURL = "https://testapi.openbanking.or.kr/v2.0/account/transaction_list/fin_num"
            apiURL = apiURL + "?bank_tran_id=" + bank_tran_id + "&fintech_use_num=" + fintechUseNum[i] + "&inquiry_type=A&inquiry_base=D&from_date=" + from_date + "&to_date=" + to_date + "&sort_order=D&tran_dtime=20201001150133"


            result = OpenBankingControllerView.goconnection(apiURL) #dict로 반환
            jsonTranObject = result
            jsonTranArray = result["res_list"]

            bankTranList = {}
            bankResList = []

            bank_name = jsonTranObject["bank_name"]
            bankTranList["bank_name"] = bank_name

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

        BalanceAmt = defaultdict(list)

        BalanceAmt["balace_amt"] = result["balance_amt"]
        BalanceAmt["bank_name"] = result["bank_name"]

        BalanceAmt = dict(BalanceAmt)

    return Response(BalanceAmt)

@api_view(['GET'])
def getMonthlyWithdrawl(request, self=None):
    if request.method:
        result = getAllAcountTransactionList.getallaccounttransactionlist(self)

        jsonObject = result
        jsonArray = jsonObject["res_list"]
        MonthlyWithdrrawlList = []
        reslistdict = {}

        for items in jsonArray:
            if items["inout_type"] == "출금":
                reslistdict["tran_date"] = items["tran_date"]
                reslistdict["tran_type"] = items["tran_type"]
                reslistdict["print_content"] = items["print_content"]
                reslistdict["balance_name"] = items["branch_name"]

                MonthlyWithdrrawlList.append(reslistdict)

        # MonthlyWithdrrawlList = json.dumps(MonthlyWithdrrawlList) #json으로 보내기
        print(type(MonthlyWithdrrawlList))
        return Response(MonthlyWithdrrawlList)








