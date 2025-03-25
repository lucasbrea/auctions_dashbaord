from flask import Flask, render_template, request
import pandas as pd
import os

app = Flask(__name__)

CSV_PATH = os.path.join("opt/render/project/src/Data/merged_auctions.csv")
DAMS_CSV_PATH = os.path.join("opt/render/project/src/Data/merge_auction_dams.csv")

HORSES_RENAMED_COLUMNS = {
    'name': 'Name',
    'studbook_id': 'Studbook ID',
    'padrillo': 'Sire',
    'M': 'Dam',
    'birth_eday':'Birth Date',
    'sex': 'Sex',
    'haras': 'Haras',
    'remate': 'Remate',
    'source': 'Source',
}
# Define which columns to show filters for
HORSES_FILTER_COLUMNS = ['name', 'studbook_id', 'padrillo', 'M', 'sex', 'haras', 'remate', 'source']
DAMS_FILTER_COLUMNS = ['name', 'padrillo', 'M', 'sex', 'haras', 'link']

def load_data(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"CSV file not found at {file_path}")
    
    df = pd.read_csv(file_path)
    
    # Convert PS, PR, and PRS to percentages
    percentage_columns = ['PS', 'PR', 'PRS','PB','PBRS']
    for col in percentage_columns:
        if col in df.columns:
            df[col] = (df[col]*100).round(2).astype(str)+"%"
    
    return df

def filter_dataframe(df, filters):
    if not filters:
        return df
    
    for column, value in filters.items():
        if value and column in df.columns:
            df = df[df[column].astype(str).str.contains(value, case=False, na=False)]
    return df

@app.route('/')
def index():
    try:
        # Load both datasets
        horses_df = load_data(CSV_PATH)
        dams_df = load_data(DAMS_CSV_PATH)

        horses_df.rename(columns=HORSES_RENAMED_COLUMNS, inplace=True)
        horses_df = horses_df.iloc[:, [0,1,6,7,8,2,3,4,5,10,9,11,12,13,14,15,16]]
        # Calculate max values for gradient columns
        gradient_columns = ['PR', 'PS', 'PRS', 'PB', 'PBRS']
        horses_max_values = {col: float(horses_df[col].str.rstrip('%').astype(float).max()) 
                           for col in gradient_columns if col in horses_df.columns}
        dams_max_values = {col: float(dams_df[col].str.rstrip('%').astype(float).max()) 
                          for col in gradient_columns if col in dams_df.columns}
        
        # Get filter values from request only for specified columns
        horses_filters = {col: request.args.get(f'horses_{col}') for col in HORSES_FILTER_COLUMNS}
        dams_filters = {col: request.args.get(f'dams_{col}') for col in DAMS_FILTER_COLUMNS}
        
        # Apply filters
        horses_df = filter_dataframe(horses_df, horses_filters)
        dams_df = filter_dataframe(dams_df, dams_filters)
        
        # Convert DataFrames to HTML tables
        horses_table = horses_df.to_html(classes='table table-striped', index=False)
        dams_table = dams_df.to_html(classes='table table-striped', index=False)
        
        return render_template('index.html', 
                             horses_table=horses_table,
                             dams_table=dams_table,
                             horses_filters=horses_filters,
                             dams_filters=dams_filters,
                             horses_max_values=horses_max_values,
                             dams_max_values=dams_max_values)
    except Exception as e:
        return render_template('index.html', error=str(e))

if __name__ == '__main__':
    app.run(debug=True) 
