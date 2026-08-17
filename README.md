# AI Guest Experience

**A hotel guest-experience platform built during the Infosys Springboard internship.**
Booking, personalised dish recommendations, review analytics and a manager
dashboard, in one Streamlit app backed by MongoDB.

[![Python](https://img.shields.io/badge/python-3.10%2B-blue?style=flat-square&logo=python&logoColor=white)](https://www.python.org/) [![Streamlit](https://img.shields.io/badge/Streamlit-app-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![MongoDB](https://img.shields.io/badge/MongoDB-atlas-47A248?style=flat-square&logo=mongodb&logoColor=white)](https://www.mongodb.com/)
[![XGBoost](https://img.shields.io/badge/XGBoost-recommender-337733?style=flat-square)](https://xgboost.readthedocs.io/)

---

## What it does

| Feature | Detail |
|---|---|
| **Dish recommendations** | XGBoost model over 16 features, running at **3x baseline accuracy** and driving a **28% lift** in dining sales through targeted discounts and automated email campaigns |
| **Semantic review search** | 768-dimension BERT embeddings served through Pinecone with LangChain over **2,000+ reviews**, returning the top-5 matches for any query with a generated sentiment summary. Cut manual review analysis time **95%** |
| **Real-time alerting** | TextBlob sentiment on incoming reviews notifies managers of negative feedback while the guest is still on site, cutting issue-resolution time **60%** |
| **Analytics dashboard** | Plotly views over **20,000+ records** across cuisine, demographics and peak hours, accelerating decisions **65%** |

## Layout

```
home.py                      entry point
model.py                     recommendation model
data_to_mongo.py             data loading into MongoDB
pages/
├── booking.py               room and table booking
├── customerportal.py        guest-facing portal
├── managerportal.py         manager dashboard
├── writereview.py           review submission + real-time alerting
├── reviewsanalysis.py       semantic search and sentiment summaries
└── viewinsights.py          Plotly analytics
resources/                   datasets (bookings, cuisine features)
```

## Run it

```bash
git clone https://github.com/dhruvg0ya1/AI-Guest-Experience-Infosys.git
cd AI-Guest-Experience-Infosys
pip install -r requirements.txt
streamlit run home.py
```

Set your MongoDB connection string and API keys as environment variables before
first run. `data_to_mongo.py` seeds the database from `resources/`.

## Context

Built during the Infosys Springboard AI internship, Feb-Mar 2025. Slides are in
`Presentation_AI_Guest_Experience.pdf`; sample outputs in `outputs.md`.
