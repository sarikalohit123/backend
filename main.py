from fastapi import FastAPI ,Request
from sqlalchemy import text
from database import engine 
from fastapi import  UploadFile, Form, File, Query
from typing import List
from fastapi.middleware.cors import CORSMiddleware
import shutil
import pandas as pd
import base64
import random
import string
import time
import os
import asyncio
import json


app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:5173'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*']

)

@app.get('/')
def start():
    return{'name':'lohit'}


@app.post('/login')
async def login_user(cred: Request):
    try:
        cred=await cred.json()
        print(f'creds:{cred}')
        username=cred.get('username')
        password=cred.get('password')
        print(f'user:{username} pswd: {password}')
        with engine.connect() as conn:
            print("Fetching users...")
            check_data = conn.execute(text(f"SELECT username, pswd FROM users where username = '{username}' and pswd = '{password}' ")).fetchall()
            print("Data from DB:", check_data[0])
            if check_data:
               print("user already in")
               check_cwms=conn.execute(text(f"select CWMS from users where username = '{check_data[0][0]}' and pswd = '{check_data[0][1]}'")).fetchall()
               print('checking cwms',check_cwms[0][0])
               if check_cwms[0][0]=='1':
                   return{"status":"true", "message":"CWMS created already"}
               else:
                   return{"status":"false", "message":"CWMS not created but registerd"}                   
            else:
                return { "status": "failed", "message": "Login failed" }

    except Exception as e:
        print(e)
        return {'status':"login failed", "message":e}


@app.post("/create_table")
def create_table_manually():
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(100) UNIQUE NOT NULL,
                pswd VARCHAR(100)  NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))

        conn.execute(text("""
            INSERT INTO users (username, pswd) VALUES
            ('admin@waregent', 'waregent123#')
        """))
        conn.commit()
    return {"message": "Table created successfully"}


@app.post('/getfiles')
async def uploadfile(myfile: list[UploadFile] = File(...), tablename : str = Form(...)):
    print(f'tablename: {tablename}')
    for i in myfile:
        # content= await i.read()
        # print(f'content:{content}')
        file_location=f'./uploads/{i.filename}'
        with open(file_location, 'wb') as buffer:
            shutil.copyfileobj(i.file,buffer)
    # await asyncio.sleep(5)
    result = gen_code(i.filename, tablename=tablename) 
    print('this is result: ',result)
    if result:          
        return result
    else:
        return{"status":"something went wrong"}


def gen_code(filename,tablename):
    try:
        file_path='./uploads'
        get_file=os.path.join(file_path,filename)
        ext=os.path.splitext(get_file)[1].lower()
        print(f'ext:{ext}')
        if ext == ".xlsx":
            ds=pd.read_excel(f'./uploads/{filename}')
        elif ext == '.csv':
            ds=pd.read_csv(f'./uploads/{filename}')
        else:
            print('invaild file')

        data=pd.DataFrame(ds)
        print(data.shape)

        check_column=data.columns.to_list()
        print(check_column)

        print(f'length of sheeet: {len(data)}')
        unique_code=[]
        for i in range(len(data)):
            st=random.choices(string.ascii_uppercase, k=2)
            nu=random.choices(string.digits, k=3)
            uc= "".join(st+nu)
            if unique_code != uc:
                unique_code.append(uc)
            else:
                print('already exist')
                continue
        # print(unique_code)
        # print(len(unique_code))
        # print(unique_code)
        # print(data)
        
        data.insert(1,'unique_code',unique_code)
        with engine.connect() as conn_:
            try:
                data.to_sql(f'{tablename}', con=conn_ , index=False)
                print('Data uploaded sucessfully...')
                status_msg = {"status": "file uploaded"}
            except Exception as e:
                print(e)
                return {'status':f'{e}'}
        with engine.connect()as con:
            try:
                con.execute(text(f"update users set CWMS = {'true'} where username = '{tablename.split('_')[0]}'"))
                con.commit()
            except Exception as e:
                return {"status":f"{e}"}
        folder_path='./uploads'
        for item in os.listdir(folder_path):
            item_path = os.path.join(folder_path, item)
            print(f'this is item_path:{item_path}')

            try:
                if os.path.isfile(item_path) or os.path.islink(item_path):
                    os.remove(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
            except Exception as e:
                print(f"⚠️ Failed to delete '{item_path}': {e}")
                return {"status":f'{e}'}

        print(f"✅ Folder '{folder_path}' has been emptied.")

        return status_msg
    except Exception as e:
        print(e)
        return {"status":f'{e}'}


@app.get('/get_table')
def get_user_table(uid: str):
    print('uid from react ',uid)
    usertables=[]
    print("fetching all tables")
    with engine.connect() as conn:
        tables=conn.execute(text(f"show tables")).fetchall()
        print(tables)
        for i in tables:
            if uid in i[0]:
                usertables.append(i[0])
        u_table=usertables[0]
        # print(u_table)
        user_table=conn.execute(text(f"select * from `{u_table}` "))
        columns = user_table.keys()
        rows = user_table.fetchall()

        # test_table=[dict(zip(columns,rows))]
        # print(f'this is test_table: {test_table}')
        # for i in rows:
        #     print(i)
        final_table=[dict(zip(columns,row)) for row in rows]
        # print(final_table)

    print(f'total res: {usertables}')
    return{'status':"fetched", "table_Data":final_table}


@app.get('/table_check')
def table_check(uid: str):
    print('this i uid from table_check: ', uid)
    with engine.connect() as conn:
        res= conn.execute(text(f'select CWMS from users where username ="{uid}"')).fetchall()
        print(f'res: {res}')
        if(res[0][0]=='1'):
            return{'status':'table_checked'}
        else:
            return{'status':'table_unchecked'}
        

@app.post('/selectedrows')
async def selectedrows(req:Request):
    print("working on selected rows...")
    mydata= await req.json()
    mylist=mydata.get('rowsdata')
    formatted_list = ",".join(f"'{i}'" for i in mylist)

    # print(f'this is a list : {mylist}')
    usertables2=[]
    with engine.connect()as conn:
        tables = conn.execute(text(f"show tables")).fetchall()
        print(tables)
        for i in tables:
            if mydata.get('uid') in i[0]:
                usertables2.append(i[0])
        # print(f"final res table of selectedrows{usertables2}")
        fetch_table= conn.execute(text(f"select * from `{usertables2[0]}` where unique_code in ({formatted_list})"))
        keys=fetch_table.keys()
        values=fetch_table.fetchall()

        fina_table_res=[dict(zip(keys,i)) for i in values]

        return{'status':200,"data":fina_table_res}



@app.post('/editrows')
async def editrows(req:Request):
    data=await req.json()
    usertables2=[]
    with engine.connect() as conn:
        tables = conn.execute(text(f"show tables")).fetchall()
        for i in tables:
            if data.get('uid') in i[0]:
                usertables2.append(i[0])
        for row in data.get('rowsdata'):
            for col,val in row.items():
               conn.execute(text(
                    f"UPDATE `{usertables2[0]}` SET {col} = :val WHERE unique_code = :code"
                ), {"val": val, "code": row["unique_code"]})

        conn.commit()

    return{
        'status':200, 'data':'successfully updated'
    }


