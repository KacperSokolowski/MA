import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as ctx
import pandas as pd

def plot_heat_map_district(
    df: pd.DataFrame,
    plot_type: str = 'count',
    recording_units_pth: str = 'geographic_data/recording_units_poland/jednostki_ewidencyjne.shp'):
    
    recording_units = gpd.read_file(recording_units_pth)

    # Get districts of Warsaw from the recording units file
    warsaw_districts = ['Bemowo', 'Białołęka', 'Bielany', 'MOKOTÓW',
                        'OCHOTA', 'PRAGA POŁUDNIE', 'Praga-Północ',
                        'REMBERTÓW', 'ŚRÓDMIEŚCIE', 'TARGÓWEK', 'URSUS',
                        'URSYNÓW', 'WAWER', 'WESOŁA', 'WILANÓW',
                        'WŁOCHY', 'WOLA', 'Żoliborz']

    districts = recording_units[recording_units.JPT_NAZWA_.isin(warsaw_districts)]
    
    # Join geo data with apartments file to count flats or calculate median rent in each district
    gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.longitude, df.latitude), crs="EPSG:4326")
    gdf = gdf.to_crs(districts.crs)
    districts_with_counts = gpd.sjoin(gdf, districts, how="left", op="within")

    if plot_type == 'count':
        # Count the number of flats in each district
        flat_counts = districts_with_counts.groupby('index_right').size()
        districts['flat_count'] = flat_counts
        districts['flat_count'] = districts['flat_count'].fillna(0)
        column_to_plot = 'flat_count'
        title = 'Heat Map of Apartments Count by District in Warsaw'
        cmap = 'Reds'
    elif plot_type == 'median_rent':
        # Calculate the median rent price in each district
        median_rent_prices = districts_with_counts.groupby('index_right')['rent_price'].median()
        districts['median_rent_price'] = median_rent_prices
        districts['median_rent_price'] = districts['median_rent_price'].fillna(0)
        column_to_plot = 'median_rent_price'
        title = 'Heat Map of Median Rent Price by District in Warsaw'
        cmap = 'Greens'
    else:
        raise ValueError("plot_type must be either 'count' or 'median_rent'")
    
    districts = districts.to_crs(epsg=3857)

    # Initialize Figure
    fig, ax = plt.subplots(1, 1, figsize=(10, 10))

    # Plot the heat map
    districts.plot(column=column_to_plot, ax=ax, cmap=cmap, linewidth=1, edgecolor='black', legend=True, alpha=0.6)

    # Add district names
    for idx, row in districts.iterrows():
        plt.annotate(text=row['JPT_NAZWA_'].upper(), xy=(row.geometry.centroid.x, row.geometry.centroid.y),
                     ha='center', fontsize=6, color='black', weight='bold')

    plt.title(title, fontsize=12, weight='bold')
    ax.set_axis_off()
    plt.show()
    
    return None

def plot_heat_map_grid_cells(
    df: pd.DataFrame,
    plot_type: str = 'count',
    warsaw_shape_pth: str = 'geographic_data/commons_poland/Gminy.shp',
    grid_cells_shape_pth: str = 'geographic_data/GRID_NSP2021_RES/GRID_NSP2021_RES.shp'):
    
    # Load shapefile with warsaw borders
    warsaw = gpd.read_file(warsaw_shape_pth)
    warsaw = warsaw[warsaw.JPT_NAZWA_.eq('Warszawa')]
    
    # Load the shapefile with grid cells
    grid_cells = gpd.read_file(grid_cells_shape_pth)
    grid_cells = grid_cells.to_crs('EPSG:4258')
    
    # Join grids with warsaw borders
    grid_cells_within_warsaw = grid_cells.overlay(warsaw)
    # Join geo data with apartments file
    gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.longitude, df.latitude), crs="EPSG:4326")
    gdf = gdf.to_crs(grid_cells_within_warsaw.crs)

    # Perform spatial join to count flats or calculate median rent in each grid cell
    grid_cells_with_counts = gpd.sjoin(gdf, grid_cells_within_warsaw, how="left", op="within")

    if plot_type == 'count':
        # Count the number of flats in each grid cell
        flat_counts = grid_cells_with_counts.groupby('index_right').size()
        grid_cells_within_warsaw['flat_count'] = flat_counts
        grid_cells_within_warsaw['flat_count'] = grid_cells_within_warsaw['flat_count'].fillna(0)
        column_to_plot = 'flat_count'
        title = 'Heat Map of Apartments Count by Grid Cells in Warsaw'
        cmap = 'Reds'
    elif plot_type == 'median_rent':
        # Calculate the median rent price in each grid cell
        median_rent_prices = grid_cells_with_counts.groupby('index_right')['rent_price'].median()
        grid_cells_within_warsaw['median_rent_price'] = median_rent_prices
        grid_cells_within_warsaw['median_rent_price'] = grid_cells_within_warsaw['median_rent_price'].fillna(0)
        column_to_plot = 'median_rent_price'
        title = 'Heat Map of Median Rent Price by Grid Cells in Warsaw'
        cmap = 'Greens'
    else:
        raise ValueError("plot_type must be either 'count' or 'median_rent'")
    
    # Convert the grid cells
    grid_cells_within_warsaw = grid_cells_within_warsaw.to_crs(epsg=3857)

    # Initialize Figure
    fig, ax = plt.subplots(1, 1, figsize=(10, 10))

    grid_cells_within_warsaw.plot(column=column_to_plot, ax=ax, cmap=cmap, linewidth=0.5, edgecolor='black', legend=True, alpha=0.6)

    # Add basemap
    ctx.add_basemap(ax, source=ctx.providers.CartoDB.Positron)

    plt.title(title, fontsize=12, weight='bold')
    ax.set_axis_off()
    plt.show()
    
    return None