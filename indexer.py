from os.path import splitext
from urllib.parse import urlparse, urldefrag
from nltk.tokenize import TweetTokenizer
from nltk.tokenize import word_tokenize
from nltk.stem.porter import *
from bs4 import BeautifulSoup
import nltk
import re
import os
import json
from json_merger import mergeFiles
from pprint import pprint
import importlib
import json_splitter

try:
    import mysql.connector
except:
    print("MySQL is not installed on this machine")


# BASE structure for inverted index (created as indexes file), can add more attributes:
# {
#   "word": {
#       "locations": {
#       doc_id: frequency
#       }
#   }
# }
# Can maybe add an "importance" value based on what document it is retrieved from
# Might want to break index into chunks so memory does not get depleted; merge all indexes together in the end


#Auxillary Structure for td-idf:
#{
#   "word": collection frequency 
# }

# Auxillary Structure for td-idf: terms for each document
# {
#   "doc": number of terms in document 
# 
# }



if __name__ == "__main__":
    try:
        sqlcheck = importlib.util.find_spec("mysql.connector")
    except:
        sqlcheck = False
    # Define MySQL connection credentials
    if sqlcheck:
        sql = mysql.connector.connect(
            host="localhost",
            user="search",
            password="",
            database="search_engine"
        )
        query = sql.cursor()
        query.execute("TRUNCATE TABLE terms")
        sql.commit()
    # Debug variable for debug output
    IS_DEBUG = True
    # Define path
    docPath = "DEV"
    # Initialize the index dictionary
    index = {} 
    # Maps doc ids to path
    pathMap = {}

    #Maps term to collection frequency 
    dfMap = {}
    #maps doc to number of terms the doc has --> changed to calculate the term vector vs document vector
    #tfMap = {} 

    # Maps doc ids to url ({doc_id --> url} must be unique)
    urlMap = {}
    
    # File "id"
    fid = 1
    # Index id for splitting
    iid = 1
    # How many files to traverse before splitting that index
    #10000
    splitter = 10000
    # Create the indexes folder if not exists
    if not os.path.exists('indexes'):
        os.makedirs('indexes')
    # Remove all contents in the indexes folder for each fresh run
    for f in os.listdir('indexes'):
        os.remove(os.path.join('indexes', f))

    # DEV/directory/files --> pages in files
    for root, dirs, files in os.walk(docPath):
        dirs.sort() #sort dirs so they are in the same order every time
        for page in files:
            
            with open(os.path.join(root, page), encoding = 'utf8') as json_file:
                data = json.load(json_file)
            extension = splitext(urlparse(data["url"]).path)[1] #gets the extension 
            if(extension != '.txt' and extension != '.php' and extension != '.bib'): #Note: Unclear whether the "parse html" part of the assignment means the content rather than the website type -Vik
                # get url in this page and clean the defragment
                parsed = urlparse(data["url"])
                clean_url = data["url"]
                if parsed.fragment != '':
                    clean_url = urldefrag(data["url"])[0]
                    #print(clean_url)
                if clean_url not in urlMap.values():
                    urlMap[fid] = clean_url
                else: 
                    continue
                    
                # create a pathMap for 
                pathMap[fid] = os.path.join(root, page)

                # add more weight to a doc based on terms when they appeared in title or headers
                # or in bold/strong sentences
                
                test_file_contents = data["content"]
                fcontent = BeautifulSoup(test_file_contents, 'lxml')
                raw_text = fcontent.get_text()
                title = fcontent.find("title")
                h1 = fcontent.find_all("h1")
                h2 = fcontent.find_all("h2")
                h3 = fcontent.find_all("h3")
                h4 = fcontent.find_all("h4")
                h5 = fcontent.find_all("h5")
                strong = fcontent.find_all("strong")
                bold = fcontent.find_all("bold")
                if title:
                    for item in title:
                        raw_text += (" " + item.text) * 5
                if h1:
                    for item in h1:
                        raw_text += (" " + item.text) * 3
                if h2:
                    for item in h2:
                        raw_text += (" " + item.text) * 2
                if h3:
                    for item in h3:
                        raw_text += " " + item.text
                if h4:
                    for item in h4:
                        raw_text += " " + item.text
                if h5:
                    for item in h5:
                        raw_text += " " + item.text
                if strong:
                    for item in strong:
                        raw_text += " " + item.text
                if bold:
                    for item in bold:
                        raw_text += " " + item.text
                if sqlcheck:
                    if title != None:
                        # This implementation minimizes the amount of SQL queries needed and space needed (checking for duplicates and selecting distinct values)
                        # Can also modify SQL server settings directly to ignore duplicate errors
                        try:
                            query.execute("INSERT INTO terms (content) VALUES (%s)", (str(title.string).encode("UTF-8"),))
                            sql.commit()
                        except:
                            pass
                ttokenizer = TweetTokenizer()
                tokens = ttokenizer.tokenize(raw_text)

                # Experimental Porter Stemmer
                ps = PorterStemmer()
                clean_tokens = [ps.stem(t) for t in tokens if t.isalnum() and t.isascii() and t != '']       # ignore non-English alphanumeric character
                clean_tokens.sort()

                #tfMap[fid] = len(clean_tokens)
                # Update the inverted index with the tokens
                for t in clean_tokens:
                    # Can probably use defaultdict to skip conditional checks?
                    if t in index:
                        # Sets are not allowed in JSON syntax so we use a list but check for duplicate elements
                        #Update: Changed  the structure to {word:{doc_id:freq}} 
                        if fid not in index[t]["locations"]:
                            index[t]["locations"][fid] = 1
                        else:
                            index[t]["locations"][fid] += 1
                    else:
                        
                        index[t] = {
                            "locations": {fid: 1}
                        }
                    
                        
                if IS_DEBUG:
                    pass
                    #    pprint(index)
                # Split so memory doesn't deplete fully
              
                if fid % splitter == 0:
                    if IS_DEBUG:
                        print("Splitting index", iid, "at fid", fid)
                    with open("indexes/index" + str(iid) + ".json", "w") as save_file:
                        
                        # must sort the indexes/terms before dumping into disk
                        
                        json.dump(index, save_file)
                    # Increment index id after dumping one index file
                    iid += 1
                    # Clearing the dictionary should certainly clear the memory, right? y
                    index.clear()
                # Increment file id after current file is done
                fid += 1
    if sqlcheck:
        sql.close()
    # The last batch might not reach (splitter #) files, so if the index is not empty, dump another file
    if len(index) != 0:
        #numWords += len(index)
        with open("indexes/index" + str(iid) + ".json", "w") as save_file:
            json.dump(index, save_file)


    #generate the collection map{
    # reminder: term -> number of documents that term appears in 
    for term in index.keys():
        total_term_freq = len(index[term]["locations"])
        dfMap[term] = total_term_freq
    dfMap["TOTAL_DOCS"] = fid-1 #probably a better way of doing this 
    
    #save the collection map
    with open("df_map.json","w") as f:
        json.dump(dfMap,f)
    #save the tf Map
    '''with open("tf_map.json","w") as f:
        json.dump(tfMap,f)'''
    # save the path map
    with open("pathmap.json", "w") as f:
        json.dump(pathMap, f)
    # save the url map
    with open("urlmap.json", "w") as urlf:
        json.dump(urlMap, urlf)
        
    # merge files
    if os.path.exists('indexes'):
        files = [f for f in os.listdir('indexes')]
    for i in range(1, iid):
        mergeFiles(files[0], files[i])
        
    # splitting all terms into separate files based on alphabetical order
    # making another dir called splitted_indexes which contains 
    # multiples index files A.json, B.json,... Z.json and misc in which term is not a word
    # will be put in misc.json
    with open(os.path.join("indexes","index1.json")) as f:    
        json_splitter.splitFile("index1.json")

    # writing report file
    '''# report 1 
    numDoc = fid
    with open("report.txt", "w") as outfile:
        outfile.write(f"Number of indexed documents:  {str(numDoc-1)}\n\n")
    
    # report 2
        with open(os.path.join("indexes","index1.json")) as f:    
            index = json.load(f)
            outfile.write(f"Number of unique words:  {str(len(index))}\n\n")
    # report 3
    # total size (in KB) of index on disk (add later)'''
