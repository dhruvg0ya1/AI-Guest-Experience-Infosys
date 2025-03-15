from pymongo import MongoClient
import pandas as pd

client = MongoClient("mongodb+srv://dhruvg0yal:r2XvD62cYiKHJ8Yh@cluster0.ghmci.mongodb.net/")

db = client["hotel_guests"]

df = pd.read_excel('AI-Guest-Experience-Infosys/resources/reviews_data.xlsx')

if "Unnamed: 0" in df.columns:
    df.drop("Unnamed: 0", axis=1, inplace=True)

collection = db["reviews_data"]

collection.insert_many(df.to_dict(orient="records"))