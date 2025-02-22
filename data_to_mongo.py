from pymongo import MongoClient
import pandas as pd

client = MongoClient("mongodb+srv://dhruvg0yal:dhruv17goyal@cluster0.ghmci.mongodb.net/")

db = client["hotel_guests"]

df = pd.read_excel('AI-Guest-Experience-Infosys/dining_info.xlsx')

df.drop('Unnamed: 0',axis=1,inplace=True)

collection = db["dining_info"]

collection.insert_many(df.to_dict(orient="records"))