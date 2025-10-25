import streamlit as st
import pandas as pd
import plotly.express as px
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
from io import BytesIO
from PIL import Image
import plotly.io as pio
import streamlit as st
from PyPDF2 import PdfReader
import re


st.set_page_config(
    page_title='Dashboard',
    page_icon='📈',
    layout='wide'
)


st.title("📚 Group Past Questions by Syllabus Topics")

# Upload syllabus and past questions PDFs
syllabus_file = st.file_uploader("Upload Syllabus PDF", type=["pdf"])
past_questions_file = st.file_uploader("Upload Past Questions & Solutions PDF", type=["pdf"])

def extract_text(pdf_file):
    text = ""
    reader = PdfReader(pdf_file)
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text

if syllabus_file and past_questions_file:
    # Extract text
    syllabus_text = extract_text(syllabus_file)
    past_qs_text = extract_text(past_questions_file)

    # Parse topics (assuming each topic is on its own line or numbered)
    topics = [line.strip() for line in syllabus_text.splitlines() if line.strip()]
    
    # Split past questions into Q&A pairs (adjust regex for your format)
    qa_pairs = re.split(r"\n?Q\d+[:.)]", past_qs_text, flags=re.IGNORECASE)
    
    grouped_data = []
    for topic in topics:
        related_qas = [qa for qa in qa_pairs if re.search(topic, qa, re.IGNORECASE)]
        for qa in related_qas:
            grouped_data.append({"Topic": topic, "Question_Answer": qa.strip()})
    
    if grouped_data:
        df = pd.DataFrame(grouped_data)
        st.success(f"Found {len(df)} matches!")
        st.dataframe(df, use_container_width=True)

        # Download as Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name="Grouped_QAs")
        st.download_button("📥 Download as Excel", data=output.getvalue(),
                           file_name="Grouped_Questions.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        st.warning("No matches found. Try refining topic names or check your PDFs.")
