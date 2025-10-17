import os
import json
import streamlit as st
import pandas as pd

# --- Constants ---
REAGENT_FILE = "reagents.json"
SOLVENT_OPTIONS = ["Water", "PBS", "DMSO", "Ethanol", "Methanol", "Culture Medium"]

# --- Dictionaries for Unit Conversions ---
MOLARITY_CONVERSIONS = {'M': 1, 'mM': 1e-3, 'µM': 1e-6, 'nM': 1e-9, 'pM': 1e-12}
MASS_CONVERSIONS = {'g': 1, 'mg': 1e-3, 'µg': 1e-6, 'ng': 1e-9}
VOLUME_CONVERSIONS = {'L': 1, 'mL': 1e-3, 'µL': 1e-6}
MASS_VOL_CONVERSIONS = {
    'g/L': 1, 'mg/L': 1e-3, 'µg/L': 1e-6,
    'g/mL': 1e3, 'mg/mL': 1, 'µg/mL': 1e-3,
    'ng/mL': 1e-6, 'µg/µL': 1, 'ng/µL': 1e-3
}
ALL_CONC_UNITS = list(MOLARITY_CONVERSIONS.keys()) + list(MASS_VOL_CONVERSIONS.keys())


# --- Helper Functions ---

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

def format_molarity(molarity_in_M):
    """Formats a molarity value into the most appropriate unit (M, mM, uM, etc.)."""
    if molarity_in_M == 0:
        return "0M"
    elif molarity_in_M >= 1:
        return f"{molarity_in_M:.4g}M"
    elif molarity_in_M >= 1e-3:
        return f"{molarity_in_M * 1e3:.4g}mM"
    # UPDATED to use 'u' and no space
    elif molarity_in_M >= 1e-6:
        return f"{molarity_in_M * 1e6:.4g}uM"
    # UPDATED to have no space
    elif molarity_in_M >= 1e-9:
        return f"{molarity_in_M * 1e9:.4g}nM"
    # UPDATED to have no space
    else:
        return f"{molarity_in_M * 1e12:.4g}pM"

def format_mass_conc(conc_in_g_per_L):
    """Formats a mass/vol concentration into the most appropriate unit (g/L, mg/L, etc.)."""
    if conc_in_g_per_L == 0:
        return "0g/L"
    if conc_in_g_per_L >= 1:
        return f"{conc_in_g_per_L:.4g}g/L"
    elif conc_in_g_per_L >= 1e-3:
        return f"{conc_in_g_per_L * 1e3:.4g}mg/L"
    # UPDATED to use 'u' and no space
    elif conc_in_g_per_L >= 1e-6:
        return f"{conc_in_g_per_L * 1e6:.4g}ug/L"
    # UPDATED to have no space
    elif conc_in_g_per_L >= 1e-9:
        return f"{conc_in_g_per_L * 1e9:.4g}ng/L"
    # UPDATED to have no space
    else:
        return f"{conc_in_g_per_L * 1e12:.4g}pg/L"

def create_download_button(df: pd.DataFrame, filename: str, label: str = "📥 Download as CSV"):
    """Creates a Streamlit download button for a pandas DataFrame."""
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label=label,
        data=csv,
        file_name=filename,
        mime='text/csv',
    )