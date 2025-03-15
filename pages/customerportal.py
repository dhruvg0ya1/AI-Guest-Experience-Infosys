import streamlit as st

def show():
    # This is called when using the session state navigation system
    setup_page()
    display_content()

def customer_portal():
    # This is called when the page is loaded directly
    setup_page()
    display_content()

def setup_page():
    # Set page configuration if this page is loaded directly
    # This will only work if it's the first Streamlit command on the page
    try:
        st.set_page_config(
            page_title="Customer Portal",
            layout="centered"
        )
    except:
        # If page config already set (like when navigating from another page), this will be skipped
        pass
        
    # Hide sidebar, sidebar navigation, and sidebar toggle button
    st.markdown("""
        <style>
            [data-testid="stSidebar"] {display: none !important;}
            [data-testid="stSidebarNav"] {display: none !important;}
            button[kind="icon"] {display: none !important;}
            [data-testid="collapsedControl"] {display: none !important;}
        </style>
    """, unsafe_allow_html=True)
    
    # Custom CSS for large buttons
    st.markdown("""
    <style>
    html, body, [class*="css"] {
        font-size: 1.2rem !important;
    }
    h1 {
        font-size: 3.5rem !important;
        text-align: center;
    }
    h2 {
        font-size: 2.5rem !important;
        text-align: center;
    }
    div.stButton > button {
        width: 100%;
        height: 80px;
        font-size: 24px !important;
        font-weight: bold;
        border-radius: 15px;
        margin-top: 20px;
        box-shadow: 2px 4px 6px rgba(0, 0, 0, 0.2);
        transition: transform 0.2s;
    }
    div.stButton > button:hover {
        transform: scale(1.05);
        box-shadow: 4px 6px 8px rgba(0, 0, 0, 0.3);
    }
    </style>
    """, unsafe_allow_html=True)

def display_content():
    # Display header
    st.markdown("<h1>Customer Portal</h1>", unsafe_allow_html=True)
    
    # Add space
    st.write("\n")
    st.write("\n")

    # Question
    st.markdown("<h2>What would you like to do?</h2>", unsafe_allow_html=True)

    # Add space
    st.write("\n")

    # Buttons arranged vertically    
    if st.button("🛎️ Make a Booking"):
        st.switch_page("pages/booking.py")
    
    if st.button("✍🏼 Write a Review"):
        st.switch_page("pages/writereview.py")
        
    # Add a button to go back to home if needed
    if st.button("🏨 Back to Home"):
        st.switch_page("home.py")

if __name__ == "__main__":
    customer_portal()