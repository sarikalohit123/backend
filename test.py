# import os
# print(os.path.getsize('./uploads/orders_data.xlsx'))  # Should be more than 0


# mylist=['UW980','KW059','JX969']

# singledata=",".join(f"'{i}'" for i in mylist)

# print(singledata)
# print(formatted_list)

# data=[{'order_no': '405-9763961-5211537', 'unique_code': 'UW980', 'order_date': 'Sun, 18 Jul, 2021, 10:38 pm IST', 'buyer': 'Mr.', 'ship_city': 'CHANDIGARH,', 'ship_state': 'CHANDIGARH', 'sku': 'SKU:  2X-3C0F-KNJE', 'description': "100% Leather Elephant Shaped Piggy Coin Bank | Block Printed West Bengal Handicrafts (Shantiniketan Art) | Money Bank for Kids | Children's Gift Ideas", 'quantity': 1, 'item_total': '₹449.00', 'shipping_fee': None, 'cod': None, 'order_status': 'Delivered to buyer'},{'order_no': '405-976343961-5211537', 'unique_code': 'zW980', 'order_date': 'Sun, 18 Jul, 2021, 10:38 pm IST', 'buyer': 'Mr.', 'ship_city': 'CHANDIGARH,', 'ship_state': 'CHANDIGARH', 'sku': 'SKU:  2X-3C0F-KNJE', 'description': "100% Leather Elephant Shaped Piggy Coin Bank | Block Printed West Bengal Handicrafts (Shantiniketan Art) | Money Bank for Kids | Children's Gift Ideas", 'quantity': 1, 'item_total': '₹449.00', 'shipping_fee': None, 'cod': None, 'order_status': 'Delivered to buyer'}]
# keyss=[]
# values=[]
# for i in data:
#     for k,v in i.items():
#         print(f'{k}  -  {v} where uniq = {i["unique_code"]}')



import pandas as pd

data = {
    "Name": ["Alice", "Bob"],
    "Age": [30, 25],
    "City": ["New York", "San Francisco"]
}

df = pd.DataFrame(data)
df.to_excel("data.xlsx", index=False)

print("Excel file created successfully!")
