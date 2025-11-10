from supabase import create_client, Client
import os
from dotenv import load_dotenv
import json
load_dotenv()

#how to init supabase in python
url: str = os.getenv("supabaseUrl")
key: str = os.getenv("supabaseKey")
supabase: Client = create_client(url, key)

# #how to load json data into database
# path = "data"

# for filename in os.listdir(path):
#     with open(os.path.join(path,filename)) as file:
#         models = json.load(file)
#         for m in models:
#             supabase.table("car").insert({"metadata":m}).execute()
            

#note that our data are jsonb objects, we need to use arrow to access
#-> returns json object
#->> string response
#::int specify return data
res = (supabase.table("car").select('metadata->model, metadata->engine_specs->Power',count="exact").eq('metadata->>brand','LEXUS').execute())
print(res)