import streamlit as st
from src.tabs import (
    experiment_designer_tab,
    dilution_master_tab,
    serial_dilution_planner_tab,
    ic50_planner_tab, # NEW import
    reagent_manager_tab
)

def main():
    """
    Main function to run the Streamlit application UI and logic.
    """
    st.set_page_config(layout="wide", page_title="Lab Toolkit")
    st.title("🧰 Lab Toolkit")

    # Define the main tabs of the application, including the new IC50 Planner
    tab_titles = [
        "🧪 Experiment Designer",
        "💧 Dilution Master",
        "📋 Serial Dilution Planner",
        "🎯 IC50 Planner", # NEW tab
        "📚 Reagent Manager"
    ]

    tabs = st.tabs(tab_titles)

    # Load the UI and logic for each tab from the imported functions
    with tabs[0]:
        experiment_designer_tab()
    with tabs[1]:
        dilution_master_tab()
    with tabs[2]:
        serial_dilution_planner_tab()
    with tabs[3]:
        ic50_planner_tab() # NEW function call
    with tabs[4]:
        reagent_manager_tab()

if __name__ == "__main__":
    main()