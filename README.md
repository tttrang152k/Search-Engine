# Million Searches per Second (name not related to MIPS i swear)
## Installation Instructions
1. Install MySQL server >= 8.0 or MariaDB server >= 10.0
2. Install dependencies from requirements.txt
3. Import search_engine.sql
4. Execute the following SQL statement
> CREATE USER 'search'@'localhost' IDENTIFIED BY '';
> GRANT ALL PRIVILEGES ON search_engine.* to 'search'@'localhost' IDENTIFIED BY '';
1. Open indexer.py, and in line 64, where it is written DocPath = "DEV",
   replace "DEV" with a directory of your choosing.
3. Run indexer.py and wait for completion
4. Run search.py (console) or webserver.py (graphical)

## Preview

![Search Home](https://i.imgur.com/9h6JcSY.png)
![Search Suggestions](https://i.imgur.com/LzPHi3o.png)
![Search Results](https://i.imgur.com/064sDhk.png)
