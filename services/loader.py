import pandas as pd

_COLLISIONS_DF = None

def load_collisions(csv_path="collisions_routieres.csv"):
    global _COLLISIONS_DF
    if _COLLISIONS_DF is not None:
        return _COLLISIONS_DF

    df = pd.read_csv(csv_path, low_memory=False)

    df["DT_ACCDN"] = pd.to_datetime(df["DT_ACCDN"], errors="coerce")
    df["LOC_LAT"] = pd.to_numeric(df["LOC_LAT"], errors="coerce")
    df["LOC_LONG"] = pd.to_numeric(df["LOC_LONG"], errors="coerce")

    df = df.dropna(subset=["LOC_LAT", "LOC_LONG"])

    _COLLISIONS_DF = df
    return df