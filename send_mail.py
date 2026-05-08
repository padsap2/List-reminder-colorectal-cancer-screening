print("STARTING MAIL SCRIPT")

import os
import smtplib

from email.message import EmailMessage
from datetime import datetime

# ================================
# CONFIG
# ================================
OUTPUT_FOLDER = (
    r"G:\Studies\Cellule Etudes\Reporting\Marketing"
    r"\List reminder colorectal cancer screening"
)

SMTP_SERVER = "smtp.office365.com"
SMTP_PORT = 587

EMAIL_ADDRESS = os.environ.get("EMAIL_USER")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")

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
# MAIL
# ================================
msg = EmailMessage()

msg["Subject"] = (
    f"CRC Screening Lists "
    f"{campaign_month:02d}/{campaign_year}"
)

msg["From"] = EMAIL_ADDRESS
msg["To"] = ",".join(RECIPIENTS)

msg.set_content(f"""
Hello,

Please find attached the colorectal cancer screening files
for {campaign_month:02d}/{campaign_year}.

Included:

- Brussels eBox
- Brussels Paper
- Wallonie eBox
- Wallonie Paper

Generated automatically.
""")

# ================================
# ATTACHMENTS
# ================================
for file in files:

    filepath = os.path.join(
        OUTPUT_FOLDER,
        file
    )

    if os.path.exists(filepath):

        with open(filepath, "rb") as f:

            msg.add_attachment(
                f.read(),
                maintype="application",
                subtype="octet-stream",
                filename=file
            )

        print(f"Attached: {file}")

    else:

        print(f"Missing file: {file}")

# ================================
# SEND
# ================================
print("ABOUT TO SEND MAIL")

with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=60) as server:

    server.starttls()

    server.login(
        EMAIL_ADDRESS,
        EMAIL_PASSWORD
    )

    server.send_message(msg)

print("MAIL REALLY SENT")