The whole point of this script is to generate a k-means cluster, and maybe graph it.
This script looks for clusters in Top 8 decks in the 2013 Magic the Gathering Standard qualifiers
by making a sparse array of all decks x all cards with either 0 or the count of that card and
comparing decks based on what cards they have.  
Without knowing anything else about MtG, it did identify the major deck archetypes in common use, as
verified by my friend Bruce Cowley, who competed at the world championships in Dublin 2013.

It currently does kmeans and metrics for the PCA'd data.  Curiously, the silhouette coeff was higher 
for PCA'd data than for the full data set.  Not sure why.  The program outputs a csv file called
kmeans-silhouette.csv that you can pull into Excel.  There is code to comment/uncomment inside if you 
want to generate the full dataset csv.

