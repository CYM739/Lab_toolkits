import streamlit as st
import pandas as pd

from common import (
    ALL_CONC_UNITS,
    MOLARITY_CONVERSIONS,
    VOLUME_CONVERSIONS,
    load_reagents,
    format_molarity,
    format_mass_conc,
    create_download_button,
    SOLVENT_OPTIONS
)

def run_tab():
    st.header("Serial Dilution Planner 📋")
    st.markdown("Plan a series of dilutions where every tube has the same final volume.")
    reagents = load_reagents()
    reagent_options = [""] + list(reagents.keys())

    st.subheader("Step 1: Define Stock and Dilution Parameters")
    selected_reagent = st.selectbox("Select a Saved Reagent (Optional)", reagent_options, key='sdp_reagent_select')
    reagent_details = reagents.get(selected_reagent, {})
    default_mw = reagent_details.get('mw', 0.0)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("#### Stock Solution")
        reagent_name = st.text_input("Reagent Name", value=selected_reagent or "My Reagent", key='sdp_reagent_name')
        stock_conc_val = st.number_input("Stock Concentration", value=10.0, min_value=0.0, format="%.4f", key='serial_stock_val')
        stock_conc_unit = st.selectbox("Stock Unit", options=ALL_CONC_UNITS, index=1, key='serial_stock_unit')
    with col2:
        st.markdown("#### Series Parameters")
        num_dilutions = st.number_input("Number of Dilutions", min_value=1, max_value=20, value=10, step=1)
        dilution_factor = st.number_input("Dilution Factor per Step", min_value=1.1, value=10.0, step=0.1, format="%.1f")
        solvent = st.selectbox("Solvent/Diluent", SOLVENT_OPTIONS, key='serial_solvent_selector')
    with col3:
        st.markdown("#### Volume & MW")
        final_vol_val = st.number_input("Final Volume per Tube", value=1000.0, min_value=0.0, key='serial_final_vol_val')
        final_vol_unit = st.selectbox("Volume Unit", options=list(VOLUME_CONVERSIONS.keys()), index=2, key='serial_final_vol_unit')
        mw = st.number_input("Molecular Weight (g/mol) (Optional)", value=default_mw, min_value=0.0, format="%.4f", key='serial_mw')

    st.markdown("---")
    if st.button("🗓️ Plan Dilution Series", type="primary"):
        if dilution_factor <= 1:
            st.error("Dilution factor must be greater than 1.")
            return

        final_vol_base = final_vol_val * VOLUME_CONVERSIONS[final_vol_unit]
        transfer_vol_base = final_vol_base / (dilution_factor - 1)
        intermediate_vol_base = final_vol_base + transfer_vol_base
        stock_for_intermediate_base = intermediate_vol_base / dilution_factor
        diluent_for_intermediate_base = intermediate_vol_base - stock_for_intermediate_base
        diluent_for_final_tube_base = final_vol_base - (final_vol_base / dilution_factor)
        
        if num_dilutions > 1:
            total_diluent_needed_base = (diluent_for_intermediate_base * (num_dilutions - 1)) + diluent_for_final_tube_base
        else:
            total_diluent_needed_base = diluent_for_final_tube_base

        stock_for_intermediate_ul = stock_for_intermediate_base * 1e6
        diluent_for_intermediate_ul = diluent_for_intermediate_base * 1e6
        diluent_for_final_tube_ul = diluent_for_final_tube_base * 1e6
        transfer_vol_ul = transfer_vol_base * 1e6
        
        st.subheader("Results")
        st.success(f"**Total Stock Needed:** `{stock_for_intermediate_ul:,.2f} µL` | **Total Solvent Needed:** `{total_diluent_needed_base * 1e6:,.2f} µL`")

        # --- NEW ACTION TABLE ---
        protocol_data = []
        if num_dilutions > 1:
            for i in range(1, num_dilutions):
                protocol_data.append({"Step": f"Prepare Tube {i}", "Action": f"Add {diluent_for_intermediate_ul:,.2f} µL", "Source": solvent, "Destination": f"Tube {i}"})
        protocol_data.append({"Step": f"Prepare Tube {num_dilutions}", "Action": f"Add {diluent_for_final_tube_ul:,.2f} µL", "Source": solvent, "Destination": f"Tube {num_dilutions}"})
        protocol_data.append({"Step": "Start Series", "Action": f"Transfer {stock_for_intermediate_ul:,.2f} µL", "Source": "Main Stock", "Destination": "Tube 1"})
        for i in range(1, num_dilutions):
            protocol_data.append({"Step": f"Dilute {i+1}", "Action": f"Transfer {transfer_vol_ul:,.2f} µL", "Source": f"Tube {i}", "Destination": f"Tube {i+1}"})
        
        st.markdown("#### Action Summary Table")
        df_protocol = pd.DataFrame(protocol_data)
        st.dataframe(df_protocol, width='stretch')
        create_download_button(df_protocol, f'serial_dilution_protocol_{reagent_name}.csv')
        
        with st.expander("Show Full Protocol Text"):
            st.info(
                f"This protocol ensures every tube has **{final_vol_val:,.2f} {final_vol_unit}** at the end.\n\n"
                f"1. **Prepare {num_dilutions} tubes.**\n"
                f"2. **For Tubes 1 to {num_dilutions-1}:** Add **`{diluent_for_intermediate_ul:,.2f} µL`** of {solvent} to each.\n"
                f"3. **For the last tube ({num_dilutions}):** Add **`{diluent_for_final_tube_ul:,.2f} µL`** of {solvent}.\n"
                f"4. **Tube 1:** Add **`{stock_for_intermediate_ul:,.2f} µL`** of your **{reagent_name}** stock solution. Mix well.\n"
                f"5. **Transfer:** Take **`{transfer_vol_ul:,.2f} µL`** from Tube 1 and add it to Tube 2. Mix well.\n"
                f"6. **Repeat Transfer:** Continue transferring **`{transfer_vol_ul:,.2f} µL`** from the previous tube to the next, until you have added to Tube {num_dilutions}.\n"
                f"7. **Discard** the final **`{transfer_vol_ul:,.2f} µL`** from Tube {num_dilutions} to maintain the final volume."
            )

        st.markdown("#### Concentration Summary")
        concentrations_raw, concentrations_formatted, is_molar, initial_conc_base = [], [], False, 0
        if stock_conc_unit in MOLARITY_CONVERSIONS:
            initial_conc_base = stock_conc_val * MOLARITY_CONVERSIONS[stock_conc_unit]
            is_molar = True
        else: # mass/vol
            initial_conc_base = stock_conc_val * MOLARITY_CONVERSIONS[stock_conc_unit]
            if mw > 0:
                is_molar = True
                initial_conc_base /= mw
        current_conc_raw, current_conc_base = stock_conc_val, initial_conc_base
        for _ in range(num_dilutions):
            current_conc_raw /= dilution_factor
            current_conc_base /= dilution_factor
            concentrations_raw.append(f"{current_conc_raw:,.4g} {stock_conc_unit}")
            if is_molar:
                concentrations_formatted.append(format_molarity(current_conc_base))
            else:
                concentrations_formatted.append(format_mass_conc(current_conc_base))
        df_summary = pd.DataFrame({'Tube #': range(1, num_dilutions + 1), 'Final Concentration (Raw)': concentrations_raw, 'Final Concentration (Formatted)': concentrations_formatted})
        st.dataframe(df_summary, width='stretch')
        create_download_button(df_summary, f'serial_dilution_{reagent_name}.csv')

