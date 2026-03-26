import pandas as pd
import duckdb

kosis_path = "data/raw/kosis/kosis_item_cpi_monthly.xlsx"
kamis_monthly_path = "data/raw/kamis/kamis_rice_monthly.xls"
faostat_path = "data/raw/faostat/agrifood_emissions.csv"

db_path = "data/processed/food_analysis.duckdb"


def build_kosis():
    kosis_df = pd.read_excel(kosis_path, engine="openpyxl")

    kosis_long = kosis_df.melt(
        id_vars=["시도별", "품목별"],
        var_name="date",
        value_name="cpi"
    )

    kosis_long["시도별"] = kosis_long["시도별"].ffill()
    kosis_long["품목별"] = kosis_long["품목별"].str.strip()

    kosis_national = kosis_long[kosis_long["시도별"] == "전국"].copy()
    kosis_national["date"] = pd.to_datetime(kosis_national["date"], format="%Y.%m")
    kosis_national["year"] = kosis_national["date"].dt.year
    kosis_national["month"] = kosis_national["date"].dt.month

    return kosis_national


def build_single_kamis_monthly(file_path: str, item_name: str, unit_name: str):
    kamis_tables = pd.read_html(file_path)
    kamis_df = max(kamis_tables, key=lambda x: x.shape[0] * x.shape[1])

    kamis_long = kamis_df.melt(
        id_vars=["구분"],
        var_name="year",
        value_name="price"
    )

    kamis_long["구분"] = kamis_long["구분"].astype(str).str.strip()
    kamis_long["year"] = kamis_long["year"].astype(str).str.strip()

    kamis_long = kamis_long[kamis_long["구분"].str.match(r"^\d{2}월$", na=False)].copy()

    kamis_long["year"] = kamis_long["year"].str.replace("년", "", regex=False)
    kamis_long["year"] = pd.to_numeric(kamis_long["year"], errors="coerce")
    kamis_long = kamis_long.dropna(subset=["year"]).copy()
    kamis_long["year"] = kamis_long["year"].astype(int)

    kamis_long["month"] = kamis_long["구분"].str.replace("월", "", regex=False).astype(int)

    kamis_long["price"] = (
        kamis_long["price"]
        .astype(str)
        .str.replace(",", "", regex=False)
        .replace("-", pd.NA)
    )
    kamis_long["price"] = pd.to_numeric(kamis_long["price"], errors="coerce")

    kamis_long["date"] = pd.to_datetime(
        kamis_long["year"].astype(str)
        + "-"
        + kamis_long["month"].astype(str).str.zfill(2)
        + "-01"
    )

    kamis_long["item"] = item_name
    kamis_long["unit"] = unit_name

    return kamis_long


def build_single_kamis_monthly(file_path: str, item_name: str, unit_name: str):
    kamis_tables = pd.read_html(file_path)

    selected_df = None
    for table in kamis_tables:
        cols = [str(c).strip() for c in table.columns]
        if "구분" in cols:
            selected_df = table.copy()
            selected_df.columns = cols
            break

    if selected_df is None:
        print(f"[DEBUG] available columns in {file_path}")
        for i, table in enumerate(kamis_tables):
            print(i, list(table.columns))
        raise ValueError(f"'구분' 컬럼이 있는 표를 찾지 못했습니다: {file_path}")

    kamis_long = selected_df.melt(
        id_vars=["구분"],
        var_name="year",
        value_name="price"
    )

    kamis_long["구분"] = kamis_long["구분"].astype(str).str.strip()
    kamis_long["year"] = kamis_long["year"].astype(str).str.strip()

    kamis_long = kamis_long[kamis_long["구분"].str.match(r"^\d{2}월$", na=False)].copy()

    kamis_long["year"] = kamis_long["year"].str.replace("년", "", regex=False)
    kamis_long["year"] = pd.to_numeric(kamis_long["year"], errors="coerce")
    kamis_long = kamis_long.dropna(subset=["year"]).copy()
    kamis_long["year"] = kamis_long["year"].astype(int)

    kamis_long["month"] = kamis_long["구분"].str.replace("월", "", regex=False).astype(int)

    kamis_long["price"] = (
        kamis_long["price"]
        .astype(str)
        .str.replace(",", "", regex=False)
        .replace("-", pd.NA)
    )
    kamis_long["price"] = pd.to_numeric(kamis_long["price"], errors="coerce")

    kamis_long["date"] = pd.to_datetime(
        kamis_long["year"].astype(str)
        + "-"
        + kamis_long["month"].astype(str).str.zfill(2)
        + "-01"
    )

    kamis_long["item"] = item_name
    kamis_long["unit"] = unit_name

    return kamis_long


def build_kamis_monthly():
    kamis_files = [
        ("data/raw/kamis/kamis_rice_monthly.xls", "쌀", "20kg"),
        ("data/raw/kamis/kamis_apple_monthly.xls", "사과", "1개"),
        ("data/raw/kamis/kamis_cabbage_monthly.xls", "배추", "1포기"),
        ("data/raw/kamis/kamis_potato_monthly.xls", "감자", "1kg"),
    ]

    frames = []
    for file_path, item_name, unit_name in kamis_files:
        df = build_single_kamis_monthly(file_path, item_name, unit_name)
        frames.append(df)

    kamis_all = pd.concat(frames, ignore_index=True)
    return kamis_all


def build_faostat():
    faostat_df = pd.read_csv(faostat_path)

    faostat_clean = faostat_df[["Area", "Item", "Year", "Unit", "Value"]].copy()
    faostat_clean.columns = ["area", "item", "year", "unit", "emissions_value"]

    return faostat_clean


kosis_clean = build_kosis()
kamis_monthly_clean = build_kamis_monthly()
faostat_clean = build_faostat()

con = duckdb.connect(db_path)

con.register("kosis_clean_df", kosis_clean)
con.register("kamis_monthly_clean_df", kamis_monthly_clean)
con.register("faostat_clean_df", faostat_clean)

con.execute("CREATE OR REPLACE TABLE kosis_clean AS SELECT * FROM kosis_clean_df")
con.execute("CREATE OR REPLACE TABLE kamis_monthly_clean AS SELECT * FROM kamis_monthly_clean_df")
con.execute("CREATE OR REPLACE TABLE faostat_clean AS SELECT * FROM faostat_clean_df")

print("DuckDB saved:", db_path)
print(con.execute("SHOW TABLES").fetchdf())

con.close()