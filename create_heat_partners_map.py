import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import numpy as np
from matplotlib.patches import Patch
import os
import tempfile
import urllib.request
import zipfile

# Load the partners data
data_path = '/Users/craig/Desktop/Maps/partners_data_with_coords (004)_reviewed_RF.xlsx'
partners_data = pd.read_excel(data_path)

# Define Sub-Saharan African countries
subsaharan_countries = [
    'Angola', 'Benin', 'Botswana', 'Burkina Faso', 'Burundi', 'Cameroon', 'Cape Verde',
    'Central African Republic', 'Chad', 'Comoros', 'Congo', 'Democratic Republic of Congo',
    "Côte d'Ivoire", 'Djibouti', 'Equatorial Guinea', 'Eritrea', 'Eswatini', 'Ethiopia', 
    'Gabon', 'Gambia', 'Ghana', 'Guinea', 'Guinea-Bissau', 'Kenya', 'Lesotho', 'Liberia',
    'Madagascar', 'Malawi', 'Mali', 'Mauritania', 'Mauritius', 'Mozambique', 'Namibia', 
    'Niger', 'Nigeria', 'Rwanda', 'Sao Tome and Principe', 'Senegal', 'Seychelles', 
    'Sierra Leone', 'Somalia', 'South Africa', 'South Sudan', 'Sudan', 'Tanzania', 'Togo', 
    'Uganda', 'Zambia', 'Zimbabwe'
]

# Filter for sub-Saharan African countries in our data
ss_africa_partners = partners_data[partners_data['Country'].isin(subsaharan_countries)]

# Count HEAT partners by country
heat_partners = ss_africa_partners.groupby('Country')['HEAT'].sum().reset_index()
print(f"HEAT partners data:\n{heat_partners}")

# Download and load Natural Earth data
def get_naturalearth_lowres():
    # URL for Natural Earth 1:110m Cultural Vectors, Admin 0 - Countries
    url = "https://www.naturalearthdata.com/http//www.naturalearthdata.com/download/110m/cultural/ne_110m_admin_0_countries.zip"
    
    # Create temporary directory
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Download the file
        zip_path = os.path.join(temp_dir, "ne_110m_admin_0_countries.zip")
        print(f"Downloading Natural Earth data from {url}")
        urllib.request.urlretrieve(url, zip_path)
        
        # Extract the files
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        
        # Find the shapefile
        shapefile_path = os.path.join(temp_dir, "ne_110m_admin_0_countries.shp")
        
        # Read the shapefile
        gdf = gpd.read_file(shapefile_path)
        return gdf
    
    except Exception as e:
        print(f"Error downloading Natural Earth data: {e}")
        return None

# Try to download and load Natural Earth data
world = get_naturalearth_lowres()

# Merge the partner counts with the world map data
# Natural Earth uses different country name keys than our dataset
# Standard column name in Natural Earth 110m for country names is 'SOVEREIGNT' or 'NAME'
name_column = 'SOVEREIGNT' if 'SOVEREIGNT' in world.columns else 'NAME'

# Create a mapping dictionary for potential name mismatches
name_mapping = {
    "Ivory Coast": "Côte d'Ivoire",
    "Democratic Republic of the Congo": "Democratic Republic of Congo",
    "Republic of the Congo": "Congo",
    "Swaziland": "Eswatini",
    "Tanzania": "United Republic of Tanzania"
}

# Apply name mapping to standardize country names
world[name_column] = world[name_column].replace(name_mapping)

# Merge data
world = world.merge(heat_partners, left_on=name_column, right_on='Country', how='left')

# Filter to only show African continent
# Natural Earth uses 'CONTINENT' or 'REGION_UN' to identify continents
continent_column = 'CONTINENT' if 'CONTINENT' in world.columns else 'REGION_UN'
africa = world[world[continent_column] == 'Africa']

# Create a figure and axis
fig, ax = plt.figure(figsize=(15, 15)), plt.gca()

# Define color scheme (from light to dark)
cmap = plt.cm.YlOrRd
norm = colors.Normalize(vmin=0, vmax=max(heat_partners['HEAT'].max(), 1))  # Ensure max is at least 1

# Plot countries with no data in light gray
africa[africa['HEAT'].isna()].plot(ax=ax, color='lightgray', edgecolor='black')

# Plot countries with data using the colormap
africa[~africa['HEAT'].isna()].plot(
    column='HEAT',
    ax=ax,
    cmap=cmap,
    norm=norm,
    edgecolor='black',
    linewidth=0.5
)

# Add a color bar
sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
sm.set_array([])
cbar = fig.colorbar(sm, ax=ax, format='%.0f', shrink=0.7)
cbar.set_label('Number of HEAT Partners', fontsize=14)

# Customize the appearance
ax.set_title('Heat Center Partners in Sub-Saharan Africa', fontsize=16, fontweight='bold')
ax.set_axis_off()

# Create a legend for countries with no data
legend_elements = [
    Patch(facecolor='lightgray', edgecolor='black', label='No HEAT Partners')
]
ax.legend(handles=legend_elements, loc='lower left', fontsize=12)

# Add country names for countries with partners
for idx, row in africa[~africa['HEAT'].isna()].iterrows():
    if pd.notna(row['HEAT']) and row['HEAT'] > 0:
        # Get centroid for label placement
        centroid = row.geometry.centroid
        ax.text(
            centroid.x, centroid.y, 
            f"{row['name']}\n({int(row['HEAT'])})", 
            fontsize=8,
            ha='center', va='center',
            bbox=dict(facecolor='white', alpha=0.5, edgecolor='none', boxstyle='round,pad=0.3')
        )

# Save the map
output_path = '/Users/craig/Desktop/Maps/heat_partners_subsaharan_africa.png'
plt.savefig(output_path, dpi=300, bbox_inches='tight')
print(f"Map saved to {output_path}")

# Create a summary CSV file with the data
summary_path = '/Users/craig/Desktop/Maps/heat_partners_summary.csv'
heat_partners.to_csv(summary_path, index=False)
print(f"Data summary saved to {summary_path}")

# Display the map
plt.show()
