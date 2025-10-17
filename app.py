# app.py
import streamlit as st
from pathlib import Path
import importlib
import re

st.set_page_config(layout="wide", page_title="Lab Toolkit")
st.title("🧰 Lab Toolkit")

def get_tabs():
    """
    Scans the 'tabs' directory, imports each tab as a module,
    and returns a dictionary of tabs.
    """
    tabs_dict = {}
    # Find all .py files in the 'tabs' directory
    tab_files = sorted(Path("tabs").glob("*.py"))
    
    for tab_file in tab_files:
        # Skip the __init__.py file
        if tab_file.name == "__init__.py":
            continue

        # Dynamically import the module
        module_name = f"tabs.{tab_file.stem}"
        try:
            tab_module = importlib.import_module(module_name)
            
            # Use regex to clean up the filename for the tab title
            # This removes the "01_", "02_" prefixes and replaces underscores with spaces
            clean_name = re.sub(r"^\d+_", "", tab_file.stem).replace("_", " ")

            # Each tab file must have a 'run_tab()' function
            if hasattr(tab_module, "run_tab"):
                tabs_dict[clean_name] = tab_module.run_tab
        except Exception as e:
            st.error(f"Error loading tab {tab_file.name}: {e}")
            
    return tabs_dict

# Get all the tab functions
tab_functions = get_tabs()
tab_titles = list(tab_functions.keys())

# Create the tabs in Streamlit
if tab_titles:
    st_tabs = st.tabs(tab_titles)
    
    # Render the content for each tab
    for tab, title in zip(st_tabs, tab_titles):
        with tab:
            # Call the run_tab() function from the imported module
            tab_functions[title]()
else:
    st.warning("No tabs found in the 'tabs' directory.")