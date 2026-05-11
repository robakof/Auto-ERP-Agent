@echo off
cd /d "%~dp0\tools"
py -m streamlit run app.py --server.headless true --server.port 8501 --server.address 192.168.80.4
