import streamlit as st
import pandas as pd
import itertools
import string
import math
import json
import os

# NEW: Import the library for Box-Behnken design
try:
    from pyDOE2 import bbdesign
except ImportError:
    st.error("The 'pyDOE2' library is not installed. Please run 'pip install pyDOE2' or ensure it's in your requirements.txt file.")
    st.stop()


st.set_page_config(layout="wide", page_title="Lab Toolkit")

# --- Helper Dictionaries and Functions (No changes here) ---

REAGENT_FILE = "reagents.json"

# Define conversion factors relative to a base unit (M, g, L)
MOLARITY_CONVERSIONS = {'M': 1, 'mM': 1e-3, 'µM': 1e-6, 'nM': 1e-9, 'pM': 1e-12}
MASS_CONVERSIONS = {'g': 1, 'mg': 1e-3, 'µg': 1e-6, 'ng': 1e-9}
VOLUME_CONVERSIONS = {'L': 1, 'mL': 1e-3, 'µL': 1e-6}
MASS_VOL_CONVERSIONS = {
    'g/L': 1, 'mg/L': 1e-3, 'µg/L': 1e-6,
    'g/mL': 1e3, 'mg/mL': 1, 'µg/mL': 1e-3,
    'ng/mL': 1e-6, 'µg/µL': 1, 'ng/µL': 1e-3
}

ALL_CONC_UNITS = list(MOLARITY_CONVERSIONS.keys()) + list(MASS_VOL_CONVERSIONS.keys())
SOLVENT_OPTIONS = ["Water", "PBS", "DMSO", "Ethanol", "Methanol", "Culture Medium"]

# --- Reagent Storage Functions (No changes here) ---

def load_reagents():
    """Loads reagents from the JSON file."""
    if not os.path.exists(REAGENT_FILE):
        return {}
    try:
        with open(REAGENT_FILE, 'r') as f:
            content = f.read()
            if not content:
                return {}
            return json.loads(content)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}

def save_reagents(reagents):
    """Saves the reagents dictionary to the JSON file."""
    with open(REAGENT_FILE, 'w') as f:
        json.dump(reagents, f, indent=4)

# --- UI Tabs ---

def format_molarity(molarity_in_M):
    """Formats a molarity value into the most appropriate unit (M, mM, µM, etc.)."""
    if molarity_in_M == 0:
        return "0 M"
    elif molarity_in_M >= 1:
        return f"{molarity_in_M:.4g} M"
    elif molarity_in_M >= 1e-3:
        return f"{molarity_in_M * 1e3:.4g} mM"
    elif molarity_in_M >= 1e-6:
        return f"{molarity_in_M * 1e6:.4g} µM"
    elif molarity_in_M >= 1e-9:
        return f"{molarity_in_M * 1e9:.4g} nM"
    else:
        return f"{molarity_in_M * 1e12:.4g} pM"
        
# --- NEW: DOE Planner Tab ---

def doe_planner_tab():
    """
    This function defines the UI and logic for the DOE Planner tab,
    specifically for generating Box-Behnken Designs.
    """
    st.header("DOE Planner: Box-Behnken Design (BBD)")
    st.info(
        "**Box-Behnken** is an efficient design for fitting response surfaces. "
        "It helps you model quadratic (curved) effects and interactions while avoiding extreme factor combinations (corners).",
        icon="🧪"
    )

    # --- Step 1: Define Factors ---
    st.subheader("Step 1: Define Your Factors (Variables)")
    num_factors = st.number_input(
        "Number of Factors (3 to 7 are typical for BBD)",
        min_value=3, max_value=10, value=4, step=1
    )
    
    center_points = st.number_input(
        "Number of Center Point Replicates",
        min_value=1, max_value=10, value=3, step=1,
        help="Replicates at the center of the design are crucial for estimating experimental error and model fit."
    )

    st.markdown("---")

    # --- Step 2: Define Factor Names and Levels ---
    st.subheader("Step 2: Define Factor Names and Levels (Concentrations)")
    factor_levels = {}
    cols = st.columns(num_factors)

    for i in range(num_factors):
        with cols[i]:
            factor_name = st.text_input(f"Name of Factor {i+1}", value=f"Factor_{string.ascii_uppercase[i]}")
            low_level = st.number_input(f"Low Level (-1) for {factor_name}", value=10.0, format="%.4f", key=f"low_{i}")
            center_level = st.number_input(f"Center Level (0) for {factor_name}", value=50.0, format="%.4f", key=f"center_{i}")
            high_level = st.number_input(f"High Level (+1) for {factor_name}", value=100.0, format="%.4f", key=f"high_{i}")
            
            # Basic validation
            if not low_level < center_level < high_level:
                st.warning("Levels should be in increasing order (Low < Center < High).")
            
            factor_levels[factor_name] = {
                -1: low_level,
                0: center_level,
                1: high_level
            }
            
    st.markdown("---")

    # --- Step 3: Generate Design ---
    st.subheader("Step 3: Generate and Download Design Table")
    if st.button("🚀 Generate Box-Behnken Design", type="primary"):
        try:
            # Generate the coded BBD matrix (-1, 0, 1)
            bbd_matrix = bbdesign(num_factors, center=center_points)
            
            # Convert the matrix to a pandas DataFrame with coded values
            factor_names = list(factor_levels.keys())
            df_coded = pd.DataFrame(bbd_matrix, columns=factor_names)
            
            # Translate coded values to real experimental values
            df_real = df_coded.copy()
            for factor in factor_names:
                df_real[factor] = df_coded[factor].map(factor_levels[factor])
            
            st.session_state['df_bbd_coded'] = df_coded
            st.session_state['df_bbd_real'] = df_real
            
            total_runs = len(df_real)
            st.success(f"Successfully generated a Box-Behnken design with **{total_runs}** experimental runs.")

        except Exception as e:
            st.error(f"An error occurred while generating the design: {e}")
            st.error("Please check that the number of factors is appropriate for BBD (usually >= 3).")

    # --- Display Results ---
    if 'df_bbd_real' in st.session_state:
        df_display = st.session_state['df_bbd_real']
        
        st.markdown("#### Experimental Runs Table (Actual Values)")
        st.dataframe(df_display, use_container_width=True)
        
        csv_data = df_display.to_csv(index=False).encode('utf-8')
        st.download_button(
           label="📥 Download as CSV",
           data=csv_data,
           file_name=f'BBD_{num_factors}factors_{len(df_display)}runs.csv',
           mime='text/csv',
        )
        
        with st.expander("Show Coded Design Matrix (-1, 0, +1)"):
            st.dataframe(st.session_state['df_bbd_coded'], use_container_width=True)


def combination_generator_tab():
    # This function remains unchanged
    st.header("Step 1: Define Your Variables")
    
    num_vars = st.selectbox(
        label="How many variables do you want to combine?",
        options=range(1, 11),
        index=2,
        help="Select the total number of factors you are testing."
    )

    variable_names = list(string.ascii_uppercase[:num_vars])
    
    st.markdown("---")
    
    st.header("Step 2: Set Number of Values for Each Variable")
    value_counts_cols = st.columns(num_vars)
    value_counts = {}
    for i, var_name in enumerate(variable_names):
        with value_counts_cols[i]:
            value_counts[var_name] = st.number_input(
                label=f"Values for Var '{var_name}'",
                min_value=1,
                value=3,
                key=f'value_count_{var_name}'
            )
            
    st.markdown("---")

    st.header("Step 3: Input the Specific Values")
    st.info("Enter your values separated by commas. For example: `10, 20, 30` or `low, medium, high`.", icon="💡")
    
    value_inputs_cols = st.columns(num_vars)
    all_inputs_valid = True
    variable_value_lists = []

    for i, var_name in enumerate(variable_names):
        with value_inputs_cols[i]:
            input_str = st.text_input(
                label=f"Enter {value_counts[var_name]} values for Var '{var_name}'",
                key=f'values_for_{var_name}'
            )
            
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
    
    st.header("Step 4: Generate & Download")

    if st.button("🚀 Generate Combinations", disabled=not all_inputs_valid, type="primary"):
        if all_inputs_valid:
            combinations = list(itertools.product(*variable_value_lists))
            df = pd.DataFrame(combinations, columns=variable_names)
            st.session_state['df_combinations'] = df
        else:
            st.warning("Please fill in all value fields correctly before generating.")

    if 'df_combinations' in st.session_state:
        df_results = st.session_state['df_combinations']
        st.success(f"Successfully generated **{len(df_results)}** combinations!")
        st.dataframe(df_results, use_container_width=True)
        csv_data = df_results.to_csv(index=False).encode('utf-8')
        st.download_button(
           label="📥 Download as CSV",
           data=csv_data,
           file_name='combinations_data.csv',
           mime='text/csv',
        )

def dilution_master_tab():
    # This function remains unchanged
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
            if stock_conc_unit in MASS_VOL_CONVERSIONS:
                mw = st.number_input("Molecular Weight (g/mol)", value=default_mw, min_value=0.01, help="MW is required to convert mass/vol to molarity for M1V1 calculations.", key='dm_mw_liquid')

        with col2:
            st.markdown("#### Target Solution")
            st.write("") 
            target_conc_val = st.number_input("Target Concentration", value=10.0, min_value=0.0, format="%.4f")
            target_conc_unit = st.selectbox("Target Unit", options=list(MOLARITY_CONVERSIONS.keys()), index=3)
        with col3:
            st.markdown("#### Final Volume")
            st.write("")
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
        elif stock_conc_unit in MASS_VOL_CONVERSIONS:
            if mw is None or mw <= 0:
                st.error("Please provide a valid Molecular Weight (>0) for the liquid stock to proceed with mass/volume units.")
                return
            conc_in_g_per_L = stock_conc_val * MASS_VOL_CONVERSIONS[stock_conc_unit]
            stock_base = conc_in_g_per_L / mw

        target_base = target_conc_val * MOLARITY_CONVERSIONS[target_conc_unit]
        final_vol_base = final_vol_val * VOLUME_CONVERSIONS[final_vol_unit]

        if stock_form == 'Solid':
            st.markdown("### Results")
            st.subheader("Part 1: Prepare Stock from Solid")
            stock_vol_base = stock_vol_val * VOLUME_CONVERSIONS[stock_vol_unit]
            
            if mw <= 0 or stock_base <= 0 or stock_vol_base <= 0:
                st.warning("Molecular weight, stock concentration, and volume must be greater than zero.")
                return

            mass_needed_g = stock_base * stock_vol_base * mw
            mass_needed_mg = mass_needed_g * 1000

            st.success(f"To create your **{stock_conc_val} {stock_conc_unit} stock** solution:\n"
                       f"1. **Weigh out `{mass_needed_mg:,.4f} mg`** of **{reagent_name}**.\n"
                       f"2. **Dissolve it in `{stock_vol_val} {stock_vol_unit}`** of **{solvent}**.")

            with st.expander("Show Mass Calculation Details"):
                st.latex(r"\text{Mass (g)} = \text{Concentration (mol/L)} \times \text{Volume (L)} \times \text{MW (g/mol)}")
                st.markdown(f"- Concentration = ${stock_conc_val}$ ${stock_conc_unit}$ (${stock_base:.2e}$ M)\n"
                            f"- Volume = ${stock_vol_val}$ ${stock_vol_unit}$ (${stock_vol_base:.2e}$ L)\n"
                            f"- MW = ${mw}$ g/mol")
                st.latex(f"\\text{{Mass}} = ({stock_base:.2e}) \\times ({stock_vol_base:.2e}) \\times ({mw:.2f}) = {mass_needed_g:.2e} \\text{{ g}} \\rightarrow \\mathbf{{{mass_needed_mg:.4f} \\text{{ mg}}}}")
            
            st.subheader("Part 2: Dilute Stock to Final Concentration")

        if stock_base <= target_base:
            st.error("Target concentration must be lower than stock concentration.")
            return
        if stock_base == 0 or target_base == 0 or final_vol_base == 0:
            st.warning("Concentrations and volume must be greater than zero.")
            return

        dilution_factor = stock_base / target_base
        stock_vol_needed_base = (target_base * final_vol_base) / stock_base
        diluent_vol_needed_base = final_vol_base - stock_vol_needed_base
        
        stock_vol_ul = stock_vol_needed_base * 1e6
        diluent_vol_ul = diluent_vol_needed_base * 1e6

        st.info(f"**Total Dilution Factor Needed:** {dilution_factor:,.2f}-fold (from {stock_conc_val} {stock_conc_unit} stock)")

        if dilution_factor <= 1000:
            st.markdown("#### Recommended: Direct Dilution")
            st.success(f"1. **Take `{stock_vol_ul:,.2f} µL`** of your **{stock_conc_val} {stock_conc_unit} {reagent_name}** stock.\n"
                       f"2. **Add it to `{diluent_vol_ul:,.2f} µL`** of **{solvent}**.\n"
                       f"3. This gives you **{final_vol_val} {final_vol_unit}** at **{target_conc_val} {target_conc_unit}**.")
            
            with st.expander("Show Dilution Calculation Details"):
                st.latex(r"M_1 V_1 = M_2 V_2 \quad \rightarrow \quad V_1 = \frac{M_2 V_2}{M_1}")
                st.markdown(f"- $M_1$ = Stock Conc. = {stock_conc_val} {stock_conc_unit} ({stock_base:.2e} M)\n"
                            f"- $V_1$ = Volume of Stock = **?**\n"
                            f"- $M_2$ = Target Conc. = {target_conc_val} {target_conc_unit} ({target_base:.2e} M)\n"
                            f"- $V_2$ = Final Volume = {final_vol_val} {final_vol_unit} ({final_vol_base:.2e} L)")
                st.latex(f"V_1 = \\frac{{({target_base:.2e}) \\times ({final_vol_base:.2e})}}{{({stock_base:.2e})}} = {stock_vol_needed_base:.2e} \\text{{ L}} \\rightarrow \\mathbf{{{stock_vol_ul:.2f} \\text{{ µL}}}}")
        
        else:
            st.markdown("#### Recommended: Serial Dilution")
            st.warning("Dilution factor is high. A serial dilution is recommended for accuracy.", icon="⚠️")

def serial_dilution_planner_tab():
    # This function remains unchanged
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
        stock_conc_unit = st.selectbox("Stock Unit", options=ALL_CONC_UNITS, index=7, key='serial_stock_unit')
        
    with col2:
        st.markdown("#### Series Parameters")
        num_dilutions = st.number_input("Number of Dilutions in Series", min_value=1, max_value=20, value=10, step=1)
        dilution_factor = st.number_input("Dilution Factor per Step", min_value=1.1, value=10.0, step=0.1, format="%.1f", help="e.g., 10 for a 1:10 dilution, 2 for a 1:2 dilution.")
        solvent = st.selectbox("Solvent/Diluent", SOLVENT_OPTIONS, key='serial_solvent_selector')
    with col3:
        st.markdown("#### Volume & MW")
        final_vol_val = st.number_input("Final Volume per Tube", value=1000.0, min_value=0.0, key='serial_final_vol_val')
        final_vol_unit = st.selectbox("Volume Unit", options=list(VOLUME_CONVERSIONS.keys()), index=2, key='serial_final_vol_unit')
        mw = st.number_input("Molecular Weight (g/mol) (Optional)", value=default_mw, min_value=0.0, format="%.4f", key='serial_mw', help="If > 0, molarity will be calculated for mass/vol units.")

    st.markdown("---")
    
    if st.button("🗓️ Plan Dilution Series", type="primary"):
        final_vol_base = final_vol_val * VOLUME_CONVERSIONS[final_vol_unit]
        transfer_vol_base = final_vol_base / (dilution_factor - 1)
        intermediate_vol_base = final_vol_base + transfer_vol_base
        stock_for_intermediate_base = intermediate_vol_base / dilution_factor
        diluent_for_intermediate_base = intermediate_vol_base - stock_for_intermediate_base
        stock_for_final_tube_base = final_vol_base / dilution_factor
        diluent_for_final_tube_base = final_vol_base - stock_for_final_tube_base
        
        if num_dilutions > 1:
            total_diluent_needed_base = (diluent_for_intermediate_base * (num_dilutions - 1)) + diluent_for_final_tube_base
        else:
            total_diluent_needed_base = diluent_for_final_tube_base

        stock_for_intermediate_ul = stock_for_intermediate_base / VOLUME_CONVERSIONS['µL']
        diluent_for_intermediate_ul = diluent_for_intermediate_base / VOLUME_CONVERSIONS['µL']
        diluent_for_final_tube_ul = diluent_for_final_tube_base / VOLUME_CONVERSIONS['µL']
        total_diluent_ul = total_diluent_needed_base / VOLUME_CONVERSIONS['µL']
        transfer_vol_ul = transfer_vol_base / VOLUME_CONVERSIONS['µL']


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
        concentrations = []
        
        initial_conc_M = None
        is_molar = False
        if stock_conc_unit in MOLARITY_CONVERSIONS:
            initial_conc_M = stock_conc_val * MOLARITY_CONVERSIONS[stock_conc_unit]
            is_molar = True
        elif stock_conc_unit in MASS_VOL_CONVERSIONS and mw > 0:
            conc_in_g_per_L = stock_conc_val * MASS_VOL_CONVERSIONS[stock_conc_unit]
            initial_conc_M = conc_in_g_per_L / mw
            is_molar = True

        current_conc_val = stock_conc_val
        current_conc_M_val = initial_conc_M

        for _ in range(num_dilutions):
            if is_molar:
                current_conc_M_val /= dilution_factor
                concentrations.append(format_molarity(current_conc_M_val))
            else:
                current_conc_val /= dilution_factor
                concentrations.append(f"{current_conc_val:,.4g} {stock_conc_unit}")
        
        df_summary = pd.DataFrame({
            'Tube #': range(1, num_dilutions + 1),
            'Final Concentration': concentrations
        })
        st.dataframe(df_summary, use_container_width=True)

def reagent_manager_tab():
    # This function remains unchanged
    st.header("Reagent Manager 📚")
    st.markdown("Store and manage your commonly used reagents.")

    reagents = load_reagents()

    with st.expander("➕ Add New Reagent", expanded=True):
        with st.form("new_reagent_form", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            with col1:
                name = st.text_input("Reagent Name*")
            with col2:
                mw = st.number_input("Molecular Weight (g/mol)*", min_value=0.01, format="%.4f")
            with col3:
                manufacturer = st.text_input("Manufacturer/Cat# (Optional)")
            
            submitted = st.form_submit_button("💾 Save New Reagent")
            if submitted:
                if not name or mw <= 0:
                    st.error("Reagent Name and a valid Molecular Weight are required.")
                elif name in reagents:
                    st.error(f"Reagent '{name}' already exists. Use the 'Edit Reagent' section to modify it.")
                else:
                    reagents[name] = {"mw": mw, "manufacturer": manufacturer}
                    save_reagents(reagents)
                    st.success(f"Saved '{name}' to your reagent list.")
                    st.experimental_rerun()
    
    st.markdown("---")

    st.subheader("Edit Reagent")
    if not reagents:
        st.info("No reagents to edit. Add a reagent above to get started.")
    else:
        reagent_to_edit = st.selectbox("Select Reagent to Edit", options=[""] + list(reagents.keys()))
        if reagent_to_edit:
            reagent_data = reagents[reagent_to_edit].copy()
            with st.form(f"edit_{reagent_to_edit}"):
                st.text_input("Reagent Name", value=reagent_to_edit, disabled=True)
                
                reagent_data['mw'] = st.number_input("Molecular Weight (g/mol)*", value=reagent_data.get('mw', 0.0), min_value=0.01, format="%.4f")
                reagent_data['manufacturer'] = st.text_input("Manufacturer/Cat#", value=reagent_data.get('manufacturer', ''))

                custom_keys = [k for k in reagent_data.keys() if k not in ['mw', 'manufacturer']]
                for key in custom_keys:
                    reagent_data[key] = st.text_input(key.capitalize(), value=reagent_data[key])
                
                st.markdown("###### Add a new field")
                col1, col2 = st.columns(2)
                with col1:
                    new_field_key = st.text_input("Field Name")
                with col2:
                    new_field_value = st.text_input("Field Value")

                update_submitted = st.form_submit_button("💾 Update Reagent")
                if update_submitted:
                    if new_field_key and new_field_value:
                        reagent_data[new_field_key] = new_field_value
                    
                    reagents[reagent_to_edit] = reagent_data
                    save_reagents(reagents)
                    st.success(f"Updated '{reagent_to_edit}'.")
                    st.experimental_rerun()

    st.markdown("---")
    
    st.subheader("Stored Reagents")
    if not reagents:
        st.info("No reagents saved yet.")
    else:
        all_keys = set()
        for data in reagents.values():
            all_keys.update(data.keys())
        
        preferred_order = ['mw', 'manufacturer']
        sorted_keys = sorted(all_keys, key=lambda k: (k not in preferred_order, k))

        reagent_list = []
        for name, data in reagents.items():
            row = {"Reagent Name": name}
            for key in sorted_keys:
                row[key.replace('_', ' ').capitalize()] = data.get(key, "N/A")
            reagent_list.append(row)
        
        df = pd.DataFrame(reagent_list)
        st.dataframe(df, use_container_width=True)

        st.subheader("Delete Reagent")
        reagent_to_delete = st.selectbox("Select Reagent to Delete", options=[""] + list(reagents.keys()), key='delete_reagent_select')
        if st.button("🗑️ Delete Selected Reagent", disabled=not reagent_to_delete):
            if reagent_to_delete in reagents:
                del reagents[reagent_to_delete]
                save_reagents(reagents)
                st.success(f"Deleted '{reagent_to_delete}'.")
                st.experimental_rerun()


def main():
    """
    Main function to run the Streamlit application UI and logic.
    """
    st.title("🧰 Lab Toolkit")
    
    # NEW: Add the DOE Planner tab
    tab_titles = [
        "🧪 DOE Planner", 
        "🔀 Combination Generator", 
        "💧 Dilution Master", 
        "📋 Serial Dilution Planner", 
        "📚 Reagent Manager"
    ]
    
    tabs = st.tabs(tab_titles)
    
    with tabs[0]:
        doe_planner_tab()
    with tabs[1]:
        combination_generator_tab()
    with tabs[2]:
        dilution_master_tab()
    with tabs[3]:
        serial_dilution_planner_tab()
    with tabs[4]:
        reagent_manager_tab()

if __name__ == "__main__":
    main()