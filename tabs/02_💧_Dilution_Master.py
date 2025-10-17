import streamlit as st
import pandas as pd

from common import (
    ALL_CONC_UNITS,
    MOLARITY_CONVERSIONS,
    VOLUME_CONVERSIONS,
    load_reagents,
    save_reagents,
    create_download_button,
    SOLVENT_OPTIONS
)

def run_tab():
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
            results_data.append({"Task": "Prepare Stock", "Action": f"Weigh {mass_needed_mg:,.4f} mg", "Source": reagent_name, "Destination": "Stock Tube"})
            results_data.append({"Task": "Prepare Stock", "Action": f"Add {stock_vol_val} {stock_vol_unit}", "Source": solvent, "Destination": "Stock Tube"})
            with st.expander("Show Full Protocol"):
                st.success(f"To create your **{stock_conc_val} {stock_conc_unit} stock**:\n"
                           f"1. **Weigh out `{mass_needed_mg:,.4f} mg`** of **{reagent_name}**.\n"
                           f"2. **Dissolve in `{stock_vol_val} {stock_vol_unit}`** of **{solvent}**.")
            st.subheader("Part 2: Dilute Stock to Final Concentration")

        if stock_base <= target_base:
            st.error("Target concentration must be lower than stock concentration.")
            return
        if stock_base <= 0 or target_base <= 0 or final_vol_base <= 0:
            st.warning("Concentrations and volume must be > 0.")
            return

        dilution_factor = stock_base / target_base
        st.info(f"**Total Dilution Factor Needed:** {dilution_factor:,.2f}-fold")

        if dilution_factor > 100:
            st.warning("Large dilution factor detected. A two-step protocol is recommended for accuracy.")
            
            # Step 1: Intermediate Stock
            factor1 = 100
            intermediate_vol_L = 0.001 # 1mL
            stock_for_inter_L = intermediate_vol_L / factor1
            diluent_for_inter_L = intermediate_vol_L - stock_for_inter_L
            
            # Step 2: Final Solution
            factor2 = dilution_factor / factor1
            stock_for_final_L = final_vol_base / factor2
            diluent_for_final_L = final_vol_base - stock_for_final_L

            results_data.extend([
                {"Task": "Make Intermediate Stock", "Action": f"Transfer {stock_for_inter_L * 1e6:.2f} µL", "Source": "Main Stock", "Destination": "Intermediate Tube"},
                {"Task": "Make Intermediate Stock", "Action": f"Add {diluent_for_inter_L * 1e6:.2f} µL", "Source": solvent, "Destination": "Intermediate Tube"},
                {"Task": "Make Final Solution", "Action": f"Transfer {stock_for_final_L * 1e6:.2f} µL", "Source": "Intermediate Stock", "Destination": "Final Tube"},
                {"Task": "Make Final Solution", "Action": f"Add {diluent_for_final_L * 1e6:.2f} µL", "Source": solvent, "Destination": "Final Tube"},
            ])
            
            with st.expander("Show Full Protocol"):
                st.markdown("**Step 1: Prepare a 1:100 Intermediate Stock**")
                st.success(f"1. **Take `{stock_for_inter_L * 1e6:.2f} µL`** of your main stock.\n"
                           f"2. **Add to `{diluent_for_inter_L * 1e6:.2f} µL`** of {solvent}.\n"
                           f"This creates 1mL of a **1:100 intermediate stock**.")
                st.markdown("**Step 2: Prepare Final Solution**")
                st.success(f"1. **Take `{stock_for_final_L * 1e6:.2f} µL`** of your intermediate stock.\n"
                           f"2. **Add to `{diluent_for_final_L * 1e6:.2f} µL`** of {solvent}.\n"
                           f"This gives **{final_vol_val} {final_vol_unit}** at **{target_conc_val} {target_conc_unit}**.")

        else:
            stock_vol_needed_base = (target_base * final_vol_base) / stock_base
            diluent_vol_needed_base = final_vol_base - stock_vol_needed_base
            stock_vol_ul = stock_vol_needed_base * 1e6
            diluent_vol_ul = diluent_vol_needed_base * 1e6

            results_data.extend([
                {"Task": "Final Dilution", "Action": f"Transfer {stock_vol_ul:,.2f} µL", "Source": "Main Stock", "Destination": "Final Tube"},
                {"Task": "Final Dilution", "Action": f"Add {diluent_vol_ul:,.2f} µL", "Source": solvent, "Destination": "Final Tube"}
            ])
            with st.expander("Show Full Protocol"):
                st.success(f"1. **Take `{stock_vol_ul:,.2f} µL`** of your **{stock_conc_val} {stock_conc_unit} {reagent_name}** stock.\n"
                           f"2. **Add to `{diluent_vol_ul:,.2f} µL`** of **{solvent}**.\n"
                           f"3. This gives **{final_vol_val} {final_vol_unit}** at **{target_conc_val} {target_conc_unit}**.")
        
        df_results = pd.DataFrame(results_data)
        st.dataframe(df_results, width='stretch')
        create_download_button(df_results, f'dilution_calculation_{reagent_name}.csv')