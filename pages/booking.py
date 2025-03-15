import streamlit as st
from datetime import date
import pandas as pd
import joblib
import xgboost
import numpy as np
from sklearn.preprocessing import LabelEncoder
from pymongo import MongoClient
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def show():
    # Hide sidebar, sidebar navigation, and sidebar toggle button
    st.markdown("""
        <style>
            [data-testid="stSidebar"] {display: none !important;}
            [data-testid="stSidebarNav"] {display: none !important;}
            button[kind="icon"] {display: none !important;}
            [data-testid="collapsedControl"] {display: none !important;}
        </style>
    """, unsafe_allow_html=True)

    # Initialize MongoDB connection
    client = MongoClient("mongodb+srv://dhruvg0yal:r2XvD62cYiKHJ8Yh@cluster0.ghmci.mongodb.net/")
    db = client["hotel_guests"]
    bookings_collection = db["bookings_data"]

    # Define DataFrame structure
    columns = ['customer_id', 'Preferred Cuisine', 'age', 'check_in_date', 'check_out_date']
    data = pd.DataFrame(columns=columns)

    # Center Title
    st.markdown("<h1 style='text-align: center; font-size: 50px;'>🏨 Hotel Booking Form</h1>", unsafe_allow_html=True)

    # Customer ID handling
    st.markdown("<p style='font-size:14px;'>Do you have a Customer ID?</p>", unsafe_allow_html=True)
    col1, col2 = st.columns([1, 1])
    with col1:
        yes_customer = st.button("Yes", key="yes_customer")
    with col2:
        no_customer = st.button("No", key="no_customer")
    if "customer_id_choice" not in st.session_state:
        st.session_state.customer_id_choice = None
    if yes_customer:
        st.session_state.customer_id_choice = "Yes"
    if no_customer:
        st.session_state.customer_id_choice = "No"
    if st.session_state.customer_id_choice == "Yes":
        customer_id = st.text_input("Enter your Customer ID", "", key="customer_id_input")
    elif st.session_state.customer_id_choice == "No":
        max_customer = bookings_collection.find_one(sort=[("customer_id", -1)])
        customer_id = max_customer["customer_id"] + 1 if max_customer else 10001
        st.markdown(f"Your assigned Customer ID: **{customer_id}**")

    # Collect user input
    age = st.number_input("Enter your age", min_value=18, step=1, key="age")

    col1, col2 = st.columns(2)
    with col1:
        checkin_date = st.date_input("Check-in date", min_value=date.today(), key="checkin_date")
    with col2:
        checkout_date = st.date_input("Check-out date", min_value=checkin_date, key="checkout_date")

    stayers = st.number_input("How many people are staying?", min_value=1, max_value=3, step=1, key="stayers")

    preferred_cuisine = st.selectbox("Preferred cuisine", ["South Indian", "North Indian", "Multi"], key="cuisine")

    st.markdown("<p style='font-size:14px;'>Do you want to book through points?</p>", unsafe_allow_html=True)
    col3, col4 = st.columns([1, 1])
    with col3:
        yes_points = st.button("Yes", key="yes_points")
    with col4:
        no_points = st.button("No", key="no_points")

    if "preferred_booking" not in st.session_state:
        st.session_state.preferred_booking = None
    if yes_points:
        st.session_state.preferred_booking = "Yes"
    if no_points:
        st.session_state.preferred_booking = "No"
    preferred_booking = st.session_state.preferred_booking

    special_requests = st.text_area("Any special requests? (Optional)", "", key="requests")
    
    # Email address for sending confirmation
    email_address = st.text_input("Enter your email for booking confirmation", "", key="email_input")

    # Handle form submission
    if st.button("Submit Booking", key="submit"):
        if customer_id:
            # Prepare booking data
            new_data = {
                'customer_id': customer_id,
                'Preferred Cusine': preferred_cuisine,
                'age': age,
                'check_in_date': checkin_date,
                'check_out_date': checkout_date,
                'booked_through_points': preferred_booking,
                'number_of_stayers': stayers
            }
            new_df = pd.DataFrame([new_data])

            # Data preprocessing
            new_df['booked_through_points'] = new_df['booked_through_points'].apply(lambda x: 1 if x == 'Yes' else 0)
            new_df['customer_id'] = new_df['customer_id'].astype(int)
            new_df['check_in_date'] = pd.to_datetime(new_df['check_in_date'])
            new_df['check_out_date'] = pd.to_datetime(new_df['check_out_date'])

            # Store booking in MongoDB
            bookings_collection.insert_one(new_df.iloc[0].to_dict())

            # Feature engineering
            new_df['check_in_day'] = new_df['check_in_date'].dt.dayofweek
            new_df['check_out_day'] = new_df['check_out_date'].dt.dayofweek
            new_df['check_in_month'] = new_df['check_in_date'].dt.month
            new_df['check_out_month'] = new_df['check_out_date'].dt.month
            new_df['stay_duration'] = (new_df['check_out_date'] - new_df['check_in_date']).dt.days

            # Load additional feature data
            customer_features = pd.read_excel('AI-Guest-Experience-Infosys/resources/customer_features.xlsx')
            customer_dish = pd.read_excel('AI-Guest-Experience-Infosys/resources/customer_fav_dish.xlsx')
            cuisine_features = pd.read_excel('AI-Guest-Experience-Infosys/resources/cuisine_features.xlsx')
            cuisine_dish = pd.read_excel('AI-Guest-Experience-Infosys/resources/cuisine_popular_dish.xlsx')

            # Data type conversion and merging
            data['customer_id'] = data['customer_id'].astype(int)
            customer_features['customer_id'] = customer_features['customer_id'].astype(int)
            customer_dish['customer_id'] = customer_dish['customer_id'].astype(int)

            # Merge all features
            new_df = new_df.merge(customer_features, on='customer_id', how='left')
            new_df = new_df.merge(cuisine_features, on='Preferred Cusine', how='left')
            new_df = new_df.merge(customer_dish, on='customer_id', how='left')
            new_df = new_df.merge(cuisine_dish, on='Preferred Cusine', how='left')

            # Remove unnecessary columns
            new_df.drop(['customer_id', 'check_in_date', 'check_out_date'], axis=1, inplace=True)

            # Encode categorical variables
            encoder = joblib.load('AI-Guest-Experience-Infosys/resources/encoder.pkl')
            categorical_cols = ['Preferred Cusine', 'customer_fav_dish', 'cuisine_popular_dish']
            encoded_test = encoder.transform(new_df[categorical_cols])
            encoded_test_df = pd.DataFrame(
                encoded_test, columns=encoder.get_feature_names_out(categorical_cols))
            new_df = pd.concat([new_df.drop(columns=categorical_cols), encoded_test_df], axis=1)

            # Load model features and label encoder
            features = list(pd.read_excel('AI-Guest-Experience-Infosys/resources/features.xlsx')[0])
            label_encoder = joblib.load('AI-Guest-Experience-Infosys/resources/label_encoder.pkl')
            new_df = new_df[features]

            # Make predictions
            model = joblib.load('AI-Guest-Experience-Infosys/resources/xgb_model.pkl')
            y_pred_prob = model.predict_proba(new_df)
            dish_names = label_encoder.classes_

            # Process prediction probabilities
            prob_df = pd.DataFrame(y_pred_prob, columns=dish_names)
            top_3_indices = np.argsort(-y_pred_prob, axis=1)[:, :3]
            top_3_dishes = dish_names[top_3_indices]
            prob_df["top_1"] = top_3_dishes[:, 0]
            prob_df["top_2"] = top_3_dishes[:, 1]
            prob_df["top_3"] = top_3_dishes[:, 2]

            # Display booking confirmation
            st.success(f"✅ Booking Confirmed!")
            st.write("📝 **Booking Details:**")
            st.write(f"**Customer ID:** {customer_id}")
            st.write(f"**Check-in:** {checkin_date}")
            st.write(f"**Age:** {age}")
            st.write(f"**Check-out:** {checkout_date}")
            st.write(f"**Preferred Cuisine:** {preferred_cuisine}")
            if special_requests:
                st.write(f"**Special Requests:** {special_requests}")

            # Process and display dish recommendations
            dishes = [
                prob_df["top_1"].iloc[0],
                prob_df["top_2"].iloc[0],
                prob_df["top_3"].iloc[0]
            ]

            # Separate thali and non-thali dishes
            thali_dishes = [dish for dish in dishes if "Thali" in dish]
            other_dishes = [dish for dish in dishes if "Thali" not in dish]

            # Display recommended dishes with discounts
            st.subheader("🍽️ Discounts for You:")
            for dish in dishes:
                if dish in thali_dishes:
                    st.write(f"✅ **{dish}** - 🎉 20% OFF!")
                else:
                    st.write(f"✅ **{dish}** - 🎉 15% OFF!")
            
            # Send confirmation email
            if email_address:
                try:
                    # Email credentials
                    sender_email = "intellgoyal@gmail.com"
                    sender_password = "zmcp wvix gdvn hdjo"
                    
                    # Create message
                    msg = MIMEMultipart()
                    msg['From'] = sender_email
                    msg['To'] = email_address
                    msg['Subject'] = f"Hotel Booking Confirmation - Customer ID: {customer_id}"
                    
                    # Email body
                    body = f"""
                    <html>
                    <body>
                    <h2>🏨 Hotel Booking Confirmation</h2>
                    <p><b>Booking Details:</b></p>
                    <ul>
                        <li><b>Customer ID:</b> {customer_id}</li>
                        <li><b>Check-in Date:</b> {checkin_date}</li>
                        <li><b>Check-out Date:</b> {checkout_date}</li>
                        <li><b>Preferred Cuisine:</b> {preferred_cuisine}</li>
                        <li><b>Number of Guests:</b> {stayers}</li>
                    """
                    
                    if special_requests:
                        body += f"<li><b>Special Requests:</b> {special_requests}</li>"
                    
                    body += """
                    </ul>
                    <p><b>🍽️ Special Dish Discounts:</b></p>
                    <ul>
                    """
                    
                    for dish in dishes:
                        if "Thali" in dish:
                            body += f"<li><b>{dish}</b> - 20% OFF!</li>"
                        else:
                            body += f"<li><b>{dish}</b> - 15% OFF!</li>"
                    
                    body += """
                    </ul>
                    <p>Thank you for choosing our hotel. We look forward to serving you!</p>
                    </body>
                    </html>
                    """
                    
                    msg.attach(MIMEText(body, 'html'))
                    
                    # Connect to Gmail server and send email
                    server = smtplib.SMTP('smtp.gmail.com', 587)
                    server.starttls()
                    server.login(sender_email, sender_password)
                    server.send_message(msg)
                    server.quit()
                    
                    st.success("✉️ Booking confirmation sent to your email!")
                    
                except Exception as e:
                    st.error(f"Could not send email confirmation: {e}")
                    
        else:
            st.warning("⚠️ Please enter your Customer ID to proceed!")

    # Add a button to go back to customer portal
    if st.button("Back to Customer Portal"):
        st.switch_page("pages/customerportal.py")

if __name__ == "__main__":
    show()