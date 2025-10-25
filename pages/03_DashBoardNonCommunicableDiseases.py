import streamlit as st
import pandas as pd
import plotly.express as px
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
from io import BytesIO
from PIL import Image
import plotly.io as pio

st.set_page_config(
    page_title='Dashboard',
    page_icon='📈',
    layout='wide'
)

# Load configuration from YAML file
with open('./config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

# Initialize Streamlit Authenticator with configuration settings
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

# Check if the user is authenticated
if not st.session_state.get("authentication_status"):
    st.info('Please log in to access the application from the MainPage.')
else:
    def main():
        # Access data from session state
        data = st.session_state.get("data_key2", None)

        if data is None:
            st.info('Please Kindly Access the DataPage to Configure your DataSet.')
        else:
            # Ensure Year is string for plotting
            if "Year" in data.columns:
                data["Year_str"] = data["Year"].astype(str)

            # ============================
            # Country + Series Filter
            # ============================
            st.title("Non Communicable Diseases Indicators Over Time")

            col1, col2 = st.columns([2, 2])
            with col1:
                selected_country = st.selectbox(
                    "Select Country",
                    options=data["Country Name"].unique(),
                    key="country_perf"
                )
            with col2:
                country_data = data[data["Country Name"] == selected_country]
                if not country_data.empty:
                    selected_series = st.selectbox(
                        "Select Series",
                        options=country_data["Series Name"].unique(),
                        key="series_filter"
                    )
                else:
                    selected_series = None

            if selected_series:
                series_data = country_data[country_data["Series Name"] == selected_series]

                if not series_data.empty:
                    st.subheader(f"Performance of {selected_country} ({selected_series})")

                    # Create three side-by-side columns
                    col_a, col_b, col_c = st.columns(3)

                    # --- Bar Chart ---
                    with col_a:
                        fig_bar = px.bar(
                            series_data,
                            x="Year_str",
                            y="OBS_VALUE",
                            title=f"Yearly OBS_VALUE",
                            template="plotly"  # keep color
                        )
                        st.plotly_chart(fig_bar, use_container_width=True)

                    # --- Pie Chart ---
                    with col_b:
                        fig_pie = px.pie(
                            series_data,
                            names="Year_str",
                            values="OBS_VALUE",
                            title=f"OBS_VALUE Share by Year",
                            template="plotly"  # keep color
                        )
                        st.plotly_chart(fig_pie, use_container_width=True)

                    # --- Line Chart ---
                    with col_c:
                        fig_line = px.line(
                            series_data,
                            x="Year_str",
                            y="OBS_VALUE",
                            markers=True,
                            title=f"OBS_VALUE Trend Over Years",
                            template="plotly"  # keep color
                        )
                        st.plotly_chart(fig_line, use_container_width=True)

                    # =========================
                    # Download All Charts Button
                    # =========================
                    bar_img = Image.open(BytesIO(pio.to_image(fig_bar, format="png"))).convert("RGB")
                    pie_img = Image.open(BytesIO(pio.to_image(fig_pie, format="png"))).convert("RGB")
                    line_img = Image.open(BytesIO(pio.to_image(fig_line, format="png"))).convert("RGB")

                    # Arrange horizontally
                    total_width = bar_img.width + pie_img.width + line_img.width
                    max_height = max(bar_img.height, pie_img.height, line_img.height)

                    combined_img = Image.new("RGB", (total_width, max_height), (255, 255, 255))
                    combined_img.paste(bar_img, (0, 0))
                    combined_img.paste(pie_img, (bar_img.width, 0))
                    combined_img.paste(line_img, (bar_img.width + pie_img.width, 0))

                    # Save to buffer
                    buf = BytesIO()
                    combined_img.save(buf, format="PNG")
                    buf.seek(0)

                    st.download_button(
                        label="📥 Download All Charts",
                        data=buf,
                        file_name=f"{selected_country}_{selected_series}_charts.png",
                        mime="image/png"
                    )

                else:
                    st.warning(f"No data available for {selected_country} in {selected_series}")

    if __name__ == '__main__':
        main()
