import streamlit as st
import pandas as pd
import plotly.express as px
from pymongo import MongoClient
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from io import BytesIO

# MongoDB Connection
client = MongoClient("mongodb+srv://dhruvg0yal:r2XvD62cYiKHJ8Yh@cluster0.ghmci.mongodb.net/")
db = client["hotel_guests"]

# Load Data
booking_df = pd.DataFrame(list(db["bookings_data"].find()))
dining_df = pd.DataFrame(list(db["dining_info"].find()))
reviews_df = pd.DataFrame(list(db["reviews_data"].find()))

# Data Cleaning
for df in [booking_df, dining_df, reviews_df]:
    df.drop(columns=["_id"], errors="ignore", inplace=True)

# Clean booking data
try:
    # Convert check_in_date and check_out_date to datetime
    booking_df["check_in_date"] = pd.to_datetime(booking_df["check_in_date"], format="mixed", errors="coerce")
    booking_df["check_out_date"] = pd.to_datetime(booking_df["check_out_date"], format="mixed", errors="coerce")
    
    # Calculate length of stay with proper error handling
    booking_df["length_of_stay"] = (booking_df["check_out_date"] - booking_df["check_in_date"]).dt.days
    # Handle any NaN values that might result
    booking_df["length_of_stay"] = booking_df["length_of_stay"].fillna(0).astype(int)
    
    # Extract week from check_in_date
    booking_df["week"] = booking_df["check_in_date"].dt.strftime('%Y-%U')
except Exception as e:
    st.error(f"Error processing booking data: {e}")
    # Create default columns if processing fails
    if "length_of_stay" not in booking_df.columns:
        booking_df["length_of_stay"] = 0
    if "week" not in booking_df.columns:
        booking_df["week"] = ""

# Clean dining data
try:
    # Convert order_time, check_in_date, and check_out_date to datetime
    dining_df["order_time"] = pd.to_datetime(dining_df["order_time"], format="mixed", errors="coerce")
    dining_df["check_in_date"] = pd.to_datetime(dining_df["check_in_date"], format="mixed", errors="coerce")
    dining_df["check_out_date"] = pd.to_datetime(dining_df["check_out_date"], format="mixed", errors="coerce")
    
    # Extract date from order_time
    dining_df["date"] = dining_df["order_time"].dt.date
except Exception as e:
    st.error(f"Error processing dining data: {e}")
    # Create date column if processing fails
    if "date" not in dining_df.columns:
        dining_df["date"] = None

# Clean reviews data
try:
    # Convert review_date to datetime
    reviews_df["review_date"] = pd.to_datetime(reviews_df["review_date"], format="mixed", errors="coerce")
    
    # Convert review_date_numeric to datetime if it exists
    if "review_date_numeric" in reviews_df.columns:
        reviews_df["review_date_numeric"] = pd.to_datetime(
            reviews_df["review_date_numeric"].astype(str), 
            format="%Y%m%d", 
            errors="coerce"
        )
    
    # Convert Rating to numeric
    reviews_df["Rating"] = pd.to_numeric(reviews_df["Rating"], errors="coerce")
except Exception as e:
    st.error(f"Error processing reviews data: {e}")

st.markdown("""
    <style>
        [data-testid="stSidebarNav"] {display: none;}
    </style>
""", unsafe_allow_html=True)

# Sidebar Filters
st.sidebar.title("Filters")
start_date = st.sidebar.date_input("Start Date", booking_df["check_in_date"].min())
end_date = st.sidebar.date_input("End Date", booking_df["check_in_date"].max())

filtered_booking_df = booking_df[(booking_df["check_in_date"] >= pd.to_datetime(start_date)) & (booking_df["check_in_date"] <= pd.to_datetime(end_date))]
filtered_dining_df = dining_df[(dining_df["order_time"] >= pd.to_datetime(start_date)) & (dining_df["order_time"] <= pd.to_datetime(end_date))]
filtered_reviews_df = reviews_df

# Sidebar Navigation
option = st.sidebar.radio("Go to", ["Hotel Booking Insights", "Dining Insights", "Reviews Analysis"])

# Add this at the bottom of your sidebar section (after the existing sidebar elements)
st.sidebar.markdown("---")  # Adds a horizontal line as a divider
if st.sidebar.button("⬅️ Back to Manager Portal"):
    # This creates a button that when clicked will redirect to managerportal.py
    st.switch_page("pages/managerportal.py")
    st.rerun()

# Hotel Booking Insights
if option == "Hotel Booking Insights":
    # Initial overall insights before cuisine filtering
    st.title("🏨 Hotel Booking Insights")
    st.subheader("Overall Booking Trends")

    # Calculate overall metrics
    total_bookings = len(booking_df)
    avg_age_all = booking_df["age"].mean()
    avg_stay_all = (pd.to_datetime(booking_df["check_out_date"]) - pd.to_datetime(booking_df["check_in_date"])).dt.days.mean()
    points_ratio = (booking_df["booked_through_points"].sum() / total_bookings) * 100
    cuisine_counts = booking_df["Preferred Cusine"].value_counts()
    most_popular_cuisine = cuisine_counts.idxmax()

    # Display overall insights
    st.markdown("""
    <style>
        .metric-card {
            background-color: #008c8c;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .metric-header {
            color: #001919;
            font-size: 20px;
            margin-bottom: 15px;
            border-bottom: 2px solid #e0e0e0;
            padding-bottom: 10px;
        }
        .metric-item {
            margin: 10px 0;
            font-size: 16px;
        }
        .metric-icon {
            margin-right: 8px;
        }
    </style>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-header">📊 Guest Demographics</div>
            <div class="metric-item"><span class="metric-icon">🔢</span> <strong>Total bookings:</strong> {total_bookings}</div>
            <div class="metric-item"><span class="metric-icon">👤</span> <strong>Average guest age:</strong> {avg_age_all:.1f} years</div>
            <div class="metric-item"><span class="metric-icon">📏</span> <strong>Age range:</strong> {booking_df["age"].min()} to {booking_df["age"].max()} years</div>
            <div class="metric-item"><span class="metric-icon">👥</span> <strong>Most bookings by age group:</strong> {(booking_df["age"] // 10 * 10).value_counts().idxmax()}s</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-header">🏨 Booking Patterns</div>
            <div class="metric-item"><span class="metric-icon">🍽️</span> <strong>Most popular cuisine:</strong> {most_popular_cuisine}</div>
            <div class="metric-item"><span class="metric-icon">📅</span> <strong>Average stay duration:</strong> {avg_stay_all:.1f} days</div>
            <div class="metric-item"><span class="metric-icon">💰</span> <strong>Bookings made with points:</strong> {points_ratio:.1f}%</div>
            <div class="metric-item"><span class="metric-icon">👪</span> <strong>Most common party size:</strong> {booking_df["number_of_stayers"].mode()[0]} people</div>
        </div>
        """, unsafe_allow_html=True)

    # Display distribution of cuisines
    st.subheader("Cuisine Preference Distribution")
    fig_cuisine_pie = px.pie(
        cuisine_counts.reset_index(),
        values="count",
        names="Preferred Cusine",
        color="Preferred Cusine",
        color_discrete_sequence=px.colors.qualitative.Bold,
        hole=0.3  # Creates a donut chart for better visual appeal
    )

    # Improve the pie chart appearance
    fig_cuisine_pie.update_traces(textposition='inside', textinfo='percent+label')
    fig_cuisine_pie.update_layout(
        legend_title="Cuisine Types",
        legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5)
    )

    st.plotly_chart(fig_cuisine_pie)

    # Add a divider
    st.markdown("---")

    # Cuisine filter section
    cuisine_filter = st.multiselect("Select Cuisine", booking_df["Preferred Cusine"].dropna().unique())

    # Define a consistent color map for cuisines
    cuisine_colors = {
        cuisine: px.colors.qualitative.Bold[i % len(px.colors.qualitative.Bold)] 
        for i, cuisine in enumerate(booking_df["Preferred Cusine"].dropna().unique())
    }

    # Create a custom color sequence based on the selected cuisines
    def get_color_sequence(cuisines):
        return [cuisine_colors[cuisine] for cuisine in cuisines]

    # Replace the pie chart with more insightful visualizations
    if cuisine_filter:
        filtered_booking_df = filtered_booking_df[filtered_booking_df["Preferred Cusine"].isin(cuisine_filter)]
        
        # Display key metrics for selected cuisines
        st.subheader("Key Insights for Selected Cuisines")
        
        # Calculate metrics
        total_bookings = len(filtered_booking_df)
        avg_stay_duration = (pd.to_datetime(filtered_booking_df["check_out_date"]) - 
                            pd.to_datetime(filtered_booking_df["check_in_date"])).dt.days.mean()
        avg_party_size = filtered_booking_df["number_of_stayers"].mean()
        avg_age = filtered_booking_df["age"].mean()
        points_bookings = filtered_booking_df["booked_through_points"].sum()
        
        # Display metrics in columns
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Bookings", f"{total_bookings}")
            st.metric("Average Age", f"{avg_age:.1f} years")
        with col2:
            st.metric("Average Stay Duration", f"{avg_stay_duration:.1f} days")
            st.metric("Points Bookings", f"{points_bookings}")
        with col3:
            st.metric("Average Party Size", f"{avg_party_size:.1f} people")
        
        # Create a bar chart for bookings by month with different colors for cuisines
        filtered_booking_df["check_in_month"] = pd.to_datetime(filtered_booking_df["check_in_date"]).dt.strftime('%B')
        month_order = ['January', 'February', 'March', 'April', 'May', 'June', 
                    'July', 'August', 'September', 'October', 'November', 'December']
        
        bookings_by_month_cuisine = filtered_booking_df.groupby(["check_in_month", "Preferred Cusine"]).size().reset_index(name="count")
        bookings_by_month_cuisine["check_in_month"] = pd.Categorical(
            bookings_by_month_cuisine["check_in_month"], 
            categories=month_order, 
            ordered=True
        )
        bookings_by_month_cuisine = bookings_by_month_cuisine.sort_values("check_in_month")
        
        # Get color sequence for selected cuisines
        color_sequence = get_color_sequence(cuisine_filter)
        
        fig_monthly = px.bar(
            bookings_by_month_cuisine, 
            x="check_in_month", 
            y="count",
            color="Preferred Cusine",
            title=f"Bookings by Month for {', '.join(cuisine_filter)}",
            labels={"check_in_month": "Month", "count": "Number of Bookings"},
            color_discrete_map={cuisine: cuisine_colors[cuisine] for cuisine in cuisine_filter}
        )
        st.plotly_chart(fig_monthly)
        
        # Create a distribution of stay durations with different colors for cuisines
        filtered_booking_df["stay_duration"] = (pd.to_datetime(filtered_booking_df["check_out_date"]) - 
                                            pd.to_datetime(filtered_booking_df["check_in_date"])).dt.days
        
        fig_duration = px.histogram(
            filtered_booking_df, 
            x="stay_duration", 
            color="Preferred Cusine",
            nbins=10,
            title=f"Stay Duration Distribution for {', '.join(cuisine_filter)}",
            labels={"stay_duration": "Stay Duration (days)"},
            color_discrete_map={cuisine: cuisine_colors[cuisine] for cuisine in cuisine_filter}
        )
        st.plotly_chart(fig_duration)
        
        # Create a heatmap instead of bubble chart for age vs party size
        # First, create a pivot table to aggregate data
        age_party_df = filtered_booking_df.copy()
        
        # Bin ages into categories for better visualization
        age_party_df['age_group'] = pd.cut(
            age_party_df['age'], 
            bins=[20, 30, 40, 50, 60, 70], 
            labels=['20-30', '30-40', '40-50', '50-60', '60-70']
        )
        
        # Create a pivot table
        heatmap_data = pd.pivot_table(
            age_party_df,
            values='stay_duration',  # Use stay duration as the value
            index='number_of_stayers',  # Party size on Y-axis
            columns='age_group',  # Age groups on X-axis
            aggfunc='mean',  # Average stay duration
            fill_value=0
        )
        
        # Create heatmap
        fig_heatmap = px.imshow(
            heatmap_data,
            labels=dict(x="Age Group", y="Party Size", color="Avg Stay Duration (days)"),
            title="Age Group vs Party Size Heatmap (Color = Average Stay Duration)",
            color_continuous_scale=px.colors.sequential.Reds
        )

        # Set grid and border color same as background
        fig_heatmap.update_traces(
            xgap=1,  # Adds a very thin gap
            ygap=1,  # Adds a very thin gap
            hoverongaps=False  # Prevents hover issues
        )

        fig_heatmap.update_layout(
            paper_bgcolor="#001919",
            plot_bgcolor="#008c8c",
            margin=dict(l=40, r=40, t=40, b=40),
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=False)
        )
        st.plotly_chart(fig_heatmap)
        
        # Add cuisine-specific insights with consistent formatting
        st.subheader("Cuisine-Specific Insights")

        # Define background and text colors for insights
        insight_bg_color = "#008c8c"
        insight_text_color = "white"
        insight_header_color = "#001919"

        # Display insights
        for cuisine in cuisine_filter:
            cuisine_df = filtered_booking_df[filtered_booking_df["Preferred Cusine"] == cuisine]

            # Calculate cuisine-specific metrics
            cuisine_avg_age = cuisine_df["age"].mean()
            cuisine_avg_party = cuisine_df["number_of_stayers"].mean()
            cuisine_avg_stay = (pd.to_datetime(cuisine_df["check_out_date"]) - 
                                pd.to_datetime(cuisine_df["check_in_date"])).dt.days.mean()
            
            # Points booking percentage
            points_percentage = (cuisine_df["booked_through_points"].sum() / len(cuisine_df)) * 100
            
            # Most common check-in month
            most_common_month = cuisine_df["check_in_month"].mode()[0] if not cuisine_df["check_in_month"].empty else "N/A"

            # Calculate repeat customer percentage
            repeat_customers = cuisine_df["customer_id"].duplicated().sum()
            repeat_percentage = (repeat_customers / len(cuisine_df)) * 100 if len(cuisine_df) > 0 else 0

            # Display insights
            st.markdown(f"""
            <div style="background-color:{insight_bg_color}; padding:20px; border-radius:10px; margin-bottom:15px; color:{insight_text_color};">
                <div style="color:{insight_header_color}; font-size:20px; margin-bottom:15px; border-bottom:2px solid #e0e0e0; padding-bottom:10px;">
                    {cuisine} Preference Insights
                </div>
                <div style="display:flex; flex-wrap:wrap; gap:20px;">
                    <div style="flex:1; min-width:250px; max-width:48%; margin-bottom:10px;">
                        <span style="margin-right:8px;">👤</span> <strong>Average guest age:</strong> {cuisine_avg_age:.1f} years
                    </div>
                    <div style="flex:1; min-width:250px; max-width:48%; margin-bottom:10px;">
                        <span style="margin-right:8px;">👪</span> <strong>Average party size:</strong> {cuisine_avg_party:.1f} people
                    </div>
                    <div style="flex:1; min-width:250px; max-width:48%; margin-bottom:10px;">
                        <span style="margin-right:8px;">📅</span> <strong>Average stay duration:</strong> {cuisine_avg_stay:.1f} days
                    </div>
                    <div style="flex:1; min-width:250px; max-width:48%; margin-bottom:10px;">
                        <span style="margin-right:8px;">💰</span> <strong>Points bookings:</strong> {points_percentage:.1f}%
                    </div>
                    <div style="flex:1; min-width:250px; max-width:48%; margin-bottom:10px;">
                        <span style="margin-right:8px;">📆</span> <strong>Most common month:</strong> {most_common_month}
                    </div>
                    <div style="flex:1; min-width:250px; max-width:48%; margin-bottom:10px;">
                        <span style="margin-right:8px;">🔄</span> <strong>Repeat customers:</strong> {repeat_percentage:.1f}%
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    else:
        st.info("Please select at least one cuisine to view insights.")
    
# Dining Insights
elif option == "Dining Insights":
    st.title("🍴 Dining Insights")
    
    # Calculate overall dining metrics
    total_orders = len(filtered_dining_df)
    avg_price = filtered_dining_df["price_for_1"].mean()
    most_ordered_dish = filtered_dining_df["dish"].value_counts().idxmax()
    avg_qty = filtered_dining_df["Qty"].mean()
    
    # Add CSS for metric cards with vertical alignment fix
    st.markdown("""
    <style>
    .metric-card {
        background-color: #008c8c;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        margin-bottom: 20px;
        height: 100%;  /* Make sure both cards have the same height */
    }
    .metric-header {
        color: #001919;
        font-size: 20px;
        margin-bottom: 15px;
        border-bottom: 2px solid #e0e0e0;
        padding-bottom: 10px;
    }
    .metric-item {
        margin: 10px 0;
        font-size: 16px;
    }
    .metric-icon {
        margin-right: 8px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Create two columns for metrics with equal height
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-header">🍽️ Order Statistics</div>
            <div class="metric-item"><span class="metric-icon">🔢</span> <strong>Total orders:</strong> {total_orders}</div>
            <div class="metric-item"><span class="metric-icon">💰</span> <strong>Average price per item:</strong> ₹{avg_price:.2f}</div>
            <div class="metric-item"><span class="metric-icon">🥄</span> <strong>Average quantity per order:</strong> {avg_qty:.1f}</div>
            <div class="metric-item"><span class="metric-icon">🍲</span> <strong>Most ordered dish:</strong> {most_ordered_dish}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        # Calculate cuisine-specific metrics
        cuisine_order_counts = filtered_dining_df["Preferred Cusine"].value_counts()
        most_dining_cuisine = cuisine_order_counts.idxmax()
        
        # Time analysis
        filtered_dining_df["hour_of_day"] = filtered_dining_df["order_time"].dt.hour
        peak_hour = filtered_dining_df["hour_of_day"].value_counts().idxmax()
        
        # Calculate in-room vs restaurant dining (based on if order time is during stay)
        filtered_dining_df["is_during_stay"] = filtered_dining_df.apply(
            lambda row: (row["order_time"] >= row["check_in_date"]) & 
                        (row["order_time"] <= row["check_out_date"]), 
            axis=1
        )
        in_house_dining_pct = (filtered_dining_df["is_during_stay"].sum() / total_orders) * 100
        
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-header">🕒 Dining Patterns</div>
            <div class="metric-item"><span class="metric-icon">🍛</span> <strong>Most popular cuisine:</strong> {most_dining_cuisine}</div>
            <div class="metric-item"><span class="metric-icon">⏰</span> <strong>Peak dining hour:</strong> {peak_hour}:00</div>
            <div class="metric-item"><span class="metric-icon">🏨</span> <strong>In-house dining:</strong> {in_house_dining_pct:.1f}%</div>
            <div class="metric-item"><span class="metric-icon">👥</span> <strong>Avg group size dining:</strong> {filtered_dining_df["number_of_stayers"].mean():.1f} people</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Dish Popularity by Cuisine
    # Group by cuisine and dish to count occurrences
    dish_by_cuisine = filtered_dining_df.groupby(["Preferred Cusine", "dish"]).size().reset_index(name="count")
    dish_by_cuisine = dish_by_cuisine.sort_values(["Preferred Cusine", "count"], ascending=[True, False])
    
    fig_dishes = px.bar(
        dish_by_cuisine, 
        x="dish", 
        y="count", 
        color="Preferred Cusine",
        title="🍲 Popular Dishes by Cuisine",
        labels={"dish": "Dish Name", "count": "Number of Orders"},
        color_discrete_sequence=px.colors.qualitative.Bold
    )
    
    fig_dishes.update_layout(xaxis={'categoryorder':'total descending'})
    st.plotly_chart(fig_dishes)
    
    # Age group preferences
    # Create age groups
    filtered_dining_df["age_group"] = pd.cut(
        filtered_dining_df["age"],
        bins=[15, 25, 35, 45, 55, 65],
        labels=["15-25", "26-35", "36-45", "46-55", "56-65"]
    )
    
    # Group by age group and cuisine
    age_cuisine_pref = filtered_dining_df.groupby(["age_group", "Preferred Cusine"]).size().reset_index(name="count")
    
    fig_age_cuisine = px.bar(
        age_cuisine_pref,
        x="age_group",
        y="count",
        color="Preferred Cusine",
        title="👥 Dining Preferences by Age Group",
        labels={"age_group": "Age Group", "count": "Number of Orders"},
        color_discrete_sequence=px.colors.qualitative.Bold
    )
    st.plotly_chart(fig_age_cuisine)
    
    # Order Time Analysis
    # Create hour bins for better visualization
    hour_bins = {
        "Morning (6-10)": (6, 10),
        "Lunch (11-14)": (11, 14),
        "Afternoon (15-17)": (15, 17),
        "Dinner (18-22)": (18, 22),
        "Late Night (23-5)": (23, 5)
    }
    
    def assign_time_period(hour):
        for period, (start, end) in hour_bins.items():
            if start <= end:
                if start <= hour <= end:
                    return period
            else:  # Handle wrap-around for late night
                if hour >= start or hour <= end:
                    return period
        return "Unknown"
    
    filtered_dining_df["time_period"] = filtered_dining_df["hour_of_day"].apply(assign_time_period)
    
    # Count orders by time period and cuisine
    time_cuisine = filtered_dining_df.groupby(["time_period", "Preferred Cusine"]).size().reset_index(name="count")
    
    # Define the correct order for time periods
    time_order = ["Morning (6-10)", "Lunch (11-14)", "Afternoon (15-17)", "Dinner (18-22)", "Late Night (23-5)"]
    time_cuisine["time_period"] = pd.Categorical(time_cuisine["time_period"], categories=time_order, ordered=True)
    time_cuisine = time_cuisine.sort_values("time_period")
    
    fig_time = px.bar(
        time_cuisine,
        x="time_period",
        y="count",
        color="Preferred Cusine",
        title="⏰ Dining Times Throughout the Day",
        labels={"time_period": "Time of Day", "count": "Number of Orders"},
        color_discrete_sequence=px.colors.qualitative.Bold
    )
    st.plotly_chart(fig_time)

# Reviews Analysis
elif option == "Reviews Analysis":
    st.title("📝 Reviews Analysis")
    
    # Calculate overall metrics for reviews
    total_reviews = len(filtered_reviews_df)
    avg_rating = filtered_reviews_df["Rating"].mean()
    rating_distribution = filtered_reviews_df["Rating"].value_counts().sort_index()
    
    # Add sentiment distribution if available
    if "sentiment_label" in filtered_reviews_df.columns:
        sentiment_distribution = filtered_reviews_df["sentiment_label"].value_counts()
        
    # Display metrics in cards similar to other sections
    st.markdown("""
    <style>
    .metric-card {
        background-color: #008c8c;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        margin-bottom: 20px;
        height: 100%;
        color: #e0e0e0;
    }
    .metric-header {
        color: #e0e0e0;
        font-size: 20px;
        margin-bottom: 15px;
        border-bottom: 2px solid #e0e0e0;
        padding-bottom: 10px;
    }
    .metric-item {
        margin: 10px 0;
        font-size: 16px;
    }
    .metric-icon {
        margin-right: 8px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Create two columns for metrics
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-header">⭐ Rating Insights</div>
            <div class="metric-item"><span class="metric-icon">📊</span> <strong>Total reviews:</strong> {total_reviews}</div>
            <div class="metric-item"><span class="metric-icon">📈</span> <strong>Average rating:</strong> {avg_rating:.1f}/10</div>
            <div class="metric-item"><span class="metric-icon">🏆</span> <strong>5-star reviews:</strong> {rating_distribution.get(10, 0)} ({(rating_distribution.get(10, 0)/total_reviews*100):.1f}%)</div>
            <div class="metric-item"><span class="metric-icon">👎</span> <strong>Low ratings (≤5):</strong> {filtered_reviews_df[filtered_reviews_df["Rating"] <= 5].shape[0]} ({filtered_reviews_df[filtered_reviews_df["Rating"] <= 5].shape[0]/total_reviews*100:.1f}%)</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        if "sentiment_label" in filtered_reviews_df.columns:
            positive_count = sentiment_distribution.get('positive', 0)
            negative_count = sentiment_distribution.get('negative', 0)
            neutral_count = sentiment_distribution.get('neutral', 0)
            positive_pct = (positive_count/total_reviews*100) if total_reviews > 0 else 0
            
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-header">🔍 Sentiment Analysis</div>
                <div class="metric-item"><span class="metric-icon">😃</span> <strong>Positive sentiment:</strong> {positive_count} ({positive_pct:.1f}%)</div>
                <div class="metric-item"><span class="metric-icon">😐</span> <strong>Neutral sentiment:</strong> {neutral_count} ({(neutral_count/total_reviews*100):.1f}%)</div>
                <div class="metric-item"><span class="metric-icon">😟</span> <strong>Negative sentiment:</strong> {negative_count} ({(negative_count/total_reviews*100):.1f}%)</div>
                <div class="metric-item"><span class="metric-icon">📉</span> <strong>Ratio:</strong> {positive_count/negative_count:.1f} positive : 1 negative</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-header">📅 Temporal Insights</div>
                <div class="metric-item"><span class="metric-icon">🗓️</span> <strong>Review period:</strong> {filtered_reviews_df["review_date"].min()} to {filtered_reviews_df["review_date"].max()}</div>
                <div class="metric-item"><span class="metric-icon">📊</span> <strong>Monthly review volume:</strong> {total_reviews / ((pd.to_datetime(filtered_reviews_df["review_date"]).max() - pd.to_datetime(filtered_reviews_df["review_date"]).min()).days / 30):.1f}</div>
                <div class="metric-item"><span class="metric-icon">🔍</span> <strong>Current guests' reviews:</strong> {filtered_reviews_df["currently_staying"].sum() if "currently_staying" in filtered_reviews_df.columns else "N/A"}</div>
                <div class="metric-item"><span class="metric-icon">🏨</span> <strong>Most reviewed room:</strong> {filtered_reviews_df["room_number"].mode()[0] if "room_number" in filtered_reviews_df.columns and not filtered_reviews_df["room_number"].isna().all() else "N/A"}</div>
            </div>
            """, unsafe_allow_html=True)
    
    # Rating Distribution with improved visualization
    st.subheader("⭐ Rating Distribution")
    
    # Add rating filter with improved default range
    rating_min = 1.0
    rating_max = 10.0
    rating_filter = st.slider("Filter by Rating", 
                             min_value=rating_min, 
                             max_value=rating_max,
                             value=(rating_min, rating_max),
                             step=0.1)
    
    filtered_by_rating_df = filtered_reviews_df[(filtered_reviews_df["Rating"] >= rating_filter[0]) & 
                                              (filtered_reviews_df["Rating"] <= rating_filter[1])]
    
    # Create histogram with clearer bins and colors
    fig_ratings = px.histogram(
        filtered_by_rating_df, 
        x="Rating", 
        nbins=10,
        color_discrete_sequence=['#00AFB9'],
        title="Hotel Rating Distribution"
    )
    
    fig_ratings.update_layout(
        xaxis_title="Rating (out of 10)",
        yaxis_title="Number of Reviews",
        bargap=0.05
    )
    
    st.plotly_chart(fig_ratings)
    
    # Sentiment Analysis Visualization (if available)
    if "sentiment_score" in filtered_reviews_df.columns and "sentiment_label" in filtered_reviews_df.columns:
        st.subheader("🔍 Sentiment Analysis")
        
        # Pie chart of sentiment labels - Only showing positive and negative
        sentiment_filtered = filtered_by_rating_df[filtered_by_rating_df["sentiment_label"].isin(["positive", "negative"])]
        fig_sentiment_pie = px.pie(
            sentiment_filtered,
            names="sentiment_label",
            color="sentiment_label",
            title="Customer Sentiment Distribution",
            color_discrete_map={
                "positive": "#26C485",
                "negative": "#EF476F"
            }
        )
        fig_sentiment_pie.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_sentiment_pie)
        
        # Scatter plot of rating vs sentiment score
        fig_sentiment_rating = px.scatter(
            filtered_by_rating_df,
            x="Rating",
            y="sentiment_score",
            color="sentiment_label",
            title="Rating vs Sentiment Score Correlation",
            color_discrete_map={
                "positive": "#26C485",
                "neutral": "#FFD166",
                "negative": "#EF476F"
            }
        )
        st.plotly_chart(fig_sentiment_rating)
        
        # Calculate correlation
        correlation = filtered_by_rating_df[["Rating", "sentiment_score"]].corr().iloc[0,1]
        st.info(f"Correlation between ratings and sentiment scores: {correlation:.2f}")
    
    # Review Text Analysis
    st.subheader("📝 Review Text Analysis")
    
    if "Review" in filtered_by_rating_df.columns:
        # Create tabs for different text analyses - removed Common Phrases tab
        text_tabs = st.tabs(["Word Cloud", "Key Complaints", "Key Praises"])
        
        with text_tabs[0]:
            # Word Cloud of Customer Feedback
            text = " ".join(filtered_by_rating_df["Review"].dropna())
            if text:
                wordcloud = WordCloud(
                    width=800, 
                    height=400, 
                    background_color="white",
                    colormap="viridis",
                    max_words=100,
                    contour_width=3,
                    contour_color='steelblue'
                ).generate(text)
                
                # Save wordcloud to buffer
                buffer = BytesIO()
                plt.figure(figsize=(10, 5))
                plt.imshow(wordcloud, interpolation="bilinear")
                plt.axis("off")
                plt.tight_layout(pad=0)
                plt.savefig(buffer, format="png", bbox_inches='tight')
                plt.close()
                
                st.image(buffer, caption="Word Cloud of Customer Reviews")
            else:
                st.warning("No review text available for the selected filters.")
        
        with text_tabs[1]:
            # Display negative reviews with low ratings - reversed colors
            negative_reviews = filtered_by_rating_df[filtered_by_rating_df["Rating"] <= 6].sort_values("Rating")
            
            if not negative_reviews.empty:
                st.write("Common Complaints (from lowest rated reviews):")
                
                for i, (_, row) in enumerate(negative_reviews.head(5).iterrows()):
                    st.markdown(f"""
                    <div style="background-color:#d32f2f; padding:15px; border-radius:5px; margin-bottom:10px;">
                        <div style="display:flex; justify-content:space-between; margin-bottom:5px;">
                            <div style="color:#ffffff;"><strong>Rating: {row['Rating']}/10</strong></div>
                            <div style="color:#ffffff;">{row['review_date'] if 'review_date' in row else ''}</div>
                        </div>
                        <div style="color:#ffffff;">{row['Review']}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No negative reviews found within the selected rating range.")
        
        with text_tabs[2]:
            # Display positive reviews with high ratings - reversed colors
            positive_reviews = filtered_by_rating_df[filtered_by_rating_df["Rating"] >= 9].sort_values("Rating", ascending=False)
            
            if not positive_reviews.empty:
                st.write("Key Praises (from highest rated reviews):")
                
                for i, (_, row) in enumerate(positive_reviews.head(5).iterrows()):
                    st.markdown(f"""
                    <div style="background-color:#2e7d32; padding:15px; border-radius:5px; margin-bottom:10px;">
                        <div style="display:flex; justify-content:space-between; margin-bottom:5px;">
                            <div style="color:#ffffff;"><strong>Rating: {row['Rating']}/10</strong></div>
                            <div style="color:#ffffff;">{row['review_date'] if 'review_date' in row else ''}</div>
                        </div>
                        <div style="color:#ffffff;">{row['Review']}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No highly positive reviews found within the selected rating range.")
    
    # Add customer segment analysis if data available
    if "customer_id" in filtered_by_rating_df.columns and "Rating" in filtered_by_rating_df.columns:
        st.subheader("👥 Customer Segment Analysis")
        
        # Calculate repeat reviewers
        reviewer_counts = filtered_by_rating_df["customer_id"].value_counts()
        repeat_reviewers = reviewer_counts[reviewer_counts > 1].count()
        repeat_pct = (repeat_reviewers / reviewer_counts.count()) * 100
        
        # Calculate average ratings by reviewer frequency
        one_time_avg = filtered_by_rating_df[filtered_by_rating_df["customer_id"].isin(reviewer_counts[reviewer_counts == 1].index)]["Rating"].mean()
        repeat_avg = filtered_by_rating_df[filtered_by_rating_df["customer_id"].isin(reviewer_counts[reviewer_counts > 1].index)]["Rating"].mean()
        
        # Display metrics with proper spacing
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("One-time Reviewers", f"{reviewer_counts[reviewer_counts == 1].count()}")
        with col2:
            st.metric("Repeat Reviewers", f"{repeat_reviewers} ({repeat_pct:.1f}%)")
        with col3:
            st.metric("Rating Difference", f"{repeat_avg - one_time_avg:.2f}", 
                     delta=f"{repeat_avg - one_time_avg:.2f}")
        
        # Create visualization of ratings by reviewer type
        rating_by_type = pd.DataFrame({
            "Reviewer Type": ["One-time Reviewers", "Repeat Reviewers"],
            "Average Rating": [one_time_avg, repeat_avg]
        })
        
        fig_reviewer_ratings = px.bar(
            rating_by_type,
            x="Reviewer Type",
            y="Average Rating",
            color="Reviewer Type",
            title="Average Ratings by Reviewer Type",
            color_discrete_sequence=["#8338EC", "#3A86FF"]
        )
        st.plotly_chart(fig_reviewer_ratings)