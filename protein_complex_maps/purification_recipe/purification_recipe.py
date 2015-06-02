
import logging
import numpy as np
import itertools as it

import argparse
import pickle

logging.basicConfig(level = logging.INFO,format='%(asctime)s %(levelname)s %(message)s')

def main():

	parser = argparse.ArgumentParser(description="Create purification recipe")
	parser.add_argument("--input_msds_pickles", action="store", nargs='+', dest="msds_filenames", required=True, 
                                    help="Filenames of MSDS pickle: pickle comes from running protein_complex_maps.util.read_ms_elutions_pickle_MSDS.py")
	parser.add_argument("--proteins", action="store", dest="proteins", nargs='+', required=True, 
                                    help="Protein ids in which to anaylze")
	parser.add_argument("--protein_percent_threshold", action="store", dest="protein_percent_threshold", type=float, required=False, default=0.9,
                                    help="Percentage of proteins that need to be present in input fractions (expressed as decimal), default 0.9 (ie 90%)")

	args = parser.parse_args()

        pr_obj = PurificationRecipe( args.msds_filenames, args.proteins, args.protein_percent_threshold )
        pr_obj.create_recipes()
        pr_obj.show_results()


class PurificationRecipe(object):

    def __init__(self, msds_filenames, proteins, protein_percent_threshold):
        self.msds_filenames = msds_filenames
        self.proteins = proteins
        self.protein_percent_threshold = protein_percent_threshold

        self.results_list = []
        self.df_dict = dict()

        self.create_data_frames()

    def create_data_frames(self,):
        #kdrew: store data in data frames
        for msds_filename in self.msds_filenames:
            msds = pickle.load( open( msds_filename, "rb" ) )
            df = msds.get_data_frame()

            print "filename: %s" % msds_filename

            missing_proteins = [ i for i in self.proteins if i not in df.columns ]
            print "missing: %s" % missing_proteins
            #kdrew: add in 0.0 rows for missing entries
            for missing_prot in missing_proteins:
                df[missing_prot] = np.repeat( 0.0, len(df.index) )


            ##kdrew: normalize by fractions (max of all fraction vectors = 1.0)
            #df = df.div( df.max(axis=1), axis=0 )

            #kdrew: normalize by fractions (sum of all fraction vectors = 1.0, i.e. probability)
            df = df.div( df.sum(axis=1), axis=0 )

            #kdrew: threshold out fraction vectors that do not have enough of the input proteins
            percent_vector = 1.0*(df[self.proteins] > 0.0).sum(axis=1)/len(self.proteins)
            df = df[percent_vector > self.protein_percent_threshold]
            #print df

            self.df_dict[ msds_filename ] = df


    def create_recipes(self,):

        #kdrew: for different possible numbers of sequential experiments
        for r in range(1, len(self.df_dict)+1):
            for exp_list in it.combinations( self.df_dict.keys(), r ):

                df_list = [ self.df_dict[exp] for exp in exp_list ] 
                df_index_list = [ list(df.index) for df in df_list ]

                for fractions in it.product(*df_index_list):

                    #kdrew: initialize vector to be the first fraction
                    combined_vector = df_list[0].loc[fractions[0]]
                    #kdrew: multiply additional fraction vectors
                    for i in range(1,len(fractions)):
                        combined_vector = combined_vector .mul( df_list[i].loc[fractions[i]], fill_value=0.0 )

                    pr = self.score_fraction( combined_vector )

                    pr.experiments=exp_list
                    pr.fractions=fractions

                    self.results_list.append(pr)

    def show_results(self,):
        sorted_results_list = sorted(self.results_list, key = lambda result : result.purity_percent)
        for result in sorted_results_list:
            print result


    def score_fraction(self, vector ):

        ##kdrew: this scoring function gives a 1*abundance to proteins within in the complex and a -1*abundance to all other proteins
        ##kdrew: the sum is the total score 
        #score_mask_1neg1 = [ 1 if i in proteins else -1 for i in vector.index]
        #vector_scored = vector * score_mask_1neg1
        #print "score %s" % (vector_scored.sum())


        #kdrew: count how many original proteins are still present (> 0.0)
        protein_count = (vector[self.proteins] > 0.0).sum()
        proteins_present = vector.index[(vector[self.proteins] > 0.0)].tolist()
        protein_percent = (1.0*protein_count)/len(self.proteins)
        #print "protein_count %s / %s = %s" % (protein_count, len(proteins), protein_percent)

        #kdrew: this scoring function gives what percent the final solution will have of proteins in the complex
        score_mask_1_0 = [ 1 if i in self.proteins else 0 for i in vector.index]
        vector_scored = vector * score_mask_1_0
        purity_percent = vector_scored.sum()/vector.sum()
        #print "percent score %s" % (purity_percent)

        pr = PurificationRecipeResult(proteins=proteins_present, protein_percent=protein_percent, purity_percent=purity_percent)

        return pr


class PurificationRecipeResult(object):

    def __init__(self, experiments=[], fractions=[], proteins=[], protein_percent=None, purity_percent=None):
        self.experiments = experiments
        self.fractions = fractions
        self.proteins = proteins
        self.protein_percent = protein_percent
        self.purity_percent = purity_percent

    def __str__(self,):
        return "experiments: %s, fractions: %s, protein_percent: %s, purity_percent: %s" % (self.experiments, self.fractions, self.protein_percent, self.purity_percent)

if __name__ == "__main__":
	main()


