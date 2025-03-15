import streamlit as st
# Hide Streamlit's sidebar and default elements
st.markdown("""
    <style>
        [data-testid="stSidebar"] {display: none !important;}
        [data-testid="stSidebarNav"] {display: none !important;}
        button[kind="icon"] {display: none !important;}
        [data-testid="collapsedControl"] {display: none !important;}
        
        /* Custom button styling for larger buttons */
        div[data-testid="stButton"] > button {
            height: 3rem;
            font-size: 1.2rem;
            width: 100%;
            padding: 0.5rem 1rem;
            margin: 0.5rem 0;
        }
    </style>
""", unsafe_allow_html=True)
# Centered title
st.markdown("<h1 style='text-align: center; font-size: 40px;'>🔑 Manager Portal</h1>", unsafe_allow_html=True)
# Initialize session state for login
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
# Sample credentials (Modify as needed)
VALID_CREDENTIALS = {
    "dhruvg096@gmail.com": "dhruv123",
}
# Check if manager is already logged in
if st.session_state.logged_in:
    st.success("✅ Login Successful! Choose an option below:")
   
    # Option buttons
    col1, col2 = st.columns(2)
   
    with col1:
        if st.button("🧐 Analyze Reviews", key="analyze_reviews"):
            st.switch_page("pages/reviewsanalysis.py")
    with col2:
        if st.button("📈 View Insights", key="view_insights"):
            st.switch_page("pages/viewinsights.py")
    # Option to log out
    if st.button("🔴 Logout"):
        st.session_state.logged_in = False
        st.rerun()
else:
    # Create input fields for login
    email = st.text_input("📧 Enter Email ID", key="email")
    password = st.text_input("🔒 Enter Password", type="password", key="password")
    # Login button action
    if st.button("Login", key="login_button"):
        if email in VALID_CREDENTIALS and password == VALID_CREDENTIALS[email]:
            st.session_state.logged_in = True
            st.success("✅ Login Successful! Choose an option below:")
            st.rerun()
        else:
            st.error("❌ Invalid Email or Password. Please try again.")
    # Add Go to Home button
    if st.button("🏨 Go to Home", key="home_button"):
        st.switch_page("home.py")