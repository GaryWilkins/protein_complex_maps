
import sys
import numpy as np
import random as r
import protein_complex_maps.correlation_util as cu
import protein_complex_maps.bicluster.bicluster as bc
import protein_complex_maps.feature_generator as fg
from scipy.stats import ks_2samp
import statsmodels.tools.sm_exceptions
import protein_complex_maps.plots.plot_bicluster as pb
import protein_complex_maps.normalization_util as nu

r.seed(123456)
np.random.seed(1234)
sample_filename = "/home/kdrew/data/protein_complex_maps/sample_data/Hs_hekN_1108_psome_exosc_randos.txt"

sample_file = open(sample_filename, 'rb')
#kdrew: eat header
line = sample_file.readline()

data = []

for line in sample_file.readlines():
	#print line
	line_data = line.split()
	line_array = map(float,line_data[2:])
	print line_array
	data.append(line_array)

#print data

data_matrix = np.asmatrix(data)

#print data_matrix


#kdrew: remove columns with all zeros
#clean_data_matrix = data_matrix.compress(~np.array(np.all(data_matrix[:]==0,axis=0))[0],axis=1)
clean_data_matrix_pre_normalized = nu.remove_zero(data_matrix)
print clean_data_matrix_pre_normalized
##kdrew: remove columns with all zeros
#self.__clean_data_matrix = self.__data_matrix.compress(~np.array(np.all(self.__data_matrix[:]==0,axis=0))[0],axis=1)

#kdrew: normalize where whole column adds to 1.0
clean_data_matrix = nu.normalize_over_rows(clean_data_matrix_pre_normalized)
print clean_data_matrix


bicluster1 = bc.Bicluster(rows = [3,10,13,14,22,26], cols = [50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70], random_module=r)

bc1_submat = bicluster1.get_submatrix(clean_data_matrix)
print bc1_submat

bc1_corrDist = cu.correlation_distribution(bc1_submat)
print bc1_corrDist

bc1_r0_corrDist = cu.correlation_distribution(bc1_submat, 0)
print bc1_r0_corrDist

#rand_bicluster1 = bc.Bicluster(rows=bicluster1.get_random_outside_rows(clean_data_matrix), cols=bicluster1.columns(), random_module=r)
#
#kdrew: index is the index in the bicluster, i is the index (row number) in the complete data matrix
#for index, i in enumerate(bicluster1.rows()):
#	print "index:%s, i:%s" % (index, i)
#	print bicluster1.get_row(clean_data_matrix, row=i)
#	submat = bicluster1.get_submatrix( clean_data_matrix )
#	print "bicluster1 submatrix:"
#	print submat
#
#	print ""
#	submatWO = bicluster1.get_submatrix( clean_data_matrix, without_rows=[i] )
#	corrDistWO = cu.correlation_distribution( submatWO )
#	print "correlation_distribution without %s:" % (i,)
#	print corrDistWO
#
#	corrDistIndex = cu.correlation_distribution( submat, index )
#	print "correlation_distribution of bicluster submatrix vs index %s:" % (index,)
#	print corrDistIndex
#
#	#ks_biclust = ks_2samp(corrDistWO, corrDistIndex)
#	#print ks_biclust
#
#	rand_bicluster1.add_row(i)
#
#	rand_submat = rand_bicluster1.get_submatrix( clean_data_matrix )
#	print "random bicluster submatrix with row %s:" % (i,)
#	print rand_submat
#	rand_submatWO = rand_bicluster1.get_submatrix( clean_data_matrix, without_rows=[i] )
#
#	randbc_corrDistWO = cu.correlation_distribution( rand_submatWO )
#	print randbc_corrDistWO
#
#	rand_bc_index = list(rand_bicluster1.rows()).index(i)
#	randbc_corrDistIndex =  cu.correlation_distribution( rand_submat, rand_bc_index )
#	print randbc_corrDistIndex
#
#	#kdrew: not really using ks tests anymore, 10/09/13
#	#ks_rand_biclust = ks_2samp(randbc_corrDistWO, randbc_corrDistIndex)
#	#print ks_rand_biclust
#
#	#kdrew: compute ratio of ks tests, this gives a value of how correlated the bicluster is compared to the background
#	#kdrew: values of ~1.0 suggest no correlation above background, small values suggest bicluster is more correlated than background
#	#print ks_biclust[0]/ks_rand_biclust[0]
#
#	print corrDistIndex.mean()
#	print randbc_corrDistIndex.mean()
#	print corrDistIndex.mean()/randbc_corrDistIndex.mean()
#
#	print ""
#
#	rand_bicluster1.remove_row(i)


featuregen = fg.FeatureGenerator(bicluster1, clean_data_matrix)
featuregen.correlation_feature_row()
featuregen.correlation_feature_column()

test_columns = ['label','corr_mean_bc','corr_mean_rand']
try:
	row_logreg, row_logit_result = featuregen.create_logistic_regression_row(test_columns)
	print row_logit_result.summary()
except statsmodels.tools.sm_exceptions.PerfectSeparationError:
	print "PerfectSeparationError"
	sys.exit(0)

try:
	column_logreg, column_logit_result = featuregen.create_logistic_regression_column()
	print column_logit_result.summary()
except statsmodels.tools.sm_exceptions.PerfectSeparationError:
	print "PerfectSeparationError"
	sys.exit(0)
 

#kdrew: annealing temperature
T=4
#kdrew: randomly pick row or column (inside or outside of bicluster)
print "rows: %s" % (len(clean_data_matrix),)
numRows, numCols = clean_data_matrix.shape
print numRows, numCols

#kdrew: probably should test for some convergence
for i in xrange(1,200):
	print "iteration: %s" % (i,)

	random_row = np.random.random_integers(0, numRows-1)
	random_column = np.random.random_integers(0, numCols-1)

	featuregen = fg.FeatureGenerator(bicluster1, clean_data_matrix)
	featuregen.correlation_feature_row()
	featuregen.correlation_feature_column()

	#test_columns = ['label','corr_mean_bc','corr_mean_rand']
	#test_columns = ['label','corr_mean_bc','tvalue_corr_mean_bc']
	test_columns = ['label','tvalue_corr_mean_bc']

	try:
		row_logreg, row_logit_result = featuregen.create_logistic_regression_row(test_columns)
		try:
			print row_logit_result.summary()
		except ValueError:
			pass
	except statsmodels.tools.sm_exceptions.PerfectSeparationError:
		print "PerfectSeparationError"

	#test_columns = ['label','corr_gain_bc','tvalue_corr_gain_bc']
	test_columns = ['label','tvalue_corr_gain_bc']
	try:
		column_logreg, column_logit_result = featuregen.create_logistic_regression_column(test_columns)
		try:
			print column_logit_result.summary()
		except ValueError:
			pass
	except statsmodels.tools.sm_exceptions.PerfectSeparationError:
		print "PerfectSeparationError"


	if random_row in bicluster1.rows():
		print "row %s in bicluster" % (random_row,)
		#kdrew: if row is inside bicluster, test if it decreases total mean correlation
		corr_with_row = cu.correlation_distribution(bicluster1.get_submatrix(clean_data_matrix))
		mean_corr_with_row = corr_with_row.mean()
		#kdrew: calculate tvalues for correlation coefficients
		tvalue_corr_with_row = cu.tvalue_correlation(corr_with_row, len(bicluster1.columns()))
		#mean_tvalue_corr_with_row = tvalue_corr_with_row.mean()

		poisson_corr_with_row, poisson_tvalue_corr_with_row = cu.poisson_correlation_distribution(bicluster1.get_submatrix(clean_data_matrix), noise_constant=1.0/clean_data_matrix.shape[1], poisson_module = np.random.poisson)
		mean_tvalue_corr_with_row = poisson_tvalue_corr_with_row.mean()

		bicluster1.remove_row(random_row)
		corr_without_row = cu.correlation_distribution(bicluster1.get_submatrix(clean_data_matrix))
		mean_corr_without_row = corr_without_row.mean()
		tvalue_corr_without_row = cu.tvalue_correlation(corr_without_row, len(bicluster1.columns()))
		#mean_tvalue_corr_without_row = tvalue_corr_without_row.mean()

		poisson_corr_without_row, poisson_tvalue_corr_without_row = cu.poisson_correlation_distribution(bicluster1.get_submatrix(clean_data_matrix), noise_constant=1.0/clean_data_matrix.shape[1], poisson_module = np.random.poisson)
		mean_tvalue_corr_without_row = poisson_tvalue_corr_without_row.mean()



		#kdrew: I was first using mean correlation as a metric to add or remove a row, now using tvalues
		#if(mean_corr_with_row >= mean_corr_without_row):
		if(mean_tvalue_corr_with_row >= mean_tvalue_corr_without_row):
			print "row does not decrease total correlation, test to keep"
			#kdrew: if no, use logistic regression to predict membership value: x
			#kdrew: p(drop|x) = math.e**(-(1-x)/T)

			bicluster1.add_row(random_row)
		else:
			#kdrew: if yes, remove row
			print "row decreases total correlation, automatically remove"

	else:
		#kdrew: if row is outside bicluster, test if it increases total mean correlation, 
		print "row %s outside of bicluster" % (random_row,)
		corr_without_row = cu.correlation_distribution(bicluster1.get_submatrix(clean_data_matrix))
		mean_corr_without_row = corr_without_row.mean()
		#kdrew: calculate tvalues for correlation coefficients
		tvalue_corr_without_row = cu.tvalue_correlation(corr_without_row, len(bicluster1.columns()))
		#mean_tvalue_corr_without_row = tvalue_corr_without_row.mean()

		poisson_corr_without_row, poisson_tvalue_corr_without_row = cu.poisson_correlation_distribution(bicluster1.get_submatrix(clean_data_matrix), noise_constant=1.0/clean_data_matrix.shape[1], poisson_module = np.random.poisson)
		mean_tvalue_corr_without_row = poisson_tvalue_corr_without_row.mean()

		bicluster1.add_row(random_row)
		corr_with_row = cu.correlation_distribution(bicluster1.get_submatrix(clean_data_matrix))
		mean_corr_with_row = corr_with_row.mean()
		#kdrew: calculate tvalues for correlation coefficients
		tvalue_corr_with_row = cu.tvalue_correlation(corr_with_row, len(bicluster1.columns()))
		#mean_tvalue_corr_with_row = tvalue_corr_with_row.mean()

		poisson_corr_with_row, poisson_tvalue_corr_with_row = cu.poisson_correlation_distribution(bicluster1.get_submatrix(clean_data_matrix), noise_constant=1.0/clean_data_matrix.shape[1], poisson_module = np.random.poisson)
		mean_tvalue_corr_with_row = poisson_tvalue_corr_with_row.mean()


		print mean_corr_with_row, mean_corr_without_row
		#kdrew: I was first using mean correlation as a metric to add or remove a row, now using tvalues
		#if(mean_corr_with_row > mean_corr_without_row):
		if(mean_tvalue_corr_with_row > mean_tvalue_corr_without_row):
			#kdrew: if yes, add row
			print "row increases total correlation, automatically add"
		else:
			print "row does not increase total correlation, test to add"
			#kdrew: if no, use logistic regression to predict membership value: x
			#kdrew: p(add|x) = math.e**(-x/T)

			bicluster1.remove_row(random_row)

	#kdrew: check to make sure random column is not all zeros across the rows of the bicluster, if so remove or do not add
	if np.all(bicluster1.get_column(clean_data_matrix, random_column) == 0):
		print "removing: random column is all zeros: %s" % (bicluster1.get_column(clean_data_matrix,random_column),)
		bicluster1.remove_column(random_column)
		continue

	
	if random_column in bicluster1.columns():
		print "column %s in bicluster" % (random_column,)
		#kdrew: if column is inside bicluster, test if it decreases total mean correlation
		corr_with_column = cu.correlation_distribution(bicluster1.get_submatrix(clean_data_matrix))
		mean_corr_with_column = corr_with_column.mean()
		tvalue_corr_with_column = cu.tvalue_correlation(corr_with_column, len(bicluster1.columns()))
		#mean_tvalue_corr_with_column = tvalue_corr_with_column.mean()

		poisson_corr_with_column, poisson_tvalue_corr_with_column = cu.poisson_correlation_distribution(bicluster1.get_submatrix(clean_data_matrix), noise_constant=1.0/clean_data_matrix.shape[1], poisson_module = np.random.poisson)
		mean_tvalue_corr_with_column = poisson_tvalue_corr_with_column.mean()

		bicluster1.remove_column(random_column)
		corr_without_column = cu.correlation_distribution(bicluster1.get_submatrix(clean_data_matrix))
		mean_corr_without_column = corr_without_column.mean()
		tvalue_corr_without_column = cu.tvalue_correlation(corr_without_column, len(bicluster1.columns()))
		#mean_tvalue_corr_without_column = tvalue_corr_without_column.mean()

		poisson_corr_without_column, poisson_tvalue_corr_without_column = cu.poisson_correlation_distribution(bicluster1.get_submatrix(clean_data_matrix), noise_constant=1.0/clean_data_matrix.shape[1], poisson_module = np.random.poisson)
		mean_tvalue_corr_without_column = poisson_tvalue_corr_without_column.mean()

		#if(mean_corr_with_column >= mean_corr_without_column ):
		if(mean_tvalue_corr_with_column >= mean_tvalue_corr_without_column ):
			print "column does not decrease total correlation, test to keep"
			#kdrew: if no, use logistic regression to predict membership value: x
			#kdrew: p(drop|x) = math.e**(-(1-x)/T)

			bicluster1.add_column(random_column)
		else:
			#kdrew: if yes, remove column
			print "column decreases total correlation, automatically remove"

	else:
		#kdrew: if column is outside bicluster, test if it increases total mean correlation, 
		print "column %s outside of bicluster" % (random_column,)
		corr_without_column = cu.correlation_distribution(bicluster1.get_submatrix(clean_data_matrix))
		mean_corr_without_column = corr_without_column.mean()
		tvalue_corr_without_column = cu.tvalue_correlation(corr_without_column, len(bicluster1.columns()))
		#mean_tvalue_corr_without_column = tvalue_corr_without_column.mean()

		poisson_corr_without_column, poisson_tvalue_corr_without_column = cu.poisson_correlation_distribution(bicluster1.get_submatrix(clean_data_matrix), noise_constant=1.0/clean_data_matrix.shape[1], poisson_module = np.random.poisson)
		mean_tvalue_corr_without_column = poisson_tvalue_corr_without_column.mean()

		bicluster1.add_column(random_column)
		corr_with_column = cu.correlation_distribution(bicluster1.get_submatrix(clean_data_matrix))
		mean_corr_with_column = corr_with_column.mean()
		tvalue_corr_with_column = cu.tvalue_correlation(corr_with_column, len(bicluster1.columns()))
		#mean_tvalue_corr_with_column = tvalue_corr_with_column.mean()

		poisson_corr_with_column, poisson_tvalue_corr_with_column = cu.poisson_correlation_distribution(bicluster1.get_submatrix(clean_data_matrix), noise_constant=1.0/clean_data_matrix.shape[1], poisson_module = np.random.poisson)
		mean_tvalue_corr_with_column = poisson_tvalue_corr_with_column.mean()

		print mean_corr_with_column, mean_corr_without_column
		#if(mean_corr_with_column > mean_corr_without_column):
		if(mean_tvalue_corr_with_column > mean_tvalue_corr_without_column):
			#kdrew: if yes, add column
			print "column increases total correlation, automatically add"
		else:
			print "column does not increase total correlation, test to add"
			#kdrew: if no, use logistic regression to predict membership value: x
			#kdrew: p(add|x) = math.e**(-x/T)

			bicluster1.remove_column(random_column)

print bicluster1.rows()
print bicluster1.columns()
print bicluster1.get_submatrix(clean_data_matrix)

bc_poisson_corr, bc_poisson_tvalue_corr = cu.poisson_correlation_distribution(bicluster1.get_submatrix(clean_data_matrix), noise_constant=1.0/clean_data_matrix.shape[1], poisson_module = np.random.poisson)
print "bicluster poisson_corr.mean: %s poisson_tvalue_corr.mean: %s" % (bc_poisson_corr.mean(), bc_poisson_tvalue_corr.mean())

whole_poisson_corr, whole_poisson_tvalue_corr = cu.poisson_correlation_distribution(clean_data_matrix, noise_constant=1.0/clean_data_matrix.shape[1], poisson_module = np.random.poisson)
print "whole matrix poisson_corr.mean: %s poisson_tvalue_corr.mean: %s" % (whole_poisson_corr.mean(), whole_poisson_tvalue_corr.mean())

pb.plot_bicluster(clean_data_matrix, bicluster1)



