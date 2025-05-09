from fastapi import FastAPI
from sqlalchemy import text
from database import engine 
from fastapi import  UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import shutil
import pandas as pd
import base64
import random
import string



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



@app.post("/create_table")
def create_table_manually():
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))
        conn.commit()
    return {"message": "Table created successfully"}


@app.post('/getfiles')
async def uploadfile(myfile: list[UploadFile] = File(...)):
    for i in myfile:
        # content= await i.read()
        # print(f'content:{content}')
        file_location=f'./uploads/{i.filename}'
        with open(file_location, 'wb') as buffer:
            shutil.copyfileobj(i.file,buffer)
            
    return{"filename":i.filename}

# ds=pd.read_csv('./uploads/test.csv')
ds=pd.read_excel('./uploads/orders_data.xlsx')
data=pd.DataFrame(ds)
# print(data['order_no'])
# print(data)
# for i in data.iterrows():
#     print(i)
print(data.shape)
# print(data.loc[1,['order_no','item_total']])
# print(data.loc[30:40:2,['order_no','item_total']])

check_column=data.columns.to_list()
print(check_column)

print(f'length of sheeet: {len(data)}')
unique_code=[]

def gen_code():
    for i in range(len(data)):
        st=random.choices(string.ascii_uppercase, k=2)
        nu=random.choices(string.digits, k=3)
        uc= "".join(st+nu)
        if unique_code != uc:
            unique_code.append(uc)
        else:
            print('already exist')
            continue
    print(unique_code)
    print(len(unique_code))
    data.insert(1,'unique_code',unique_code)
    with engine.connect() as conn_:
        try:
            data.to_sql('orders_data', con=conn_ , index=True)
            print('Data uploaded sucessfully...')
        except Exception as e:
            print(e)
            

gen_code()

print(unique_code)
print(data)
