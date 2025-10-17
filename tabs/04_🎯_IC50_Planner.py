import streamlit as st
import pandas as pd
import numpy as np
from common import (
    MOLARITY_CONVERSIONS,
    VOLUME_CONVERSIONS,
    load_reagents,
    format_molarity,
    create_download_button,
    SOLVENT_OPTIONS
)

# --- Tab 4: IC50 Planner ---
def run_tab():
    st.header("IC50 Dose-Response Planner 🎯")
    st.markdown("Design a non-uniform, multi-stage serial dilution protocol to efficiently determine IC50 values.")
    
    reagents = load_reagents()
    reagent_options = [""] + list(reagents.keys())

    st.subheader("Step 1: Define Reagent and Volumes")
    col1, col2 = st.columns(2)
    with col1:
        reagent_name = st.selectbox("Select Reagent", reagent_options, key='ic50_reagent')
        stock_conc_val = st.number_input("Main Stock Concentration", value=10.0, min_value=0.0, format="%.4f", key='ic50_stock_val')
        stock_conc_unit = st.selectbox("Main Stock Unit", list(MOLARITY_CONVERSIONS.keys()), index=1, key='ic50_stock_unit')
    with col2:
        final_vol_val = st.number_input("Final Volume per Well/Tube", value=100.0, min_value=0.0, key='ic50_final_vol_val')
        final_vol_unit = st.selectbox("Final Volume Unit", list(VOLUME_CONVERSIONS.keys()), index=2, key='ic50_final_vol_unit')
        
    st.markdown("---")
    
    st.subheader("Step 2: Define Concentration Series")
    col3, col4, col5 = st.columns(3)
    with col3:
        highest_conc_val = st.number_input("Highest Concentration", value=10.0, min_value=0.0, format="%.4f", key='ic50_high_val')
        highest_conc_unit = st.selectbox("Highest Conc. Unit", list(MOLARITY_CONVERSIONS.keys()), index=2, key='ic50_high_unit')
    with col4:
        st.markdown("##### Number of Points per Range")
        num_sparse_upper = st.number_input("Upper Sparse", min_value=1, value=2, step=1, help="Points at high concentrations, spaced far apart.")
        num_dense = st.number_input("Dense", min_value=1, value=6, step=1, help="Points clustered around the estimated IC50.")
        num_sparse_lower = st.number_input("Lower Sparse", min_value=0, value=2, step=1, help="Points at low concentrations, spaced far apart.")
    with col5:
        st.markdown("##### Dilution Factors per Range")
        sparse_factor = st.number_input("Sparse Factor", min_value=1.1, value=10.0, step=0.1, format="%.1f")
        dense_factor = st.number_input("Dense Factor", min_value=1.1, value=2.0, step=0.1, format="%.1f")

    st.markdown("---")

    if st.button("🚀 Generate Protocol", type="primary"):
        # --- Input Validation and Base Unit Conversion ---
        main_stock_base = stock_conc_val * MOLARITY_CONVERSIONS[stock_conc_unit]
        highest_conc_base = highest_conc_val * MOLARITY_CONVERSIONS[highest_conc_unit]
        final_vol_base = final_vol_val * VOLUME_CONVERSIONS[final_vol_unit]

        if main_stock_base <= highest_conc_base:
            st.error("The 'Highest Concentration' must be lower than the 'Main Stock Concentration'.")
            return

        # --- Generate Concentration List ---
        upper_sparse_concs, dense_concs, lower_sparse_concs = [], [], []
        
        current_conc = highest_conc_base
        for _ in range(num_sparse_upper):
            upper_sparse_concs.append(current_conc)
            current_conc /= sparse_factor
        
        for _ in range(num_dense):
            dense_concs.append(current_conc)
            current_conc /= dense_factor

        for _ in range(num_sparse_lower):
            lower_sparse_concs.append(current_conc)
            current_conc /= sparse_factor

        final_concentrations = upper_sparse_concs + dense_concs + lower_sparse_concs
        
        st.subheader("Dilution Protocol")

        # --- Helper function for generating protocol for a single group ---
        def generate_group_protocol(title, concs, factor, source_stock_conc, point_offset):
            if not concs: return

            st.markdown(f"#### {title} (Points #{point_offset + 1} to #{point_offset + len(concs)})")
            
            st.markdown(f"**Part A: Prepare Tube for Point #{point_offset + 1}**")
            group_start_conc = concs[0]
            is_series = len(concs) > 1
            
            # The first tube needs extra volume if it's used for the next transfer
            transfer_vol = final_vol_base / (factor - 1) if is_series and factor > 1 else 0
            initial_tube_vol = final_vol_base + transfer_vol

            stock_vol_needed_base = (group_start_conc * initial_tube_vol) / source_stock_conc
            stock_vol_needed_ul = stock_vol_needed_base * 1e6
            diluent_vol_needed_base = initial_tube_vol - stock_vol_needed_base

            MIN_PIPETTE_VOL_UL = 1.0
            
            # If stock volume is too low, create an intermediate stock first
            if stock_vol_needed_ul < MIN_PIPETTE_VOL_UL:
                st.warning(f"Direct dilution requires `{stock_vol_needed_ul:.3f} µL` of main stock, which is too low. A two-step dilution will be used for this group.")
                
                # Make a 1:10 intermediate stock (a common lab practice)
                intermediate_stock_conc = source_stock_conc / 10.0
                st.info(f"**Step A1: Create a 1:10 Intermediate Stock ({format_molarity(intermediate_stock_conc)})**\n\n"
                        f"1. **Combine `10 µL`** of your **Main Stock** with **`90 µL`** of solvent.\n"
                        f"2. Use this new intermediate stock for the next step.")
                
                # Recalculate volumes using the intermediate stock
                stock_vol_from_inter_base = (group_start_conc * initial_tube_vol) / intermediate_stock_conc
                diluent_vol_from_inter_base = initial_tube_vol - stock_vol_from_inter_base
                
                st.success(f"**Step A2: Prepare Tube for Point #{point_offset + 1} (Conc: {format_molarity(group_start_conc)})**\n\n"
                           f"1. **Take `{stock_vol_from_inter_base * 1e6:.2f} µL`** of the **1:10 Intermediate Stock**.\n"
                           f"2. **Add `{diluent_vol_from_inter_base * 1e6:.2f} µL`** of solvent.")
            else:
                # Direct dilution is fine
                st.success(
                    f"This tube is **Point #{point_offset + 1}** (conc: **{format_molarity(group_start_conc)}**).\n\n"
                    f"1. **Take `{stock_vol_needed_ul:.2f} µL`** of your **Main Stock** ({format_molarity(source_stock_conc)}).\n"
                    f"2. **Add `{diluent_vol_needed_base * 1e6:.2f} µL`** of solvent."
                )

            if is_series:
                 st.markdown(f"**Part B: Perform {factor}-fold Serial Dilution**")
                 diluent_for_tubes = final_vol_base - (final_vol_base / factor)
                 protocol_steps = [
                     f"1. **Prepare {len(concs) - 1} new tubes** for points #{point_offset + 2} through #{point_offset + len(concs)}.",
                     f"2. **Add `{diluent_for_tubes * 1e6:.2f} µL` of solvent** to each of these new tubes.",
                     f"3. **Transfer `{transfer_vol * 1e6:.2f} µL`** from the **Point #{point_offset + 1}** tube into the next tube (this creates Point #{point_offset + 2}). Mix well.",
                     f"4. **Continue transferring `{transfer_vol * 1e6:.2f} µL`** sequentially for the remaining tubes in this series.",
                     f"5. **Important**: Discard the final `{transfer_vol * 1e6:.2f} µL` from the very last tube to ensure all tubes have the correct final volume of {final_vol_val} {final_vol_unit}."
                 ]
                 st.info("\n".join(protocol_steps))

        # --- Generate Protocol for each section ---
        point_offset = 0
        generate_group_protocol("Upper Sparse Range", upper_sparse_concs, sparse_factor, main_stock_base, point_offset)
        point_offset += len(upper_sparse_concs)
        
        generate_group_protocol("Dense Range", dense_concs, dense_factor, main_stock_base, point_offset)
        point_offset += len(dense_concs)

        generate_group_protocol("Lower Sparse Range", lower_sparse_concs, sparse_factor, main_stock_base, point_offset)

        # --- Display Final Summary Table ---
        st.markdown("---")
        st.subheader("Final Concentration Summary")
        summary_data = [{"Point #": i + 1, "Final Concentration": format_molarity(c)} for i, c in enumerate(final_concentrations)]
        df_summary = pd.DataFrame(summary_data)
        st.dataframe(df_summary, width='stretch')
        create_download_button(df_summary, f'IC50_protocol_summary_{reagent_name}.csv')