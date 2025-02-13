from fastapi import FastAPI, Request, Body
from pydantic import BaseModel
from time import time
import httpx
import asyncio
import json

app = FastAPI()

hostName = "localhost"
serverPort = 8080
url = 'https://evervale.amocrm.ru/api/v4/'
bearer = 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImp0aSI6ImJmNDgxMTMyOWMwNDA1MmI5YmQ1OGU4MWU0MTYzZmU1ZDg4ZWE3ZDZlODBhNzZlNjY0OWMyYmFiN2VkNTc0ZGI1MDA5OTBmZTI5MGVlMWI5In0.eyJhdWQiOiIyNGVjM2VkMS05ZTk3LTQ3MjItOGZmZC0xMzcxZjlhMTA4ZTAiLCJqdGkiOiJiZjQ4MTEzMjljMDQwNTJiOWJkNThlODFlNDE2M2ZlNWQ4OGVhN2Q2ZTgwYTc2ZTY2NDljMmJhYjdlZDU3NGRiNTAwOTkwZmUyOTBlZTFiOSIsImlhdCI6MTczMTE1OTIyMSwibmJmIjoxNzMxMTU5MjIxLCJleHAiOjE3OTg3NjE2MDAsInN1YiI6IjExMjgyMjU4IiwiZ3JhbnRfdHlwZSI6IiIsImFjY291bnRfaWQiOjMxODUyMzY2LCJiYXNlX2RvbWFpbiI6ImFtb2NybS5ydSIsInZlcnNpb24iOjIsInNjb3BlcyI6WyJjcm0iLCJmaWxlcyIsImZpbGVzX2RlbGV0ZSIsIm5vdGlmaWNhdGlvbnMiLCJwdXNoX25vdGlmaWNhdGlvbnMiXSwiaGFzaF91dWlkIjoiMzk5YzM2YWUtMTkzOC00NDEyLWFiNjktY2ExOGFmN2VhYjYzIiwiYXBpX2RvbWFpbiI6ImFwaS1iLmFtb2NybS5ydSJ9.FKSCBBvEfdiAjF-YKDee8vbWTbp-pXOqzL3bm34Ms5gjAexB7JJBZmmRy1lMM9RVFAGzojimV3qljQ3xBc5whNgzBV3iDXB10niql9ugKqMWFAoPpBcFzmAmq65-YDG2jlXnMVs-csXw0YATqHFVfdppNX6tBCublwJkaXs2n5yPtb5Sl02TRoBNYPRTS5fhtsuUcjJEUYL07AlwllwWtdamyZgaZzpB52HfQ6vcwSR-zjyMdYY2hfY6j64wCerQ8BnfvqiI_1LYx-aKzIRo4Noxyfni8GESqyIYzqBllqcsdcIdvNQ0cRy65hDh7iYk6cR1VDbwMLf8UgnlMaCqpA'
headers = {
  'User-Agent': 'My App v1.0',
  'Authorization': bearer,
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
    # Убираем пробелы из строки и конвертируем в целое число
    price_value = int(str(data.price).replace(" ", "")) if data.price else 0  # Убедимся, что price — это int
    custom_field_value = int(round(data.price * 0.03)) if data.price else 0  # Округляем результат до целого числа

    data = {
       'name': data.name,
       'price': custom_field_value,  # Здесь цена с пробелами, преобразованная в целое число
       'responsible_user_id': data.user_id,
       'pipeline_id': pipeline_id,  # Использование глобальной переменной
       'custom_fields_values': [
           {'field_id': 901863, 'values': [{'enum_id': 1637499}]},
           {'field_id': 840025, 'values': [{'enum_id': 606855}]},
           {'field_id': 838641, 'values': [{'value': data.link}]},
           {'field_id': 923969, 'values': [{'value': price_value}]},  # Сюда передаем цену как целое число
           {'field_id': 923963, 'values': [{'value': data.address}]},
           # Удалено проблемное поле для проверки ошибки
           # {'field_id': 897279, 'values': [{'value': data.phone}]},
           {'field_id': 923965, 'values': [{'value': data.seller}]}
       ]
    }
    data = "[" + json.dumps(data) + "]"
    response = await client.post(url + 'leads', headers=headers, data=data)
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
