This program uses Googles GData library to query a Google Spreadsheet for data.
This requires an application-specific password that I replaced with the
string 'password-goes-here' for this publicly-checked-in code.  Obviously this 
won't work so I saved a raw copy of the data from GData into ML.raw.  This is 
exactly what comes back from GData.

The point of this program was to use Logistic Regression to determine the rela-
tionship between my motorcycle's miles-per-gallon and two variables, days-between-
tank-fills and gallons filled.  These two variables ended up getting me 0.81 in 
Mean AUC.

Usage:
python hw3c.py

