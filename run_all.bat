@echo off

cd /d C:\Users\M509PSAO\Projects\List_reminder_colorectal_cancer_screening

call .venv\Scripts\activate

python Cancer_pipeline_automate_Brussels.py

python Cancer_pipeline_automate_Wallonie.py

python send_mail.py
