from fastapi import FastAPI, Request, Body
from pydantic import BaseModel
from time import time
import httpx
import asyncio
import json

app = FastAPI()

hostName = "localhost"
serverPort = 8080
#url = 'https://b24-002xma.bitrix24.ru/rest/1/g7hvqhdqpk69goyy/crm.lead.add.json'

headers = {
  'Accept' : 'application/json',
  'Content-Type': 'application/json'
}

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
    response = await client.get(url + 'users', headers=headers)
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
    response = await client.get(url + 'leads?filter[name]=' + name, headers=headers)
    response_content = response.content
    print(f"Response content: {response_content}")

    if response.status_code == 204:
        return response.status_code

    try:
        return response.json()
    except json.JSONDecodeError:
        print("Failed to decode JSON response")
        return None

async def get_leads(client, page):
    response = await client.get(url + 'leads?page=' + page + '&limit=250', headers=headers)
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
              'TITLE': data.name
       }
    }
    
    data = json.dumps(data)
    print(data)
    response = await client.post(url, headers=headers, data=data)
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
        'responsible_user_id': data.user_id,
        'custom_fields_values': [
            {'field_id': 897351, 'values': [
                {
                    "value": None
                }
            ]
            }  # Установка значения null для поля field_id: 897351
        ]
    }
    data = "[" + json.dumps(data) + "]"
    response = await client.patch(url + 'leads', headers=headers, data=data)
    response_content = response.content
    print(f"Response content: {response_content}")
    try:
        return response.json()
    except json.JSONDecodeError:
        print("Failed to decode JSON response")
        return None

async def task(data, type, lead, page):
    async with httpx.AsyncClient() as client:
        if data and data.lead_id:
            tasks = [patch_lead(client, data)]
        elif data:
            tasks = [post_lead(client, data) for i in range(1)]
        elif type == 'users':
            tasks = [get_users(client) for i in range(1)]
        elif type == 'leads':
            tasks = [get_leads(client, page) for i in range(1)]
        elif type == 'filter':
            tasks = [check_lead(client, lead) for i in range(1)]
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
async def users(type: str | None = None, lead: str | None = None, page: str | None = None):
    start = time()
    output = await task(None, type, lead, page)
    print("time: ", time() - start)
    return output
