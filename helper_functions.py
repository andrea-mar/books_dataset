
import pandas as pd  # For data understanding and preparation
import numpy as np  # For processing vectors
import seaborn as sns  # For visualization
import matplotlib.pyplot as plt  # For plotting
from matplotlib.colors import LinearSegmentedColormap  # To create custom colormaps
from matplotlib.figure import Figure  # For figure customization
from matplotlib.axes import Axes  # For axes customization
from typing import Tuple  # For typing function outputs


def plot_correlation_matrix(df: pd.DataFrame, threshold: float=0.8, figsize: Tuple[int, int]=(14, 14)) -> Tuple[Figure, Axes]:
    """
    Plots a heatmap of the correlation matrix for the given DataFrame.

    This function visualizes feature correlations in a clear and concise way:
    - The lower triangle displays all correlations.
    - The upper triangle only displays correlations with an absolute value greater than 0.6.
    - Correlation values are annotated on the heatmap for better interpretability.
    - A custom dark-red-to-white colormap is used to emphasize the strength of correlations.

    Parameters:
        df (pandas.DataFrame): The DataFrame containing numerical features to compute the correlation matrix.

    Returns:
        Tuple[Figure, Axes]: A tuple containing the Matplotlib `figure` and `axes` objects.
    """
    # Calculate the correlation matrix
    corr = df.corr()
    
    # Convert correlation matrix to numpy array for easier indexing
    corr_array = corr.values
    feature_names = corr.columns
    
    # Create a mask for the upper triangle
    mask = np.triu(np.ones_like(corr_array, dtype=bool))
    
    # Mask correlations below the threshold
    mask_lower = np.abs(corr_array) < threshold
    mask = mask & mask_lower
    
    # Set up the matplotlib figure
    fig, ax = plt.subplots(figsize=figsize)
    
    # Create custom colormap: dark red -> white -> dark red
    colors = [(0.55, 0, 0), (1, 1, 1), (0.55, 0, 0)]  # dark red, white, dark red
    custom_cmap = LinearSegmentedColormap.from_list('custom', colors, N=256)
    
    # Plot the masked heatmap
    masked_corr = np.ma.masked_where(mask, corr_array)
    cax = ax.imshow(masked_corr, cmap=custom_cmap, interpolation='nearest', vmin=-1, vmax=1)
    
    # Add correlation values
    for i in range(len(feature_names)):
        for j in range(len(feature_names)):
            if not mask[i, j]:  # Only show values where mask is False
                text_color = 'white' if abs(corr_array[i, j]) > 0.5 else 'black'
                ax.text(j, i, f'{corr_array[i, j]:.2f}', 
                       ha='center', va='center', color=text_color)
    
    # Add color bar
    cbar = fig.colorbar(cax, ax=ax, shrink=0.8)
    cbar.ax.set_ylabel('Correlation', rotation=-90, va="bottom")
    
    # Set axis labels
    ax.set_xticks(np.arange(len(feature_names)))
    ax.set_yticks(np.arange(len(feature_names)))
    ax.set_xticklabels(feature_names, rotation=90)
    ax.set_yticklabels(feature_names)
    
    # Add labels for x and y axes
    plt.xlabel('Features', size=10)
    plt.ylabel('Features', size=10)
    plt.title(f'Correlation Matrix : All Correlations Below the Diagonal;\nAbove the Diagonal, Only Correlations > ±{threshold}', size=12)
    
    # Remove gridlines
    ax.grid(False)
    
    # Adjust layout
    plt.tight_layout()
    
    return fig, ax



def missing_values_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Summarizes columns in a DataFrame with significant missing values.

    Args:
        df (DataFrame): The input DataFrame to analyze.

    Returns:
        DataFrame: A DataFrame containing the count and percentage of missing values 
                   for columns with more than 70% missing data, sorted by percentage 
                   in descending order.

    The returned DataFrame has the following structure:
        - `Missing Values`: Total number of missing values per column.
        - `Percentage`: Percentage of missing values per column.
    """
    # Count total missing values for each column
    missing_count = df.isnull().sum()

    # Calculate percentage of missing values for each column
    missing_percentage = (df.isnull().sum() / len(df)) * 100

    # Create a DataFrame summarizing the missing data
    missing_summary = pd.DataFrame({
        'Missing Values': missing_count,
        'Percentage': missing_percentage
    })

    # Filter only columns with missing data and sort by the most missing
    missing_summary = missing_summary[missing_summary['Percentage'] > 70]
    missing_summary = missing_summary.sort_values(by='Percentage', ascending=False)

    return missing_summary

