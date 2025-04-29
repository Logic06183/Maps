import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import numpy as np
from matplotlib.patches import Patch

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

# Load world map data
world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))

# Merge the partner counts with the world map data
world = world.merge(heat_partners, left_on='name', right_on='Country', how='left')

# Filter to only show African continent
africa = world[world['continent'] == 'Africa']

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

# Display the map
plt.show()
