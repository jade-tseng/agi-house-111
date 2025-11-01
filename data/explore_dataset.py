import pandas as pd
import os
import glob

# Get all CSV files in the data directory
csv_files = glob.glob("*.csv")
print(f"Found {len(csv_files)} CSV files:")
for file in csv_files:
    print(f"  - {file}")

# Load the first CSV file to explore structure
if csv_files:
    first_file = csv_files[0]
    print(f"\nExploring structure of: {first_file}")
    
    # Read first few rows to understand structure
    df_sample = pd.read_csv(first_file, nrows=5)
    print(f"\nDataset shape (first 5 rows): {df_sample.shape}")
    print(f"\nColumns: {list(df_sample.columns)}")
    print(f"\nFirst few rows:")
    print(df_sample)
    
    # Get full dataset info
    df_full = pd.read_csv(first_file)
    print(f"\nFull dataset shape: {df_full.shape}")
    print(f"\nData types:")
    print(df_full.dtypes)
    
    print(f"\nBasic statistics:")
    print(df_full.describe())
    
    # Check for missing values
    print(f"\nMissing values:")
    print(df_full.isnull().sum())
    
    # Show unique values for categorical columns (if any)
    for col in df_full.columns:
        if df_full[col].dtype == 'object':
            unique_count = df_full[col].nunique()
            if unique_count < 20:  # Only show if reasonable number of unique values
                print(f"\nUnique values in '{col}' ({unique_count} unique):")
                print(df_full[col].value_counts().head(10))
            else:
                print(f"\n'{col}' has {unique_count} unique values (too many to display)")
