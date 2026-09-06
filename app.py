# app.py
import streamlit as st
import streamlit.components.v1 as components
import os

# Configure wide fullscreen layout
st.set_page_config(
    page_title="BatteryGate — EV Battery Intelligence",
    layout="wide",
    page_icon="⚡",
    initial_sidebar_state="collapsed"
)

# Hide Streamlit default header, footer, and padding for a seamless full-screen app
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .block-container {
        padding: 0 !important;
        margin: 0 !important;
        max-width: 100% !important;
    }
    iframe {
        width: 100vw !important;
        height: 100vh !important;
        border: none !important;
    }
</style>
""", unsafe_allow_html=True)

# ⚠️ PASTE YOUR LIVE AWS LAMBDA FUNCTION URL HERE:
AWS_LAMBDA_URL = "https://rh3tpejwo2iyov7nmgrtfomyji0sohry.lambda-url.us-east-1.on.aws/"

# Read the HTML file and inject your live AWS URL
html_file_path = os.path.join(os.path.dirname(__file__), "index.html")

if os.path.exists(html_file_path):
    with open(html_file_path, "r", encoding="utf-8") as f:
        html_code = f.read()
        
    # Automatically inject your real AWS Lambda URL into the HTML
    html_code = html_code.replace(
        'var LAMBDA_URL = "https://rh3tpejwo2iyov7nmgrtfomyji0sohry.lambda-url.us-east-1.on.aws/";',
        f'var LAMBDA_URL = "{AWS_LAMBDA_URL}";'
    )
    
    # Render the full interactive application
    components.html(html_code, height=950, scrolling=True)
else:
    st.error("⚠️ `index.html` not found. Please save the HTML code as `index.html` in the same folder!")