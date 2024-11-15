import streamlit as st
import os
import google.generativeai as genai
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io

def create_pdf(syllabus):
    # Create a bytes buffer for the PDF
    buffer = io.BytesIO()
    # Create a PDF canvas
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Set title
    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, height - 50, "Generated Syllabus")

    # Set content
    p.setFont("Helvetica", 12)
    text_y = height - 100
    for line in syllabus.split('\n'):
        p.drawString(100, text_y, line)
        text_y -= 20  # Move down for next line

    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer

def app():
    # Configure the API key
    genai.configure(api_key="AIzaSyDz4dp_SP7TK5ETtagw2sZwyAc5VlFjzxA")

    def get_gemini_response(question, prompt):
        full_prompt = f"{prompt}\nGenerate only the given level of the syllabus."
        model = genai.GenerativeModel('gemini-1.5-pro-latest')
        response = model.generate_content([full_prompt, question])
        return response.text

    # Streamlit app layout
    st.title("Syllabus Generator")

    # Input fields
    question = st.text_input("Enter your course topic:", "")

    # Button to generate syllabus
    if st.button("Generate Syllabus"):
        if question:
            # Define the prompt dynamically inside the button logic
            prompt = f"""
                Create a course syllabus for the requested topic. Please provide all the three versions: Beginner, Intermediate, and Advanced. Each version should have the following components:

                - Course Title and Level: {question} 
                - Course Description: A brief overview of what the course covers.
                - Course Outline: Provide a detailed weekly breakdown based on the(or module structure) with key topics covered per week/module and it should be in the lesson wise.
                - Course Duration: Indicate the estimated time commitment required per week.
                
                Module Title: Provide a relevant title.
                    Subtopics: List each subtopic within the module (e.g., 'Module 1: Introduction to {question}', followed by subtopics like ‘Basic Concepts’, ‘Terminology’, etc.).
                
                **Beginner**: Focus on fundamental concepts, introducing terminology, and building foundational skills.
                **Intermediate**: Emphasize problem-solving, hands-on projects, and deeper exploration of core topics.
                **Advanced**: Cover complex topics, real-world applications, and advanced projects or case studies.

                Make sure the language, topics, and depth of content reflect the skill level for each version. The syllabi should be formatted neatly and clearly. Avoid any redundant or irrelevant information and say sorry if I don't have information for that.
                I NEED ALL THE THREE VERSIONS OF THE SYLLABUS LIKE BEGINNER,INTERMEDIATE,ADVANCED
                ### STRICTLY YOU SHOULD GIVE ONLY THE GIVEN {question} SYLLABUS CONTENT I PROVIDE AND DO NOT GIVE IRRELEVANT SYLLABUS ###
                ### STRICTLY YOU SHOULD NOT PROVIDE IRRELEVANT ANSWERS OTHER THAN FRAMING THE SYLLABUS ###
            """

            syllabus = get_gemini_response(question, prompt)
            st.write(syllabus)

            # Create a PDF download link
            pdf_buffer = create_pdf(syllabus)
            st.download_button("Download Syllabus as PDF", pdf_buffer, "syllabus.pdf", "application/pdf")
        else:
            st.warning("Please enter a course topic.")
