#!/usr/bin/python -tt

import re
import sys
import sqlite3 as lite
import numpy as np
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.preprocessing import scale
from time import time
from sklearn import metrics
import pylab as pl
from mpl_toolkits.mplot3d import Axes3D

################# FUNCTIONS START ###############
def db_connect(db_name):
    con = None
    try:
        con = lite.connect(db_name)
    except lite.Error as e:
        print "DB Connect error %s: "% e.args[0]
        sys.exit(1)
    
    return con


def bench_k_means(estimator, name, data, silhouette_results):
    t0 = time()
    estimator.fit(data)
    print('init\t\ttime\tinertia\thomo\tcompl\tv-meas\tARI\tAMI\tsilhouette')
    print('% 9s\t %.2fs\t%i\t%.3f\t%.3f\t%.3f\t%.3f\t%.3f\t%.3f' % \
        (name, (time() - t0), \
        estimator.inertia_, \
        metrics.homogeneity_score(labels, estimator.labels_), \
        metrics.completeness_score(labels, estimator.labels_), \
        metrics.v_measure_score(labels, estimator.labels_), \
        metrics.adjusted_rand_score(labels, estimator.labels_), \
        metrics.adjusted_mutual_info_score(labels,  estimator.labels_), \
        metrics.silhouette_score(data, estimator.labels_, metric='euclidean')))
    return str(metrics.silhouette_score(data,estimator.labels_, metric='euclidean')) 
 

def dump_to_csv(filename, data, estimator, labels):
    try: 
        file_handle = open(filename,'w')
        deck_in_clusters = ""
        for i in range(len(data)): 
            pred = estimator.predict(data[i])
            deck_in_clusters += str(labels[i])+','+str(pred[0])+'\n'
        file_handle.write(deck_in_clusters)
        file_handle.close()
    except:
        print "Problem in dump_to_csv."
        sys.exit(1)
################# FUNCTIONS END #################
# The whole point of this script is to generate a k-means cluster, and maybe graph it.
# This script looks for clusters in Top 8 decks in the 2013 Magic the Gathering Standard qualifiers
# by making a sparse array of all decks x all cards with either 0 or the count of that card and
# comparing decks based on what cards they have.  
# Without knowing anything else about MtG, it did identify the major deck archetypes in common use, as
# verified by my friend Bruce who competed at the world championships in Dublin 2013.

# Connect to database
db_conn = db_connect('mycards.sqlite')
cursor = db_conn.cursor()

# Retrieve deck information
query = "SELECT DISTINCT(id),playerName, deckName FROM decks"
cursor.execute(query)
deck_list_data = cursor.fetchall()
deck_list = []
labels = []
for deck in deck_list_data:
    deck_list.append(deck[0])
    labels.append(deck[2])
deck_count = len(deck_list)

# Retrieve the cards in those decks
query = "SELECT DISTINCT(card_name) FROM deck_cards_join"
cursor.execute(query)
deck_cards = cursor.fetchall()
# Need to convert from list of tuples to list of single values
deck_cards_list = []
for card in deck_cards:
    deck_cards_list.append(card[0])
card_count = len(deck_cards)

# Make an array of 0s, # of decks high and # of cards wide
# I think numpy has this
deck_card_matrix = np.zeros((deck_count, card_count),np.int8)

# get deck_min to calculate index of deck in matrix
query = "SELECT MIN(id) from decks"
cursor.execute(query)
deck_min = cursor.fetchone()
deck_min = deck_min[0]

# Now query this for all deck-card data
query = "SELECT d.id, dcj.card_name, dcj.count FROM decks d, deck_cards_join dcj WHERE d.id = dcj.deck_id ORDER BY d.id ASC, dcj.count ASC"
cursor.execute(query)
deck_card_data = cursor.fetchall()
print "deck_card_data len " + str(len(deck_card_data))

# Iterate over each card and set the correct value to count
#  Bam!  There is your sparse matrix!
for deck_id, card_name, card_count in deck_card_data:

    # Calculate deck index
    deck_index = deck_id - deck_min

    # Calculate card index
    card_index = deck_cards_list.index(card_name)

    # Update deck_card_matrix[deck_index,card_index] = card_count
    deck_card_matrix[deck_index, card_index] = card_count


# Begin the KMeans part
#np_digits = len(np.unique(deck_card_matrix))
silhouette_results = 'clusters,silhouette\n'
trash = ''
for np_digits in range(2,25):
    print "processing %s clusters - " % str(np_digits)
    #silhouette_results += str(np_digits)+","+bench_k_means(KMeans(init='k-means++', n_clusters=np_digits, n_init=10),"k-means++", deck_card_matrix, silhouette_results)+"\n"
    # Comment out next two lines and uncomment line above for full data set instead of PCA reduced set
    reduced_deck_data = PCA(n_components=np_digits).fit_transform(deck_card_matrix)
    silhouette_results += str(np_digits) +","+str(bench_k_means(KMeans(init='k-means++', n_clusters=np_digits, n_init=1), "PCA-based",reduced_deck_data, silhouette_results))+"\n"
print"\n"
print"\n"
file_handle = open('kmeans-silhouette.csv','w')
file_handle.write(silhouette_results)
file_handle.close()

# Uncomment the next section to get a popup window with a graph of the clusters.
'''
# Can these be visualized?
pca = PCA(n_components=2)
reduced_deck_data = pca.fit_transform(deck_card_matrix)
print "pca explained variance ratio_: "+str(pca.explained_variance_ratio_)

kmeans = KMeans(init="k-means++", n_clusters=11, n_init=10)
kmeans.fit(reduced_deck_data)

# Dump to CSV to look at in Excel
dump_to_csv('kmeans1.csv',reduced_deck_data, kmeans, labels)

h = 0.02
x_min, x_max = reduced_deck_data[:,0].min()+1, reduced_deck_data[:,0].max()-1
y_min,y_max = reduced_deck_data[:,1].min()+1, reduced_deck_data[:,1].max()-1
xx,yy = np.meshgrid(np.arange(x_min,x_max,h), np.arange(y_min,y_max,h))

print "xx shape: "+str(xx.shape)+", yy shape: "+str(yy.shape)
print "kmeans: "+str(kmeans)
Z = kmeans.predict(np.c_[xx.ravel(), yy.ravel()])
Z = Z.reshape(xx.shape)
pl.figure(1)
pl.clf()
pl.imshow(Z, interpolation='nearest', extent=(xx.min(), xx.max(), yy.min(), yy.max()), \
                              cmap=pl.cm.Paired, aspect='auto', origin='lower')
pl.plot(reduced_deck_data[:,0],reduced_deck_data[:,1],'k.', markersize=2)
centroids = kmeans.cluster_centers_
#pl.scatter(centroids[:,0], centroids[:,1], marker='x', s=169, linewidths=3,color='w', zorder=10)
# Label with text labels via pl.annotate since scatter only lets you use marks
#http://stackoverflow.com/questions/5147112/matplotlib-how-to-put-individual-tags-for-a-scatter-plot
for label, x, y in zip(deck_list,reduced_deck_data[:,0],reduced_deck_data[:,1]):
    pl.annotate(label, xy=(x,y), xytext=(0,0),size=8,  textcoords='offset points')

pl.title('K-Means clustering on Pro Tour Top 8 decks, early 2013')
pl.xlim(x_min, x_max)
pl.ylim(y_min,y_max)
pl.xticks(())
pl.yticks(())
pl.show()
'''

