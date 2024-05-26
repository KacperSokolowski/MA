import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as ctx
import pandas as pd
import seaborn as sns
import random

def plot_heat_map_district(
    df: pd.DataFrame,
    plot_type: str = 'count',
    recording_units_pth: str = 'geographic_data/recording_units_poland/jednostki_ewidencyjne.shp') -> None:
    """
    Plots a heat map of Warsaw districts showing either the count of apartments or the median rent price.

    Parameters:
    - df (pd.DataFrame): The DataFrame containing apartment data with 'longitude' and 'latitude' columns.
    - plot_type (str): The type of plot to create. Either 'count' to show the number of apartments or 'median_rent'
      to show the median rent price. Defaults to 'count'.
    - recording_units_pth (str): The file path to the shapefile containing the recording units.

    Returns:
    - None: This function does not return a value but displays a heat map of the specified plot type.

    The function performs the following steps:
    1. Loads the shapefile containing polish recording units and filters it to include only Warsaw districts.
    2. Creates a GeoDataFrame from the input DataFrame with apartment locations.
    3. Performs a spatial join to count apartments or calculate median rent in each district.
    4. Plots a heat map of the specified plot type using a color map and adds district names for context.
    
    Raises:
    - ValueError: If `plot_type` is not 'count' or 'median_rent'.
    """

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
    grid_cells_shape_pth: str = 'geographic_data/GRID_NSP2021_RES/GRID_NSP2021_RES.shp') -> None:
    """
    Plots a heat map of grid cells in Warsaw showing either the count of apartments or the median rent price.

    Parameters:
    - df (pd.DataFrame): The DataFrame containing apartment data with 'longitude' and 'latitude' columns.
    - plot_type (str): The type of plot to create. Either 'count' to show the number of apartments or 'median_rent' 
      to show the median rent price. Defaults to 'count'.
    - warsaw_shape_pth (str): The file path to the shapefile containing Warsaw borders.
    - grid_cells_shape_pth (str): The file path to the shapefile containing the grid cells.

    Returns:
    - None: This function does not return a value but displays a heat map of the specified plot type.

    The function performs the following steps:
    1. Loads the shapefile containing polish municipalities borders and filters it to include only Warsaw.
    2. Loads the shapefile containing the grid cells and converts the coordinate reference system.
    3. Overlays the grid cells with Warsaw borders to filter grid cells within Warsaw.
    4. Creates a GeoDataFrame from the input DataFrame with apartment locations.
    5. Performs a spatial join to count apartments or calculate median rent in each grid cell.
    6. Plots a heat map of the specified plot type using a color map and adds a basemap for context.
    
    Raises:
    - ValueError: If `plot_type` is not 'count' or 'median_rent'.
    """
    
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

def plot_categorical_distributions(
    df: pd.DataFrame,
    max_unique_values: int = 10,
    num_cols:int = 3) -> None:
    """
    Plots the distributions of categorical variables in a DataFrame.

    Parameters:
    - df (pd.DataFrame): The DataFrame containing the data to be plotted.
    - max_unique_values (int): The maximum number of unique values a column can have to be considered categorical. 
      Defaults to 10.
    - num_cols (int): The number of columns in the plot grid. Defaults to 3.

    Returns:
    - None: This function does not return a value but displays the plots of categorical variable distributions.
    """

    categorical_cols = [col for col in df.columns if df[col].nunique() < max_unique_values]

    num_rows = (len(categorical_cols) + num_cols - 1) // num_cols
    fig, axes = plt.subplots(nrows=num_rows, ncols=num_cols, figsize=(15, 15))

    for i, ax in zip(categorical_cols, axes.flatten()):
        if df[i].dtype.kind in 'iuf' and df[i].nunique() <= max_unique_values:
            order = sorted(df[i].unique())
            sns.countplot(x=df[i], ax=ax, order=order)
            ax.tick_params(axis='x', rotation=0)
        else:
            sns.countplot(x=df[i], ax=ax, order=df[i].value_counts().index)
            ax.tick_params(axis='x', rotation=45)
        
        ax.set_title(f"{i}")
        ax.set_xlabel("")
        ax.set_ylabel("Count")
        ax.grid(True)

        total = float(len(df[i]))
        for p in ax.patches:
            height = p.get_height()
            ax.annotate(f'{(height/total)*100:.2f}%', 
                        (p.get_x() + p.get_width() / 2., height), 
                        ha='center', va='bottom')

    plt.suptitle('Distributions of categorical variables', size=20, y=1)
    plt.tight_layout()
    plt.show()

    return None

def plot_continuous_distributions(
    df: pd.DataFrame,
    max_unique_values: int = 20,
    num_cols: int = 3,
    sample_size: int = 1000) -> None:
    """
    Plots the distributions of continuous variables in a DataFrame.

    Parameters:
    - df (pd.DataFrame): The DataFrame containing the data to be plotted.
    - max_unique_values (int): The minimum number of unique values a column must have to be considered continuous. 
      Defaults to 20.
    - num_cols (int): The number of columns in the plot grid. Defaults to 3.
    - sample_size (int): The number of samples to plot if the DataFrame is larger than this value. 
      Defaults to 1000.

    Returns:
    - None: This function does not return a value but displays the plots of continuous variable distributions.

    The function identifies columns with more unique values than the specified `max_unique_values` and plots 
    their distributions using histograms with KDE (Kernel Density Estimate) plots.
    If the DataFrame has more rows than the `sample_size`, a random sample 
    of the specified size is taken to create the plots for efficiency. The 'rent_price' column has a specific 
    filter applied to exclude values above 20000.
    """
    continuous_cols = [col for col in df.columns if col not in ['longitude', 'latitude'] and df[col].dtype.kind in 'iuf' and df[col].nunique() > max_unique_values]

    if len(df) > sample_size:
        df_sample = df.sample(n=sample_size, random_state=42)
    else:
        df_sample = df.copy()

    num_rows = (len(continuous_cols) + num_cols - 1) // num_cols
    fig, axes = plt.subplots(nrows=num_rows, ncols=num_cols, figsize=(15, 15))

    for i, ax in zip(continuous_cols, axes.flatten()):
        if i == 'rent_price':
            data_to_plot = df_sample[df_sample[i] < 20000] if len(df) > sample_size else df[df[i] < 20000]
        else:
            data_to_plot = df_sample if len(df) > sample_size else df

        sns.histplot(data_to_plot[i], ax=ax, kde=True)
        ax.set_title(f"{i}")
        ax.set_xlabel("Value")
        ax.set_ylabel("Frequency")
        ax.grid(True)

    plt.suptitle('Distributions of Continuous Variables', size=20, y=1)
    plt.tight_layout()
    plt.subplots_adjust(top=0.95)
    plt.show()

    return None


def plot_scatter_continuous_vs_rent(
    df: pd.DataFrame,
    max_unique_values: int = 20,
    sample_size: int = 1000) -> None:
    """
    Plots scatter plots of continuous variables against 'rent_price' in a DataFrame.

    Parameters:
    - df (pd.DataFrame): The DataFrame containing the data to be plotted.
    - max_unique_values (int): The minimum number of unique values a column must have to be considered continuous.
      Defaults to 20.
    - sample_size (int): The number of samples to plot if the DataFrame is larger than this value.
      Defaults to 1000.

    Returns:
    - None: This function does not return a value but displays scatter plots of continuous variables against 'rent_price'.

    The function identifies continuous columns with more unique values than the specified `max_unique_values` and
    plots scatter plots against 'rent_price'. The plots are arranged in a grid with 2 columns. If the DataFrame has 
    more rows than the `sample_size`, a random sample of the specified size is taken to create the plots for efficiency. 
    Specific filters are applied to 'rent_price', 'building_height', and 'year_of_construction' for cleaner visualization.
    """

    colors = ["darkseagreen", "steelblue", "mediumpurple", "orange", 
              "pink", "olivedrab", "turquoise", "salmon", 
              "slategray", "#fbb4ae"]

    continuous_cols = [col for col in df.columns if col not in ['longitude', 'latitude', 'rent_price'] and df[col].dtype.kind in 'iuf' and df[col].nunique() > max_unique_values]

    df_filtered = df[(df['rent_price'] < 20000) & 
                     (df['building_height'] < 30) & 
                     (df['year_of_construction'] > 1900)].copy()

    if len(df_filtered) > sample_size:
        df_sample = df_filtered.sample(n=sample_size, random_state=42)
    else:
        df_sample = df_filtered

    num_plots = len(continuous_cols)
    num_cols = 2
    num_rows = (num_plots + num_cols - 1) // num_cols
    fig, axes = plt.subplots(nrows=num_rows, ncols=num_cols, figsize=(15, num_rows * 5))

    axes = axes.flatten()

    for i, feature in enumerate(continuous_cols):
        color = random.choice(colors)
        sns.scatterplot(ax=axes[i], data=df_sample, x=feature, y='rent_price', color=color, alpha=0.5)
        sns.regplot(ax=axes[i], data=df_sample, x=feature, y='rent_price', scatter=False, color=color, line_kws={"alpha":0.2, "lw":2})
        axes[i].set_title(f'Relationship between {feature} and Rent Price')
        axes[i].set_xlabel(f'{feature}')
        axes[i].set_ylabel('Rent Price')

    plt.tight_layout()
    plt.show()

    return None


def plot_boxplots_categorical_vs_rent(
    df: pd.DataFrame,
    max_unique_values: int = 10,
    num_cols: int = 3,
    sample_size: int = 1000) -> None:
    """
    Plots boxplots of categorical variables against 'rent_price' in a DataFrame.

    Parameters:
    - df (pd.DataFrame): The DataFrame containing the data to be plotted.
    - max_unique_values (int): The maximum number of unique values a column can have to be considered categorical. 
      Defaults to 10.
    - num_cols (int): The number of columns in the plot grid. Defaults to 3.
    - sample_size (int): The number of samples to plot if the DataFrame is larger than this value. 
      Defaults to 1000.

    Returns:
    - None: This function does not return a value but displays boxplots of categorical variables against 'rent_price'.

    The function identifies columns with fewer unique values than the specified `max_unique_values` and plots 
    their distributions using boxplots. The plots are arranged in a grid with `num_cols` columns. If the DataFrame has 
    more rows than the `sample_size`, a random sample of the specified size is taken to create the plots for efficiency. 
    The 'rent_price' column is filtered to exclude values above 20000 for cleaner visualization.
    """

    categorical_cols = [col for col in df.columns if df[col].nunique() < max_unique_values]

    df_filtered = df[df['rent_price'] < 20000]

    if len(df_filtered) > sample_size:
        df_sample = df_filtered.sample(n=sample_size, random_state=42)
    else:
        df_sample = df_filtered

    num_rows = (len(categorical_cols) + num_cols - 1) // num_cols
    fig, axes = plt.subplots(nrows=num_rows, ncols=num_cols, figsize=(15, num_rows * 5))

    for i, ax in zip(categorical_cols, axes.flatten()):
        sns.boxplot(ax=ax, data=df_sample, x=i, y='rent_price')
        ax.set_title(f'Rent Price Distribution by {i}')
        ax.set_xlabel(f'{i}')
        ax.set_ylabel('Rent Price')
        ax.tick_params(axis='x', rotation=45)
        ax.grid(True)

    plt.suptitle('Boxplots of Categorical Variables vs Rent Price', size=20, y=1)
    plt.tight_layout()
    plt.subplots_adjust(top=0.95) 
    plt.show()

    return None

def plot_boxplots_rent_price_by_district(
    df: pd.DataFrame,
    sample_size: int = 1000) -> None:
    """
    Plots a boxplot of 'rent_price' distribution by 'district' in a DataFrame.

    Parameters:
    - df (pd.DataFrame): The DataFrame containing the data to be plotted.
    - sample_size (int): The number of samples to plot if the DataFrame is larger than this value.
      Defaults to 1000.

    Returns:
    - None: This function does not return a value but displays a boxplot of 'rent_price' distribution by 'district'.

    The function filters the DataFrame to include only rows where 'rent_price' is less than 20000 for cleaner visualization.
    If the DataFrame has more rows than the `sample_size`, a random sample of the specified size is taken to create the plot
    for efficiency. The boxplot is created with 'district' on the x-axis and 'rent_price' on the y-axis.
    """

    df_filtered = df[df['rent_price'] < 20000].copy()

    if len(df_filtered) > sample_size:
        df_sample = df_filtered.sample(n=sample_size, random_state=42)
    else:
        df_sample = df_filtered

    fig, ax = plt.subplots(figsize=(12, 6))

    sns.boxplot(ax=ax, data=df_sample, x='district', y='rent_price')
    ax.set_title('Rent Price Distribution by District')
    ax.set_xlabel('District')
    ax.set_ylabel('Rent Price')
    ax.tick_params(axis='x', rotation=45)
    ax.grid(True)

    plt.tight_layout()
    plt.show()

    return None