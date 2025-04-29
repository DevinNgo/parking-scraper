# model.py
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.ensemble import RandomForestRegressor  # Random forest is better than LR when working with 

def prediction_model():
    # Combine datasets and rename columns
    parking = pd.read_csv('https://raw.githubusercontent.com/NguyenJimmyT/webscraperSenior/refs/heads/main/parking_data.csv')
    filler = pd.read_csv('https://raw.githubusercontent.com/NguyenJimmyT/webscraperSenior/refs/heads/main/Modified_Parking_Data__Higher_availability_near_8_PM_.csv')

    parking = pd.concat([parking, filler])

    # Convert the strucutres and levels to titlecase if they are not
    parking['structure'] = parking['structure'].str.title()
    parking['level'] = parking['level'].str.title()

    parking = parking.rename(columns={
        'timeScrape': 'time',
        'lastUpdated': 'date',
    })

    parking['date'] = pd.to_datetime(parking['date'])

    # Remove Fullerton Free Church because there is no parking data
    parking = parking[parking['structure'] != 'Fullerton Free Church']

    # Fix time values
    parking['time'] = parking['date'].dt.strftime('%H:%M:%S')

    # Remove and reorder columns
    parking = parking[['structure', 'level', 'available', 'total', 'date', 'time']]

    # Delete rows if their date and level values are the same
    parking = parking.drop_duplicates(subset=['date', 'level'])

    # Convert all 'Full' into 0
    parking['available'] = parking['available'].replace('Full', 0)

    parking['available'] = parking['available'].astype(int)

    # Add days
    parking['day_of_week'] = parking['date'].dt.day_name()

    # Add semester weeks
    semester_start = pd.to_datetime('2025-01-20')  # Example: Jan 20, 2025
    parking['days_since_start'] = (parking['date'] - semester_start).dt.days
    parking['semester_week'] = (parking['days_since_start'] // 7) + 1

    # Add times
    parking['hour'] = pd.to_datetime(parking['time'], format='%H:%M:%S').dt.hour
    parking['minute'] = pd.to_datetime(parking['time'], format='%H:%M:%S').dt.minute
    parking['half_hour'] = parking['hour'] + (parking['minute'] >= 30) * 0.5

    # Replace all 120 in total with 220 because of error in CSUF site
    parking['total'] = parking['total'].replace(120, 220)

    # Parking structure availability
    group_sum = parking.groupby(['structure', 'date', 'time'])['available'].transform('sum')
    group_total = parking.groupby(['structure', 'date', 'time'])['total'].transform('sum')
    parking['current_struc_avail'] = group_sum
    parking['total_struc_avail'] = group_total

    # Reorganize by structure and datetime
    parking = parking.sort_values(by=['date', 'time', 'level']).reset_index(drop=True)

    # Add a boolean for before/after spring break, dates after march 31st are after
    parking['before_spring_break'] = (parking['date'] < pd.to_datetime('2025-03-31'))

    # percentage full = (total_struc_avail - current_struc_avail)/total_struc_avail
    parking['percentage_full'] = (parking['total_struc_avail'] - parking['current_struc_avail']) / parking['total_struc_avail']

    # a. define features
    cat_feats = ['structure', 'day_of_week', 'before_spring_break']
    num_feats = ['semester_week', 'half_hour']

    # b. transformer
    preproc = ColumnTransformer([
    ('cat', OneHotEncoder(handle_unknown='ignore'), cat_feats),
    ('num', 'passthrough', num_feats)
    ])

    # c. pipeline
    model = Pipeline([
    ('pre', preproc),
    ('reg', RandomForestRegressor(n_estimators=100, random_state=42))
    ])

    # d. train–test split (hold out today)
    today = pd.to_datetime(datetime.now()).normalize()
    train = parking[parking['date'] < today]
    X_train = train[cat_feats + num_feats]
    y_train = train['current_struc_avail']
    model.fit(X_train, y_train)

    # --- 1. build a list of 5-minute times ---
    times = pd.date_range("08:00", "20:00", freq="5min").time

    # --- 2. all structures & constant features for “today” ---
    today = pd.to_datetime("today").normalize()
    structures = parking['structure'].unique()
    dow    = today.day_name()
    bsb    = today < pd.to_datetime('2025-03-31')
    sweek  = ((today - pd.to_datetime('2025-01-20')).days // 7) + 1

    # --- 3. assemble predict‐rows ---
    rows = []
    for t in times:
        hh = t.hour + (t.minute >= 30)*0.5
        for struct in structures:
            rows.append({
                'structure': struct,
                'day_of_week':        dow,
                'before_spring_break': bsb,
                'semester_week':      sweek,
                'half_hour':          hh,
                'time':               t.strftime("%H:%M:%S")
            })
    pd_grid = pd.DataFrame(rows)

    # --- 4. predict & round to int ---
    feat_cols = cat_feats + num_feats  # ['structure','day_of_week','before_spring_break','semester_week','half_hour']
    pd_grid['avail'] = model.predict(pd_grid[feat_cols]).round().astype(int)

    # --- 5. pivot into the desired dict‐of‐dicts ---
    pivot = pd_grid.pivot(index='time', columns='structure', values='avail')
    forecast_dict = pivot.to_dict(orient='index')

    return forecast_dict




