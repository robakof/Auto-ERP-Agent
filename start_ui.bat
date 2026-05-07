@echo off
cd /d "%~dp0\tools"
py -m streamlit run app.py --server.headless true --server.port 8501
