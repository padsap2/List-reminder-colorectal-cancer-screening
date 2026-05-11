print("STARTING MAIL SCRIPT")

import os
import win32com.client as win32

from datetime import datetime

# ================================
# CONFIG
# ================================
OUTPUT_FOLDER = (
    r"G:\Studies\Cellule Etudes\Reporting\Marketing"
    r"\List reminder colorectal cancer screening"
)

RECIPIENTS = [
    "patrice.sapalo@partenamut.be"
]

# ================================
# DATE
# ================================
today = datetime.today()

campaign_month = today.month
campaign_year = today.year

# ================================
# FILES
# ================================
files = [

    f"Brussels_eBox_Send_{campaign_month:02d}_{campaign_year}.xlsx",

    f"Brussels_Paper_Send_{campaign_month:02d}_{campaign_year}.xlsx",

    f"Wallonie_eBox_Send_{campaign_month:02d}_{campaign_year}.xlsx",

    f"Wallonie_Paper_Send_{campaign_month:02d}_{campaign_year}.xlsx"
]

# ================================
# OUTLOOK
# ================================
print("OPENING OUTLOOK")

outlook = win32.Dispatch("Outlook.Application")

mail = outlook.CreateItem(0)

mail.To = ";".join(RECIPIENTS)

mail.Subject = (
    f"CRC Screening Lists "
    f"{campaign_month:02d}/{campaign_year}"
)

mail.Body = f"""
Hello,

Please find attached the colorectal cancer screening files
for {campaign_month:02d}/{campaign_year}.

Included:

- Brussels eBox
- Brussels Paper
- Wallonie eBox
- Wallonie Paper

Generated automatically.
"""

# ================================
# ATTACHMENTS
# ================================
for file in files:

    filepath = os.path.join(
        OUTPUT_FOLDER,
        file
    )

    if os.path.exists(filepath):

        mail.Attachments.Add(filepath)

        print(f"Attached: {file}")

    else:

        print(f"Missing file: {file}")

# ================================
# SEND
# ================================
print("SENDING MAIL")

mail.Send()

print("MAIL SENT SUCCESSFULLY")