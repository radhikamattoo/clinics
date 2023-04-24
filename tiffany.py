# Radhika Mattoo, radhika095@gmail.com
import json
import os
import pandas as pd
import geocoder
import numpy as np
import plotly.express as px
from urllib.request import urlopen


def clean_data(kid_df, clinic_df):
    density_to_int_map = {
        'low': 0.0,
        'med': 0.5,
        'medium': 0.5,
        'high': 1.0
    }    
    for idx, row in kid_df.iterrows():
        zip_code = row['Zip code']
        density_str = row['Density ']
        if not pd.isna(density_str):
            density_str = density_str.strip()
            density = density_to_int_map[density_str]
            kid_df.at[idx,'Density '] = density
        
        if not pd.isna(zip_code):
            kid_df.at[idx,'Zip code'] =  str(int(float(row['Zip code'])))
            
        print(kid_df.iloc[idx])
            
    clinic_df["Latitude"] = np.nan
    clinic_df["Longitude"] = np.nan
    clinic_df["Density"] = np.nan            
    for idx, row in clinic_df.iterrows():
        address = row['Address']
        # Clean longer-form zip codes with "-"
        zip_code = str(row['Zip code'])
        zip_code = zip_code.split('.')[0]
        zip_code = zip_code.split('-')[0]
        clinic_df.at[idx, 'Zip code'] = zip_code
        
        # Get long/lat coordinates from address and add as column
        result = geocoder.arcgis(location=address)
        coordinates = result.latlng
        clinic_df.at[idx,'Latitude'] = coordinates[0]
        clinic_df.at[idx,'Longitude'] = coordinates[1]
            
        # Match with kid_df column Density based on zip
        kid_row = kid_df.loc[kid_df['Zip code'] == zip_code]
        # There are clinics where there aren't kids, so there will be no matching zip in the kid df. Default to 'low'        
        # print(f"Empty Kid row for zip code {zip_code}: {kid_row.empty}")

        density = 0.0
        if not kid_row.empty:
            density = kid_row['Density '].values[0]
        clinic_df.at[idx,'Density'] = density
        
        print(clinic_df.iloc[idx])
    
    # Write each dataframe to a different worksheet.
    with pd.ExcelWriter("./data_cleaned.xlsx", engine="xlsxwriter") as writer:

        clinic_df.to_excel(writer, sheet_name="Clinic Data")
        kid_df.to_excel(writer, sheet_name="Kid Data")
    
    return kid_df, clinic_df    
    

def create_map(kid_df, clinic_df, zipcodes):
    # Create scatter plot of clinic locations
    # Color the dots based on Density (maps to )
    print(f"Generating scatter plot of clinic locations")
    print(f"{clinic_df.shape[0]} clinics to plot")
    fig = px.scatter_mapbox(clinic_df, 
                            lat="Latitude", 
                            lon="Longitude", 
                            hover_name="Address", 
                            hover_data=["Address", "Density", "Clinic Name", "Acceptance"],
                            color="Acceptance",
                            color_continuous_scale='gray',
                            # size="Density",
                            zoom=8, 
                            height=800,
                            width=800)
    fig.update_layout(mapbox_style="open-street-map")
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    
    print(f"{kid_df.shape[0]} zips to plot")
    fig2 = px.choropleth_mapbox(kid_df, 
                        geojson=zipcodes, 
                        locations='Zip code', 
                        color='Density ',
                        color_continuous_scale="gray",
                        range_color=(0,1),
                        featureidkey="properties.ZCTA5CE10")
    # fig.update_layout(mapbox_style="open-street-map")
    # fig.update_geos(
    #     visible=False, resolution=50, scope="usa",
    #     showsubunits=True, subunitcolor="Blue"
    # )    
    trace0 = fig2 # the second map from the previous code
    fig.add_trace(trace0.data[0])
    trace0.layout.update(showlegend=False)
    fig.show()  
                         

if __name__ == '__main__':
    if not os.path.exists('./data_cleaned.xlsx'):
        kid_df = pd.read_excel('./data.xlsx', sheet_name='kid data', usecols="A,B",converters={'Zip code':str})
        clinic_df = pd.read_excel('./data.xlsx', sheet_name='clinic data', usecols="A,B,C,D",converters={'Zip code':str})
        kid_df, clinic_df = clean_data(kid_df, clinic_df)
    else:
        clinic_df = pd.read_excel('./data_cleaned.xlsx', sheet_name='Clinic Data', usecols="B,C,D,E,F,G,H")
        kid_df = pd.read_excel('./data_cleaned.xlsx', sheet_name='Kid Data', usecols="B,C")
        
    if not os.path.exists('./zip-codes.json'):
        with urlopen('https://raw.githubusercontent.com/OpenDataDE/State-zip-code-GeoJSON/master/ny_new_york_zip_codes_geo.min.json') as response:
            zipcodes = json.load(response)       
            
        with open('./zip-codes.json', 'w')  as f:
            json.dump(zipcodes, f)
    else:
        with open('./zip-codes.json', 'r') as f:
            zipcodes = json.load(f)
        
    # print(clinic_df.head())
    # print()
    # print(clinic_df.columns)        
    
    create_map(kid_df, clinic_df, zipcodes)


