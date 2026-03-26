@echo off
cd /d "D:\UdzialySieciowe\Aplikacje nie ruszac, nie zmieniac\ui"
py -m streamlit run tools/app.py --server.headless true --server.port 8501
