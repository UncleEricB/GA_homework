#!/usr/bin/python -tt

import sys
import numpy as np
from sklearn import linear_model, cross_validation
import os
import urllib
import re
import csv
import sqlite3 as lite

####################### FUNCTIONS START #######################
def dbConnect():
    con = None
    try:
        con = lite.connect('JJsplits.db.sqlite')
    except lite.Error as e:
        print "DB Connect error %s: " % e.args[0]
        sys.exit(1)

    return con


def scrapeURL(url):
    cleanedData = None
    # Grab the raw data from the URL
    rawURLData  = urllib.urlopen(url).read()
    # Clip off the top part
    sections = re.compile('<td class=xl[0-9]{7}></td>\n+\s*').split(rawURLData)
    for section in sections:
        if (re.compile('^</tr>').match(section)):
        # If you are in the data section, then clip off the non-data bottom part
            (cleanedData, trash) = re.compile('\s*<\!\[if supportMisalignedColumns\]>').split(section,2)

    return cleanedData


def readURLFile(fileName):
    htmlTableData = None
    try:
        fileHandle = open(fileName,'r')
    except:
        print "Can't open "+str(fileName)
        sys.exit(1)
    tmpData = fileHandle.read()
    # Split off the HTML before the table
    sections = re.compile('\s*<td class=xl[0-9]{7}>Finish Time</td>\s*\n').split(tmpData)
    for section in sections:
        if (re.compile('^\s*</tr>').match(section)):
            # You are in the data section so clip off the part below the table
            (cleanHTMLData, trash) = re.compile('\s*<\!\[if supportMisalignedColumns\]>').split(section,2)

    return cleanHTMLData


def populateDatabase(dbConn,cleanHTMLData):
    lines = re.compile('\n').split(cleanHTMLData)
    fieldCount = 0  # which field am I processing? 
    dataStructure = {}
    elapsedSplits = []
    deltaSplits = []
    totalDistance = 100.9   # Total race miles
    cursor = dbConn.cursor()

    # This whole thing works because the data is consistently ordered, at least.
    for line in lines:
        # Does this line have useful data?
        p = re.compile('\s*<td (height=[0-9.]{1,3} )*class=xl[0-9]{7}.*>(.+)</td>').match(line)
        if p:
            if fieldCount == 0:         # if this is the Place field #0
                name = 'R'+str(p.group(2))
                place = p.group(2)
            elif fieldCount == 3:       # if this is the Age field #3
                age = p.group(2)
            elif fieldCount == 4:       # if this is the Gender field #4
                gender = p.group(2)
            elif fieldCount == 6:       # if this is the State field #6
                state = p.group(2)
            elif fieldCount in (8,9,10,11,12,13):       # these are the mileage time splits
                if p.group(2) == '-':
                    elapsedSplits.append(0)
                else:
                    elapsedSplits.append(timeToInt(p.group(2)))



                # If no elapsedSplits yet, then append directly to deltaSplits
                if len(elapsedSplits) <= 1:
                    deltaSplits.append(timeToInt(p.group(2)))
                else:
                    if p.group(2) == '-':
                        deltaSplits.append(0)
                    else:
                    # Else subtract previous elapsedSplits from current
                        deltaSplits.append(elapsedSplits[len(elapsedSplits)-1]-elapsedSplits[len(elapsedSplits)-2])

            elif fieldCount == 14:
                if p.group(2) == '-':
                    finishTime = 0
                else:
                    finishTime = timeToInt(p.group(2))
                # Calculate the mean pace
                meanPace = finishTime/totalDistance
                # Stick everything into the database
                try:
                    whereAmI = "INSERT INTO Runner"
                    cursor.execute("INSERT INTO Runner VALUES('%s','%s','%s','%s','%s','%s','%s')" % (name, place, age, gender, state, finishTime, int(meanPace)))
                    dbConn.commit()
                    whereAmI = "INSERT INTO Elapsed_Splits"
                    cursor.execute("INSERT INTO Elapsed_Splits VALUES('"+name+"', '"+str(elapsedSplits[0])+"', '"+ str(elapsedSplits[1])+"', '"+str(elapsedSplits[2])+"', '"+ str(elapsedSplits[3])+"', '"+str(elapsedSplits[4])+"', '"+str(elapsedSplits[5])+"')")
                    dbConn.commit()
                    whereAmI = "INSERT INTO Delta_Splits"
                    cursor.execute("INSERT INTO Delta_Splits VALUES('"+name+"','"+str(deltaSplits[0])+"', '"+str(deltaSplits[1])+"', '"+str(deltaSplits[2])+"', '"+str(deltaSplits[3])+"', '"+str(deltaSplits[4])+"', '"+str(deltaSplits[5])+"')")
                    dbConn.commit()
                #except lite.Error as e:
                except Exception as e:
                    #print "DB INSERT error %s: " % e.args[0]
                    print "DB INSERT error: "+str(e)+" at "+whereAmI
                    sys.exit(1)

                # Now reset some vars
                name=None
                age=None 
                gender=None
                state=None
                fieldCount = -1  # I'm about to increment fieldCount for every pass through 
                elapsedSplits = []
                deltaSplits = []
            # Done processing this field so increment fieldCount
            fieldCount += 1

    return 
            

def timeToInt(timeVal):
    seconds = None
    # Convert an hour:minute:second time to seconds
    timeParts = re.compile('^([0-9]{1,2}):([0-9]{2}):([0-9]{2})').match(timeVal)
    try:
        seconds = int(timeParts.group(1))*3600+int(timeParts.group(2))*60+int(timeParts.group(3))
    except Exception as error:
        print "timeToInt error: "+str(error)
        print "\ttimeVal: "+str(timeVal)
        print "\ttimePart[1]: "+str(timeParts.group(1))

    return seconds


def executeQuery(dbConn, query):
    resultSet = None
    arrArrRS = []

    try:
        cursor = dbConn.cursor()
        cursor.execute(query)
        resultSet = cursor.fetchall()
    except Exception as error:
        print "DB SELECT problem! "+str(error)

    return resultSet


def regressThis(xResultSet, yResultSet, reportTitle):
    SEED = 13
    split = 0.3   # Used to divide Test from Train
    np.random.seed(SEED)
    indices = np.random.permutation(len(xResultSet))   # Mix up the indices for better training

    testTrainCutoff = int(len(xResultSet)*split)
    xTest = xResultSet[indices[0:testTrainCutoff]]
    xTrain = xResultSet[indices[testTrainCutoff:]]
    yTest = yResultSet[indices[0:testTrainCutoff]]
    yTrain = yResultSet[indices[testTrainCutoff:]]

    model = linear_model.LinearRegression()     # Create the LR model
    model.fit(xTrain,yTrain)                    # Train the model
    score = model.score(xTest,yTest)            # Test the model
    print reportTitle
    print "%s runners in this set. " % str(len(xResultSet))
    print "%s in Train set, %s in Test set." % (str(len(xTrain)), str(len(xTest)))
    print "Coefficients are: "+str(model.coef_)
    print "Intercept is: "+str(model.intercept_)
    print "Score via LR is: "+str(score)
    print "\n"

    #xTrain, xTest, yTrain yTest = cross_validation.train_test_split(xResultSet, yResultSet, test_size = 0.2, random_state=SEED)
    
####################### FUNCTIONS END #########################

# Define Variables
sourceURL = 'http://aravaiparunning.com/results/2012JJResults100m.html'
#fileURL = '../../data/hw2/2012JJResults100m.html'
fileURL = "2012JJResults100m.html"
dir_out = '../../data/hw2/'
urlData = None  # Default, to check if anything was read in later
resultSet = None
dbConn = None

# Connect to DB
dbConn = dbConnect()

# Get the HTML data
#urlData = scrapeURL(sourceURL)   # This works but sometimes I'm working offline so I use next line
urlData = readURLFile(fileURL)  # This works too but I have everything in sqlite now so save cycles
if urlData == None:
    print "Trouble parsing URL data!"
    sys.exit(1)

# Build the data structure
#NEXT LINE IS GOOD BUT COMMENTED OUT SO I DON'T HAVE TO RE-POPULATE DB EVERY TIME
populateDatabase(dbConn,urlData)

# Test the whole field on separate split times, not elapsed times
query ="SELECT e.s1, e.s2, e.s3, e.s4, e.s5, e.s6 " + \
       "FROM Elapsed_Splits as e, Runner as r " + \
       "WHERE e.Runner = r.Runner "+ \
       "AND r.FinishTime > 0 " + \
       "ORDER BY r.Place ASC"
xResultSet = np.asarray(executeQuery(dbConn,query))

query ="SELECT r.FinishTime " + \
       "FROM Runner as r " + \
       "WHERE r.FinishTime > 0 " + \
       "ORDER BY r.Place ASC"
yResultSet = np.asarray(executeQuery(dbConn, query))

regressThis(xResultSet, yResultSet,"Elapsed Splits for all Finishers")

# Test the top-half of the field on deviation from their cum avg pace.
query = "SELECT d.s1, d.s2, d.s3, d.s4, d.s5, d.s6 " + \
        "FROM Delta_Splits as d, Runner as r " + \
        "WHERE r.Place < 183 " + \
        "  AND r.Runner = d.Runner " + \
        "ORDER BY r.Place ASC"
xResultSet = np.asarray(executeQuery(dbConn, query))

query = "SELECT r.FinishTime "+ \
        "FROM Runner as r " + \
        "WHERE r.Place < 183 "+ \
        "ORDER BY r.Place ASC"
yResultSet = np.asarray(executeQuery(dbConn, query))

regressThis(xResultSet, yResultSet, "Delta Splits, Top Half of Field")


# Test delta - mean for men 35-45
query = "SELECT d.s1-(r.MeanPace*15.4) as dm1, d.s2-(r.MeanPace*15.4) as dm2, "+ \
        "d.s3-(r.MeanPace*15.4) as dm3, d.s4-(r.MeanPace*15.4) as dm4, "+ \
        "d.s5-(r.MeanPace*15.4) as dm5, d.s6-(r.MeanPace*15.4) as dm6 "+ \
        "FROM Delta_Splits as d, Runner as r " + \
        "WHERE r.Age >= 35 "+ \
        "  AND r.Age <= 45 "+ \
        "  AND r.Gender = 'Male' "+ \
        "  AND r.Runner = d.Runner "+ \
        "ORDER BY r.Place ASC"
xResultSet = np.asarray(executeQuery(dbConn, query))

query = "SELECT r.FInishTime "+ \
        "FROM Runner as r "+ \
        "WHERE r.Age >= 35 "+ \
        "  AND r.Age <= 45 "+ \
        "  AND r.Gender = 'Male' "+ \
        "ORDER BY r.Place ASC"
yResultSet = np.asarray(executeQuery(dbConn, query))
regressThis(xResultSet, yResultSet, "Delta-MeanPace, Men 35-45\nWas this lap over or under pace?")

# How does the first half affect the final time?
query = "SELECT d.s1, d.s2, d.s3 "+ \
        "FROM Delta_Splits as d, Runner as r "+ \
        "WHERE d.Runner = r.Runner "+ \
        "ORDER BY r.Place ASC"
xResultSet = np.asarray(executeQuery(dbConn, query))

query = "SELECT r.FinishTime "+ \
        "FROM Runner as r "+ \
        "ORDER by r.Place ASC"
yResultSet = np.asarray(executeQuery(dbConn, query))

regressThis(xResultSet, yResultSet, "First 3 laps, all finishers")

# How does the second half affect the final time?
query = "SELECT d.s4, d.s5, d.s6 "+ \
        "FROM Delta_Splits as d, Runner as r "+ \
        "WHERE d.Runner = r.Runner "+ \
        "ORDER BY r.Place ASC"
xResultSet = np.asarray(executeQuery(dbConn, query))

query = "SELECT r.FinishTime "+ \
        "FROM Runner as r "+ \
        "ORDER by r.Place ASC"
yResultSet = np.asarray(executeQuery(dbConn, query))

regressThis(xResultSet, yResultSet, "Second 3 laps, all finishers")
# Finalize
# Close database handle
dbConn.close()

