#!/usr/bin/python -tt

import sys
import numpy as np
from sklearn import linear_model, cross_validation
import os
import urllib
import re
import csv

####################### FUNCTIONS START #######################
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
    sections = re.compile('<td class=xl[0-9]{7}></td>\n+\s*').split(tmpData)
    for section in sections:
        if (re.compile('^</tr>')/match(section)):
            # You are in the data section so clip off the part below the table
            (cleanHTMLData, trash) = re.compile('\s*<\!\[if supportMisalignedColumns\]>').split(section,2)

    return cleanHTMLData


def buildDataStructure(cleanHTMLData):
    lines = re.compile('\n').split(cleanHTMLData)
    currentRunner = 1   # Keep track of the runner I'm importing although I'll be pulling this from
                        # the data as the Place field
    fieldCount = 0  # which field am I processing? 
    dataStructure = {}
    name, age, gender, state, fieldCount, meanPace = None
    elapsedSplits = []
    deltaSplits = []
    totalDistance = 100.9   # Total race miles

    # This whole thing works because the data is consistently ordered, at least.
    for line in lines:
        # Does this line have useful data?
        p = re.compile('\s*<td (height=[0-9.]{1,3} )*class=xl[0-9]{7}.*>(.+)</td>').match(line)
        if p:
            if fieldCount == 0:         # if this is the Place field #0
                name = 'R'+str(p.group(2))
            elif fieldCount == 3:       # if this is the Age field #3
                age = p.group(2)
            elif fieldCount == 4:       # if this is the Gender field #4
                gender = p.group(2)
            elif fieldCount == 6:       # if this is the State field #6
                state = p.group(2)
            elif fieldCount in (8,9,10,11,12,13):       # these are the mileage time splits
                elapsedSplits.append(p.group(2))
                if len(elapsedSplits) > 1:
                    deltaSplits.append(timeToInt(p.group(2)))
                else:
                deltaSplits.append(timeToInt(elapsedSplits[len(elapsedSplits)-1])-timeToInt(elapsedSplits[len(elapsedSplits)-2]))
            elif fieldCount == 14:
                finishTime = timeToInt(p.group(2))
                # Calculate the mean pace
                meanPace = finishTime/totalDistance
                # Stick everything into the data structure
                dataStructure[name] = { 'age':age, 'gender':gender, 'state':state, 'elapsedSplits':elapsedSplits, \
                                        'deltaSplits':deltaSplits, 'finishTime':finishTime, 'meanPace':meanPace }
                # Now reset some vars
                name, age, gender, state, fieldCount = None
                elapsedSplits = []
                deltaSplits = []
            # Done processing this field so increment fieldCount
            fieldCount += 1

    return dataStructure
            

def timeToInt(timeVal):
    seconds = None
    # Convert an hour:minute:second time to seconds
    timeParts = re.compile('([0-9]{1,2}):([0-9]{2}):([0-9]{2})').match(timeVal)
    seconds = int(timeParts.group(1))*3600+int(timeParts.group(2))*60+int(timeParts.group(3))

    return seconds


def extraceDataSet(dataStructure, conditions):
    extractedArray = []   # This holds whatever we are returning
    conditionKeys = conditions.keys()  # to see what is being asked for
    addMeFlag = True    # Default is to add this record unless changed to False
    
    for key in dataStructure.keys():
        # extract place from key
        place = pe.compile('R([0-9]+)').match(key)
        if (not('R_start' in conditionsKeys and conditions('R_start')>=place)):
            addMeFlag = False
        elif (not ('R_end' in conditionKeys and conditions('R_end') <= place)):
            addMeFlag = False

        # Keep repeating for supported conditions
        # If we made it through conditions check and flag is still True, then add it
        if addMeFlag:
            extractedArray.append(dataStructure[key][conditions['return'])

    return extractedArray

####################### FUNCTIONS END #########################

# Define Variables
sourceURL = 'http://aravaiparunning.com/results/2012JJSplits.htm'
fileURL = '../../data/hw2/2012JJResults100m.html'
dir_out = '../../data/hw2/'
urlData = None  # Default, to check if anything was read in later
dataStructure = None   # ditto

# Get the HTML data
#urlData = scrapeURL(sourceURL)   # This works but sometimes I'm working offline so I use this
urlData = readURLFile(fileURL)

if urlData == None:
    print "Trouble parsing URL data!"
    sys.exit(1)

# Build the data structure
dataStructure = buildDataStructure(urlData)

if dataStructure == None:
    print "Trouble building data structure!"
    sys.exit(1)

# Test the whole field on separate split times, not elapsed times
conditions = { 'return':'deltaSplits' } # return array of runners with array of this value

# Test the top-half of the field on deviation from their cum avg pace.
conditions = { 'return':'deltaPaceSplit',
               'R_start': 1,
               'R_end': len(dataStructure)/2   # datastructure.keys()!
             }

# Test Men 35-45 on something
conditions = { 'return' : 'deltaSplits',
               'gender' : 'Male',
               'age_start':35,
               'age_end':45
             }
