import streamlit as st
from streamlit_option_menu import option_menu
import test_1
import prompt
import test_2

# Ensure `st.set_page_config()` is the very first Streamlit command
st.set_page_config(
    page_title="Syllabus Generator",
    page_icon="📘",
    layout="wide"
)

# Class to manage multiple apps
class MultiApp:
    def __init__(self):
        self.apps = []

    def add_app(self, title, function):
        self.apps.append({
            "title": title,
            "function": function
        })

    def run(self):
        with st.sidebar:
            app = option_menu(
                menu_title="MENU",
                options=["Prompt to Syllabus", "Course link to Syllabus", "Topic to syllabus"],
                default_index=0,
                styles={
                    "container": {"padding": "5!important", "background-color": "white"},
                    "icon": {"color": "blue", "font-size": "23px"},
                    "nav-link": {
                        "color": "black",
                        "font-size": "20px",
                        "text-align": "left",
                        "margin": "0px",
                        "--hover-color": "#85929E",
                    },
                    "nav-link-selected": {"background-color": "#EAECEE"},
                },
            )
        if app == "Prompt to Syllabus":
            prompt.app()
        elif app == "Course link to Syllabus":
            test_1.app()
        elif app == "Topic to syllabus":
            test_2.app()


# Initialize and run the app
app = MultiApp()
app.run()
