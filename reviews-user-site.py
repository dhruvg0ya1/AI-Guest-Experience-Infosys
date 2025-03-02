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

# Set environment variables 
os.environ["TOGETHER_API_KEY"] = '<API KEY>'

# Initialize Pinecone
pc = Pinecone(api_key='<API KEY>')
index = pc.Index(host="<HOST URL>")

# Initialize Together embedding model
embeddings = TogetherEmbeddings(
    model='togethercomputer/m2-bert-80M-8k-retrieval',
    together_api_key=os.environ["TOGETHER_API_KEY"]
)

# Function to send email notification to manager
def send_email_notification(review_data):
    sender_email = "intellgoyal@gmail.com"
    sender_password = "zmcp wvix gdvn hdjo"
    manager_email = "dhruvg096@gmail.com"
    
    # Create message
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = manager_email
    msg['Subject'] = "New Real-Time Hotel Review Alert"
    
    # Email body
    body = f"""
    Dear Manager,
    
    A new review has been submitted by a current guest:
    
    Customer ID: {review_data['customer_id']}
    Room Number: {review_data['room_number']}
    Rating: {review_data['Rating']}
    Review: {review_data['Review']}
    
    This requires your immediate attention as it's from a guest currently staying at the hotel.
    
    Hotel Review System
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
                # Load existing data
                df = pd.read_excel('AI-Guest-Experience-Infosys/resources/reviews_data.xlsx')
                
                # Generate new review ID
                new_review_id = df['review_id'].max() + 1 if not df.empty else 1
                
                # Current date in format YYYYMMDD
                today = datetime.now()
                date_str = int(today.strftime("%Y%m%d"))
                
                # Create new row for dataframe
                new_review = {
                    'review_id': new_review_id,
                    'customer_id': customer_id,
                    'room_number': room_number,
                    'Review': review,
                    'Rating': rating,
                    'review_date': date_str,
                    'currently_staying': currently_staying
                }
                
                # Add to dataframe
                df = pd.concat([df, pd.DataFrame([new_review])], ignore_index=True)
                
                # Save updated dataframe
                df.to_excel('AI-Guest-Experience-Infosys/resources/reviews_data.xlsx', index=False)
                
                # Create embedding for the new review
                review_embedding = embeddings.embed_query(review)
                
                # Define metadata
                metadata = {
                    'review_id': str(new_review_id),
                    'customer_id': customer_id,
                    'room_number': room_number,
                    'Rating': rating,
                    'review_date': date_str,
                    'currently_staying': currently_staying
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
                
                # If customer is currently staying, send email notification
                if currently_staying:
                    if send_email_notification(new_review):
                        st.info("The hotel manager has been notified of your review.")
                    else:
                        st.warning("Could not notify the manager, but your review was saved.")
                        
            except Exception as e:
                st.error(f"Error submitting review: {str(e)}")
