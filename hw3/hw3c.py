#!/Users/eblumenau/anaconda/bin/python -tt
#/usr/bin/python -tt

import gdata.docs
import gdata.docs.service
import gdata.spreadsheet.service
import re, sys
import numpy as np
from sklearn import (metrics, linear_model, preprocessing, cross_validation)
from sklearn.preprocessing import scale
from sklearn.cluster import KMeans
from time import time


#################### FUNCTIONS START #######################
def scrape_from_google(email, password, ss_source, wb_source):
    gd_client = gdata.spreadsheet.service.SpreadsheetsService()
    gd_client.email = email
    gd_client.password = password
    gd_client.ProgrammaticLogin()
    worksheet_id = None
    raw_data = ""        # raw in the sense that it is straight from Google, not usable yet

    query = gdata.spreadsheet.service.DocumentQuery()
    query['title'] = ss_source
    query['title-exact'] = 'true'
    
    ss_feed = gd_client.GetSpreadsheetsFeed(query=query)
    spreadsheet_id = ss_feed.entry[0].id.text.rsplit('/',1)[1]
    wb_feed = gd_client.GetWorksheetsFeed(spreadsheet_id)
    for i in range(len(wb_feed.entry)):
        # Find the index that matches wb_source
        if wb_feed.entry[i].id.text == wb_source:
            worksheet_id = wb_feed.entry[i].id.text.rsplit('/',1)[1]
            break
    if worksheet_id is None: 
        print "Couldn't find a worksheet called "+str(wb_source)+" in spreadsheet "+str(ss_source)
        sys.exit(1)
    
    rows = gd_client.GetListFeed(spreadsheet_id, worksheet_id).entry
    for row in rows:
        for key in row.custom:
          raw_data = raw_data + "\n"+str(key)+": "+str(row.custom[key].text)
        raw_data = raw_data + "\n\n"

    return raw_data


def load_from_file(filename):

    try:
        file_handle = open(filename, 'r')
        file_data = file_handle.read()
        file_handle.close()
    except:
        print "Couldn't open file or read it in."
        sys.exit(1)

    return file_data


def parse_raw_data(raw_data, good_mpg):
    data_dict = {}
    X = []
    y = []

    entries = re.compile('\n\n\n', re.M).split(raw_data)
    for entry in entries:
        # Split entry into rows
        tDict = {}
        rows = re.compile('\n').split(entry)   
        for row in rows:
            if row == '':
                continue
            key, value = re.compile(':\s*').split(row,2)
            if (value == "None") or (key == ''):
                continue  # Go to the next row
            tDict.update({str(key):value})
        if '_cn6ca' in tDict.keys():   # _cn6ca is the unique identifier
            data_dict.update({str(tDict['_cn6ca']):
                {'deltamiles':tDict['deltamiles'],
                 'costOfFile':tDict['_chk2m'],
                 'deltadays':tDict['deltadays'],
                 'dateOfFill':tDict['_cokwr'],
                 'gallonsOfGas':tDict['_cre1l'],
                 'milesPerGallon':tDict['milesgallon'],
                 'odometer':tDict['_cpzh4'],
                 'tripometer':tDict['_ciyn3']
                }})

    for key in data_dict.keys():
        if float(data_dict[key]['gallonsOfGas']) >= 0.0:
            X.append([float(data_dict[key]['gallonsOfGas']),
                      int(data_dict[key]['deltadays'])
                     ])
        if float(data_dict[key]['milesPerGallon']) >= good_mpg:
            y.append(1)
        else:
            y.append(-1)

    return np.array(X), np.array(y)


def logreg(X,y):
    model = linear_model.LogisticRegression(C=1)

    # Create an instance of Neighbors Classifier and fit the data
    encoder = preprocessing.OneHotEncoder()
    encoder.fit(X)

    mean_auc = 0.0

    n = 10  # Repeat cross-validation 10x
    for i in range(n):
        x_train, x_test, y_train, y_test = cross_validation.train_test_split(X,y, test_size=0.20, random_state=i*SEED)
        x_train = encoder.transform(x_train)
        x_test = encoder.transform(x_test)
        model.fit(x_train, y_train)
        predictions = model.predict_proba(x_test)[:,1]

        # Computer AUC metric for this CV fold
        fpr, tpr, thresholds = metrics.roc_curve(y_test, predictions)
        roc_auc = metrics.auc(fpr, tpr)
        print "AUC (fold %d/%d): %f" % (i+1, n, roc_auc)
        mean_auc += roc_auc

    print "Mean AUC: %f" % (mean_auc/n)


def output_kmeans(estimator_model,data, n_digits):
    estimator = KMeans(init=estimator_model, n_clusters=n_digits, n_init=10)
    t0=time()
    estimator.fit(data)
    t1=time()
    print "% 9s\t%.2f\t%i\t%.3f\t%.3f\t%.3f\t%.3f\t%.3f\t%.3f" %(estimator_model,(t1-t0),estimator.inertia_,metrics.homogeneity_score(y, estimator.labels_),metrics.completeness_score(y, estimator.labels_), metrics.v_measure_score(y, estimator.labels_), metrics.adjusted_rand_score(y, estimator.labels_), metrics.adjusted_mutual_info_score(y, estimator.labels_), metrics.silhouette_score(data, estimator.labels_, metric='euclidean', sample_size=len(X)))


def kmeans(X,y):
    # http://scikit-learn.org/stable/auto_examples/cluster/plot_kmeans_digits.html
    # X is the features
    data = scale(X)

    n_samples, n_features = data.shape
    n_digits = len(np.unique(y))
    
    #sample_size = len(X)  # example had 300
    print "n_digits: %d, \t n_samples %d, \t n_features %d" %(n_digits, n_samples, n_features)

    print('% 9s' % '\t\ttime\tinertia\thomo\tcompl\tv-meas\tARI\tAMI\tsilhouette')
    output_kmeans("k-means++",data,n_digits)
    output_kmeans("random", data, n_digits)


#################### FUNCTIONS END #########################


# Load it from the web.  od5 is the worksheet id.  Have to dig that out manually
#raw_data = scrape_from_google('eric.blumenau@gmail.com','xjkhiarembsxiyif','Motorcycle Log','https://spreadsheets.google.com/feeds/worksheets/tqi5NZjF1KVTLk0JI2TsnPg/private/full/od5')

# or read it from a file
raw_data = load_from_file("ML.raw")
X,y = parse_raw_data(raw_data, 38.0)
SEED = 13

logreg(X,y)
kmeans(X,y)

