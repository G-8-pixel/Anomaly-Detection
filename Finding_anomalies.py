#!/usr/bin/env python
# coding: utf-8

# ### Read RA list

# In[1]:


import pandas as pd
import numpy as np

ra_list = pd.read_excel('D:/SVL/2021-06-16_ra_list_v1.6.xlsx', keep_default_na = False, na_values = [''])
ra_list


# ### Finding anomalies

# In[2]:


def find_anomalies(raList, leiData):
    
    jurisdiction_by_ra = raList.fillna('--').groupby('Registration Authority Code')['Country Code'].apply(list)
#     print('Jurisdiction by RA given as a list: ', jurisdiction_by_ra.head(15))
    
    tmp=leiData[leiData['Entity.LegalJurisdiction'].notnull() & 
       leiData['Entity.RegistrationAuthority.RegistrationAuthorityID'].notnull() &
       (~leiData['Entity.RegistrationAuthority.RegistrationAuthorityID'].isin(['RA777777', 'RA888888', 'RA999999']))
                
    ].assign(ra_jurisdictions=lambda d: d['Entity.RegistrationAuthority.RegistrationAuthorityID'].apply(lambda x: tuple(jurisdiction_by_ra.get(x, [])))
    ).assign(not_covered= lambda d: d.apply(lambda row: row['Entity.LegalJurisdiction'][:2] not in jurisdiction_by_ra.get(row['Entity.RegistrationAuthority.RegistrationAuthorityID'], []), axis=1)) 
    
    not_covered = tmp[tmp.not_covered]
    
    return not_covered


# ### Chunking LEI data, Call the function to find anomalies, Concatenate the results

# In[3]:


# chunks = pd.concat(lei_data, ignore_index = True)


cols = ['LEI', 'Entity.LegalName','Entity.RegistrationAuthority.RegistrationAuthorityID', 'Entity.RegistrationAuthority.RegistrationAuthorityEntityID', 
        'Entity.RegistrationAuthority.OtherRegistrationAuthorityID','Entity.LegalJurisdiction','Entity.EntityStatus','Registration.RegistrationStatus', 'Registration.ManagingLOU']

# num_rows = 1

# num_rows = 0
chunks = pd.DataFrame()
# Step 1: using chunksize method in order to reduce memory consumption
lei_data = pd.read_csv('D:/SVL/20211202-0800-gleif-goldencopy-lei2-golden-copy.csv',
    low_memory=False, dtype=str, na_values=[''], keep_default_na=False, usecols = cols, chunksize=400000)
for chunk in lei_data:
    # calculate the size of total data/ total number of rows
#     num_rows = num_rows + len(chunk)
#     print('CHUNK LEIs')
#     print(chunk)

    # Step 2: Call the function. Show anomalies
    result = find_anomalies (ra_list, chunk)
    # print('ANOMALIES', result)
    
# print(num_rows) 

    # chunking into smaller csv files
#     chunk.to_csv('D:/SVL/Chunks/Lei golden copy chunk' + str(num_rows) + '.csv', index= False)
#     num_rows += 1
    
    # Step 3: Concatenate the results
    chunks = pd.concat([chunks, result]) 
new_chunks = chunks.reset_index()
new_chunks
# len(chunks) 
# chunk.info()


# In[173]:


data_merged = pd.merge(new_chunks, ra_list, left_on = 'Entity.RegistrationAuthority.RegistrationAuthorityID', right_on='Registration Authority Code', how='left')
data_merged


# In[183]:


drop_duplicates= data_merged.drop_duplicates('LEI')
drop_duplicates


# In[185]:


drop_duplicates.groupby(['Entity.LegalJurisdiction', 'Country Code']).size().reset_index()


# In[187]:


drop_duplicates[(drop_duplicates['Entity.LegalJurisdiction'] == 'GB') & (drop_duplicates['Country Code'] == 'NO') ]


# ### Results as a single excel file

# In[169]:


results = pd.ExcelWriter('D:/SVL/Chunks/findingAnomalies.xlsx')
new_chunks.to_excel(results, sheet_name = 'Anomalies')
results.close()

