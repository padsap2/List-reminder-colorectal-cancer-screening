# %%
import os
os.environ["OPENBLAS_NUM_THREADS"] = "1"

import pandas as pd
import jaydebeapi
import jpype

from datetime import datetime
from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv, find_dotenv

import warnings
warnings.filterwarnings("ignore")

load_dotenv(find_dotenv())

# ================================
# CONFIG
# ================================
campaign_year = 2026
campaign_month = 4

data_date = (
    datetime(campaign_year, campaign_month, 1)
    - relativedelta(months=1)
)

data_month = data_date.month
data_year = data_date.year

start_of_month = datetime(data_year, data_month, 1)

end_of_month = (
    start_of_month
    + relativedelta(months=1)
    - relativedelta(days=1)
)

start_ts = start_of_month.strftime("%Y-%m-%d 00:00:00")
end_ts = end_of_month.strftime("%Y-%m-%d 23:59:59")

today = datetime.today()

current_start = datetime(today.year, today.month, 1)

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

print("\n================ CONFIG: Brussels ================")
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
            lambda x: ''.join(x) if isinstance(x, tuple) else str(x)
        )
        .str.strip()
    )

# ================================
# CONNECTION
# ================================
def connect():

    jar_path = r"C:\db2\db2jcc4.jar"

    java_home = r"C:\Program Files\Java\jdk-17"

    os.environ["JAVA_HOME"] = java_home

    os.environ["PATH"] = (
        java_home + r"\bin;" +
        java_home + r"\bin\server;" +
        os.environ["PATH"]
    )

    if not jpype.isJVMStarted():

        jpype.startJVM(
            java_home + r"\bin\server\jvm.dll",
            "-Xmx2g",
            "-Djava.class.path=" + jar_path
        )

    conn = jaydebeapi.connect(
        "com.ibm.db2.jcc.DB2Driver",
        "jdbc:db2://s998lp1dbbi01.jablux.cpc998.be:50004/ods500",
        ["m509psao", os.getenv("DB_PASSWORD")]
    )

    return conn

conn = connect()

# ================================
# DB QUERY
# ================================
query = f"""
SELECT
    p.EXIDSA,
    p.PROVSA,
    v.VPV1SV,
    p.NAIDSA,

    CASE
        WHEN s.EXIDSA IS NOT NULL THEN 1
        ELSE 0
    END AS OPT_OUT_FLAG

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
)
"""

df = pd.read_sql(query, conn)

df.columns = [str(c).upper() for c in df.columns]

print("\nDB RAW:", len(df))
print("DB UNIQUE:", df["EXIDSA"].nunique())

# ================================
# CLEAN DB
# ================================
df["EXID"] = (
    df["EXIDSA"]
    .astype(str)
    .str.strip()
)

df["VPV1SV"] = (
    df["VPV1SV"]
    .astype(str)
)

df = df[
    (df["VPV1SV"] >= "000")
    &
    (
        (df["VPV1SV"] < "750")
        |
        (df["VPV1SV"] > "755")
    )
]

df = df.groupby(
    "EXID",
    as_index=False
).agg({
    "PROVSA": "first",
    "VPV1SV": "first",
    "OPT_OUT_FLAG": "max",
    "NAIDSA": "first"
})

print("DB FINAL:", len(df))

# ================================
# POP
# ================================
pop = pd.read_excel(
    r"C:\Users\M509PSAO\Desktop\EXIDs\POP_ELIGIBLE_PARTENAMUT_2026_NEW.xlsx"
)

pop["EXID"] = anatella_cast(
    pop["EXID"]
)

pop = pop.drop_duplicates("EXID")

print("POP:", len(pop))

# ================================
# BASE
# ================================
base = pop.merge(
    df,
    on="EXID",
    how="inner"
)

# ================================
# FILTERS
# ================================
base = base[

    (
        pd.to_numeric(
            base["PROVSA"],
            errors="coerce"
        ) == 10
    )

    &

    (
        pd.to_numeric(
            base["OPT_OUT_FLAG"],
            errors="coerce"
        ) == 0
    )
]

print("BASE FILTERED:", len(base))

base["MOIS_NAISS"] = (
    base["NAIDSA"]
    .astype(str)
    .str[4:6]
    .astype(int)
)

# ================================
# MYMUT
# ================================
mymut = pd.read_excel(
    r"C:\Users\M509PSAO\Desktop\EXIDs\Mymut_accounts_03.xlsx",
    usecols=[
        "EXTERNAL_ID",
        "MMT_HAS_MYMUT_ACCOUNT_ISACTIVE_CNT"
    ]
)

mymut = mymut[
    mymut["MMT_HAS_MYMUT_ACCOUNT_ISACTIVE_CNT"] == 1
]

mymut["EXTERNAL_ID"] = anatella_cast(
    mymut["EXTERNAL_ID"]
)

mymut = mymut.drop_duplicates("EXTERNAL_ID")

print("Mymut count:", len(mymut))

base["EXID"] = (
    base["EXID"]
    .astype(str)
    .str.strip()
)

mymut["EXTERNAL_ID"] = (
    mymut["EXTERNAL_ID"]
    .astype(str)
    .str.strip()
)

base = base.merge(
    mymut[["EXTERNAL_ID"]],
    left_on="EXID",
    right_on="EXTERNAL_ID",
    how="left"
).drop(columns=["EXTERNAL_ID"])

# ================================
# EBOX READ
# ================================
ebox_read = pd.read_sql(
    """
    SELECT DISTINCT
        BENEFICIARYEXID

    FROM ODS509.V_INF_ODS_DOCUMENT

    WHERE ORGANIZATION = '509'
    AND "READ" = 1
    AND OUTPUTCHANNELS = 'infobox'
    AND READDATE >= ADD_MONTHS(CURRENT_DATE, -18)
    AND READDATE < DATE '9999-01-01'
    """,
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
not_read = pd.read_sql(
    f"""
    SELECT DISTINCT
        BENEFICIARYEXID

    FROM ODS509.V_INF_ODS_DOCUMENT

    WHERE ORGANIZATION = '509'
    AND "READ" = 0
    AND RECEIVEDATE BETWEEN TIMESTAMP '{start_ts}'
                        AND TIMESTAMP '{end_ts}'
    AND NAME LIKE 'NMKTCBI%'
    AND NOTIFICATIONREQUESTSTATUS = 'DELIVERED'
    """,
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
print("eBox send:", len(visited_month))
print("Paper send:", len(paper_send_total))
print("  -- NO EBOX:", len(not_visited_month))
print("  -- NOT READ:", len(not_read))

# ================================
# EXPORT
# ================================
export_path = r"C:\Users\M509PSAO\Desktop\EXIDs"

visited_month.to_excel(
    os.path.join(
        export_path,
        "Bruxelles_eBox_Send_April_2026.xlsx"
    ),
    index=False
)

paper_send_total.to_excel(
    os.path.join(
        export_path,
        "Bruxelles_Paper_Send_April_2026.xlsx"
    ),
    index=False
)

print("Export completed successfully.")

# ================================
# CLOSE CONNECTION
# ================================
conn.close()