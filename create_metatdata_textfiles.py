
# coding: utf-8

# In[ ]:

get_ipython().system('pip install regex # A sligthly better version of RE')
get_ipython().system('pip install html5lib # For Pandas read_html used to parse mapping wikitables ')
get_ipython().system('pip install pandas # A great library for data wrangling (and analysis) ')


# In[1]:

import pandas as pd 
import numpy as np
import regex
import os 


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

# In[2]:

def strip(text):
    try:
        return text.strip()
    except AttributeError:
        return text
    
it_converters = {"Nome_foto":strip, "Anno":strip, "Luogo":strip, "Nome_monumento":strip, "Descrizione":strip, "Nome_autore":strip}
metadata_it = pd.read_excel("./data/COH_GAR_metadata.xlsx",sheetname="Italian", skiprows=[1], converters=it_converters) # empty first row

en_converters = {"Title":strip, "Year":strip, "Place": strip, "Subject":strip, "Description":strip, "Author":strip, "Commons_category":strip}
metadata_en = pd.read_excel("./data/COH_GAR_metadata.xlsx",sheetname="English", converters=en_converters)


# In[3]:

metadata_it.head()


# In[77]:

metadata_en.head()


# In[4]:

merged = pd.concat([metadata_it,metadata_en], axis=1) 
merged.head()


# In[5]:

pd.isnull(merged.Description)


# # Keyword mappings
# 
# Manual mappings of places, people and keywords for categories. They are published as wikitables and can be found here:
# 
# https://commons.wikimedia.org/w/index.php?title=Special%3APrefixIndex&prefix=Gruppo+Archeologico+Romano%2FBatch+upload%2F&namespace=4

# ## Places (Luogo)
# 
# We have two different mappings of places, one general based on the column "Place (Luogo)" in the original metadata file and one more specific which is a combination of the columns "Place (Luogo)" and "Subject (Nome_monumento)". 
# 
# The mapping can be found here:
# 
# https://commons.wikimedia.org/wiki/Commons:Gruppo_Archeologico_Romano/Batch_upload/places

# In[6]:

place_mappings_url = "https://commons.wikimedia.org/wiki/Commons:Gruppo_Archeologico_Romano/Batch_upload/places"
place_mappings = pd.read_html(place_mappings_url, attrs = {"class":"wikitable"}, header=0)
# print(len(place_mappings))
place_mappings_general = place_mappings[0]
# Strip away potential surrounding whitespace
place_mappings_general["Luogo"] = place_mappings_general.Luogo.str.strip() 
place_mappings_general["wikidata"] = place_mappings_general.wikidata.str.strip()
#place_mappings_general["wikidata"] = place_mappings_general.wikidata.str.replace("\-", "")
place_mappings_general["category"] = place_mappings_general.category.str.strip() 
#place_mappings_general["category"] = place_mappings_general.category.str.replace("\-", "") 

place_mappings_general = place_mappings_general.set_index("Luogo")

place_mappings_specific = place_mappings[1]
# Strip away potential surrounding whitespace
place_mappings_specific["Luogo"] = place_mappings_specific.Luogo.str.strip()
place_mappings_specific["Nome_monumento"] = place_mappings_specific.Nome_monumento.str.strip()

place_mappings_specific["category"] = place_mappings_specific.category.str.strip()
#place_mappings_specific["category"] = place_mappings_specific.category.str.replace("\-", "")
place_mappings_specific["wikidata"] = place_mappings_specific.wikidata.str.strip()
#place_mappings_specific["wikidata"] = place_mappings_specific.wikidata.str.replace("\-", "")

place_mappings_specific["Specific_place"] = place_mappings_specific.Luogo + " " + place_mappings_specific.Nome_monumento
place_mappings_specific = place_mappings_specific[["Specific_place" ,"Luogo","Nome_monumento","category","wikidata"]]
place_mappings_specific = place_mappings_specific.set_index("Specific_place")


# Check that all '-' are replaced with empty strings

# In[7]:

print(place_mappings_specific["wikidata"].head(10))


# In[8]:

place_mappings_specific["wikidata"].head(10)


# In[9]:

place_mappings_specific.loc["Serjilla Andron"]["wikidata"]


# In[10]:

pd.isnull(place_mappings_specific.loc["Serjilla Andron"]["wikidata"])


# In[11]:

place_mappings_specific.loc["Serjilla Andron"]["wikidata"] == "-"


# In[14]:

pd.isnull(place_mappings_specific.wikidata)


# In[12]:

place_mappings_general.head(3)


# In[13]:

place_mappings_specific.head(3)


# In[131]:

spec = pd.Series(list(place_mappings_specific.index))
spec[spec.str.contains("Jable")]


# # Population of the Photograph template
# 
# ## Template mapping

#  The master template mapping lives as [a task on Phabricator](https://phabricator.wikimedia.org/T139724)

# ## Collect original filenames

# In[45]:

sub_dirs = []
original_filenames = []

root_dir = "/Users/mos/GAR pictures for WMSE/"
for root, dirs, files in os.walk("/Users/mos/GAR pictures for WMSE/"):
    sub_dirs.extend(dirs)
for dir in sub_dirs:
    for root, dirs, files in os.walk(root_dir + dir):
        for file in files:
            if file.endswith(".JPG") or file.endswith(".jpg"):
                original_filenames.append(file)
print("Subdirs: {}\nlen(original_filenames): {}\nFiles in metadata file: 426".format(len(sub_dirs), len(original_filenames)))


# ## Create wikitext for image pages
# Available as .py script on [my github](https://github.com/mattiasostmar/GAR_Syria_2016-06/blob/master/create_metatdata_textfiles.py)

# In[34]:

# remove possible diuplicate files with other extension names
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
        print("Warning! Empty Author column in row no {} photo {}".format(row_no, row["Nome_foto"]))
        photographer = "|photographer = "
        faulty_images += 1
    template_parts.append(photographer)
    
    title_it =  "{{it|'''" + regex.sub("_"," ",row["Nome_foto"][:-3]) + "'''}}"
    
    title = "|title = " + title_it
    template_parts.append(title)
    
    if pd.notnull(row["Description"]):
        description_en = "{{en| " + row["Description"] + "}}"
    else:
        description_en = "{{en| " + str(row["Subject"]) + ", " + str(row["Place"]) + " in " + str(row["Year"]) + "}}"
    
    if pd.notnull(row["Descrizione"]):
        description_it = "{{it| " + row["Descrizione"] + "}}"
    else:
        description_it = "{{it| " + str(row["Nome_monumento"]) + ", " + str(row["Luogo"]) + ", " + str(row["Anno"]) + "}}"
    
    description = "|description = " + description_it + "\n" + description_en
    template_parts.append(description)
    
    depicted_people = "|depicted people ="
    template_parts.append(depicted_people)
    # Workoaround that we don't have actual specific places in mapping table
    spec_place = row["Luogo"] + " " + row["Nome_monumento"]
    
    if not place_mappings_specific.loc[spec_place]["wikidata"] == "-" and pd.notnull(place_mappings_specific.loc[spec_place]["wikidata"]): 
        depicted_place = "|depicted place = {{city|" +         place_mappings_specific.loc[spec_place]["wikidata"] + "}}"
        #print(depicted_place)
    elif not place_mappings_general.loc[row["Luogo"]]["wikidata"] == "-" or pd.isnull(place_mappings_general.loc[row["Luogo"]]["wikidata"]):
        depicted_place = "|depicted place = {{city|" +         place_mappings_general.loc[row["Luogo"]]["wikidata"] + "}}"
        #print(depicted_place)
    else:
        depicted_place = "|depicted place = " + row["Luogo"] + " " + row["Nome_monumento"]
        #print(depicted_place)
    template_parts.append(depicted_place)
    
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
    
    source = "|source = " + row["Nome_foto"] + "\n{{Gruppo Archeologico Romano cooperation project|COH}}"
    template_parts.append(source)
    
    if pd.notnull(row["Author"]):
        permission = "|permission = {{CC-BY-SA-4.0|" + row["Author"][4:] + " / GAR}}\n{{PermissionOTRS|id=2016042410005958}}"
    else:
        permission = "|permission = {{CC-BY-SA-4.0|Gruppo Archeologico Romano}}\n{{PermissionOTRS|id=2016042410005958}}"
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
    translation_needed_category = "[[Category:Images_from_GAR_Syria_needing_english_translation]]"
    
    if place_mappings_specific.loc[spec_place]["category"] != "-" and pd.notnull(place_mappings_specific.loc[spec_place]["category"]): 
        
        specific_place_category = "[[" + place_mappings_specific.loc[spec_place]["category"] + "]]"
        print("{} {}".format(row["Title"], specific_place_category)) 
     
    elif place_mappings_general.loc[row["Luogo"]]["category"] != "-" and pd.notnull(place_mappings_general.loc[row["Luogo"]]["category"]):
        general_place_category = "[[" + place_mappings_general.loc[row["Luogo"]]["category"] + "]]"
        #print(general_place_category)
    
    # [[Category:Images_from_GAR_Syria_2016-06]]
    else:
        maintanence_category = "[[Category:Images_from_GAR_without_categories]]"
        uncategorized_images += 1
    
    # manage content categories
    if specific_place_category :
        categories_list.append(specific_place_category)
        OK_images += 1
    elif general_place_category and not specific_place_category:
        categories_list.append(general_place_category)
        OK_images += 1 
    else:
        categories_list.append(maintanence_category)

    categories_list.append(batchupload_category)
    categories_list.append(translation_needed_category)
        
    #print(categories_list)
    
    # Filename: <Nome_foto[:-3]>_GAR_<Nome_foto[-3:]>.<ext>
    outpath = "./photograph_template_texts/"
    fname = row["Nome_foto"][:-3] + " - " + "GAR" + " - " + row["Nome_foto"][-3:] # + ".JPG" Hack, extension ought to be dynamic
    
    
    if not os.path.exists(outpath):
        os.mkdir(outpath)
        outfile = open(outpath + fname, "w")
        outfile.write("\n".join(template_parts) + "\n" + "\n".join(categories_list))
    else:
        outfile = open(outpath + fname, "w")
        outfile.write("\n".join(template_parts) + "\n" + "\n".join(categories_list))
    
print("Stats: \nTotal images {}\nOK images {}\nUncategorized images {}\nImages missing author {}".format(total_images, OK_images - faulty_images, uncategorized_images, faulty_images ))


# In[142]:

for row_no, row in merged.iterrows():
    print(pd.notnull(place_mappings_specific.loc[row["Luogo"] + " " + row["Nome_monumento"]]["category"]))


# In[21]:

get_ipython().system('ls -la ./photograph_template_texts/ | head -n10')


# ## Tests

# In[ ]:

depicted_place = "|depicted place = {{city|" + place_mappings_specific.loc[row["Luogo"]]["wikidata"] + "}}"


# In[15]:

place_mappings_specific


# In[ ]:



