#!/usr/bin/env python
# Radhika Mattoo, radhika095@gmail.com
import os
import plotly.express as px
from utils import get_zipcode_data, get_cleaned_data

DEBUG = False
DATA_DIR = "../data"


def generate_zipcode_density_map(kid_df, zipcodes):
    """Generates color-scaled map of NYC Zipcodes and their clinic Density"""
    # Map the density_to_int_map to RGB colors
    density_to_rgb = [
        [0.0, "white"],
        [0.33, "rgb(211, 211, 211)"],
        [0.5, "rgb(147, 147, 147)"],
        [1.0, "rgb(103, 103, 103)"],
    ]

    print(f"Generating choropleth of {kid_df.shape[0]} zip code densities")
    fig = px.choropleth_mapbox(
        kid_df,
        geojson=zipcodes,
        locations="Zip code",
        color="Density ",
        color_continuous_scale=density_to_rgb,
        featureidkey="properties.ZIP",
        zoom=10,
        height=800,
        width=800,
        center={"lat": 40.73, "lon": -73.93},
    )
    fig.update_layout(mapbox_style="carto-positron")
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})

    return fig


def generate_clinic_acceptance_map(fig, clinic_df):
    """Overlays map figure with scatterplot of clinic locations colored by Acceptance."""
    print(f"Generating scatter plot of {clinic_df.shape[0]} clinic locations")

    # Color the dots based on Acceptance
    clinic_df["colors"] = clinic_df["Acceptance"].apply(
        lambda x: "rgb(233,233,233)" if x == "conditional" else "black"
    )
    # Create black outline for dot size 10
    fig.add_scattermapbox(
        below="",
        mode="markers",
        lat=clinic_df["Latitude"],
        lon=clinic_df["Longitude"],
        marker=dict(color="black", size=10),
    )

    # Actual dot with color based on colors column.
    fig.add_scattermapbox(
        below="",
        mode="markers",
        lat=clinic_df["Latitude"],
        lon=clinic_df["Longitude"],
        text=clinic_df["Clinic Name"],
        marker=dict(color=clinic_df["colors"], size=8),
    )
    return fig


def create_map(
    kid_df,
    clinic_df,
    zipcodes,
):
    """Creates choropleth mapbox for Zip Codes based on Density, then overlays with scattermapbox of clinic locations colored by Acceptance."""
    figure_filepath = os.path.join(DATA_DIR, "map.png")

    # Color NYC zip codes based on density
    fig = generate_zipcode_density_map(kid_df, zipcodes)

    # Overlay Clinic locations colored by Accpetance
    fig = generate_clinic_acceptance_map(fig, clinic_df)

    if DEBUG:
        print("Rendering...")
        fig.show()

    print(f"Saving map to {figure_filepath}")
    fig.write_image(figure_filepath)


def main():
    original_filename = os.path.join(DATA_DIR, "data.xlsx")
    cleaned_filename = os.path.join(DATA_DIR, "data_cleaned.xlsx")
    zipcode_geodata, zipcodes = get_zipcode_data(DATA_DIR)

    clinic_df, kid_df = get_cleaned_data(original_filename, cleaned_filename, zipcodes)

    if DEBUG:
        # Get df of black dots (acceptance, i.e. anything but 'conditional')
        black_dots = clinic_df.loc[clinic_df["Acceptance"] == "yes"]
        print(f"There are {black_dots.shape[0]} clinics with YES")
        black_dots_with_density = black_dots.loc[black_dots["Density"] != 0.0]
        print(
            f"There are {black_dots_with_density.shape[0]} YES clinics in non-0 density zip codes"
        )
    create_map(kid_df, clinic_df, zipcode_geodata)


if __name__ == "__main__":
    main()
