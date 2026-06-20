@echo off
echo === Starting Precise3DM Lead Generator ===

REM --- Activate venv ---
call experimental\Scripts\activate.bat

REM --- Run Streamlit app ---
streamlit run streamlit_lead_generator.py

pause
