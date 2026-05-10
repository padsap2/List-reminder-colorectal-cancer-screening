# List-reminder-colorectal-cancer-screening
List reminder colorectal cancer screening

# List Reminder Colorectal Cancer Screening

Automation scripts for generating colorectal cancer screening reminder lists for:

- Brussels
- Wallonie

The scripts connect to the DB2 database, identify eligible members, apply business filters, detect eBox activity, and export final reminder files for operational use.

---

# Scripts

## 1. `Cancer_pipeline_automate_Brussels.py`

Generates:

- Brussels eBox reminder list
- Brussels paper reminder list

### Logic

The script:

1. Connects to DB2 using `jaydebeapi` + `jpype`
2. Loads eligible members from:
   - `ODS509.ODS_PSTATA`
   - `ODS509.ODS_PSTATV`
3. Detects opt-out members using:
   - `ODS509.V_ISE_ODS_WWWSIGNAL`
4. Filters:
   - Brussels province only (`PROVSA = 10`)
   - Valid affiliation
   - Valid VPV ranges
   - Active members only
5. Loads eligible population file:
   - `POP_ELIGIBLE_PARTENAMUT_2026_NEW.xlsx`
6. Detects:
   - Members active on eBox
   - Members who did not read previous campaigns
7. Splits:
   - eBox send
   - Paper send
8. Exports final Excel files

### Outputs

- `Brussels_eBox_Send_MM_YYYY.xlsx`
- `Brussels_Paper_Send_MM_YYYY.xlsx`

---

## 2. `Cancer_pipeline_automate_Wallonie.py`

Generates:

- Wallonie eBox reminder list
- Wallonie paper reminder list

### Logic

The script:

1. Connects to DB2 using `jaydebeapi` + `jpype`
2. Loads eligible members from:
   - `ODS509.ODS_PSTATA`
   - `ODS509.ODS_PSTATV`
3. Detects opt-out members using:
   - `ODS509.V_ISE_ODS_WWWSIGNAL`
4. Filters:
   - Wallonie provinces only:
     - 4
     - 5
     - 6
     - 7
     - 12
5. Loads eligible population files:
   - `P80_WLL_PARTENAMUT_2026_ENVOI.xlsx`
   - `P20-80_WLL_PARTENAMUT_2026_ENVOI.xlsx`
   - `P20_WLL_PARTENAMUT_2026_ENVOI.xlsx`
6. Detects:
   - Members active on eBox
   - Members who did not read previous campaigns
7. Removes:
   - Opt-out members
8. Splits:
   - eBox send
   - Paper send
9. Exports final Excel files

### Outputs

- `Wallonie_eBox_Send_MM_YYYY.xlsx`
- `Wallonie_Paper_Send_MM_YYYY.xlsx`

---

# Technologies

- Python 3.11
- pandas
- jaydebeapi
- jpype
- DB2 JDBC Driver (`db2jcc4.jar`)
- openpyxl
- python-dotenv

---

# Required Files

## DB2 Driver

Place in project root:

```text
db2jcc4.jar
```

---

## Population Files

Located in:

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

# Export Location

Generated files are exported to:

```text
G:\Studies\Cellule Etudes\Reporting\Marketing\List reminder colorectal cancer screening
```

---

# Validation Output

Each script prints validation statistics such as:

- Base population
- Opt-out count
- eBox send count
- Paper send count
- Not visited count
- Not read count

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

# Notes

- Scripts are designed for monthly execution.
- Campaign month is automatically derived from current date.
- Previous month is used as data month.
- eBox activity is checked over the last 18 months.
- Duplicate EXIDs are automatically removed.

---

# Author

Patrice Sapalo
