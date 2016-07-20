
# coding: utf-8

# In[ ]:

get_ipython().system('pip install regex # A sligthly better version of RE')
get_ipython().system('pip install html5lib # For Pandas read_html used to parse mapping wikitables ')
get_ipython().system('pip install pandas # A great library for data wrangling (and analysis) ')


# In[13]:

import pandas as pd 
import regex
import os 
from polyglot.text import Text


# # Metadata and mappings
# The template mapping can be found here:
# 
# Phabricator task [T139724](https://phabricator.wikimedia.org/T139724)
# 
# The original metadata is a Google Spreadsheet located here:
# 
# https://docs.google.com/spreadsheets/d/1s6l0Ms_14_b3wZhPHGgbCYFCs0nrKlD9E-Uxk_r3Mnc/edit?ts=57737736#gid=0
# 
# The doc below is downloaded locally 2016-07-19 16:55

# In[3]:

metadata_it = pd.read_excel("./data/COH_GAR_metadata.xlsx",sheetname="Italian", skiprows=[1]) # empty first row
metadata_en = pd.read_excel("./data/COH_GAR_metadata.xlsx",sheetname="English")


# In[4]:

metadata_it.head()


# In[5]:

metadata_en.head()


# In[6]:

merged = pd.concat([metadata_it,metadata_en], axis=1) 
merged.head()


# # Keyword mappings
# 
# Manual mappings of places, people and keywords for categories. They are published as wikitables and can be found here:
# 
# https://commons.wikimedia.org/w/index.php?title=Special%3APrefixIndex&prefix=Gruppo+Archeologico+Romano%2FBatch+upload%2F&namespace=4

# ## Places (Luogo)
# 
# We have two different mappings of places, one general based on the column "Place (Luogo)" in the original metadata file and one more specific which is a combination of the columns "Place (Luogo)" and "Subject (Nome monumento)". 
# 
# The mapping can be found here:
# 
# https://commons.wikimedia.org/wiki/Commons:Gruppo_Archeologico_Romano/Batch_upload/places

# In[7]:

place_mappings_url = "https://commons.wikimedia.org/wiki/Commons:Gruppo_Archeologico_Romano/Batch_upload/places"
place_mappings = pd.read_html(place_mappings_url, attrs = {"class":"wikitable"}, header=0)
# print(len(place_mappings))
place_mappings_general = place_mappings[0]
place_mappings_general = place_mappings_general.set_index("Luogo")
place_mappings_specific = place_mappings[1]
place_mappings_specific["Specific place"] = place_mappings_specific.Luogo + " " + place_mappings_specific["Nome monumento"]
place_mappings_specific = place_mappings_specific[["Specific place" ,"Luogo","Nome monumento","category","wikidata"]]
place_mappings_specific = place_mappings_specific.set_index("Specific place")


# In[8]:

print(place_mappings_general.head(10))


# In[9]:

print(place_mappings_specific.head(10))


# # Population of {{Photograph}}
# 
# ## Template mapping

# In[16]:

desc = "Rovine del tempio di Giove all'ingresso del"
text = Text(desc)


# In[22]:

lang = text.language


# In[23]:

lang.code

 |photographer       = <en-Author[4:]>
 |title              =  
{{it|’’’<Nome foto[:-3]>’’’}}
{{en|<Title[:-3]>}}
 |description        =
{{en|<Description> OR <Subject>, <Place> in <year>}}
{{it|<Descrizione> OR <Nome monumento>, <Luogo>, <Anno>}} 
 |depicted people    = 
 |depicted place     =  {{city|<wikidata from Specific Place mapping> OR <wikidata from Luogo (place) mapping>}} OR <Subject, Place>
 |date               = <Year>
 |medium             = 
 |dimensions         =
 |institution        = {{Institution:Gruppo Archeologico Romano}}
 |department         =
 |references         =
 |object history     =
 |exhibition history =
 |credit line        =
 |inscriptions       =
 |notes              =
 |accession number   =
 |source             = {{Gruppo Archeologico Romano cooperation project|COH}}
 |permission         = {{CC-BY-SA-4.0|<en-Author[4:]> / ”GAR”}}
{{PermissionOTRS|id=2016042410005958}}
 |other_versions     =
}}
# ## Code
# Available as .py script on [my github](https://github.com/mattiasostmar/GAR_Syria_2016-06/blob/master/create_metatdata_textfiles.py)

# In[24]:

get_ipython().system('rm -rf ./photograph_template_texts/*')
total_images = 0
OK_images = 0
uncategorized_images = 0
faulty_images = 0

for row_no, row in merged.iterrows():
    total_images += 1
    
    template_parts = []
    
    header = "{{Photograph"
    template_parts.append(header)
    
    if not pd.isnull(row["Author"]):
        photographer = "|photographer = " + row["Author"][4:]
    else:
        print("Warning! Empty Author column in row no {} photo {}".format(row_no, row["Nome foto"]))
        photographer = "|photographer = "
        faulty_images += 1
    template_parts.append(photographer)
    
    title_it =  "{{it|'''" + regex.sub("_"," ",row["Nome foto"][:-3]) + "'''}}"
    title_en = "{{en|'''" + regex.sub("_"," ", row["Title"][:-3]) + "'''}}"
    title = "|title = " + title_it + title_en
    template_parts.append(title)
    
    if pd.notnull(row["Description"]):
        text = Text(row["Description"])
        lang = text.language
        
        if lang.code != "en":
            print("name {} text {} lang code {} - expected 'en'".format(row["Title"], text, lang.code))
        else:
            if len(row["Description"].split()) >= 3:
                description_en = "{{en| = " + row["Description"] + "}}"
            else:
                description_en = "{{en| = " + str(row["Subject"]) + " " + str(row["Place"]) + " in " + str(row["Year"]) + "}}"
    else:
        if lang.code != "en":
            print("name {} text {} lang code {} - expected 'en'".format(row["Title"], text, lang.code))
        else:    
            description_en = "{{en| = " + str(row["Subject"]) + " " + str(row["Place"]) + " in " + str(row["Year"]) + "}}"
    
    if pd.notnull(row["Descrizione"]):
        if len(row["Descrizione"].split()) >= 3:
            description_it = "{{it| = " + row["Descrizione"] + "}}"
        else:
            description_it = "{{it| = " + str(row["Nome monumento"]) + " " + str(row["Luogo"]) + " " + str(row["Anno"]) + "}}"
    else:
        description_it = "{{it| = " + str(row["Nome monumento"]) + " " + str(row["Luogo"]) + " " + str(row["Anno"]) + "}}"
    
    description = "|description = " + description_it + description_en
    template_parts.append(description)
    
    depicted_people = "|depicted people ="
    template_parts.append(depicted_people)
    
    if pd.notnull(place_mappings_specific.loc[row["Luogo"] + " " + row["Nome monumento"]]["wikidata"]):
        depicted_place = "|depicted place = {{city|" +         place_mappings_specific.loc[row["Luogo"] + " " + row["Nome monumento"]]["wikidata"] + "}}"
        #print(depicted_place)
    elif pd.notnull(place_mappings_general.loc[row["Luogo"]]["wikidata"]):
        depicted_place = "|depicted place = {{city|" +         place_mappings_general.loc[row["Luogo"]]["wikidata"] + "}}"
        #print(depicted_place)
    else:
        depicted_place = "|depicted place = " + row["Luogo"] + " " + row["Nome monumento"]
        #print(depicted_place)
    
    if pd.notnull(row["Year"]):
        date = "|date = " + str(row["Year"])
    else:
        date = "|date = "
    template_parts.append(date)
        
    medium = "|medium =" 
    template_parts.append(medium)
    
    dimensions = "|dimensions ="
    template_parts.append(dimensions)
    
    institution = "|institution = {{Institution:Gruppo Archeologico Romano}}"
    template_parts.append(institution)
    
    department = "|department ="
    template_parts.append(department)
    
    references = "|references ="
    template_parts.append(references)
    
    object_history = "|object history ="
    template_parts.append(object_history)
    
    exhibition_history = "|exhibition history ="
    template_parts.append(exhibition_history)
    
    credit_line = "|credit line ="
    template_parts.append(credit_line)
    
    inscriptions = "|inscriptions ="
    template_parts.append(inscriptions)
    
    notes = "|notes ="
    template_parts.append(notes)
    
    accession_number = "|accession number ="
    template_parts.append(accession_number)
    
    source = "|source = {{Gruppo Archeologico Romano cooperation project|COH}}"
    template_parts.append(source)
    
    if pd.notnull(row["Author"]):
        permission = "|permission = {{CC-BY-SA-4.0|" + row["Author"][4:] + "|GAR}}{{PermissionOTRS|id=2016042410005958}}"
    else:
        permission = "|permission = {{CC-BY-SA-4.0|Gruppo Archeologico Romano}}{{PermissionOTRS|id=2016042410005958}}"
    template_parts.append(permission)
    
    other_versions = "|other_versions ="
    template_parts.append(other_versions)
    
    template_parts.append("}}")
    
    
    categories_list = []
    # [[Category:<Category from Specific Place> AND/OR <Category from Luogo (place)>]] 
    specific_place_category = None
    general_place_category = None
    maintanence_category = None
    batchupload_category = "[[Category:Images_from_GAR_2016-06]]"
    
    if pd.notnull(place_mappings_specific.loc[row["Luogo"] + " " + row["Nome monumento"]]["category"]):
        specific_place_category = "[[" + place_mappings_specific.loc[row["Luogo"] + " " + row["Nome monumento"]]["category"] + "]]"
        #print(specific_place_category)
    
    elif pd.notnull(place_mappings_general.loc[row["Luogo"]]["category"]):
        general_place_category = "[[" + place_mappings_general.loc[row["Luogo"]]["category"] + "]]"
        #print(general_place_category)
    
    # [[Category:Images_from_GAR_Syria_2016-06]]
    else:
        maintanence_category = "[[Category:Images_from_GAR_without_categories]]"
        uncategorized_images += 1
    
    # manage content categories
    if specific_place_category:
        categories_list.append(specific_place_category)
        OK_images += 1
    elif general_place_category and not specific_place_category:
        categories_list.append(general_place_category)
        OK_images += 1 
    else:
        categories_list.append(maintanence_category)

    categories_list.append(batchupload_category)

    #print(categories_list)
    
    # Filename: <Nome foto[:-3]>_GAR_<Nome foto[-3:]>.<ext>
    outpath = "./photograph_template_texts/"
    fname = row["Nome foto"][:-3] + " - " + "GAR" + " - " + row["Nome foto"][-3:] + ".JPG" # Hack, extension ought to be dynamic
    if not os.path.exists(outpath):
        os.mkdir(outpath)
        outfile = open(outpath + fname, "w")
        outfile.write("\n".join(template_parts) + "\n" + "\n".join(categories_list))
    else:
        outfile = open(outpath + fname, "w")
        outfile.write("\n".join(template_parts) + "\n" + "\n".join(categories_list))
    
print("Stats: \nTotal images {}\nOK images {}\nUncategorized images {}\nImages missing author {}".format(total_images, OK_images - faulty_images, uncategorized_images, faulty_images ))


# In[21]:

get_ipython().system('ls -la ./photograph_template_texts/ | head -n10')


# ## Tests

# In[ ]:

depicted_place = "|depicted place = {{city|" + place_mappings_specific.loc[row["Luogo"]]["wikidata"] + "}}"


# In[15]:

place_mappings_specific


# In[ ]:



