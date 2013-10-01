Running splitsAsPredictors.py
---------------------------------

This program is currently set up to scrape a website, parse data out of a table and into a 
sqlite database and then run queries to generate specific datasets and calculate linear 
regressions on those datasets.

Actually, the website isn't responding tonight so I set the script up to read in a saved copy 
of the website and parse that out.

Usage:
clear; cp JJsplits.db.sqlite.empty JJsplits.db.sqlite; ./splitsAsPredictors.py

This clears out the previous database before every run because I have a field marked
as unique so running the script again on the same db would violate that.

The code is commented on wher you can turn off the web-scraping and database populating, 
once you have a valid sqlite db.

