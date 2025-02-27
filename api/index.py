from fastapi import FastAPI, Request, Body
from pydantic import BaseModel
from time import time
import httpx
import asyncio
import json
import imaplib
import email
from email.header import decode_header
import base64
#from bs4 import BeautifulSoup
import re

app = FastAPI()

hostName = "localhost"
serverPort = 8080
#url = 'https://b24-002xma.bitrix24.ru/rest/1/ofz3113rxnyv8qfv/'

url = 'https://b24-mhfw1p.bitrix24.ru/rest/1/etnwm06bccntmdyo/'

headers = {
  'Accept' : 'application/json',
  'Content-Type': 'application/json'
}

password = "M3Eva6YCigJXNt0bZyGc"
username = "dosmtv@mail.ru"
imap_server = "imap.mail.ru"

async def check_mail(client):
    print('checking started')
    imap = imaplib.IMAP4_SSL(imap_server)
    print(imap)
    print(imap.login(username, password))
    imap.select("INBOX")
    result, data = imap.uid('search', None, "UNSEEN")
    if result == 'OK':
        response = await client.post("https://mdevelopeur.retailcrm.ru/api/v5/orders/create?apiKey=nHY0H7zd7UWwcEiwN0EbwhXz2eGY9o9G", data={"order":{"email": "dd@mail.ru"}})
        for num in data[0].split():
            result, data = imap.uid('fetch', num, '(RFC822)')
            if result == 'OK':
                email_message = email.message_from_bytes(data[0][1])
                print('From:' + email_message['From'])
                print('To:' + email_message['To'])
                print('Date:' + email_message['Date'])
                print('Subject:' + str(email_message['Subject']))

            

# Глобальная переменная для pipeline_id
pipeline_id = 8412118

class Lead(BaseModel):
    name: str | None = None
    user_id: int | None = None
    address: str | None = None
    price: int | None = None  # Убедитесь, что price — это целое число
    phone: str | None = None
    link: str | None = None
    seller: str | None = None
    lead_id: int | None = None
    action: str | None = None

async def get_body(request: Request):
    return await request.json()

async def get_users(client):
    response = await client.post(url + 'user.get.json', headers=headers)
    response_content = response.content
    print(f"Response content: {response_content}")
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        return None
    try:
        return response.json()
    except json.JSONDecodeError:
        print("Failed to decode JSON response")
        return None

async def check_lead(client, name):
    data = {
       'filter'  : {'=TITLE' : name}
    }
    data = json.dumps(data)
    response = await client.post(url + 'crm.lead.list.json', headers=headers, data=data)
    response_content = response.content
    print(f"Response content: {response_content}")
    if response.status_code == 204:
        return response.status_code
    try:
        return response.json()
    except json.JSONDecodeError:
        print("Failed to decode JSON response")
        return None

async def get_leads(client, start):
    data = {
       'start' : start, 
       'select' : ['TITLE','UF_CRM_URL', 'ASSIGNED_BY_ID', 'COMMENTS', 'DATE_CREATE', 'DATE_MODIFY', 'STAGE_ID']
    }
    data = json.dumps(data)
    response = await client.post(url + 'crm.deal.list.json', headers=headers, data=data)
    response_content = response.content
    print(f"Response content: {response_content}")
    if response.status_code == 204:
        return response.status_code
    try:
        return response.json()
    except json.JSONDecodeError:
        print("Failed to decode JSON response")
        return None

async def post_lead(client, data):
    data = {
       'fields': {
              'TITLE': data.name.replace('На карте', ''),
              'ASSIGNED_BY_ID': data.user_id,
                #'ADDRESS': data.address.replace('На карте', ''),  
                'UF_CRM_PRICE' : data.price,
                 'CATEGORY_ID': 0,
                    'UF_CRM_URL': data.link,
                      'UF_CRM_SELLER': data.seller.replace('Автор объявления', ''),
                        'OPPORTUNITY': int(round(data.price * 0.03)),
                        'UF_CRM_PHONE': data.phone
       },

    }
    data = json.dumps(data)
    response = await client.post(url + 'crm.deal.add.json', headers=headers, data=data)
    response_content = response.content
    print(f"Response content: {response_content}")
    try:
        return response.json()
    except json.JSONDecodeError:
        print("Failed to decode JSON response")
        return None

async def patch_lead(client, data):
    data = {
        'id': data.lead_id,
          'fields': {
              'ASSIGNED_BY_ID': data.user_id,
                'STATUS_DESCRIPTION': ''
           }       
    }
    data = json.dumps(data)
    response = await client.patch(url + 'crm.deal.update', headers=headers, data=data)
    response_content = response.content
    print(f"Response content: {response_content}")
    try:
        return response.json()
    except json.JSONDecodeError:
        print("Failed to decode JSON response")
        return None

async def task(data, type, lead, start):
    async with httpx.AsyncClient() as client:
        if data and data.lead_id:
            tasks = [patch_lead(client, data)]
        elif data:
            tasks = [post_lead(client, data) for i in range(1)]
        elif type == 'users':
            tasks = [get_users(client) for i in range(1)]
        elif type == 'leads':
            tasks = [get_leads(client, start) for i in range(1)]
        elif type == 'filter':
            tasks = [check_mail(client) for i in range(1)]
        result = await asyncio.gather(*tasks)
        return result

@app.post('/api')
async def handle_request(request: Request):
    data = await request.json()
    lead = Lead(**data)
    start = time()
    output = await task(lead, None, None, None)
    print("time: ", time() - start)
    return output

@app.get('/api')
async def users(type: str | None = None, lead: str | None = None, start: str | None = None):
    #start = time()
    output = await task(None, type, lead, start)
    #print("time: ", time() - start)
    return output