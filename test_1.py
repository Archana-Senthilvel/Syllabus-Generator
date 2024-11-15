import streamlit as st
import time
from xhtml2pdf import pisa
import io
from selenium.webdriver.common.by import By
from seleniumbase import Driver
import json
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
import requests
from bs4 import BeautifulSoup
import re

def app():
    def convert_html_to_pdf(html_content):
        pdf = io.BytesIO()
        pisa_status = pisa.CreatePDF(html_content, dest=pdf)
        if pisa_status.err:
            return None
        return pdf.getvalue()

    # Function to combine syllabi into a structured format
    def generate_response(course_data):
        combined_syllabus = {}
        for course, data in course_data.items():
            # Check if 'syllabus' key exists in the course data
            if isinstance(data, dict) and 'syllabus' in data:
                combined_syllabus[course] = data['syllabus']
            else:
                combined_syllabus[course] = data  # If it's already a string or doesn't have a 'syllabus' key, use it directly
        return json.dumps(combined_syllabus, indent=2)

    # Function to generate syllabi based on levels
    def generate_syllabus(input, level):
        time.sleep(2)
        
        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-pro-latest",
            temperature=0,
            max_tokens=None,
            timeout=None,
            max_retries=2,
            backoff_factor=2,
            verbose=True,
            streaming=True,
            google_api_key="AIzaSyDz4dp_SP7TK5ETtagw2sZwyAc5VlFjzxA",
        )
        
        prompt_text = f"You are an expert in SYLLABUS GENERATOR. Your task is to analyze the combined course syllabus and provide the {level} level topics in a clean, structured format using the following structure: 'Module 1: _' followed by lessons under each module. Ensure the topics are structured in a module-wise format, with multiple modules, each containing lessons, and leave one line between each module for clarity. Maintain the sequential order of modules, and do not include any preamble, conclusion, or JSON formatting."
        
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", prompt_text),
                ("human", "{input}"),
            ]
        )
        
        chain = prompt | llm | StrOutputParser()
        result = chain.stream({"input": input})
        combined_result = ''.join(result)
        return combined_result

    # Functions to extract syllabi from different platforms
    def udemy_extract_syllabus(udemy_url):
        driver = Driver(uc=True, headless=True)
        try:
            driver.get(udemy_url)
            name = driver.find_element(By.CSS_SELECTOR, "h1[data-purpose='lead-title']").text
            time.sleep(1)

            element = driver.find_element(By.CSS_SELECTOR, 'div[data-purpose="course-curriculum"] button[data-purpose="expand-toggle"].ud-btn.ud-btn-medium.ud-btn-ghost')
            element.click()

            data = {}
            div = driver.find_element(By.CSS_SELECTOR, 'div[data-purpose="course-curriculum"]')
            for section in div.find_elements(By.CSS_SELECTOR, "div.accordion-panel-module--panel--Eb0it.section--panel--qYPjj"):
                title_element = section.find_element(By.CSS_SELECTOR, "span.section--section-title--svpHP")
                subdata = []

                for sublinks in section.find_elements(By.CSS_SELECTOR, "span.ud-btn-label"):
                    subdata.append(sublinks.text)

                for subtitles in section.find_elements(By.CSS_SELECTOR, "span.section--item-title--EWIuI "):
                    subdata.append(subtitles.text)

                data[title_element.text] = subdata

            course_data = {"course_title": name, "syllabus": data}
            driver.quit()
            return course_data
        except Exception as e:
            st.error(f"Error extracting syllabus: {e}")
            return {}

    def edx_extract_syllabus(url):
        driver = Driver(uc=True, headless=True)
        try:
            driver.get(url)
            cname = driver.find_element(By.CSS_SELECTOR, 'h2[class="program-pathway-title"]').text

            lists = driver.find_elements(By.CSS_SELECTOR, 'div.collapsible-trigger[role="button"][tabindex="0"][aria-expanded="false"]')
            data = []
            for i in lists:
                driver.execute_script("arguments[0].scrollIntoView();", i)
                driver.execute_script("arguments[0].click();", i)

            links = driver.find_elements(By.CSS_SELECTOR, 'div.collapsible-body a.inline-link[__tracked="true"]')
            for i in links:
                data.append(i.get_attribute("href"))

            syllabus_div = {}
            for i in data:
                try:
                    def clean(text):
                        s = text.replace("\n", "")
                        s = s.replace("Skip Syllabus", " ")
                        s = s.replace("•", ",")
                        return s.strip()

                    driver.get(i)
                    time.sleep(2)
                    name = driver.find_element(By.CSS_SELECTOR, "#main-content > div > div.course-header > div > div.row.no-gutters > div.col-md-7.pr-4 > h1").text
                    driver.find_element(By.CSS_SELECTOR, "button#syllabus.preview-expand-cta").click()
                    elements = driver.find_elements(By.CSS_SELECTOR, ".course-main .preview-expand-component")
                    sub_syllabus = clean(elements[2].text)
                    syllabus_div[name] = [sub_syllabus]

                except Exception as e:
                    print(f"Error: {e}")

            course_data = {"course_title": cname, "syllabus": syllabus_div}
            driver.quit()

            return course_data
        except Exception as e:
            st.error(f"Error extracting syllabus: {e}")
            return {}

    def coursera_extract_syllabus(link):
        response = requests.get(link)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            course_data = soup.find('div', class_='css-fndret')
            return course_data.text.strip() if course_data else "Syllabus not found."
        else:
            return f"Failed to retrieve the webpage. Status code: {response.status_code}"

    def greatlearn_extract_syllabus(link):
        response = requests.get(link)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            course_description = soup.find('div', class_='acc-section gl-accordion-new')
            return course_description.text.strip() if course_description else "Course description not found."
        else:
            return f"Failed to retrieve the webpage. Status code: {response.status_code}"


    def extract_syllabus(link):
        supported_patterns = {
            "udemy": r"^https:\/\/www\.udemy\.com\/course\/.+",
            "edx": r"^https:\/\/www\.edx\.org\/certificates\/.+",
            "coursera": r"^https:\/\/www\.coursera\.org\/learn\/.+",
            "greatlearning": r"^https:\/\/www\.mygreatlearning\.com\/.+"
        } 
        if not any(re.match(pattern, link) for pattern in supported_patterns.values()):
            st.error("Invalid link. Only specific course links from Udemy, Coursera, Great Learning, and edX are supported.")
            return "Invalid link"
        
        if "udemy" in link:
            return udemy_extract_syllabus(link)
        elif "edx" in link:
            return edx_extract_syllabus(link)
        elif "coursera" in link:
            return coursera_extract_syllabus(link)
        elif "greatlearning" in link:
            return greatlearn_extract_syllabus(link)
        else:
            st.error("Only supported platforms are Udemy, Coursera, Great Learning, and edX.")
            return "Unsupported platform"


    # Streamlit app code
    st.title("Syllabus generator")

    if "course_links" not in st.session_state:
        st.session_state.course_links = ["", ""]

    def add_course_link():
        st.session_state.course_links.append("")

    def remove_course_link(index):
        if st.session_state.course_links:
            st.session_state.course_links.pop(index)

    for i, link in enumerate(st.session_state.course_links):
        col1, col2 = st.columns([8, 2])
        with col1:
            st.session_state.course_links[i] = st.text_input(f"Enter course link {i+1}:", link, key=f"course_link_{i}")
        with col2:
            if i < 2:
                st.button(f"Clear", key=f"remove_{i}", on_click=lambda idx=i: remove_course_link(idx))

    st.button("Add another course link", on_click=add_course_link)

    # Initialize session state variables if not already set
    if "course_data" not in st.session_state:
        st.session_state.course_data = None
    if "combined_syllabus" not in st.session_state:
        st.session_state.combined_syllabus = None
    if "beginner_syllabus" not in st.session_state:
        st.session_state.beginner_syllabus = None
    if "intermediate_syllabus" not in st.session_state:
        st.session_state.intermediate_syllabus = None
    if "advanced_syllabus" not in st.session_state:
        st.session_state.advanced_syllabus = None

    # Button to generate syllabus
    if st.button("Generate Syllabus"):
        if st.session_state.get("course_links"):
            with st.spinner("Extracting syllabus..."):
                p1 = st.progress(0)
                course = {}

                # Extract syllabus from each course link
                for i, link in enumerate(st.session_state.course_links):
                    p1.progress(int((i / len(st.session_state.course_links)) * 100))
                    syllabus = extract_syllabus(link)
                    course[f"course_{i+1}"] = syllabus

            p1.progress(100)
            # st.success("Syllabus Extracted")
            p1.empty()

            if course:
                # Store the extracted course data in session state
                st.session_state.course_data = course

                # Display the extracted syllabus in JSON format
                # st.subheader("Extracted Syllabus:")
                # st.json(course)

                # Generate combined and level-specific syllabuses
                st.session_state.combined_syllabus = generate_response(course)
                st.session_state.beginner_syllabus = generate_syllabus(
                    st.session_state.combined_syllabus, "beginner"
                )
                st.session_state.intermediate_syllabus = generate_syllabus(
                    st.session_state.combined_syllabus, "intermediate"
                )
                st.session_state.advanced_syllabus = generate_syllabus(
                    st.session_state.combined_syllabus, "advanced"
                )

    # Ensure course data is available before showing the selectbox
    if st.session_state.course_data:
        # Selectbox for choosing syllabus level
        selected_level = st.selectbox(
            "Select Syllabus Level",
            options=["Beginner", "Intermediate", "Advanced"]
        )

        # Function to display and download syllabus
        def display_syllabus(level, syllabus):
            st.subheader(f"{level.capitalize()} Syllabus")
            st.text_area(f"{level.capitalize()} Syllabus:", syllabus, height=300)
            pdf = convert_html_to_pdf(f"<pre>{syllabus}</pre>")
            if pdf:
                st.download_button(
                    f"Download {level.capitalize()} Syllabus PDF",
                    pdf,
                    file_name=f"{level.lower()}_syllabus.pdf"
                )

        # Display the syllabus based on the selected level
        if selected_level == "Beginner":
            display_syllabus("beginner", st.session_state.beginner_syllabus)
        elif selected_level == "Intermediate":
            display_syllabus("intermediate", st.session_state.intermediate_syllabus)
        elif selected_level == "Advanced":
            display_syllabus("advanced", st.session_state.advanced_syllabus)