import os
os.environ["OPENBLAS_NUM_THREADS"] = "1"

import pandas as pd
import jaydebeapi
import jpype
import gc

from datetime import datetime
from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv, find_dotenv

import warnings
warnings.filterwarnings("ignore")

load_dotenv(find_dotenv())

# ================================
# AUTO CONFIG
# ================================
today = datetime.today()

campaign_year = today.year
campaign_month = today.month

# Previous month
data_date = today - relativedelta(months=1)

data_month = data_date.month
data_year = data_date.year

# ================================
# PERIODS
# ================================
start_of_month = datetime(data_year, data_month, 1)

end_of_month = (
    start_of_month
    + relativedelta(months=1)
    - relativedelta(days=1)
)

start_ts = start_of_month.strftime("%Y-%m-%d 00:00:00")
end_ts = end_of_month.strftime("%Y-%m-%d 23:59:59")

current_start = datetime(
    today.year,
    today.month,
    1
)

current_end = (
    current_start
    + relativedelta(months=1)
    - relativedelta(days=1)
)

current_next = (
    current_start
    + relativedelta(months=1)
)

vpodsa_date_current = current_end.strftime("%Y%m%d")
vpadsa_next_current = current_next.strftime("%Y%m%d")

print("\n================ CONFIG: Wallonie ================")
print("Campaign month:", campaign_month)
print("Data month:", data_month)
print("DB snapshot month:", today.month)

# ================================
# HELPERS
# ================================
def anatella_cast(series):

    return (
        pd.to_numeric(series, errors="coerce")
        .dropna()
        .astype("int64")
        .astype(str)
    )

def normalize_exid(x):

    if pd.isna(x):
        return None

    try:
        return str(int(str(x).strip()))
    except:
        return None

def clean_exid(series):

    return (
        series.apply(
            lambda x: ''.join(x)
            if isinstance(x, tuple)
            else str(x)
        )
        .str.strip()
    )

# ================================
# CONNECTION
# ================================
def connect():

    jar_path = os.path.join(
        os.getcwd(),
        "db2jcc4.jar"
    )

    print("CURRENT DIR:", os.getcwd())
    print("JAR PATH:", jar_path)
    print("JAR EXISTS:", os.path.exists(jar_path))

    java_home = r"C:\Program Files\Java\jdk-17"

    os.environ["JAVA_HOME"] = java_home

    os.environ["PATH"] = (
        java_home + r"\bin;" +
        java_home + r"\bin\server;" +
        os.environ["PATH"]
    )

    if not os.path.exists(jar_path):

        raise FileNotFoundError(
            f"DB2 driver not found at: {jar_path}"
        )

    if not jpype.isJVMStarted():

        jpype.startJVM(
            jpype.getDefaultJVMPath(),
            "-Xmx2g",
            classpath=[jar_path]
        )

    print("JVM STARTED:", jpype.isJVMStarted())

    conn = jaydebeapi.connect(
        "com.ibm.db2.jcc.DB2Driver",
        "jdbc:db2://s998lp1dbbi01.jablux.cpc998.be:50004/ods500",
        ["m509psao", "Oong)ieVoh1W"],
        jars=jar_path
    )

    return conn

conn = connect()

# ================================
# DB QUERY
# ================================
query = f"""
WITH BASE AS (

    SELECT

        TRIM(p.EXIDSA) AS EXID,

        SMALLINT(p.PROVSA) AS PROVSA,

        v.VPV1SV,

        p.NAIDSA,

        SMALLINT(
            CASE
                WHEN s.EXIDSA IS NOT NULL THEN 1
                ELSE 0
            END
        ) AS OPT_OUT_FLAG,

        ROW_NUMBER() OVER (
            PARTITION BY p.EXIDSA
            ORDER BY p.EXIDSA
        ) AS RN

    FROM ODS509.ODS_PSTATA p

    LEFT JOIN ODS509.ODS_PSTATV v
        ON p.EXIDSA = v.EXIDSV

    LEFT JOIN (

        SELECT DISTINCT
            REPLACE(TARGETID, ',', '') AS EXIDSA

        FROM ODS509.V_ISE_ODS_WWWSIGNAL

        WHERE SIGNALID = 'CampagneCC'
          AND INACTIVE = 0

    ) s
        ON p.EXIDSA = s.EXIDSA

    WHERE (

        p.VPODSA >= {vpodsa_date_current}

        AND p.VPACSA <> 'O'

        AND (
            (
                p.VPACSA = 'T'
                AND p.VPADSA <= {vpadsa_next_current}
            )

            OR (

                p.VPACSA IN ('A','B','C','L')

                AND p.VPADSA < {vpadsa_next_current}
            )
        )

        AND p.IV00SA = 'B'

        AND v.VPV1SV >= '000'

        AND (
            v.VPV1SV < '750'
            OR v.VPV1SV > '755'
        )

        -- WALLONIE FILTER
        AND p.PROVSA IN (4,5,6,7,12)
    )
)

SELECT
    EXID,
    PROVSA,
    VPV1SV,
    NAIDSA,
    OPT_OUT_FLAG

FROM BASE

WHERE RN = 1
"""

print("\nLoading optimized DB query...")

df = pd.read_sql(query, conn)

df.columns = [str(c).upper() for c in df.columns]

print("DB FINAL:", len(df))
print("UNIQUE EXID:", df["EXID"].nunique())

# ================================
# MEMORY OPTIMIZATION
# ================================
df["PROVSA"] = pd.to_numeric(
    df["PROVSA"],
    downcast="integer"
)

df["OPT_OUT_FLAG"] = pd.to_numeric(
    df["OPT_OUT_FLAG"],
    downcast="integer"
)

# ================================
# POP FILES
# ================================
pop_files = [
    r"G:\Studies\Cellule Etudes\Reporting\Marketing\List reminder colorectal cancer screening\P80_WLL_PARTENAMUT_2026_ENVOI.xlsx",
    r"G:\Studies\Cellule Etudes\Reporting\Marketing\List reminder colorectal cancer screening\P20-80_WLL_PARTENAMUT_2026_ENVOI.xlsx",
    r"G:\Studies\Cellule Etudes\Reporting\Marketing\List reminder colorectal cancer screening\P20_WLL_PARTENAMUT_2026_ENVOI.xlsx"
]

# ================================
# LOAD + APPEND FILES
# ================================
pop = pd.concat(
    [pd.read_excel(file, usecols=["EXID"]) for file in pop_files],
    ignore_index=True
)

pop.columns = [str(c).upper() for c in pop.columns]

pop["EXID"] = anatella_cast(
    pop["EXID"]
)

pop = pop.drop_duplicates("EXID")

print("POP TOTAL:", len(pop))
print("POP UNIQUE EXID:", pop["EXID"].nunique())

# ================================
# BASE
# ================================
base = pop.merge(
    df,
    on="EXID",
    how="inner"
)

del pop
del df
gc.collect()

print("BASE:", len(base))

# ================================
# OPT OUT COUNT
# ================================
opted_out_count = (
    pd.to_numeric(
        base["OPT_OUT_FLAG"],
        errors="coerce"
    ) == 1
).sum()

print("OPTED OUT MEMBERS:", opted_out_count)

# ================================
# REMOVE OPT OUT
# ================================
base = base[
    pd.to_numeric(
        base["OPT_OUT_FLAG"],
        errors="coerce"
    ) == 0
]

print(
    "BASE FILTERED "
    "(after opt out filter):",
    len(base)
)

# ================================
# BIRTH MONTH
# ================================
base["MOIS_NAISS"] = (
    base["NAIDSA"]
    .astype(str)
    .str[4:6]
    .astype("int8")
)

# ================================
# EBOX READ
# ================================
ebox_query = """
SELECT DISTINCT
    BENEFICIARYEXID

FROM ODS509.V_INF_ODS_DOCUMENT

WHERE ORGANIZATION = '509'
AND "READ" = 1
AND OUTPUTCHANNELS = 'infobox'
AND READDATE >= ADD_MONTHS(CURRENT_DATE, -18)
AND READDATE < DATE '9999-01-01'
"""

ebox_read = pd.read_sql(
    ebox_query,
    conn
)

ebox_read["user_exid"] = clean_exid(
    ebox_read["BENEFICIARYEXID"]
)

ebox_read["user_exid"] = anatella_cast(
    ebox_read["user_exid"]
)

ebox_read["user_exid"] = (
    ebox_read["user_exid"]
    .apply(normalize_exid)
    .str.upper()
)

ebox_read = ebox_read[
    ["user_exid"]
].drop_duplicates()

print("READ count:", len(ebox_read))

# ================================
# NOT READ
# ================================
not_read_query = f"""
SELECT DISTINCT
    BENEFICIARYEXID

FROM ODS509.V_INF_ODS_DOCUMENT

WHERE ORGANIZATION = '509'
AND "READ" = 0
AND RECEIVEDATE BETWEEN TIMESTAMP '{start_ts}'
                     AND TIMESTAMP '{end_ts}'
AND NAME LIKE 'NMKTCBI%'
AND NOTIFICATIONREQUESTSTATUS = 'DELIVERED'
"""

not_read = pd.read_sql(
    not_read_query,
    conn
)

not_read["EXID"] = clean_exid(
    not_read["BENEFICIARYEXID"]
)

not_read["EXID"] = anatella_cast(
    not_read["EXID"]
)

not_read["EXID"] = (
    not_read["EXID"]
    .apply(normalize_exid)
    .str.upper()
)

not_read = not_read[
    ["EXID"]
].drop_duplicates()

print("NOT READ count:", len(not_read))

# ================================
# NORMALIZATION
# ================================
base["EXID"] = (
    base["EXID"]
    .apply(normalize_exid)
    .str.upper()
)

# ================================
# VISITED / NOT VISITED
# ================================
ebox_active_exids = set(
    ebox_read["user_exid"]
)

visited = base[
    base["EXID"].isin(ebox_active_exids)
].drop_duplicates("EXID")

not_visited = base[
    ~base["EXID"].isin(ebox_active_exids)
].drop_duplicates("EXID")

# ================================
# MONTH FILTER
# ================================
visited_month = visited[
    visited["MOIS_NAISS"] == data_month
][["EXID"]]

not_visited_month = not_visited[
    not_visited["MOIS_NAISS"] == data_month
][["EXID"]]

print("NOT VISITED:", len(not_visited_month))
print("VISITED:", len(visited_month))

# ================================
# FINAL LOGIC
# ================================
paper_send_total = pd.concat([
    not_visited_month,
    not_read
]).drop_duplicates(subset=["EXID"])

# ================================
# VALIDATION
# ================================
print("\n================ VALIDATION ================")

print("BASE:", len(base))
print("OPTED OUT:", opted_out_count)
print("eBox send:", len(visited_month))
print("Paper send:", len(paper_send_total))
print("  -- NO EBOX:", len(not_visited_month))
print("  -- NOT READ:", len(not_read))

# ================================
# EXPORT
# ================================
export_path = r"G:\Studies\Cellule Etudes\Reporting\Marketing\List reminder colorectal cancer screening"

visited_month.to_excel(
    os.path.join(
        export_path,
        f"Wallonie_eBox_Send_{campaign_month:02d}_{campaign_year}.xlsx"
    ),
    index=False
)

paper_send_total.to_excel(
    os.path.join(
        export_path,
        f"Wallonie_Paper_Send_{campaign_month:02d}_{campaign_year}.xlsx"
    ),
    index=False
)

print("Export Wallonie completed successfully.")

# ================================
# CLOSE CONNECTION
# ================================
conn.close()