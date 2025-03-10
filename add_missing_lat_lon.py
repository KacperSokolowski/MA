from datakit import *

path = f'data_processed/main.csv'
df = pd.read_csv(path)
df_miss_loc = df[df.latitude.isna()]
df_miss_loc = add_geo_location(df_miss_loc)
df.set_index('link', inplace=True)
df_miss_loc.set_index('link', inplace=True)

df['latitude'] = df['latitude'].fillna(df_miss_loc['latitude'])
df['longitude'] = df['longitude'].fillna(df_miss_loc['longitude'])
df.reset_index(inplace=True)
df = df[[df.columns[1], df.columns[2], 'link'] + [col for col in df.columns if col not in [df.columns[1], df.columns[2], 'link']]]
df.to_csv(path,
          encoding='utf-8',
          index=False)