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

# Define Sub-Saharan African countries with all possible naming variations
subsaharan_countries = [
    'Angola', 'Republic of Angola', 'People\'s Republic of Angola',
    'Benin', 'Republic of Benin', 'Dahomey',
    'Botswana', 'Republic of Botswana',
    'Burkina Faso', 'Burkina', 'Upper Volta',
    'Burundi', 'Republic of Burundi',
    'Cabo Verde', 'Cape Verde', 'Republic of Cabo Verde',
    'Cameroon', 'Republic of Cameroon', 'United Republic of Cameroon',
    'Central African Republic', 'CAR',
    'Chad', 'Republic of Chad',
    'Comoros', 'Union of the Comoros',
    'Congo', 'Republic of Congo', 'Republic of the Congo', 'Congo-Brazzaville',
    'Democratic Republic of Congo', 'DR Congo', 'DRC', 'DROC', 'Congo-Kinshasa', 'Democratic Republic of the Congo',
    "Côte d'Ivoire", 'Ivory Coast', 'Republic of Côte d\'Ivoire',
    'Djibouti', 'Republic of Djibouti',
    'Equatorial Guinea', 'Republic of Equatorial Guinea',
    'Eritrea', 'State of Eritrea',
    'Eswatini', 'Kingdom of Eswatini', 'Swaziland',
    'Ethiopia', 'Federal Democratic Republic of Ethiopia',
    'Gabon', 'Gabonese Republic', 'Republic of Gabon',
    'Gambia', 'The Gambia', 'Republic of The Gambia',
    'Ghana', 'Republic of Ghana',
    'Guinea', 'Republic of Guinea',
    'Guinea-Bissau', 'Republic of Guinea-Bissau',
    'Kenya', 'Republic of Kenya',
    'Lesotho', 'Kingdom of Lesotho',
    'Liberia', 'Republic of Liberia',
    'Madagascar', 'Republic of Madagascar',
    'Malawi', 'Republic of Malawi',
    'Mali', 'Republic of Mali',
    'Mauritania', 'Islamic Republic of Mauritania',
    'Mauritius', 'Republic of Mauritius',
    'Mozambique', 'Republic of Mozambique',
    'Namibia', 'Republic of Namibia',
    'Niger', 'Republic of Niger',
    'Nigeria', 'Federal Republic of Nigeria',
    'Rwanda', 'Republic of Rwanda',
    'Sao Tome and Principe', 'São Tomé and Príncipe', 'Democratic Republic of São Tomé and Príncipe',
    'Senegal', 'Republic of Senegal',
    'Seychelles', 'Republic of Seychelles',
    'Sierra Leone', 'Republic of Sierra Leone',
    'Somalia', 'Federal Republic of Somalia',
    'South Africa', 'Republic of South Africa', 'RSA',
    'South Sudan', 'Republic of South Sudan',
    'Sudan', 'Republic of Sudan',
    'Tanzania', 'United Republic of Tanzania',
    'Togo', 'Togolese Republic', 'Republic of Togo',
    'Uganda', 'Republic of Uganda',
    'Zambia', 'Republic of Zambia',
    'Zimbabwe', 'Republic of Zimbabwe'
]

# Filter for sub-Saharan African countries in our data
ss_africa_partners = partners_data[partners_data['Country'].isin(subsaharan_countries)]

# Count HE²AT partners by country
heat_partners = ss_africa_partners.groupby('Country')['HE²AT'].sum().reset_index()
print(f"HE²AT partners data:\n{heat_partners}")

# Load Natural Earth data from CartoDB's public data server
world_url = "https://cartodb-basemaps-a.global.ssl.fastly.net/carto-db/assets/ne_110m_admin_0_countries.json"

try:
    print(f"Loading world boundaries from CartoDB")
    world = gpd.read_file(world_url)
    print(f"Successfully loaded world boundaries")
except Exception as e:
    print(f"Error loading world boundaries from CartoDB: {e}")
    # Fallback to local file if needed
    print("Attempting to use GeoPandas sample datasets...")
    try:
        # Try to use the built-in sample data in newer versions of GeoPandas
        import geopandas.datasets
        sample_data_path = geopandas.datasets.get_path('naturalearth_lowres')
        world = gpd.read_file(sample_data_path)
        print("Successfully loaded sample data")
    except Exception as e2:
        print(f"Error loading sample data: {e2}")
        # Use a simpler alternative approach
        print("Using alternative data source...")
        world_url = "https://raw.githubusercontent.com/johan/world.geo.json/master/countries.geo.json"
        world = gpd.read_file(world_url)
        print("Successfully loaded alternative data source")

# Merge the partner counts with the world map data
# Different sources use different column names for country names
# Check all possible column names and use what's available
possible_name_columns = ['SOVEREIGNT', 'NAME', 'name', 'NAME_LONG', 'SOV_A3', 'name_long', 'admin']
name_column = None

for col in possible_name_columns:
    if col in world.columns:
        name_column = col
        print(f"Using '{name_column}' as the country name column")
        break

if name_column is None:
    print("Country name column not found. Available columns:")
    print(world.columns.tolist())
    name_column = world.columns[0]  # Use the first column as a fallback

# Create a comprehensive mapping dictionary for country name standardization
name_mapping = {
    # Côte d'Ivoire variations
    "Ivory Coast": "Côte d'Ivoire",
    "Republic of Côte d'Ivoire": "Côte d'Ivoire",
    "Cote d'Ivoire": "Côte d'Ivoire",
    "Cote d'Ivoire": "Côte d'Ivoire",
    
    # Congo variations
    "Republic of the Congo": "Congo",
    "Republic of Congo": "Congo",
    "Congo-Brazzaville": "Congo",
    "Congo, Rep.": "Congo",
    
    # DRC variations
    "Democratic Republic of the Congo": "Democratic Republic of Congo",
    "DR Congo": "Democratic Republic of Congo",
    "DRC": "Democratic Republic of Congo",
    "DROC": "Democratic Republic of Congo",
    "Congo-Kinshasa": "Democratic Republic of Congo",
    "Congo, Dem. Rep.": "Democratic Republic of Congo",
    
    # Eswatini/Swaziland
    "Swaziland": "Eswatini",
    "Kingdom of Eswatini": "Eswatini",
    
    # Tanzania
    "Tanzania": "United Republic of Tanzania",
    "Republic of Tanzania": "United Republic of Tanzania",
    "United Republic of Tanzania": "Tanzania",
    
    # Cape Verde
    "Cabo Verde": "Cape Verde",
    "Republic of Cabo Verde": "Cape Verde",
    
    # Gambia
    "The Gambia": "Gambia",
    "Republic of The Gambia": "Gambia",
    
    # São Tomé and Príncipe
    "Sao Tome and Principe": "São Tomé and Príncipe",
    "Democratic Republic of São Tomé and Príncipe": "São Tomé and Príncipe",
    
    # Remove Republic/Kingdom prefixes for consistency
    "Republic of South Africa": "South Africa",
    "Republic of Kenya": "Kenya",
    "Republic of Uganda": "Uganda",
    "Republic of Senegal": "Senegal",
    "Republic of Nigeria": "Nigeria",
    "Federal Republic of Nigeria": "Nigeria",
    "Republic of Ghana": "Ghana",
    "Republic of Malawi": "Malawi",
    "Republic of Rwanda": "Rwanda",
    "Republic of Botswana": "Botswana",
    "Republic of Mozambique": "Mozambique",
    "Republic of Zimbabwe": "Zimbabwe",
    "Kingdom of Lesotho": "Lesotho"
}

# Apply name mapping to standardize country names
world[name_column] = world[name_column].replace(name_mapping)

# Merge data
world = world.merge(heat_partners, left_on=name_column, right_on='Country', how='left')

# Filter to only show African continent
# Different sources use different column names for continents
possible_continent_columns = ['CONTINENT', 'REGION_UN', 'continent', 'region', 'REGION']
continent_column = None

for col in possible_continent_columns:
    if col in world.columns:
        continent_column = col
        print(f"Using '{continent_column}' as the continent column")
        break

# If no continent column is found, we'll filter manually by country names in Africa
if continent_column is None:
    print("Continent column not found. Filtering by country name...")
    # Define African countries
    african_countries = subsaharan_countries + [
        'Algeria', 'Egypt', 'Libya', 'Morocco', 'Tunisia', 'Western Sahara'
    ]
    africa = world[world[name_column].isin(african_countries)]
else:
    # Different sources might use different values for Africa
    possible_africa_values = ['Africa', 'AFRICA', 'Africa and the Middle East']
    mask = world[continent_column].isin(possible_africa_values)
    africa = world[mask]

# Print information about the resulting map data
print(f"\nCountries in map data: {len(africa)}")
print(f"Countries with HE²AT partner data: {len(africa[~africa['HE²AT'].isna()])}")
print(f"Countries missing HE²AT partner data: {len(africa[africa['HE²AT'].isna()])}")

# Print countries with HE²AT data that were successfully mapped
matched_countries = set(africa[~africa['HE²AT'].isna()]['Country'].tolist())
print(f"\nCountries with HE²AT data that were successfully mapped: {matched_countries}")

# Check for countries in our dataset that didn't match to the map
dataset_countries = set(heat_partners['Country'].tolist())
unmatched_countries = dataset_countries - matched_countries
if unmatched_countries:
    print(f"\nWARNING: These countries from our dataset did not match to the map: {unmatched_countries}")
    # Try to identify what these countries might be called in the map data
    for country in unmatched_countries:
        possible_matches = [c for c in africa[name_column].tolist() if c and country.lower() in c.lower()]
        if possible_matches:
            print(f"  '{country}' might match to: {possible_matches}")
            # Try to manually match the country
            for match in possible_matches:
                africa.loc[africa[name_column] == match, 'Country'] = country
                africa.loc[africa[name_column] == match, 'HE²AT'] = heat_partners[heat_partners['Country'] == country]['HE²AT'].values[0]
                print(f"  Manually matched '{country}' to '{match}'")

# Create a figure and axis
fig, ax = plt.figure(figsize=(15, 15)), plt.gca()

# Define color scheme (from light to dark)
cmap = plt.cm.YlOrRd
norm = colors.Normalize(vmin=0, vmax=max(heat_partners['HE²AT'].max(), 1))  # Ensure max is at least 1

# Plot countries with no data in light gray
africa[africa['HE²AT'].isna()].plot(ax=ax, color='lightgray', edgecolor='black')

# Plot countries with data using the colormap
africa[~africa['HE²AT'].isna()].plot(
    column='HE²AT',
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
cbar.set_label('Number of HE²AT Partners', fontsize=14)

# Customize the appearance
ax.set_title('HE²AT Center Partners in Sub-Saharan Africa', fontsize=16, fontweight='bold')
ax.set_axis_off()

# No legend for countries with no data (as requested)

# Add country names for countries with partners
for idx, row in africa[~africa['HE²AT'].isna()].iterrows():
    if pd.notna(row['HE²AT']) and row['HE²AT'] > 0:
        # Get centroid for label placement
        centroid = row.geometry.centroid
        # Use the Country column from our dataset if available, otherwise fallback to map data name
        country_name = row['Country'] if pd.notna(row['Country']) else row[name_column]
        # Handle case when neither is available
        if pd.isna(country_name) and name_column in row and pd.notna(row[name_column]):
            country_name = row[name_column]
        
        ax.text(
            centroid.x, centroid.y, 
            f"{country_name}\n({int(row['HE²AT'])})", 
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
