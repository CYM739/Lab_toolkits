import streamlit as st
import pandas as pd
from common import (
    load_reagents,
    save_reagents,
    create_download_button
)

# --- Tab 5: Reagent Manager ---
def run_tab():
    st.header("Reagent Manager 📚")
    st.markdown("Store and manage your commonly used reagents.")
    reagents = load_reagents()

    with st.expander("➕ Add New Reagent", expanded=True):
        with st.form("new_reagent_form", clear_on_submit=True):
            name = st.text_input("Reagent Name*")
            mw = st.number_input("Molecular Weight (g/mol)*", min_value=0.01, format="%.4f")
            manufacturer = st.text_input("Manufacturer/Cat# (Optional)")
            if st.form_submit_button("💾 Save New Reagent"):
                if not name or mw <= 0:
                    st.error("Reagent Name and a valid MW are required.")
                elif name in reagents:
                    st.error(f"Reagent '{name}' already exists.")
                else:
                    reagents[name] = {"mw": mw, "manufacturer": manufacturer}
                    save_reagents(reagents)
                    st.success(f"Saved '{name}'.")
                    st.rerun()
    
    st.markdown("---")
    st.subheader("Stored Reagents")
    if not reagents:
        st.info("No reagents saved yet.")
    else:
        reagent_list = [{"Reagent Name": name, **data} for name, data in reagents.items()]
        df = pd.DataFrame(reagent_list)
        st.dataframe(df, width='stretch')
        create_download_button(df, 'reagent_list.csv')

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Edit Reagent")
            reagent_to_edit = st.selectbox("Select Reagent to Edit", options=[""] + list(reagents.keys()))
            if reagent_to_edit:
                reagent_data = reagents[reagent_to_edit]
                new_mw = st.number_input("New MW", value=reagent_data['mw'], min_value=0.01, format="%.4f", key=f"edit_mw_{reagent_to_edit}")
                new_mfr = st.text_input("New Manufacturer", value=reagent_data.get('manufacturer', ''), key=f"edit_mfr_{reagent_to_edit}")
                if st.button("💾 Update Reagent"):
                    reagents[reagent_to_edit] = {"mw": new_mw, "manufacturer": new_mfr}
                    save_reagents(reagents)
                    st.success(f"Updated '{reagent_to_edit}'.")
                    st.rerun()
        with col2:
            st.subheader("Delete Reagent")
            reagent_to_delete = st.selectbox("Select Reagent to Delete", options=[""] + list(reagents.keys()), key='delete_select')
            if st.button("🗑️ Delete Selected Reagent", disabled=not reagent_to_delete, type="secondary"):
                del reagents[reagent_to_delete]
                save_reagents(reagents)
                st.success(f"Deleted '{reagent_to_delete}'.")
                st.rerun()