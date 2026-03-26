import pandas as pd

kosis_path = "data/raw/kosis/kosis_item_cpi_monthly.xlsx"
kamis_annual_path = "data/raw/kamis/kamis_retail_annual.xls"
kamis_monthly_path = "data/raw/kamis/kamis_rice_monthly.xls"
faostat_path = "data/raw/faostat/agrifood_emissions.csv"


def preview_dataframe(name: str, df: pd.DataFrame, n: int = 5) -> None:
    print(f"\n=== {name} ===")
    print("shape:", df.shape)
    print("columns:", list(df.columns))
    print(df.head(n))
    print()


kosis_df = pd.read_excel(kosis_path, engine="openpyxl")

kamis_annual_tables = pd.read_html(kamis_annual_path)
kamis_monthly_tables = pd.read_html(kamis_monthly_path)

kamis_annual_df = max(kamis_annual_tables, key=lambda x: x.shape[0] * x.shape[1])
kamis_monthly_df = max(kamis_monthly_tables, key=lambda x: x.shape[0] * x.shape[1])

faostat_df = pd.read_csv(faostat_path)

preview_dataframe("KOSIS", kosis_df)
preview_dataframe("KAMIS annual", kamis_annual_df)
preview_dataframe("KAMIS monthly", kamis_monthly_df)
preview_dataframe("FAOSTAT", faostat_df)

print("\nKOSIS columns:")
print(kosis_df.columns)

print("\nKAMIS monthly columns:")
print(kamis_monthly_df.columns)

print("\nFAOSTAT columns:")
print(faostat_df.columns)

print("\n=== KOSIS transformed preview ===")

kosis_long = kosis_df.melt(
    id_vars=["시도별", "품목별"],
    var_name="date",
    value_name="cpi"
)

print(kosis_long.head(10))
print(kosis_long.shape)

preview_dataframe("FAOSTAT", faostat_df)

print("\n=== KOSIS cleaned preview ===")

kosis_long["시도별"] = kosis_long["시도별"].ffill()
kosis_long["품목별"] = kosis_long["품목별"].str.strip()

kosis_national = kosis_long[kosis_long["시도별"] == "전국"].copy()

print(kosis_national.head(10))
print(kosis_national.shape)
print(kosis_national["시도별"].unique())

print("\n=== KOSIS date converted preview ===")

kosis_national["date"] = pd.to_datetime(kosis_national["date"], format="%Y.%m")
kosis_national["year"] = kosis_national["date"].dt.year
kosis_national["month"] = kosis_national["date"].dt.month

print(kosis_national.head(10))
print(kosis_national.dtypes)

print("\n=== KAMIS monthly transformed preview ===")

kamis_monthly_long = kamis_monthly_df.melt(
    id_vars=["구분"],
    var_name="year",
    value_name="price"
)

kamis_monthly_long["구분"] = kamis_monthly_long["구분"].astype(str).str.strip()
kamis_monthly_long["year"] = kamis_monthly_long["year"].astype(str).str.strip()

# 월 데이터만 남기기
kamis_monthly_long = kamis_monthly_long[
    kamis_monthly_long["구분"].str.match(r"^\d{2}월$", na=False)
].copy()

# 평년 열 제외
kamis_monthly_long = kamis_monthly_long[
    kamis_monthly_long["year"].str.contains("년", na=False)
].copy()

kamis_monthly_long["month"] = (
    kamis_monthly_long["구분"]
    .str.replace("월", "", regex=False)
    .astype(int)
)

kamis_monthly_long["year"] = (
    kamis_monthly_long["year"]
    .str.replace("년", "", regex=False)
)

kamis_monthly_long["year"] = pd.to_numeric(
    kamis_monthly_long["year"],
    errors="coerce"
)

kamis_monthly_long = kamis_monthly_long.dropna(subset=["year"]).copy()
kamis_monthly_long["year"] = kamis_monthly_long["year"].astype(int)

kamis_monthly_long["price"] = (
    kamis_monthly_long["price"]
    .astype(str)
    .str.replace(",", "", regex=False)
    .replace("-", pd.NA)
)

kamis_monthly_long["price"] = pd.to_numeric(kamis_monthly_long["price"], errors="coerce")

kamis_monthly_long["date"] = pd.to_datetime(
    kamis_monthly_long["year"].astype(str)
    + "-"
    + kamis_monthly_long["month"].astype(str).str.zfill(2)
    + "-01"
)

print(kamis_monthly_long.head(12))
print(kamis_monthly_long.shape)
print(kamis_monthly_long.dtypes)