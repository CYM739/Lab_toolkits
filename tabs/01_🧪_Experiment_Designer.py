import streamlit as st
import pandas as pd
import itertools
import string
from pyDOE2 import bbdesign
from common import create_download_button

# --- Tab 1: Experiment Designer ---
def run_tab():
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
