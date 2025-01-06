# Radhika Mattoo, radhika095@gmail.com
import json
import os
import pandas as pd
import geocoder
import numpy as np
from urllib.request import urlopen


def get_zipcode_data(data_dir):
    """Downloads NYC zipcode JSON and parses raw zipcodes from them."""
    path = os.path.join(data_dir, "nyc-zip-code.json")
    if not path:
        with urlopen(
            "https://raw.githubusercontent.com/gdobler/nycep/master/d3/data/nyc-zip-code.json"
        ) as response:
            zipcode_geodata = json.load(response)

        with open(path, "w") as f:
            json.dump(zipcode_geodata, f)
    else:
        with open(path, "r") as f:
            zipcode_geodata = json.load(f)

    zipcodes = [z["properties"]["ZIP"] for z in zipcode_geodata["features"]]

    return zipcode_geodata, zipcodes


def clean_kid_excel_sheet(kid_df, zipcodes):
    """Performs type parsing for Zip Codes and Density mapping. Fills in missing NYC zip codes with default Density."""
    density_to_int_map = {
        "missing": 0.0,
        "low": 0.33,
        "med": 0.5,
        "medium": 0.5,
        "high": 1.0,
    }

    # Clean the kid excel sheet
    for idx, row in kid_df.iterrows():
        zip_code = row["Zip code"]
        density_str = row["Density "]
        # Convert string Density column to integer from above map
        if not pd.isna(density_str):
            density_str = density_str.strip()
            density = density_to_int_map[density_str]
            kid_df.at[idx, "Density "] = density

        # Cast Zip Code to string
        if not pd.isna(zip_code):
            kid_df.at[idx, "Zip code"] = str(int(float(row["Zip code"])))

    # Fill DF with all Zipcodes in NYC area
    for zipcode in zipcodes:
        kid_row = kid_df.loc[kid_df["Zip code"] == zipcode]

        # If Zip Code not found in DF, add it.
        if kid_row.empty:
            new_row = {"Zip code": zipcode, "Density ": 0.0}
            kid_df = kid_df._append(new_row, ignore_index=True)

    return kid_df


def clean_clinic_excel_sheet(clinic_df, kid_df):
    """Translates address to lat/long, standardizes Zip Code, and creates Density column based on matching zip in kid_df"""
    # Create new columns for Lat/Long/Density
    clinic_df["Latitude"] = np.nan
    clinic_df["Longitude"] = np.nan
    clinic_df["Density"] = np.nan
    for idx, row in clinic_df.iterrows():
        address = row["Address"]
        # Clean longer-form zip codes with "-"
        zip_code = str(row["Zip code"])
        zip_code = zip_code.split(".")[0]
        zip_code = zip_code.split("-")[0]
        clinic_df.at[idx, "Zip code"] = zip_code

        # Get long/lat coordinates from address and add as column
        result = geocoder.arcgis(location=address)
        coordinates = result.latlng
        clinic_df.at[idx, "Latitude"] = coordinates[0]
        clinic_df.at[idx, "Longitude"] = coordinates[1]

        # Match with kid_df column Density based on zip
        kid_row = kid_df.loc[kid_df["Zip code"] == zip_code]

        # There are clinics where there aren't kids, so there will be no matching zip in the kid df. Default to 'missing'
        density = 0.0
        if not kid_row.empty:
            density = kid_row["Density "].values[0]
        clinic_df.at[idx, "Density"] = density

    return clinic_df


def clean_data(kid_df, clinic_df, zipcodes, cleaned_filename):
    """Cleans up original data sheets and saves to new excel file."""
    kid_df = clean_kid_excel_sheet(kid_df, zipcodes)

    clinic_df = clean_clinic_excel_sheet(clinic_df, kid_df)

    # Write each dataframe to a different worksheet.
    with pd.ExcelWriter(cleaned_filename, engine="xlsxwriter") as writer:
        clinic_df.to_excel(writer, sheet_name="Clinic Data")
        kid_df.to_excel(writer, sheet_name="Kid Data")

    return kid_df, clinic_df
