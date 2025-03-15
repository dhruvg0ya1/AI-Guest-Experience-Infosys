import streamlit as st
import pandas as pd
from langchain_together import TogetherEmbeddings
from pinecone import Pinecone
from together import Together
import os

# Set environment variables 
os.environ["TOGETHER_API_KEY"] = '466374da823b330f9c3220e7a00338f785e19267c3d73d1b46d5418eeeb2df20'

# Load data
df = pd.read_excel('AI-Guest-Experience-Infosys/resources/reviews_data.xlsx')

# Initialize Pinecone
pc = Pinecone(api_key='pcsk_6QU3Wn_TYSERjoUfwFhw9NqavXRWdHzEBfp2gJz61SgHAZn9YJ9qDLYXNgKsJFJXpewH1M')
index = pc.Index(host="https://hotel-reviews-f6ut8af.svc.aped-4627-b74a.pinecone.io")

# Initialize Together embedding model
embeddings = TogetherEmbeddings(
    model='togethercomputer/m2-bert-80M-8k-retrieval',
    together_api_key=os.environ["TOGETHER_API_KEY"]
)

# Initialize Together client
client = Together(api_key=os.environ["TOGETHER_API_KEY"])

# Hide Streamlit's sidebar and default elements & Make buttons full width
st.markdown("""
    <style>
        [data-testid="stSidebar"] {display: none !important;}
        [data-testid="stSidebarNav"] {display: none !important;}
        button[kind="icon"] {display: none !important;}
        [data-testid="collapsedControl"] {display: none !important;}
        
        /* Center-align everything */
        .center {text-align: center !important;}

        /* Make buttons full-width */
        .stButton>button {
            width: 100% !important;
            padding: 12px !important;
            font-size: 16px !important;
            border-radius: 8px !important;
            display: block !important;
        }
    </style>
""", unsafe_allow_html=True)

# Center title
st.markdown("<h1 class='center'>Hotel Customers' Reviews Analysis</h1>", unsafe_allow_html=True)

# Input fields
query = st.text_input("Enter a query about customer reviews:", "How is the food quality?")

# 🔥 **Put Start Date & End Date in the Same Line**
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("Start Date")
with col2:
    end_date = st.date_input("End Date")

rating_filter = st.slider("Select Rating Filter", 1, 10, (1, 10))

# Center the button
if st.button("🔍 Analyze Reviews", key="analyze_button"):
    query_embedding = embeddings.embed_query(query)

    start_date_str = int(start_date.strftime("%Y%m%d"))
    end_date_str = int(end_date.strftime("%Y%m%d"))

    results = index.query(
        vector=query_embedding,
        top_k=5,
        namespace="",
        filter={
            "review_date": {"$gte": start_date_str, "$lte": end_date_str},
            "Rating": {"$gte": rating_filter[0], "$lte": rating_filter[1]}
        },
        include_metadata=True
    )

    matches = results["matches"]

    if not matches:
        st.warning("No matching reviews found")
    else:
        matched_ids = [int(match["metadata"]["review_id"]) for match in matches if "metadata" in match and "review_id" in match["metadata"]]

        if matched_ids:
            req_df = df[df["review_id"].isin(matched_ids)]

            if not req_df.empty:
                concatenated_reviews = " ".join(req_df["Review"].tolist())

                response = client.chat.completions.create(
                    model="meta-llama/Llama-Vision-Free",
                    messages=[{
                        "role": "user",
                        "content": f"""
                        Briefly summarize the overall sentiment of customers based on these reviews - 
                        {concatenated_reviews} and query of the manager {query}.
                        Stick to specific query of manager, and keep it concise.
                        Do not mention the name of the hotel.
                        """}]
                )

                st.subheader("Review Analysis")
                st.write(response.choices[0].message.content)

                st.subheader("Matching Reviews")
                st.dataframe(req_df[["Review", "Rating"]], use_container_width=True)
            else:
                st.warning("No matching reviews found in the dataset")
        else:
            st.warning("Could not extract review IDs from the matches")

# Full-width "Back to Manager Portal" button
if st.button("⬅️ Back to Manager Portal", key="back_button"):
    st.switch_page("pages/managerportal.py")