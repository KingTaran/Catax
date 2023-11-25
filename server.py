import pymongo
import pandas as pd
import time

# Set up your MongoDB connection
client = pymongo.MongoClient("mongodb://gewgawrav:catax1234@chongodb.catax.me")
database_name = "MasterCC"
collection_name = "BTCAlpha"

# Access the specified database and collection
db = client[database_name]
collection = db[collection_name]

# Measure the start time
start_time = time.time()

# Retrieve data from the collection
cursor = collection.find()

# Convert the cursor to a Pandas DataFrame
df = pd.DataFrame(list(cursor))

# Get unique values of parent_sym and child_sym
unique_parent_sym_values = df['parent_sym'].unique()
unique_child_sym_values = df['child_sym'].unique()

# Connect to your local MongoDB
local_db_url = "mongodb://localhost:27017"
client_local = pymongo.MongoClient(local_db_url)


# Iterate through unique parent_sym and child_sym combinations
for parent_sym_value in unique_parent_sym_values:
    for child_sym_value in unique_child_sym_values:
        # Select rows for the current combination of parent_sym and child_sym
        subset_rows = df[(df['parent_sym'] == parent_sym_value) & (df['child_sym'] == child_sym_value)]

        # Select rows where all four columns have a value of zero
        condition = (subset_rows['open'] == 0) & (subset_rows['high'] == 0) & (subset_rows['low'] == 0) & (subset_rows['close'] == 0)

        # Select rows based on the condition
        df_selected = subset_rows[~condition]

        # Convert the "time" column to datetime for proper sorting
        df_selected['time'] = pd.to_datetime(df_selected['time'], format='%Y-%m-%d %H:%M:%S')

        # Sort the DataFrame based on the "time" column
        df_sorted = df_selected.sort_values(by='time')

        # Calculate the mean of "open" and "close" for each row
        df_sorted['mean_open_close'] = df_sorted[['open', 'close']].mean(axis=1)

        # Drop the specified column
        df_sorted = df_sorted.drop(columns=['time'])
        df_sorted = df_sorted.drop(columns=['conversionType'])
        df_sorted = df_sorted.drop(columns=['conversionSymbol'])
        
        # Add new columns with the same value for all rows
        df_sorted['source'] = 'crypto-compare'
        df_sorted['exchange'] = collection_name
        df_sorted['candle'] = 'hourly'

        # Specify the collection name where you want to save the cleaned data
        local_collection_name = f"{parent_sym_value}_{child_sym_value}"

        # Convert the DataFrame to a NumPy array for MongoDB insertion
        # Assuming df_sorted is your DataFrame
        data_to_insert = df_sorted.to_dict(orient='records')

        # Create the local MongoDB collection if it doesn't exist
        # if local_collection_name not in client_local[collection_name].list_collection_names():
        #    client_local[collection_name].create_collection(local_collection_name)

        # Drop the existing documents in the local MongoDB collection
        # client_local[collection_name][local_collection_name].delete_many({})
        local_database='PAIR_CLUSTER'
        
        if data_to_insert:
            client_local[local_database][local_collection_name].insert_many(data_to_insert)
        else:
            print("Warning: 'processed_data' is an empty list.")
            
# Measure the end time
end_time = time.time()

# Calculate the execution time
execution_time = end_time - start_time

print(f"Execution time: {execution_time} seconds")
     
# Close the MongoDB connections
client.close()
client_local.close()
