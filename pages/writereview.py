import streamlit as st
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from langchain_together import TogetherEmbeddings
from pinecone import Pinecone
from together import Together
from datetime import datetime
import os
from textblob import TextBlob
from pymongo import MongoClient

# Set environment variables 
os.environ["TOGETHER_API_KEY"] = '466374da823b330f9c3220e7a00338f785e19267c3d73d1b46d5418eeeb2df20'

# Initialize Pinecone
pc = Pinecone(api_key='pcsk_6QU3Wn_TYSERjoUfwFhw9NqavXRWdHzEBfp2gJz61SgHAZn9YJ9qDLYXNgKsJFJXpewH1M')
index = pc.Index(host="https://hotel-reviews-f6ut8af.svc.aped-4627-b74a.pinecone.io")

# Initialize Together embedding model
embeddings = TogetherEmbeddings(
    model='togethercomputer/m2-bert-80M-8k-retrieval',
    together_api_key=os.environ["TOGETHER_API_KEY"]
)
# Initialize MongoDB connection
client = MongoClient("mongodb+srv://dhruvg0yal:r2XvD62cYiKHJ8Yh@cluster0.ghmci.mongodb.net/")
db = client["hotel_guests"]
reviews_collection = db["reviews_data"]

# Function to analyze sentiment of review text
def analyze_sentiment(review_text):
    analysis = TextBlob(review_text)
    # TextBlob polarity ranges from -1 (negative) to 1 (positive)
    sentiment_score = analysis.sentiment.polarity
    is_negative = sentiment_score < 0
    return {
        'score': sentiment_score,
        'is_negative': is_negative,
        'sentiment_label': 'negative' if is_negative else 'positive'
    }

# Function to send email notification to manager (ONLY IF THE GUEST IS CURRENTLY STAYING)
def send_email_notification(review_data, sentiment_info):
    sender_email = "intellgoyal@gmail.com"
    sender_password = "zmcp wvix gdvn hdjo"
    manager_email = "dhruvg096@gmail.com"
    
    # Create message
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = manager_email
    msg['Subject'] = "URGENT: Negative Review from Current Guest"

    body = f"""
    Dear Manager,

    A negative review has been submitted by a current guest:

    Customer ID: {review_data['customer_id']}
    Room Number: {review_data['room_number']}
    Rating: {review_data['Rating']}
    Review: {review_data['Review']}

    Sentiment Analysis:
    Score: {sentiment_info['score']:.2f} (Negative)

    This requires your IMMEDIATE ATTENTION as the guest is currently staying at the hotel.
    You may have an opportunity to address their concerns before checkout.
    
    🏨 Hotel
    """

    msg.attach(MIMEText(body, 'plain'))

    try:
        # Setup SMTP server
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        text = msg.as_string()
        server.sendmail(sender_email, manager_email, text)
        server.quit()
        return True
    except Exception as e:
        st.error(f"Email notification failed: {str(e)}")
        return False

# Streamlit UI
st.markdown("""
    <style>
        [data-testid="stSidebar"] {display: none !important;}
        [data-testid="stSidebarNav"] {display: none !important;}
        button[kind="icon"] {display: none !important;}
        [data-testid="collapsedControl"] {display: none !important;}
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center;'>Hotel Review Submission</h1>", unsafe_allow_html=True)

# Input form for customer review
with st.form("review_form"):
    customer_id = st.text_input("Customer ID")
    room_number = st.text_input("Room Number")
    rating = st.slider("Rating", 1, 10, 5)
    review = st.text_area("Your Review")
    currently_staying = st.checkbox("I am currently staying at the hotel")
    
    submitted = st.form_submit_button("Submit Review")
    
    if submitted:
        if not customer_id or not review or not room_number:
            st.error("Please fill in all required fields.")
        else:
            try:
                # Analyze sentiment of the review
                sentiment_info = analyze_sentiment(review)
                
                # Load existing data
                df = pd.read_excel('AI-Guest-Experience-Infosys/resources/reviews_data.xlsx')
                
                # Generate new review ID
                new_review_id = df['review_id'].max() + 1 if not df.empty else 1
                
                # Convert review_id to standard Python int
                new_review_id = int(new_review_id)

                # Current date in format YYYYMMDD
                today = datetime.now()
                date_str = int(today.strftime("%Y%m%d"))
                
                # Create new row for database
                new_review = {
                    'review_id': new_review_id,
                    'customer_id': customer_id,
                    'room_number': room_number,
                    'Review': review,
                    'Rating': rating,
                    'review_date': date_str,
                    'currently_staying': currently_staying,
                    'sentiment_score': sentiment_info['score'],
                    'sentiment_label': sentiment_info['sentiment_label']
                }
                
                # Insert data into MongoDB
                reviews_collection.insert_one(new_review)
                
                # Create embedding for the new review
                review_embedding = embeddings.embed_query(review)
                
                # Define metadata (include sentiment information)
                metadata = {
                    'review_id': str(new_review_id),
                    'customer_id': customer_id,
                    'room_number': room_number,
                    'Rating': rating,
                    'review_date': date_str,
                    'currently_staying': currently_staying,
                    'sentiment_score': sentiment_info['score'],
                    'sentiment_label': sentiment_info['sentiment_label']
                }
                
                # Upload to Pinecone
                index.upsert(
                    vectors=[
                        {
                            "id": f"review_{new_review_id}",
                            "values": review_embedding,
                            "metadata": metadata
                        }
                    ],
                )
                
                st.success("Your review has been submitted successfully!")
                
                # Display sentiment information
                sentiment_color = "red" if sentiment_info['is_negative'] else "green"
                st.markdown(f"<p style='color:{sentiment_color}'>Sentiment analysis: {sentiment_info['sentiment_label'].capitalize()} ({sentiment_info['score']:.2f})</p>", unsafe_allow_html=True)
                
                # Send email notification ONLY if the user is currently staying AND review is negative
                if currently_staying and sentiment_info['is_negative']:
                    if send_email_notification(new_review, sentiment_info):
                        st.info("The hotel manager has been notified of your urgent review.")
                    else:
                        st.warning("Could not notify the manager, but your review was saved.")
                        
            except Exception as e:
                st.error(f"Error submitting review: {str(e)}")

# Add a button to go back to customer portal
if st.button("Back to Customer Portal"):
    st.switch_page("pages/customerportal.py")