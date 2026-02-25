import pandas as pd

_REQ311_DF = None

def load_311(csv_path: str = "requetes311.csv") -> pd.DataFrame:
    global _REQ311_DF
    if _REQ311_DF is not None:
        return _REQ311_DF

    df = pd.read_csv(csv_path, low_memory=False)

    # date création (ex: "2023-07-10T20:15:39")
    if "DDS_DATE_CREATION" in df.columns:
        df["DDS_DATE_CREATION"] = pd.to_datetime(df["DDS_DATE_CREATION"], errors="coerce")

    # long/lat si besoin
    if "LOC_LAT" in df.columns:
        df["LOC_LAT"] = pd.to_numeric(df["LOC_LAT"], errors="coerce")
    if "LOC_LONG" in df.columns:
        df["LOC_LONG"] = pd.to_numeric(df["LOC_LONG"], errors="coerce")

    _REQ311_DF = df
    return _REQ311_DF