import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader

# Streamlit page setup
st.set_page_config(
    page_title='Digital_Health_E_Commerce_Platform_in_Africa_Project',
    page_icon='🏘️',
    layout='wide'
)

# Load config.yaml file
with open('./config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

# Initialize authenticator (positional args!)
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

# Sidebar
with st.sidebar:
    st.title("📊 Navigation")
    authenticator.login()

# Check authentication status
if st.session_state.get("authentication_status"):
    # ✅ LOGGED IN
    authenticator.logout("Logout", "sidebar")
    st.sidebar.success(f"Welcome {st.session_state['name']} 👋")

    # MAIN CONTENT
    st.markdown("<h2 style='color:#0066ff;'>Welcome to the Digital_Health_E_Commerce_Platform_in_Africa_Project Data Analysis </h2>", unsafe_allow_html=True)
    st.image('./Images/welcomepage.jpeg', use_container_width=True, output_format="auto")

    col1, col2 = st.columns(2)
    with col1:
        st.header("App Information 💬")
        st.write("Access the Data for the Digital_Health_E_Commerce_Platform_in_Africa_Project")

        st.header("Dataset Information")
        st.write("- World Development Indicators")
        st.write("- Non Communicable Diseases")
        st.write("- Population")
        st.write("- Technology Performance Indicators")
       
    with col2:
        st.header("How to Use the App")
        st.write("* Click on any of the  'DashBoard' page.")
        st.write("* Analyse Data by Selecting the input Features.")
        st.write("* Analyse is grouped in Univariate, Bivariate and Multivariate")

        st.header("Source Code")
        st.markdown("[GitHub Repository](https://github.com/RichieRichMoC/Digital_Health_E_Commerce_Platform_in_Africa_Project)")

        st.header("Social Handles")
        st.write("- [GitHub](https://github.com/RichieRichMoC)")
        st.write("- [LinkedIn](https://www.linkedin.com/in/richmond-kantam-97b5b1278/)")
        st.write("- [Website](https://richierichmoc-consult-2.onrender.com/)")

elif st.session_state.get("authentication_status") is False:
    st.error("🚫 Username/Password is incorrect")
    st.code("Username: beatit\nPassword: abc123")

elif st.session_state.get("authentication_status") is None:
    st.warning("Please enter your username and password.")
