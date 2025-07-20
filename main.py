from fastapi import FastAPI ,Request, Response
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
import io



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
    


@app.post("/signup")
async def create_new_user(usr: Request):
    try:
        cred=await cred.json()
        print(f'creds:{cred}')
        username=cred.get('username')
        email=cred.get('email')
        password=cred.get('password')
        print(f'user:{username} email: {email}')
        with engine.connect() as conn:
            print("Fetching users...")
            check_data = conn.execute(text(f"INSERT INTO users (username, email, pswd) VALUES({username},{email},{password})"))
            conn.commit()
            if check_data:
                return{"status":"200", "message":"user added"}                   
            else:
                return { "status": "failed", "message": "signup failed" }

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
async def uploadfile(
        myfile: List[UploadFile] = File(...),
        tablename: str = Form(...)
        ):
    print(f'tablename: {tablename}')

    for uploaded_file in myfile:
        content = await uploaded_file.read()
        filename = uploaded_file.filename
        ext = os.path.splitext(filename)[1].lower()

        if ext == ".xlsx":
            df = pd.read_excel(io.BytesIO(content))
        elif ext == ".csv":
            df = pd.read_csv(io.BytesIO(content))
        else:
            return {"status": f"Unsupported file type: {ext}"}

        result = gen_code(df, tablename, filename)
        if not result.get("status", "").startswith("file uploaded"):
            return result

    return {"status": "All files uploaded successfully"}


def gen_code(data: pd.DataFrame, tablename: str, filename: str):
    try:
        print(f"Processing: {filename}")
        print(f"Shape: {data.shape}")
        print(f"Columns: {data.columns.tolist()}")

        # Add SLNO and unique_code
        unique_codes = set()
        code_list = []
        SLNO = list(range(len(data)))

        while len(code_list) < len(data):
            st = ''.join(random.choices(string.ascii_uppercase, k=2))
            nu = ''.join(random.choices(string.digits, k=3))
            uc = st + nu
            if uc not in unique_codes:
                unique_codes.add(uc)
                code_list.append(uc)

        data.insert(1, 'unique_code', code_list)

        # Save to DB
        with engine.begin() as conn:
            data.to_sql(tablename, con=conn, index=False, if_exists='replace')

            conn.execute(text(
                f"ALTER TABLE {tablename} ADD COLUMN SLNO INT AUTO_INCREMENT PRIMARY KEY"
            ))

        # Update users table
        with engine.begin() as conn:
            conn.execute(text(
                f"UPDATE users SET CWMS = 1 WHERE username = '{tablename.split('_')[0]}'"
            ))

        print("file uploaded")
        return {"status": "file uploaded"}
    except Exception as e:
        print(f"Error: {e}")
        return {"status": str(e)}



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
        user_table=conn.execute(text(f"select * from `{u_table}` Order by SLNO Desc"))
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

@app.post('/addrow')
async def addrow(req:Request):
    data=await req.json()
    print(f"this is new row_data: {data['new_data']}")
    usertables2=[]
    with engine.connect() as conn:
        tables = conn.execute(text(f"show tables")).fetchall()
        for i in tables:
            if data.get('uid') in i[0]:
                usertables2.append(i[0])
        print(f"this is user_table:{usertables2}")
        u_codes=conn.execute(text(f"select unique_code from `{usertables2[0]}` ")).fetchall()
        Existing_unique_codes=[i[0] for i in u_codes]
        print(Existing_unique_codes)
        st=random.choices(string.ascii_uppercase, k=2)
        nu=random.choices(string.digits, k=3)
        uc= "".join(st+nu)
        new_uc=""
        if uc not in Existing_unique_codes:
            new_uc=uc
            data['new_data']['unique_code']=uc
            print(f"this is new uc: {new_uc}")
        else:
            new_uc="CWMS_$"

        keyss=data['new_data'].keys()
        print(f"keyss:{keyss}")
        values = data['new_data'].values()
        safe_values = ', '.join(f"'{str(v)}'" for v in values)
        print(safe_values)
        print(type(safe_values))
        try:
            query = f"INSERT INTO `{usertables2[0]}` ({', '.join(data['new_data'].keys())}) VALUES ({safe_values})"
            
            conn.execute(text(query))
            conn.commit()
            return{'':200,'response':'success'}

        except Exception as e:
            return{'status':400,'response':'failed'}


@app.post("/download-template-csv")
async def download_csv(req:Request):
    data=await req.json()
    uid=data['uid']
    usertables=[]
    with engine.connect() as conn:
        tables=conn.execute(text(f"show tables")).fetchall()
        print(tables)
        for i in tables:
            if uid in i[0]:
                usertables.append(i[0])
        u_table=usertables[0]
        # print(u_table)
        user_table=conn.execute(text(f"select * from `{u_table}` Order by SLNO Desc"))
        columns = user_table.keys()
        columns=[i for i in columns if i  not in ('SLNO', 'unique_code')]

    df=pd.DataFrame(columns=columns)
    csv_data = df.to_csv(index=False)
 
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=template.csv"}
    )

@app.post('/addnewfile')
async def uploadnewfile(
    mynewfile: List[UploadFile] = File(...),
    uid: str = Form(...)
):
    print(f"this is user_id: {uid}")
    for i in mynewfile:
        content = await i.read()
        result = store_file_from_memory(content, i.filename, uid)
        if not result or result.get("status") != 200:
            return {"status": "something went wrong"}
    return {"status": 200, "message": "Files inserted successfully"}


def store_file_from_memory(file_content, filename, uid):
    try:
        ext = os.path.splitext(filename)[1].lower()
        print(f'ext: {ext}')
        if ext == ".xlsx":
            ds = pd.read_excel(io.BytesIO(file_content))
        elif ext == ".csv":
            ds = pd.read_csv(io.BytesIO(file_content))
        else:
            return {"status": 400, "error": "Invalid file type"}

        data = pd.DataFrame(ds)
        print(f"Data shape: {data.shape}")
        check_rows = data.to_dict(orient='records')

        # Get the user's table
        usertables = []
        with engine.connect() as conn:
            tables = conn.execute(text("SHOW TABLES")).fetchall()
            for t in tables:
                if uid in t[0]:
                    usertables.append(t[0])
            if not usertables:
                return {"status": 404, "error": "User table not found"}
            u_table = usertables[0]

            # Get existing unique_codes
            existing_codes = conn.execute(
                text(f"SELECT unique_code FROM `{u_table}`")
            ).fetchall()
            existing_codes = {row[0] for row in existing_codes}

        # Generate and insert unique_code
        all_unique_codes = set()
        for i, row in enumerate(check_rows):
            while True:
                code = ''.join(random.choices(string.ascii_uppercase, k=2) + random.choices(string.digits, k=3))
                if code not in existing_codes and code not in all_unique_codes:
                    row['unique_code'] = code
                    all_unique_codes.add(code)
                    break
                # Optional: add retry cap

        insert_keys = check_rows[0].keys()
        print(f"Inserting into table: {u_table}")
        print(f"Keys: {insert_keys}")

        with engine.begin() as conn:
            for row in check_rows:
                cleaned_row = {k: (None if str(v).lower() == 'nan' else v) for k, v in row.items()}
                placeholders = ", ".join([f":{key}" for key in cleaned_row])
                query = text(f"""
                    INSERT INTO `{u_table}` ({', '.join(cleaned_row)})
                    VALUES ({placeholders})
                """)
                conn.execute(query, cleaned_row)

        print("Rows inserted successfully.")
        return {"status": 200, "response": "success"}

    except Exception as e:
        print(f"Error: {e}")
        return {"status": 500, "error": str(e)}