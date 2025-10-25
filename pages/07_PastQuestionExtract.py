import streamlit as st
import PyPDF2
import pandas as pd
import re
from io import BytesIO
import os

def extract_keywords_from_syllabus_pdf(uploaded_syllabus_pdf):
    """
    Extract syllabus areas and keywords from a PDF syllabus document
    """
    try:
        # Read PDF content
        pdf_reader = PyPDF2.PdfReader(uploaded_syllabus_pdf)
        syllabus_text = ""
        
        for page in pdf_reader.pages:
            syllabus_text += page.extract_text() + "\n"
        
        # Extract syllabus areas and their content
        syllabus_areas = extract_syllabus_areas(syllabus_text)
        
        # Generate keywords for each area
        syllabus_keywords = {}
        for area_name, area_content in syllabus_areas.items():
            keywords = generate_keywords_from_content(area_content, area_name)
            syllabus_keywords[area_name] = keywords
        
        return syllabus_keywords, syllabus_text
        
    except Exception as e:
        st.error(f"Error processing syllabus PDF: {str(e)}")
        return None, None

def extract_syllabus_areas(syllabus_text):
    """
    Extract syllabus areas from the syllabus text
    """
    syllabus_areas = {}
    
    # Common patterns for syllabus structure
    patterns = [
        # Pattern for "A) Area Name" format
        r'([A-Z]\))\s*([^\.\n]+?)\s*(?=[A-Z]\)|\n\n|$)',
        # Pattern for numbered sections "1. Area Name"
        r'(\d+\.)\s*([^\.\n]+?)\s*(?=\d+\.|\n\n|$)',
        # Pattern for bold or heading-like text
        r'\n\s*([A-Z][A-Za-z\s]{10,50}?)\s*\n',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, syllabus_text, re.MULTILINE | re.DOTALL)
        if matches:
            for match in matches:
                if len(match) >= 2:
                    area_code = match[0].strip()
                    area_name = match[1].strip()
                    # Extract content for this area
                    area_content = extract_area_content(syllabus_text, area_code, area_name)
                    syllabus_areas[area_name] = area_content
            break
    
    # If no structured patterns found, try to extract major sections
    if not syllabus_areas:
        # Look for lines that seem like section headers
        lines = syllabus_text.split('\n')
        current_area = None
        current_content = []
        
        for line in lines:
            line = line.strip()
            if len(line) > 5 and (line.isupper() or re.match(r'^[A-Z][A-Za-z\s]{10,}', line)):
                if current_area and current_content:
                    syllabus_areas[current_area] = ' '.join(current_content)
                current_area = line
                current_content = []
            elif current_area and line:
                current_content.append(line)
        
        if current_area and current_content:
            syllabus_areas[current_area] = ' '.join(current_content)
    
    return syllabus_areas

def extract_area_content(full_text, area_code, area_name):
    """
    Extract the content for a specific syllabus area
    """
    # Look for content between this area and the next one
    pattern = rf"{re.escape(area_code)}\s*{re.escape(area_name)}(.*?)(?=(?:[A-Z]\)|\d+\.|\n\n|[A-Z][A-Z\s]{{10,}}|\Z))"
    match = re.search(pattern, full_text, re.DOTALL | re.IGNORECASE)
    
    if match:
        return match.group(1).strip()
    else:
        # Fallback: look for the area name and take next 500 characters
        pattern = rf"{re.escape(area_name)}(.*?)(?=\n\n|\Z)"
        match = re.search(pattern, full_text, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()[:500]
    
    return area_name  # Return area name as fallback content

def generate_keywords_from_content(content, area_name):
    """
    Generate relevant keywords from syllabus area content
    """
    # Combine area name and content for keyword extraction
    full_text = f"{area_name} {content}".lower()
    
    # Remove common stop words
    stop_words = {
        'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 
        'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 
        'had', 'having', 'do', 'does', 'did', 'doing', 'will', 'would', 'could', 'should',
        'may', 'might', 'must', 'can', 'shall'
    }
    
    # Extract meaningful words (3+ characters)
    words = re.findall(r'\b[a-zA-Z]{3,}\b', full_text)
    
    # Filter out stop words and get unique words
    keywords = [word for word in words if word not in stop_words]
    
    # Add common accounting/finance terms that might be relevant
    accounting_terms = {
        'financial', 'reporting', 'accounting', 'standards', 'ifrs', 'ias', 'gaap',
        'consolidated', 'group', 'subsidiary', 'associate', 'joint', 'venture',
        'financial statements', 'balance sheet', 'income statement', 'cash flow',
        'ratio analysis', 'performance', 'profitability', 'liquidity', 'gearing',
        'lease', 'financial instruments', 'hedging', 'derivatives', 'taxation',
        'ethics', 'governance', 'sustainability', 'environmental', 'social',
        'audit', 'assurance', 'compliance', 'regulation', 'framework'
    }
    
    # Add relevant accounting terms
    for term in accounting_terms:
        if term in full_text:
            keywords.extend(term.split())
    
    # Prioritize longer words and unique terms
    keywords = list(set(keywords))  # Remove duplicates
    keywords.sort(key=lambda x: len(x), reverse=True)  # Sort by length
    
    # Return top 15-20 most relevant keywords
    return keywords[:20]

def load_syllabus_structure(uploaded_syllabus_file):
    """Load syllabus structure data from Excel file (optional)"""
    try:
        syllabus_df = pd.read_excel(uploaded_syllabus_file)
        return syllabus_df
    except Exception as e:
        st.error(f"Error loading syllabus structure file: {str(e)}")
        return None

def extract_pdf_content(uploaded_file, syllabus_keywords=None):
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
            syllabus_area = map_question_to_syllabus(question_text, syllabus_keywords) if syllabus_keywords is not None else "Syllabus not loaded"
            
            pdf_content['questions'].append(f"QUESTION {question_number}: {question_text[:500]}...")
            pdf_content['suggested_solutions'].append(solution_text[:500] + "..." if solution_text else "Not available")
            pdf_content['mark_allocations'].append(marks)
            pdf_content['syllabus_areas'].append(syllabus_area)
    
    return pdf_content

def map_question_to_syllabus(question_text, syllabus_keywords):
    """
    Map question content to syllabus areas based on extracted keywords from PDF
    """
    if not syllabus_keywords:
        return "Syllabus not loaded"
    
    question_text_lower = question_text.lower()
    
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
    st.title("📊 PDF Exam Paper Extractor with Dynamic Syllabus Mapping")
    st.write("Upload PDF exam papers and a PDF syllabus document to extract questions and map to syllabus areas")
    
    # Syllabus PDF upload
    st.sidebar.header("📚 Syllabus PDF Configuration")
    uploaded_syllabus_pdf = st.sidebar.file_uploader(
        "Upload Syllabus PDF Document",
        type=['pdf'],
        help="Upload a PDF file containing the detailed syllabus with areas and descriptions"
    )
    
    syllabus_keywords = None
    syllabus_text = ""
    
    if uploaded_syllabus_pdf:
        with st.spinner("Extracting syllabus areas and keywords from PDF..."):
            syllabus_keywords, syllabus_text = extract_keywords_from_syllabus_pdf(uploaded_syllabus_pdf)
        
        if syllabus_keywords:
            st.sidebar.success(f"Syllabus PDF processed! Found {len(syllabus_keywords)} areas.")
            st.sidebar.subheader("📋 Extracted Syllabus Areas")
            
            # Display extracted areas
            for area_name, keywords in list(syllabus_keywords.items())[:6]:  # Show first 6
                with st.sidebar.expander(f"{area_name[:40]}..." if len(area_name) > 40 else area_name):
                    st.write(f"**Keywords:** {', '.join(keywords[:8])}{'...' if len(keywords) > 8 else ''}")
                    st.write(f"**Total keywords:** {len(keywords)}")
            
            if len(syllabus_keywords) > 6:
                st.sidebar.info(f"... and {len(syllabus_keywords) - 6} more areas")
        else:
            st.sidebar.error("Could not extract syllabus areas from the PDF.")
    
    # Optional: Syllabus structure upload (Excel with weights)
    st.sidebar.header("📊 Optional: Syllabus Structure")
    uploaded_syllabus_structure = st.sidebar.file_uploader(
        "Upload Syllabus Structure (Excel with weights - Optional)",
        type=['xlsx', 'xls'],
        help="Optional: Upload an Excel file with syllabus areas and weightings for better analysis"
    )
    
    syllabus_df = None
    if uploaded_syllabus_structure:
        syllabus_df = load_syllabus_structure(uploaded_syllabus_structure)
        if syllabus_df is not None:
            st.sidebar.success("Syllabus structure loaded!")
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
        if syllabus_keywords is None:
            st.warning("⚠️ No syllabus PDF loaded. Please upload a syllabus PDF document above.")
            return
        
        st.success(f"Uploaded {len(uploaded_files)} file(s)")
        
        all_data = []
        
        for uploaded_file in uploaded_files:
            with st.spinner(f"Processing {uploaded_file.name}..."):
                try:
                    content = extract_pdf_content(uploaded_file, syllabus_keywords)
                    
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
            st.subheader("📊 Syllabus Coverage Analysis")
            
            # Calculate marks per syllabus area
            syllabus_analysis = df.groupby('Syllabus Area').agg({
                'Mark Allocation': lambda x: sum(int(m) for m in x if m.isdigit()),
                'Question Number': 'count'
            }).rename(columns={'Mark Allocation': 'Total Marks', 'Question Number': 'Question Count'})
            
            if syllabus_analysis['Total Marks'].sum() > 0:
                syllabus_analysis['Percentage of Total'] = (
                    syllabus_analysis['Total Marks'] / syllabus_analysis['Total Marks'].sum() * 100
                ).round(2)
            
            st.dataframe(syllabus_analysis)
            
            # Display syllabus coverage chart
            if not syllabus_analysis.empty:
                col1, col2 = st.columns(2)
                
                with col1:
                    if syllabus_analysis['Total Marks'].sum() > 0:
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
                if not syllabus_analysis.empty:
                    syllabus_analysis.to_excel(writer, sheet_name='Syllabus_Analysis')
                
                # Syllabus keywords reference sheet
                if syllabus_keywords:
                    syllabus_ref_data = []
                    for area, keywords in syllabus_keywords.items():
                        syllabus_ref_data.append({
                            'Syllabus Area': area,
                            'Keywords': ', '.join(keywords),
                            'Keyword Count': len(keywords)
                        })
                    syllabus_ref_df = pd.DataFrame(syllabus_ref_data)
                    syllabus_ref_df.to_excel(writer, sheet_name='Syllabus_Keywords', index=False)
                
                # Auto-adjust column widths
                for sheet_name in writer.sheets:
                    worksheet = writer.sheets[sheet_name]
                    if sheet_name == 'Extracted_Questions':
                        for idx, col in enumerate(df.columns):
                            max_len = max(df[col].astype(str).str.len().max(), len(col)) + 2
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
                st.metric("Syllabus Areas Covered in All", unique_syllabus_areas)
            
            # Syllabus extraction details
            st.subheader("🔍 Syllabus Extraction Details")
            st.info(f"✅ Successfully extracted {len(syllabus_keywords)} syllabus areas from the PDF document")
            st.write("The system automatically generated keywords from each syllabus area's content for intelligent question mapping.")
            
        else:
            st.warning("No questions were extracted from the uploaded files.")

if __name__ == "__main__":
    main()