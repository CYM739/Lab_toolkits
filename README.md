# 🧰 Lab Toolkit

A multi-tool Streamlit application designed to assist with common molecular biology lab calculations and experimental design.

## Features

-   **Experiment Designer**:
    -   **Full Factorial**: Generate all possible combinations of variables.
    -   **Optimized Design (Box-Behnken)**: Create statistically optimized experimental plans for response surface methodology.
-   **Dilution Master**: Calculate dilutions from solid or liquid stocks.
-   **Serial Dilution Planner**: Plan complex serial dilution series with constant volumes.
-   **Reagent Manager**: A local database to store and manage molecular weights and other details of commonly used reagents.

## How to Run

1.  **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd Lab_Toolkit
    ```

2.  **Run the setup script:**
    -   On Windows, simply double-click `start_web.bat`.
    -   This script will automatically create a virtual environment, install the required packages from `requirements.txt`, and launch the Streamlit app.

3.  **Manual Setup (Alternative):**
    ```bash
    # Create a virtual environment
    python -m venv venv

    # Activate it
    # On Windows:
    venv\Scripts\activate
    # On macOS/Linux:
    # source venv/bin/activate

    # Install dependencies
    pip install -r requirements.txt

    # Run the app
    streamlit run app.py
    ```

## Dependencies
- streamlit
- pandas
- pyDOE2