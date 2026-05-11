# List Reminder Colorectal Cancer Screening

Automation project for generating colorectal cancer screening reminder lists for:

- Brussels
- Wallonie

The project is fully automated through a Jenkins job and exports operational Excel files used for reminder campaigns.

---

# Jenkins Automation

## Jenkins Job Name

```text
List_reminder_colorectal_cancer_screening
```

## Automated Flow

The Jenkins job automatically:

1. Pulls the latest version from GitHub
2. Installs Python dependencies
3. Executes the Brussels pipeline
4. Executes the Wallonie pipeline
5. Exports final Excel files to the shared drive

---

# Scripts

## 1. Brussels Pipeline

### Script

```text
Cancer_pipeline_automate_Brussels.py
```

### Description

Generates:

- Brussels eBox reminder list
- Brussels paper reminder list

### Main Logic

The script:

- Connects to DB2
- Retrieves eligible members
- Applies affiliation filters
- Applies VPV filters
- Filters Brussels members only (`PROVSA = 10`)
- Detects opt-out members
- Detects eBox activity
- Detects members who did not read previous campaigns
- Generates:
  - eBox send list
  - paper send list

### Outputs

```text
Brussels_eBox_Send_MM_YYYY.xlsx
Brussels_Paper_Send_MM_YYYY.xlsx
```

---

## 2. Wallonie Pipeline

### Script

```text
Cancer_pipeline_automate_Wallonie.py
```

### Description

Generates:

- Wallonie eBox reminder list
- Wallonie paper reminder list

### Main Logic

The script:

- Connects to DB2
- Retrieves eligible members
- Applies affiliation filters
- Applies VPV filters
- Filters Wallonie provinces:
  - 4
  - 5
  - 6
  - 7
  - 12
- Detects opt-out members
- Detects eBox activity
- Detects members who did not read previous campaigns
- Generates:
  - eBox send list
  - paper send list

### Outputs

```text
Wallonie_eBox_Send_MM_YYYY.xlsx
Wallonie_Paper_Send_MM_YYYY.xlsx
```

---

# Technologies

- Python 3.11
- pandas
- jaydebeapi
- jpype
- openpyxl
- python-dotenv

---

# Required Files

## DB2 JDBC Driver

Place in project root:

```text
db2jcc4.jar
```

---

# Population Files

## Brussels

```text
POP_ELIGIBLE_PARTENAMUT_2026_NEW.xlsx
```

## Wallonie

```text
P80_WLL_PARTENAMUT_2026_ENVOI.xlsx
P20-80_WLL_PARTENAMUT_2026_ENVOI.xlsx
P20_WLL_PARTENAMUT_2026_ENVOI.xlsx
```

---

# Export Location

Generated files are exported to:

```text
G:\Studies\Cellule Etudes\Reporting\Marketing\List reminder colorectal cancer screening
```

---

# Environment Variables

Create a `.env` file:

```env
DB_PASSWORD=your_password
```

---

# Installation

Install dependencies:

```bash
pip install -r requirements.txt
```

---

# Execution

Run Brussels:

```bash
python Cancer_pipeline_automate_Brussels.py
```

Run Wallonie:

```bash
python Cancer_pipeline_automate_Wallonie.py
```

---

# Validation Output

Both scripts print validation statistics during execution.

Example:

```text
================ VALIDATION ================

BASE: 46158
OPTED OUT: 293
eBox send: 2517
Paper send: 3123
  -- NO EBOX: 1456
  -- NOT READ: 1667
```

---

# Scheduling

The Jenkins job is intended for monthly execution.

The scripts automatically:

- Detect current campaign month
- Use previous month as data month
- Generate monthly exports dynamically

---

# Mail Sending

Automatic mail sending via Jenkins is currently disabled.

Generated files can still be sent manually from a local machine or Visual Studio environment.

---

# Repository

```text
https://github.com/DAnAOps/List-reminder-colorectal-cancer-screening
```

---

# Author

Patrice Sapalo

