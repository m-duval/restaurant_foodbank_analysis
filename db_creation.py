import pandas as pd
import numpy as np
from sqlalchemy import create_engine

# read in data files
food_services_df = pd.read_excel('db/FoodServicesAllReporting.xlsx')
public_facilities_df = pd.read_excel('db/PublicFacilitiesAllReporting.xlsx')
whsl_retail_manufacture_df = pd.read_excel('db/WholesaleRetailManufacturersAllReporting.xlsx')
receiving_food_df = pd.read_excel('db/FoodBanksReceiving.xlsx')

# create one base datafram
frames = [food_services_df, public_facilities_df, whsl_retail_manufacture_df]
food_output_df = pd.concat(frames)



# strip hanging space on 'Full-Service Restaurants'
naics = 'NAICS_CODE_DESCRIPTION'
food_output_df.loc[food_output_df[naics]=='Full-Service Restaurants ', naics] = 'Full-Service Restaurants'
# strip lead/trail space on specified columns (different method)
food_output_df['NAME'] = food_output_df['NAME'].str.strip()
food_output_df['ADDRESS'] = food_output_df['ADDRESS'].str.strip()
food_output_df['CITY'] = food_output_df['CITY'].str.strip()
food_output_df['COUNTY'] = food_output_df['COUNTY'].str.strip()
food_output_df['STATE'] = food_output_df['STATE'].str.strip()
food_output_df['UNIQUEID'] = food_output_df['UNIQUEID'].str.strip()
food_output_df['NAICS_CODE_DESCRIPTION'] = food_output_df['NAICS_CODE_DESCRIPTION'].str.strip()



#     FINAL_OUTPUT = CLEANED EXCESS PRODUCERS BY DROPPING NON-USABLE FOOD PRODUCTS

drop_codes = ([311999,311313,312120,311314,311351,311920,311352,424450,445292,312140,311930,
               311211,311520,311213,311340,311212,722515,312111,311942,311221,312130])
final_output = food_output_df[~food_output_df['NAICS_CODE'].isin(drop_codes)]


#     INDIVIDUAL DATAFRAMES (TABLES FOR .sqlite FILE)

# pull ALL schools
all_schools_df = final_output[final_output['NAICS_CODE']=='SCHOOL']

# pull public schools
public_schools_df = final_output[final_output['NAICS_CODE_DESCRIPTION']=='TYPE: Public Elementary & Secondary']

# pull private schools
private_schools_df = final_output[final_output['NAICS_CODE_DESCRIPTION']=='TYPE: Private Elementary & Secondary']

# pull postsecondary schools
postsecondary_schools_df = final_output[final_output['NAICS_CODE_DESCRIPTION']=='TYPE: Postsecondary']

# pull correctional facilities
corrections_df = final_output[final_output['UNIQUEID'].str.contains('COR')]

# pull healthcare facilities & drop 'Specialty (except Psychiatric and Substance Abuse) Hospitals'
healthcare_df = (final_output[final_output['UNIQUEID'].str.contains('HEA') 
                 & ~final_output['NAICS_CODE_DESCRIPTION'].str.contains('Specialty')])

# pull restaurants/hotels/caterers/casinos [HOSPITALITY]
restaurants_codes = [311811,722330,722511,722513,722514,721120,713210,722320,721110]
restaurant_df = final_output[final_output['NAICS_CODE'].isin(restaurants_codes)]

# pull grocery/market/wholesale/food clubs
grocery_df = (final_output[final_output['NAICS_CODE_DESCRIPTION'].str.contains('Club', case=False) 
              | final_output['NAICS_CODE_DESCRIPTION'].str.contains('Market', case=False) 
              | final_output['NAICS_CODE_DESCRIPTION'].str.contains('Merchant', case=False)
              | final_output['NAICS_CODE'].isin([445299,445291])])

# pull manufacturers/producers/processers
production_df = (final_output[final_output['NAICS_CODE_DESCRIPTION'].str.contains('Pro', case=False)
                 | final_output['NAICS_CODE_DESCRIPTION'].str.contains('Canning', case=False) 
                 | final_output['NAICS_CODE_DESCRIPTION'].str.contains('Commercial', case=False) 
                 | final_output['NAICS_CODE_DESCRIPTION'].str.contains('Manufactur', case=False) 
                 | final_output['NAICS_CODE_DESCRIPTION'].str.contains('Refining', case=False)                            
                 | final_output['NAICS_CODE_DESCRIPTION'].str.contains('Slaughter', case=False)])
production_df = production_df[~production_df['NAICS_CODE_DESCRIPTION'].str.contains('Merchant', case=False)]



#     INDIVIDUAL DATAFRAMES (TABLES FOR .sqlite FILE) CONT.

# total excess food produced by zip, ordered by descending EXCESSFOOD_TONYEAR_LOWEST sum
low_excessfood_by_zipcode = (final_output.groupby('ZIP_CODE')
                         ['EXCESSFOOD_TONYEAR_LOWEST', 'EXCESSFOOD_TONYEAR_HIGHEST']
                         .sum().sort_values('EXCESSFOOD_TONYEAR_LOWEST', ascending=False)
                         .nlargest(3, 'EXCESSFOOD_TONYEAR_LOWEST'))

# total excess food produced by zip, ordered by descending EXCESSFOOD_TONYEAR_HIGHEST sum
high_excessfood_by_zipcode = (final_output.groupby('ZIP_CODE')
                         ['EXCESSFOOD_TONYEAR_LOWEST', 'EXCESSFOOD_TONYEAR_HIGHEST']
                         .sum().sort_values('EXCESSFOOD_TONYEAR_HIGHEST', ascending=False)
                         .nlargest(3, 'EXCESSFOOD_TONYEAR_HIGHEST'))

# total excess food produced by business type, ordered by descending EXCESSFOOD_TONYEAR_LOWEST sum
low_excess_by_naics_desc = (final_output.groupby('NAICS_CODE_DESCRIPTION')
                        ['EXCESSFOOD_TONYEAR_LOWEST', 'EXCESSFOOD_TONYEAR_HIGHEST']
                        .sum().round(2).sort_values('EXCESSFOOD_TONYEAR_LOWEST', ascending=False)
                        .nlargest(3, 'EXCESSFOOD_TONYEAR_LOWEST'))

# total excess food produced by business type, ordered by descending EXCESSFOOD_TONYEAR_LOWEST sum
high_excess_by_naics_desc = (final_output.groupby('NAICS_CODE_DESCRIPTION')
                        ['EXCESSFOOD_TONYEAR_LOWEST', 'EXCESSFOOD_TONYEAR_HIGHEST']
                        .sum().round(2).sort_values('EXCESSFOOD_TONYEAR_HIGHEST', ascending=False)
                        .nlargest(3, 'EXCESSFOOD_TONYEAR_HIGHEST'))



#     BUILD OUT DATABASE CONNECTION AND WORK TOOLS

# path to sqlite
food_database_path = "db/excess_food.sqlite"
# set engine for communication with the database
engine = create_engine(f"sqlite:///{food_database_path}", echo=False)
# create connection
conn = engine.connect()



#     SEND ALL DATAFRAMES TO THE .sqlite FILE

all_schools_df.to_sql('all_schools', conn, if_exists="replace")
public_schools_df.to_sql('public_schools', conn, if_exists="replace")
private_schools_df.to_sql('private_schools', conn, if_exists="replace")
postsecondary_schools_df.to_sql('postsecondary_schools', conn, if_exists="replace")
corrections_df.to_sql('corrections', conn, if_exists="replace")
healthcare_df.to_sql('healthcare', conn, if_exists="replace")
restaurant_df.to_sql('restaurant', conn, if_exists="replace")
grocery_df.to_sql('grocery', conn, if_exists="replace")
production_df.to_sql('production', conn, if_exists="replace")
low_excessfood_by_zipcode.to_sql('low_excessfood_by_zipcode', conn, if_exists="replace")
high_excessfood_by_zipcode.to_sql('high_excessfood_by_zipcode', conn, if_exists="replace")
low_excess_by_naics_desc.to_sql('low_excess_by_naics_desc', conn, if_exists="replace")
high_excess_by_naics_desc.to_sql('high_excess_by_naics_desc', conn, if_exists="replace")



#     CLOSE CONNECTION TO DATABASE

conn.close()





print('db_creation FILE HAS COMPLETED RUNNING')