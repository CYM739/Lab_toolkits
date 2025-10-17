import streamlit as st
import pandas as pd
import itertools
import string
import numpy as np
from pyDOE2 import bbdesign

# Import shared constants and functions from the common module
from .common import (
    ALL_CONC_UNITS,
    MOLARITY_CONVERSIONS,
    VOLUME_CONVERSIONS,
    load_reagents,
    save_reagents,
    format_molarity,
    format_mass_conc,
    create_download_button,
    SOLVENT_OPTIONS
)

# --- Tab 1: Experiment Designer ---
def experiment_designer_tab():
    st.header("Experiment Designer")
    st.markdown("Choose a method to design your experiment. Use **Full Factorial** to test every possible combination, or an **Optimized Design** to efficiently study factor effects and interactions.")

    sub_tab1, sub_tab2 = st.tabs(["Full Factorial (All Combinations)", "Optimized Design (Box-Behnken)"])

    with sub_tab1:
        st.subheader("Step 1: Define Your Variables")
        num_vars = st.selectbox("How many variables do you want to combine?", range(1, 11), index=2, help="Select the total number of factors you are testing.", key="ff_num_vars")
        variable_names = list(string.ascii_uppercase[:num_vars])
        st.markdown("---")

        st.subheader("Step 2: Set Number of Values for Each Variable")
        value_counts_cols = st.columns(num_vars)
        value_counts = {}
        for i, var_name in enumerate(variable_names):
            with value_counts_cols[i]:
                value_counts[var_name] = st.number_input(f"Values for Var '{var_name}'", value=3, min_value=1, key=f'ff_value_count_{var_name}')
        st.markdown("---")

        st.subheader("Step 3: Input the Specific Values")
        st.info("Enter your values separated by commas. For example: `10, 20, 30` or `low, medium, high`.", icon="💡")
        value_inputs_cols = st.columns(num_vars)
        all_inputs_valid = True
        variable_value_lists = []

        for i, var_name in enumerate(variable_names):
            with value_inputs_cols[i]:
                input_str = st.text_input(f"Enter {value_counts[var_name]} values for Var '{var_name}'", key=f'ff_values_for_{var_name}')
                if input_str:
                    values = [v.strip() for v in input_str.split(',') if v.strip()]
                    if len(values) == value_counts[var_name]:
                        variable_value_lists.append(values)
                    else:
                        st.error(f"Expected {value_counts[var_name]} values, but got {len(values)}.")
                        all_inputs_valid = False
                else:
                    all_inputs_valid = False
        st.markdown("---")

        st.subheader("Step 4: Generate & Download")
        if st.button("🚀 Generate Combinations", disabled=not all_inputs_valid, type="primary"):
            if all_inputs_valid:
                combinations = list(itertools.product(*variable_value_lists))
                df = pd.DataFrame(combinations, columns=variable_names)
                st.session_state['df_combinations'] = df

        if 'df_combinations' in st.session_state:
            df_results = st.session_state['df_combinations']
            st.success(f"Successfully generated **{len(df_results)}** combinations!")
            st.dataframe(df_results, width='stretch')
            create_download_button(df_results, 'combinations_data.csv')

    with sub_tab2:
        st.info("**Box-Behnken** is an efficient design for fitting response surfaces. It helps you model quadratic (curved) effects and interactions while avoiding extreme factor combinations (corners).", icon="🧪")
        st.subheader("Step 1: Define Your Factors (Variables)")
        num_factors = st.number_input("Number of Factors (3 to 7 are typical for BBD)", min_value=3, max_value=10, value=4, step=1)
        center_points = st.number_input("Number of Center Point Replicates", min_value=1, max_value=10, value=3, step=1, help="Replicates at the center are crucial for estimating experimental error and model fit.")
        st.markdown("---")

        st.subheader("Step 2: Define Factor Names and Levels (Concentrations)")
        factor_levels = {}
        cols = st.columns(num_factors)
        for i in range(num_factors):
            with cols[i]:
                factor_name = st.text_input(f"Name of Factor {i+1}", f"Factor_{string.ascii_uppercase[i]}", key=f"bbd_name_{i}")
                low_level = st.number_input(f"Low Level (-1) for {factor_name}", value=10.0, format="%.4f", key=f"low_{i}")
                center_level = st.number_input(f"Center Level (0) for {factor_name}", value=50.0, format="%.4f", key=f"center_{i}")
                high_level = st.number_input(f"High Level (+1) for {factor_name}", value=100.0, format="%.4f", key=f"high_{i}")
                if not low_level < center_level < high_level:
                    st.warning("Levels should be in increasing order (Low < Center < High).")
                factor_levels[factor_name] = {-1: low_level, 0: center_level, 1: high_level}
        st.markdown("---")

        st.subheader("Step 3: Generate and Download Design Table")
        if st.button("🚀 Generate Box-Behnken Design", type="primary"):
            try:
                bbd_matrix = bbdesign(num_factors, center=center_points)
                factor_names = list(factor_levels.keys())
                df_coded = pd.DataFrame(bbd_matrix, columns=factor_names)
                df_real = df_coded.copy()
                for factor in factor_names:
                    df_real[factor] = df_coded[factor].map(factor_levels[factor])
                st.session_state['df_bbd_coded'] = df_coded
                st.session_state['df_bbd_real'] = df_real
                st.success(f"Generated a BBD with **{len(df_real)}** runs.")
            except Exception as e:
                st.error(f"An error occurred: {e}")

        if 'df_bbd_real' in st.session_state:
            df_display = st.session_state['df_bbd_real']
            st.markdown("#### Experimental Runs Table (Actual Values)")
            st.dataframe(df_display, width='stretch')
            create_download_button(df_display, f'BBD_{num_factors}factors_{len(df_display)}runs.csv')
            with st.expander("Show Coded Design Matrix (-1, 0, +1)"):
                st.dataframe(st.session_state['df_bbd_coded'], width='stretch')

# --- Tab 2: Dilution Master ---
def dilution_master_tab():
    st.header("Dilution Master 🧪")
    st.markdown("Calculate dilutions for your reagents, starting from liquid or solid form.")
    reagents = load_reagents()
    reagent_options = [""] + list(reagents.keys())

    st.subheader("Step 1: Define Your Reagent and Solvent")
    selected_reagent = st.selectbox("Select a Saved Reagent (Optional)", reagent_options, key='dm_reagent_select')
    reagent_details = reagents.get(selected_reagent, {})
    default_mw = reagent_details.get('mw', 100.0)
    stock_form = st.radio("Select Stock Form", ('Liquid', 'Solid'), key='stock_form_selector', horizontal=True)
    solvent = st.selectbox("Select Solvent/Diluent", SOLVENT_OPTIONS, key='solvent_selector')
    st.markdown("---")
    mw = None

    if stock_form == 'Liquid':
        st.subheader("Step 2: Define Stock and Target Concentrations")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("#### Stock Solution")
            reagent_name = st.text_input("Reagent/Drug Name", value=selected_reagent or "My Reagent", key='dm_reagent_name')
            stock_conc_val = st.number_input("Stock Concentration", value=1.0, min_value=0.0, format="%.4f")
            stock_conc_unit = st.selectbox("Stock Unit", options=ALL_CONC_UNITS, index=1)
            if stock_conc_unit in MOLARITY_CONVERSIONS:
                mw = default_mw
            else:
                mw = st.number_input("Molecular Weight (g/mol)", value=default_mw, min_value=0.01, help="MW is required to convert mass/vol to molarity.", key='dm_mw_liquid')

        with col2:
            st.markdown("#### Target Solution")
            target_conc_val = st.number_input("Target Concentration", value=10.0, min_value=0.0, format="%.4f")
            target_conc_unit = st.selectbox("Target Unit", options=list(MOLARITY_CONVERSIONS.keys()), index=3)
        with col3:
            st.markdown("#### Final Volume")
            final_vol_val = st.number_input("Final Volume", value=1.0, min_value=0.0)
            final_vol_unit = st.selectbox("Final Volume Unit", options=list(VOLUME_CONVERSIONS.keys()), index=1)
    elif stock_form == 'Solid':
        st.subheader("Step 2: Define Solid and Desired Stock Solution")
        col1, col2, col3 = st.columns(3)
        with col1:
            reagent_name = st.text_input("Reagent/Drug Name", value=selected_reagent or "My Reagent", key='dm_reagent_name_solid')
            mw = st.number_input("Molecular Weight (g/mol)", value=default_mw, min_value=0.01, key='dm_mw_solid')
        with col2:
            stock_conc_val = st.number_input("Desired Stock Concentration", value=10.0, min_value=0.0, format="%.4f", key='solid_stock_conc_val')
            stock_conc_unit = st.selectbox("Stock Unit", options=list(MOLARITY_CONVERSIONS.keys()), index=1, key='solid_stock_conc_unit')
        with col3:
            stock_vol_val = st.number_input("Volume of Stock to Make", value=1.0, min_value=0.0, key='solid_stock_vol_val')
            stock_vol_unit = st.selectbox("Stock Volume Unit", options=list(VOLUME_CONVERSIONS.keys()), index=1, key='solid_stock_vol_unit')
        
        st.markdown("---")
        st.subheader("Step 3: Define Final Target Solution")
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            target_conc_val = st.number_input("Target Concentration", value=10.0, min_value=0.0, format="%.4f", key='solid_target_conc_val')
            target_conc_unit = st.selectbox("Target Unit", options=list(MOLARITY_CONVERSIONS.keys()), index=3, key='solid_target_conc_unit')
        with col_t2:
            final_vol_val = st.number_input("Final Volume", value=1.0, min_value=0.0, key='solid_final_vol_val')
            final_vol_unit = st.selectbox("Final Volume Unit", options=list(VOLUME_CONVERSIONS.keys()), index=1, key='solid_final_vol_unit')

    st.markdown("---")
    if st.button("🔬 Calculate Dilution", type="primary"):
        stock_base = 0.0
        if stock_conc_unit in MOLARITY_CONVERSIONS:
            stock_base = stock_conc_val * MOLARITY_CONVERSIONS[stock_conc_unit]
        else:
            if mw is None or mw <= 0:
                st.error("Please provide a valid Molecular Weight (>0) for the liquid stock.")
                return
            conc_in_g_per_L = stock_conc_val * MOLARITY_CONVERSIONS[stock_conc_unit]
            stock_base = conc_in_g_per_L / mw
        target_base = target_conc_val * MOLARITY_CONVERSIONS[target_conc_unit]
        final_vol_base = final_vol_val * VOLUME_CONVERSIONS[final_vol_unit]
        results_data = []
        if stock_form == 'Solid':
            st.markdown("### Results")
            st.subheader("Part 1: Prepare Stock from Solid")
            stock_vol_base = stock_vol_val * VOLUME_CONVERSIONS[stock_vol_unit]
            if mw <= 0 or stock_base <= 0 or stock_vol_base <= 0:
                st.warning("MW, stock concentration, and volume must be > 0.")
                return
            mass_needed_g = stock_base * stock_vol_base * mw
            mass_needed_mg = mass_needed_g * 1000
            st.success(f"To create your **{stock_conc_val} {stock_conc_unit} stock**:\n"
                       f"1. **Weigh out `{mass_needed_mg:,.4f} mg`** of **{reagent_name}**.\n"
                       f"2. **Dissolve in `{stock_vol_val} {stock_vol_unit}`** of **{solvent}**.")
            st.subheader("Part 2: Dilute Stock to Final Concentration")
            results_data.append({"Task": "Prepare Stock", "Parameter": "Mass to Weigh", "Value": f"{mass_needed_mg:,.4f} mg"})
            results_data.append({"Task": "Prepare Stock", "Parameter": "Solvent Volume", "Value": f"{stock_vol_val} {stock_vol_unit}"})
        if stock_base <= target_base:
            st.error("Target concentration must be lower than stock concentration.")
            return
        if stock_base <= 0 or target_base <= 0 or final_vol_base <= 0:
            st.warning("Concentrations and volume must be > 0.")
            return
        dilution_factor = stock_base / target_base
        stock_vol_needed_base = (target_base * final_vol_base) / stock_base
        diluent_vol_needed_base = final_vol_base - stock_vol_needed_base
        stock_vol_ul = stock_vol_needed_base * 1e6
        diluent_vol_ul = diluent_vol_needed_base * 1e6
        st.info(f"**Total Dilution Factor Needed:** {dilution_factor:,.2f}-fold")
        st.success(f"1. **Take `{stock_vol_ul:,.2f} µL`** of your **{stock_conc_val} {stock_conc_unit} {reagent_name}** stock.\n"
                   f"2. **Add to `{diluent_vol_ul:,.2f} µL`** of **{solvent}**.\n"
                   f"3. This gives **{final_vol_val} {final_vol_unit}** at **{target_conc_val} {target_conc_unit}**.")
        results_data.append({"Task": "Final Dilution", "Parameter": "Stock Volume Needed", "Value": f"{stock_vol_ul:,.2f} µL"})
        results_data.append({"Task": "Final Dilution", "Parameter": "Diluent Volume Needed", "Value": f"{diluent_vol_ul:,.2f} µL"})
        df_results = pd.DataFrame(results_data)
        st.dataframe(df_results, width='stretch')
        create_download_button(df_results, f'dilution_calculation_{reagent_name}.csv')

# --- Tab 3: Serial Dilution Planner ---
def serial_dilution_planner_tab():
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
        total_diluent_ul = total_diluent_needed_base * 1e6
        diluent_for_intermediate_ul = diluent_for_intermediate_base * 1e6
        diluent_for_final_tube_ul = diluent_for_final_tube_base * 1e6
        transfer_vol_ul = transfer_vol_base * 1e6
        
        st.subheader("Results")
        st.success(f"**Total Stock Needed (for first tube):** `{stock_for_intermediate_ul:,.2f} µL` of **{reagent_name}**\n\n"
                   f"**Total {solvent} Needed:** `{total_diluent_ul:,.2f} µL`")

        st.markdown("#### Protocol for Constant Final Volume")
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

# --- Tab 4: IC50 Planner ---
def ic50_planner_tab():
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
        est_ic50_val = st.number_input("Estimated IC50", value=100.0, min_value=0.0, format="%.4f", key='ic50_est_val')
        target_conc_unit = st.selectbox("Unit for IC50 & Series", list(MOLARITY_CONVERSIONS.keys()), index=3, key='ic50_target_unit')
    with col4:
        st.markdown("##### Number of Points per Range")
        num_sparse_upper = st.number_input("Upper Sparse", min_value=0, value=2, step=1)
        num_dense = st.number_input("Dense", min_value=2, value=6, step=1)
        num_sparse_lower = st.number_input("Lower Sparse", min_value=0, value=2, step=1)
    with col5:
        st.markdown("##### Dilution Factors per Range")
        sparse_factor = st.number_input("Sparse Factor", min_value=1.1, value=10.0, step=0.1)
        dense_factor = st.number_input("Dense Factor", min_value=1.1, value=2.0, step=0.1)

    st.markdown("---")

    if st.button("🚀 Generate Cascading Protocol", type="primary"):
        # Convert all inputs to base units (M and L) for calculation
        main_stock_base = stock_conc_val * MOLARITY_CONVERSIONS[stock_conc_unit]
        highest_conc_base = highest_conc_val * MOLARITY_CONVERSIONS[highest_conc_unit]
        final_vol_base = final_vol_val * VOLUME_CONVERSIONS[final_vol_unit]

        # --- REWRITTEN: Concentration Generation Logic ---
        upper_sparse_concs, dense_concs, lower_sparse_concs = [], [], []
        
        # 1. Generate Upper Sparse concentrations
        if num_sparse_upper > 0:
            current_conc = highest_conc_base
            for _ in range(num_sparse_upper):
                upper_sparse_concs.append(current_conc)
                current_conc /= sparse_factor
        
        # 2. Generate Dense concentrations
        if num_dense > 0:
            # Start dense series from the next dilution step after the upper sparse series
            start_conc_dense = (upper_sparse_concs[-1] / sparse_factor) if upper_sparse_concs else highest_conc_base
            current_conc = start_conc_dense
            for _ in range(num_dense):
                dense_concs.append(current_conc)
                current_conc /= dense_factor

        # 3. Generate Lower Sparse concentrations
        if num_sparse_lower > 0:
            # Start lower series from the next dilution step after the dense series
            start_conc_lower = (dense_concs[-1] / dense_factor) if dense_concs else highest_conc_base
            current_conc = start_conc_lower
            for _ in range(num_sparse_lower):
                lower_sparse_concs.append(current_conc)
                current_conc /= sparse_factor

        final_concentrations = upper_sparse_concs + dense_concs + lower_sparse_concs
        
        # --- Helper for protocol generation ---
        def generate_protocol_section(title, concs, factor, start_stock_conc, start_stock_name):
            if not concs: return None
            
            st.markdown(f"#### {title}")
            intermediate_stock_conc = concs[0]

            st.markdown(f"**Step 1: Prepare Starting Stock for this Range (`{format_molarity(intermediate_stock_conc)}`)**")
            # For the very first section, the stock is prepared from the main stock
            if title == "Upper Sparse Range Protocol":
                # This is a direct dilution to make the first intermediate stock
                stock_vol_needed = (intermediate_stock_conc * final_vol_base) / start_stock_conc
                diluent_vol_needed = final_vol_base - stock_vol_needed
                st.success(f"To create the first working stock for this series:\n"
                           f"- Take **{stock_vol_needed * 1e6:.2f} µL** of your **{start_stock_name}**.\n"
                           f"- Add **{diluent_vol_needed * 1e6:.2f} µL** of solvent.\n"
                           f"This makes your `{format_molarity(intermediate_stock_conc)}` stock.")
            else:
                # For subsequent sections, the stock is from the extra tube of the previous dilution
                st.success(f"Take the **{start_stock_name}** you prepared in the previous step to use as the stock for this range.")

            st.markdown("**Step 2: Perform Serial Dilution**")
            transfer_vol = final_vol_base / (factor - 1) if factor > 1 else final_vol_base
            intermediate_tube_vol = final_vol_base + transfer_vol
            stock_for_first_tube = intermediate_tube_vol / factor
            diluent_for_intermediate_tubes = intermediate_tube_vol - stock_for_first_tube
            diluent_for_last_tube = final_vol_base - (final_vol_base / factor)

            is_last_stage = (title == "Lower Sparse Range Protocol")
            num_tubes = len(concs) if is_last_stage or (title == "Dense Range Protocol" and not lower_sparse_concs) else len(concs) + 1
            extra_tube_text = "" if is_last_stage or (title == "Dense Range Protocol" and not lower_sparse_concs) else f" (Tube {num_tubes} will be the stock for the next range)"

            protocol_steps = [f"1. **Prepare {num_tubes} tubes.**{extra_tube_text}"]
            if num_tubes > 1:
                protocol_steps.append(f"2. **Tubes 1 to {num_tubes-1}:** Add **{diluent_for_intermediate_tubes * 1e6:.2f} µL** of solvent.")
                protocol_steps.append(f"3. **Last Tube ({num_tubes}):** Add **{diluent_for_last_tube * 1e6:.2f} µL** of solvent.")
            else:
                 protocol_steps.append(f"2. **To Tube 1:** Add **{diluent_for_last_tube * 1e6:.2f} µL** of solvent.")
            
            protocol_steps.append(f"4. **Tube 1:** Add **{stock_for_first_tube * 1e6:.2f} µL** of your `{format_molarity(intermediate_stock_conc)}` stock. Mix well.")
            protocol_steps.append(f"5. **Transfer {transfer_vol * 1e6:.2f} µL** sequentially from Tube 1 to Tube {num_tubes}.")
            
            st.info("\n".join(protocol_steps))
            
            return concs[-1] / factor if not is_last_stage and not (title == "Dense Range Protocol" and not lower_sparse_concs) else None

        st.subheader("Results")
        # --- Generate Protocol for each section ---
        dense_stock_conc = generate_protocol_section("Upper Sparse Range Protocol", upper_sparse_concs, sparse_factor, main_stock_base, f"Main Stock ({format_molarity(main_stock_base)})")
        if dense_concs:
            lower_stock_conc = generate_protocol_section("Dense Range Protocol", dense_concs, dense_factor, dense_stock_conc, f"'{format_molarity(dense_stock_conc)}' Stock (from previous step)")
        if lower_sparse_concs:
            generate_protocol_section("Lower Sparse Range Protocol", lower_sparse_concs, sparse_factor, lower_stock_conc, f"'{format_molarity(lower_stock_conc)}' Stock (from previous step)")

        # --- Display Final Summary Table ---
        summary_data = [{"Point #": i + 1, "Final Concentration": format_molarity(c)} for i, c in enumerate(final_concentrations)]
        df_summary = pd.DataFrame(summary_data)
        st.markdown("#### Final Concentration Summary")
        st.dataframe(df_summary, width='stretch')
        create_download_button(df_summary, f'IC50_summary_{reagent_name}.csv')

# --- Tab 5: Reagent Manager ---
def reagent_manager_tab():
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
