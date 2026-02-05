"""
Data Processor v1.0
A simple data processing application that demonstrates layer caching issues.
"""

import pandas as pd
import numpy as np
from pathlib import Path

def process_data():
    """Process sample data files."""
    print("Data Processor v1.0")
    print("=" * 50)
    
    data_dir = Path("data")
    
    if not data_dir.exists():
        print("⚠️  No data directory found. Creating sample data...")
        data_dir.mkdir(exist_ok=True)
        
        # Create sample CSV
        sample_data = pd.DataFrame({
            'id': range(1, 101),
            'value': np.random.randint(1, 1000, 100),
            'category': np.random.choice(['A', 'B', 'C'], 100)
        })
        sample_data.to_csv(data_dir / 'sample.csv', index=False)
        print("✓ Created sample.csv")
    
    # Process all CSV files
    csv_files = list(data_dir.glob('*.csv'))
    
    if not csv_files:
        print("No CSV files to process.")
        return
    
    print(f"\nFound {len(csv_files)} CSV file(s):")
    
    for csv_file in csv_files:
        df = pd.read_csv(csv_file)
        print(f"\n📊 {csv_file.name}")
        print(f"   Rows: {len(df)}")
        print(f"   Columns: {list(df.columns)}")
        
        if 'value' in df.columns:
            print(f"   Average value: {df['value'].mean():.2f}")
            print(f"   Max value: {df['value'].max()}")
            print(f"   Min value: {df['value'].min()}")
    
    print("\n" + "=" * 50)
    print("✓ Processing complete!")

if __name__ == "__main__":
    process_data()
