import json
import re
from collections import defaultdict
import os
import sys



# Call this on a singular index to split it into alphabetical/miscellaneous files
def splitFile(f1: str) -> None:
    # Create the split_indexes folder if not exists
    if not os.path.exists('split_indexes'):
        os.makedirs('split_indexes')
    # Remove all contents in the split_indexes folder for each fresh run
    for f in os.listdir('split_indexes'):
        os.remove(os.path.join('split_indexes', f))
    d = defaultdict(lambda: dict())
    alpha = re.compile("[A-Za-z]")
    with open(os.path.join("indexes",f1)) as f:
        data = json.load(f)
    for k,v in data.items():
        #print(k, v)
        if alpha.search(k[0]):
            d[k[0].lower()].update({k: v})
        else:
            d["misc"].update({k: v})
    for k,v in d.items():
        #print(k)
        with open(os.path.join("split_indexes",k + ".json"), "w") as f:
            json.dump(v, f)

# Splits inverted index into 1MB chunks
def splitFileV2(f1 :str) -> None:
    # Create the split_indexes folder if not exists
    if not os.path.exists('split_indexes'):
        os.makedirs('split_indexes')
    # Remove all contents in the split_indexes folder for each fresh run
    for f in os.listdir('split_indexes'):
        os.remove(os.path.join('split_indexes', f))
    d = defaultdict(lambda: dict())
    # Index for split index file
    index = 0
    # beginning term of the index
    begin = None
    # end term of the index
    end = None
    splitmap = dict()
    with open(os.path.join("indexes",f1)) as f:
        data = json.load(f)
    for k,v in sorted(data.items()):
        if begin == None:
            begin = k
        end = k
        d[0].update({k: v})
        #print(sys.getsizeof(d[0]))
        if get_size(d) >= 5000000:
            with open(os.path.join("split_indexes",str(index) + ".json"), "w") as f:
                json.dump(d[0], f)
            splitmap[str(index)] = {"begin": begin, "end": end}
            begin = None
            end = None
            index += 1
            d.clear()
    if get_size(d) != 0:
        with open(os.path.join("split_indexes",str(index) + ".json"), "w") as f:
            json.dump(d[0], f)
    with open("splitmap.json", "w") as f:
        json.dump(splitmap,f)

# Obtained from https://stackoverflow.com/questions/45393694/size-of-a-dictionary-in-bytes
# Used with splitFileV2 function
def get_size(obj, seen=None):
    """Recursively finds size of objects"""
    size = sys.getsizeof(obj)
    if seen is None:
        seen = set()
    obj_id = id(obj)
    if obj_id in seen:
        return 0
    # Important mark as seen *before* entering recursion to gracefully handle
    # self-referential objects
    seen.add(obj_id)
    if isinstance(obj, dict):
        size += sum([get_size(v, seen) for v in obj.values()])
        size += sum([get_size(k, seen) for k in obj.keys()])
    elif hasattr(obj, '__dict__'):
        size += get_size(obj.__dict__, seen)
    elif hasattr(obj, '__iter__') and not isinstance(obj, (str, bytes, bytearray)):
        size += sum([get_size(i, seen) for i in obj])
    return size
