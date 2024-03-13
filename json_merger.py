import json
import os

# Call this function recursively until only one file is left in the indexes directory
def mergeFiles(f1: str, f2: str) -> None:
    # Open and load both files
    with open(os.path.join("indexes",f1)) as f:
        data1 = json.load(f)
    with open(os.path.join("indexes",f2)) as f:
        data2 = json.load(f)
    # Iterate through key-value pairs and add to the second dictionary
    for k,v in data1.items():
        # If not exists in dict #2, just add it
        if k not in data2:
            data2[k] = v
        else:
            # If exists, append locations but make sure not to duplicate
            for i in v["locations"]:
                if i not in data2[k]["locations"]:
                    data2[k]["locations"][i] = 0

                data2[k]["locations"][i] += data1[k]["locations"][i]
    # Save the data to file 1
    with open(os.path.join("indexes",f1), "w") as f:
        json.dump(data2, f)
    # Delete file 2
    os.remove(os.path.join("indexes",f2))
