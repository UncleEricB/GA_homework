#!/usr/bin/python

#######################################
# Homework #1   Eric Blumenau
# ./hw1d.py -n <int, req'd> -k <int, opt> --verbose <opt>
# If k is given at command line, program only cross validates on that k
# else program cycles from 1-10, step 3 to cross validate on several k's
#######################################
import numpy as np
import math
import sys     # to see sys.argv[]
import getopt  # to parse sys.argv[]
from sklearn import datasets
from sklearn.neighbors import KNeighborsClassifier
from sklearn import cross_validation  # to use pre-built cross-validation

################# FUNCTIONS START ##########################
def printUsage():  
# Doesn't do much but can get called from several places to put in a function
    print './hw1d.py -n <int> -k <int, optional> --verbose (optional)' 

def processCommandLine(argv):
# processes command-line input, setting some defaults if no input is given
# or dying gracefully if required input isn't given

    k=0   # Default, if remains 0 then program will cycle through its own k's
    n = None  # Default, to catch if it isn't set
    VERBOSE = False  # Default is quiet mode

    try:
        opts, args = getopt.getopt(argv[1:],"n:k:",["verbose"])
    except:   # on error, die gracefully
        printUsage()
        sys.exit(1)

    for opt, arg in opts:
        if opt == "-n":
            n = int(arg)  # Cast it to int, just in case
        elif opt == "-k":
            k = int(arg)  # Cast it to int, just in case
        elif opt == "--verbose":
            VERBOSE = True  # spits out info for each validation iteration
        else:
            printUsage()  # if unsupported entry, die gracefully
            sys.exit(1)

    if n == None:    # if required field not present, die gracefully
        printUsage()
        sys.exit(1)

    return n, k, VERBOSE


def prepareData():
# Loads the iris dataset, separates out data and classes 
    iris = datasets.load_iris()
    iris_x = iris.data
    iris_y = iris.target

    return iris_x, iris_y


def xValidateKFold(n, k, iris_x, iris_y, VERBOSE):
# K Fold cross validation
# n = # of folds
# k = # of nearest neighbors to check
# iris_x = data
# iris_y = classes
# VERBOSE = flag to spit out more information on each fold iteration

# Create the cross validator
    kf = cross_validation.KFold(n=len(iris_x), n_folds = n, random_state=0)
    if VERBOSE:
        print "kFold validator: "+str(kf)

    avgScore = 0.0  # function returns avg score for all runs

# for each set of training and test data
    for train_index, test_index in kf:
        knn = KNeighborsClassifier(n_neighbors=k)   # Create Classifier
        knn.fit(iris_x[train_index],iris_y[train_index])  # Training Classifier
        prediction = knn.predict(iris_x[test_index])  # Predict on test data
        score = knn.score(iris_x[test_index], iris_y[test_index])  # Evaluate success of prediction
        avgScore += score  # Accrue score for averaging
        if VERBOSE:
            print "\tscore for this validation round: "+str(score)

    return avgScore/float(n)    # Return average score for all iterations
                                # cast n to float to ensure proper division, instead of using
                                # from __future__ 
################# FUNCTIONS END ############################
        

if __name__ == "__main__":
    n,k,VERBOSE = processCommandLine(sys.argv)   # Gather info from command line
    iris_x, iris_y = prepareData()  # Prepare data and classes
    if k > 0:   # use the k passed in from command line
        avgScore = xValidateKFold(n,k,iris_x, iris_y, VERBOSE)   # Cross validate by K Folds method
        print "KFolds score for k=%s is %s" % (str(k), str(avgScore))
    else:   # cycle through some Ks
        for i in xrange(1,11,3):  # 1, 4, 7, 10
            avgScore = xValidateKFold(n,i,iris_x, iris_y, VERBOSE)   # Cross validate by K Folds method
            print "KFolds score for k=%s is %s" % (str(i), str(avgScore))+"\n"

