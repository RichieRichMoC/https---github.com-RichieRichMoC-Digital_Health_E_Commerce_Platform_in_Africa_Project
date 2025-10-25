import streamlit as st
import PyPDF2
import pandas as pd
import re
from io import BytesIO
import os

def load_syllabus(uploaded_syllabus_file):
    """Load syllabus data from Excel file"""
    try:
        syllabus_df = pd.read_excel(uploaded_syllabus_file)
        return syllabus_df
    except Exception as e:
        st.error(f"Error loading syllabus file: {str(e)}")
        return None

def extract_pdf_content(uploaded_file, syllabus_df=None):
    """
    Extract content from PDF file and structure it with syllabus mapping
    """
    pdf_content = {
        'filename': uploaded_file.name,
        'exams_type': '',
        'questions': [],
        'suggested_solutions': [],
        'mark_allocations': [],
        'syllabus_areas': []
    }
    
    # Read PDF content
    pdf_reader = PyPDF2.PdfReader(uploaded_file)
    full_text = ""
    
    for page in pdf_reader.pages:
        full_text += page.extract_text() + "\n"
    
    # Extract exam type
    exam_type_match = re.search(r'(NOVEMBER|MAY|MARCH|SEPTEMBER)\s+\d{4}\s+(.*?)(?:\n|$)', full_text, re.IGNORECASE)
    if exam_type_match:
        pdf_content['exams_type'] = f"{exam_type_match.group(1)} {exam_type_match.group(2)}"
    
    # Extract questions and solutions
    questions = re.split(r'QUESTION\s+(ONE|TWO|THREE|FOUR|FIVE|SIX|SEVEN|EIGHT|NINE|TEN)', full_text)
    
    for i in range(1, len(questions), 2):
        if i < len(questions):
            question_number = questions[i]
            question_content = questions[i+1] if i+1 < len(questions) else ""
            
            # Split question and solution
            parts = re.split(r'(SOLUTION|ANSWER|WORKINGS)', question_content, maxsplit=1, flags=re.IGNORECASE)
            
            question_text = parts[0] if len(parts) > 0 else ""
            solution_text = parts[2] if len(parts) > 2 else ""
            
            # Extract mark allocation
            marks_match = re.search(r'\(Total:\s*(\d+)\s*marks\)', question_text)
            marks = marks_match.group(1) if marks_match else ""
            
            # Clean up text
            question_text = re.sub(r'\s+', ' ', question_text).strip()
            solution_text = re.sub(r'\s+', ' ', solution_text).strip()
            
            # Map to syllabus area
            syllabus_area = map_question_to_syllabus(question_text, syllabus_df) if syllabus_df is not None else "Syllabus not loaded"
            
            pdf_content['questions'].append(f"QUESTION {question_number}: {question_text[:500]}...")
            pdf_content['suggested_solutions'].append(solution_text[:500] + "..." if solution_text else "Not available")
            pdf_content['mark_allocations'].append(marks)
            pdf_content['syllabus_areas'].append(syllabus_area)
    
    return pdf_content

def map_question_to_syllabus(question_text, syllabus_df):
    """
    Map question content to syllabus areas based on keywords
    """
    question_text_lower = question_text.lower()
    
    # Define keywords for each syllabus area
    syllabus_keywords = {
        'Application of International Financial Reporting Standards': [
            'ifrs', 'ias', 'international financial reporting', 'accounting standard',
            'financial reporting', 'consolidated', 'group', 'subsidiary', 'associate',
            'joint venture', 'business combination', 'goodwill', 'fair value',
            'impairment', 'revenue recognition', 'lease', 'financial instrument',
            'eps', 'earnings per share', 'deferred tax', 'provision'
        ],
        'Preparation of financial statements for a group': [
            'consolidated', 'group', 'subsidiary', 'parent', 'nci', 'non-controlling',
            'goodwill', 'elimination', 'intercompany', 'acquisition', 'disposal',
            'consolidation adjustment', 'group structure'
        ],
        'Evaluate entity position, performance and prospects using a range of financial and other data': [
            'ratio', 'analysis', 'performance', 'profitability', 'liquidity', 'gearing',
            'efficiency', 'position', 'prospects', 'financial health', 'evaluation',
            'comparative analysis', 'investment decision', 'report', 'recommendation'
        ],
        'Specialized transactions': [
            'lease', 'financial instrument', 'hedge', 'foreign currency', 'derivative',
            'share-based payment', 'pension', 'insurance', 'extractive industry',
            'agriculture', 'service concession', 'discontinued operation'
        ],
        'Environmental, social and governance issues, sustainability reporting, contemporary issues and ethics': [
            'ethics', 'ethical', 'governance', 'sustainability', 'environmental',
            'social', 'esg', 'corporate governance', 'ethical issue', 'director',
            'proposal', 'conflict', 'transparency', 'accountability'
        ]
    }
    
    # Find the best matching syllabus area
    best_match = "Unknown Syllabus Area"
    max_keyword_count = 0
    
    for area, keywords in syllabus_keywords.items():
        keyword_count = sum(1 for keyword in keywords if keyword in question_text_lower)
        if keyword_count > max_keyword_count:
            max_keyword_count = keyword_count
            best_match = area
    
    return best_match if max_keyword_count > 0 else "General/Unknown"

def main():
    st.title("📊 PDF Exam Paper Extractor with Syllabus Mapping")
    st.write("Upload PDF exam papers and syllabus Excel file to extract questions, solutions, and map to syllabus areas")
    
    # Syllabus upload
    st.sidebar.header("📚 Syllabus Configuration")
    uploaded_syllabus_file = st.sidebar.file_uploader(
        "Upload Syllabus Excel File",
        type=['xlsx', 'xls'],
        help="Upload an Excel file containing syllabus areas and weightings"
    )
    
    syllabus_df = None
    if uploaded_syllabus_file:
        syllabus_df = load_syllabus(uploaded_syllabus_file)
        if syllabus_df is not None:
            st.sidebar.success("Syllabus loaded successfully!")
            st.sidebar.subheader("Syllabus Overview")
            st.sidebar.dataframe(syllabus_df)
    
    # Main PDF upload
    st.header("📄 PDF Exam Papers")
    uploaded_files = st.file_uploader(
        "Upload PDF files", 
        type=['pdf'], 
        accept_multiple_files=True,
        help="Upload one or more PDF exam papers"
    )
    
    if uploaded_files:
        st.success(f"Uploaded {len(uploaded_files)} file(s)")
        
        all_data = []
        
        for uploaded_file in uploaded_files:
            with st.spinner(f"Processing {uploaded_file.name}..."):
                try:
                    content = extract_pdf_content(uploaded_file, syllabus_df)
                    
                    # Create rows for each question
                    for i in range(len(content['questions'])):
                        row = {
                            'PDF Name': content['filename'],
                            'Exam Type': content['exams_type'],
                            'Question Number': f"Q{i+1}",
                            'Question': content['questions'][i],
                            'Suggested Solution': content['suggested_solutions'][i],
                            'Mark Allocation': content['mark_allocations'][i] or "Not specified",
                            'Syllabus Area': content['syllabus_areas'][i]
                        }
                        all_data.append(row)
                        
                except Exception as e:
                    st.error(f"Error processing {uploaded_file.name}: {str(e)}")
        
        if all_data:
            # Create DataFrame
            df = pd.DataFrame(all_data)
            
            # Display preview
            st.subheader("📋 Extracted Data Preview")
            st.dataframe(df)
            
            # Syllabus analysis
            if syllabus_df is not None:
                st.subheader("📊 Syllabus Coverage Analysis")
                
                # Calculate marks per syllabus area
                syllabus_analysis = df.groupby('Syllabus Area').agg({
                    'Mark Allocation': lambda x: sum(int(m) for m in x if m.isdigit()),
                    'Question Number': 'count'
                }).rename(columns={'Mark Allocation': 'Total Marks', 'Question Number': 'Question Count'})
                
                syllabus_analysis['Percentage of Total'] = (
                    syllabus_analysis['Total Marks'] / syllabus_analysis['Total Marks'].sum() * 100
                ).round(2)
                
                st.dataframe(syllabus_analysis)
                
                # Display syllabus coverage chart
                col1, col2 = st.columns(2)
                
                with col1:
                    st.bar_chart(syllabus_analysis['Total Marks'])
                    st.caption("Marks Distribution by Syllabus Area")
                
                with col2:
                    st.bar_chart(syllabus_analysis['Question Count'])
                    st.caption("Question Count by Syllabus Area")
            
            # Export to Excel
            st.subheader("📥 Export to Excel")
            
            # Create Excel file with multiple sheets
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                # Main data sheet
                df.to_excel(writer, sheet_name='Extracted_Questions', index=False)
                
                # Syllabus analysis sheet
                if syllabus_df is not None:
                    syllabus_analysis.to_excel(writer, sheet_name='Syllabus_Analysis')
                    syllabus_df.to_excel(writer, sheet_name='Syllabus_Reference', index=False)
                
                # Auto-adjust column widths for all sheets
                for sheet_name in writer.sheets:
                    worksheet = writer.sheets[sheet_name]
                    for idx, col in enumerate(df.columns if sheet_name == 'Extracted_Questions' else syllabus_analysis.columns):
                        max_len = max(
                            df[col].astype(str).str.len().max() if sheet_name == 'Extracted_Questions' 
                            else syllabus_analysis[col].astype(str).str.len().max(), 
                            len(col)
                        ) + 2
                        worksheet.set_column(idx, idx, min(max_len, 50))
            
            output.seek(0)
            
            # Download button
            st.download_button(
                label="📥 Download Excel File",
                data=output,
                file_name="extracted_questions_with_syllabus.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
            # Statistics
            st.subheader("📊 Extraction Statistics")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total PDFs", len(uploaded_files))
            with col2:
                st.metric("Total Questions", len(all_data))
            with col3:
                questions_with_marks = len([x for x in all_data if x['Mark Allocation'] != "Not specified"])
                st.metric("Questions with Marks", questions_with_marks)
            with col4:
                unique_syllabus_areas = len(set([x['Syllabus Area'] for x in all_data]))
                st.metric("Syllabus Areas Covered", unique_syllabus_areas)
            
        else:
            st.warning("No questions were extracted from the uploaded files.")

if __name__ == "__main__":
    main()