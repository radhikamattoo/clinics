# Radhika Mattoo, radhika095@gmail.com
import json
import os
import pandas as pd
import geocoder
import numpy as np
import plotly.express as px
from urllib.request import urlopen


def clean_data(kid_df, clinic_df, zipcodes):
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
        
            
    for zipcode in zipcodes:
        kid_row = kid_df.loc[kid_df['Zip code'] == zipcode]
        
        if kid_row.empty:
            new_row = {'Zip code': zipcode, 'Density ': 0.0}
            kid_df = kid_df.append(new_row, ignore_index = True)
            
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
    # Color the dots based on Acceptance
    print(f"Generating scatter plot of {clinic_df.shape[0]} clinic locations")
    clinic_colors = {"conditional": 'black', 'yes': 'white'}
    fig = px.scatter_mapbox(clinic_df, 
                            lat="Latitude", 
                            lon="Longitude", 
                            hover_name="Address", 
                            hover_data=["Address", "Density", "Clinic Name", "Acceptance"],
                            color="Acceptance",
                            color_discrete_map=clinic_colors,
                            zoom=8, 
                            height=800,
                            width=800)
    fig.update_layout(mapbox_style="carto-positron")
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    # Hardcode increase the size of the clinic markers for visibility
    fig.update_traces(marker={'size': 10})
    
    
    # Create choropleth of zip codes colored based on Density
    print(f"Generating choropleth of {kid_df.shape[0]} zip code densities")
    fig2 = px.choropleth_mapbox(kid_df, 
                        geojson=zipcodes, 
                        locations='Zip code', 
                        color='Density ',
                        # color_continuous_scale="Greys",
                        # range_color=(0.0,1.0),
                        featureidkey="properties.ZIP")
    fig.add_trace(fig2.data[0])
    fig2.layout.update(showlegend=False)
    print("Rendering...")
    fig.show()  
                         

if __name__ == '__main__':
    if not os.path.exists('./nyc-zip-code.json'):
        with urlopen('https://raw.githubusercontent.com/gdobler/nycep/master/d3/data/nyc-zip-code.json') as response:
            zipcode_geodata = json.load(response)       
            
        with open('./nyc-zip-code.json', 'w')  as f:
            json.dump(zipcode_geodata, f)
    else:
        with open('./nyc-zip-code.json', 'r') as f:
            zipcode_geodata = json.load(f)    
    
    # Raw zipcodes
    zipcodes = [z['properties']['ZIP'] for z in zipcode_geodata['features']]
            
    if not os.path.exists('./data_cleaned.xlsx'):
        kid_df = pd.read_excel('./data.xlsx', sheet_name='kid data', usecols="A,B",converters={'Zip code':str})
        clinic_df = pd.read_excel('./data.xlsx', sheet_name='clinic data', usecols="A,B,C,D",converters={'Zip code':str})
        kid_df, clinic_df = clean_data(kid_df, clinic_df, zipcodes)
    else:
        clinic_df = pd.read_excel('./data_cleaned.xlsx', sheet_name='Clinic Data', usecols="B,C,D,E,F,G,H")
        kid_df = pd.read_excel('./data_cleaned.xlsx', sheet_name='Kid Data', usecols="B,C")
        

            
            
    create_map(kid_df, clinic_df, zipcode_geodata)


