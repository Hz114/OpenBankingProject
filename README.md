# Open Banking Project

### 가상환경
>가상환경 실행하기 </br>
>*Django개발은 반드시 가상환경을 키고 시작*  
`source myvenv/Scripts/activate`
>
>가상환경 끄기  
`deactivate`

>가상환경에 설치  
`pip install -r requirements.txt`
</br>

***

### Django  
>secrets.json 파일 생성 후 내용입력 </br>
>*manage.py와 같은 경로에 secrets.json을 생성해야 작동* 
```
{
  "SECRET_KEY" : "Project폴더의 settings.py의 SECRET_KEY"
  "API_TOKEN" : "오픈뱅킹 API token" ,
  "API_USER_SEQ_NO" : "오픈뱅킹 API user sequence number"
}
```  


>Django 서버 작동 <br/>
> `python manage.py runserver`  


>Django DB 변경시 실행
```
python manage.py makemigrations 
python manage.py migrate
```

>Django DB admin생성 <br/>
`python manage.py createsuperuser`
__
### 참고
> :
