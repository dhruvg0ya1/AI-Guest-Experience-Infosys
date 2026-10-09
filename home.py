import streamlit as st
from pages import booking, customerportal

# Set page configuration first, before any other Streamlit commands
st.set_page_config(
    page_title="Hotel",
    page_icon="🏨",
    layout="centered"
)

# Hide sidebar, sidebar navigation, and sidebar toggle button
st.markdown("""
    <style>
        [data-testid="stSidebar"] {display: none !important;}
        [data-testid="stSidebarNav"] {display: none !important;}
        button[kind="icon"] {display: none !important;}
        [data-testid="collapsedControl"] {display: none !important;}
    </style>
""", unsafe_allow_html=True)

# Custom CSS for global font size increase and button styling
st.markdown("""
<style>
html, body, [class*="css"] {
    font-size: 1.2rem !important;
}
h1 {
    font-size: 3.5rem !important;
}
h2, h3 {
    font-size: 2.5rem !important;
}
div.stButton > button {
    width: 100%;
    height: 100px;
    font-size: 40px !important;
    font-weight: bold;
    border-radius: 15px;
    margin-top: 20px;
    box-shadow: 2px 4px 6px rgba(0, 0, 0, 0.2);
    transition: transform 0.2s;
}
div.stButton > button:hover {
    transform: scale(1.05);
    box-shadow: 0px 6px 12px rgba(0, 0, 0, 0.3);
}
</style>
""", unsafe_allow_html=True)

def main():
    # Initialize session state for role if it doesn't exist
    if 'role' not in st.session_state:
        st.session_state.role = None
        
    # Display header with hotel emoji (larger size)
    st.markdown("<h1 style='text-align: center;'>🏨 Hotel</h1>", unsafe_allow_html=True)
    st.write("")
    st.write("")
    
    # Create container for better styling
    container = st.container()
    
    # Ask user if they are a customer or manager with larger text
    st.markdown("<h2 style='text-align: center;'>Are you a customer or the manager?</h2>", unsafe_allow_html=True)
    st.write("")
    
    # Create two big buttons with rounded corners
    col1, col2 = st.columns(2, gap="large")
    
    with col1:
        if st.button("Customer", key="customer_btn"):
            st.session_state.role = "customer"
            st.switch_page("pages/customerportal.py")
    
    with col2:
        if st.button("Manager", key="manager_btn"):
            st.session_state.role = "manager"
            st.switch_page("pages/managerportal.py")  # Note: Fixed the typo in managerportal.py

if __name__ == "__main__":
    main()