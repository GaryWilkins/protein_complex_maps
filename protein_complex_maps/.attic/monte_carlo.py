
import math as m
import logging
import protein_complex_maps.bicluster.bicluster as bc

logging.basicConfig(level = logging.DEBUG,format='%(asctime)s %(levelname)s %(message)s')

class MonteCarlo(object):

	def __init__( self, scorefunction, temp, random_module=None ):
		self.__scorefunction = scorefunction
		self.__starting_temp = temp
		self.__temp = temp

		self.__low_scoring_bicluster = None
		self.__low_score = None
		self.__current_bicluster = None
		self.__current_score = None

		self.__accepts = 0
		self.__rejects = 0
		self.__thermal_accepts = 0
		self.__score_accepts = 0
		self.__lowscore_accepts = 0

		self.__result_history = []
		self.__score_history = []
		self.__score_diff_history = []

		self.__iterations = 0 
		self.__iterations_since_last_accept = 0


		if random_module == None:
			try:
				import random 
			except ImportError:
				self.__random_module = None
				logging.warning("Setting random module to None, things probably will not work properly")
			else:
				self.__random_module = random
		else:
			self.__random_module = random_module


	def reset(self, ):

		self.__temp = self.__starting_temp
		self.__low_scoring_bicluster = None
		self.__low_score = None
		self.__current_bicluster = None
		self.__current_score = None

		self.__accepts = 0
		self.__rejects = 0
		self.__thermal_accepts = 0
		self.__score_accepts = 0
		self.__lowscore_accepts = 0

		self.__result_history = []
		self.__score_history = []
		self.__score_diff_history = []

		self.__iterations = 0 
		self.__iterations_since_last_accept = 0

	def reset_temp(self,):
		self.__temp = self.__starting_temp

	def temp(self, temp=None):
		if temp == None:
			return self.__temp
		self.__temp = temp

	def lowscore_bicluster(self,):
		return self.__low_scoring_bicluster

	def lowscore(self,):
		return self.__low_scoring
		
	def current_bicluster(self,):
		return self.__current_bicluster

	def current_score(self,):
		return self.__current_score

	#kdrew: recent iterations takes an int to calculate acceptance rate over the last x iterations, default None means all iterations
	def accept_rate(self, recent_iterations=None):
		if recent_iterations == None:
			return 1.0*self.__accepts/self.__iterations
		else:
			recent_history = self.__result_history[-1*recent_iterations:]
			rejects = recent_history.count('reject')
			return 1.0*(recent_iterations-rejects)/recent_iterations

	def iterations(self, ):
		return self.__iterations
	
	def iterations_since_last_accept(self,):
		return self.__iterations_since_last_accept
	
	def accepts(self,):
		return self.__accepts

	def rejects(self,):
		return self.__rejects

	def thermal_accepts(self,):
		return self.__thermal_accepts

	def score_accepts(self,):
		return self.__score_accepts

	def lowscore_accepts(self,):
		return self.__lowscore_accepts

	def result_history(self,):
		return self.__result_history

	def score_history(self,):
		return self.__score_history

	def score_diff_history(self,):
		return self.__score_diff_history

	def boltzmann(self, data_matrix, trial_bicluster):

		#trial_score = self.__scorefunction(data_matrix, trial_bicluster)
		trial_score = self.__scorefunction( trial_bicluster.get_submatrix(data_matrix) )

		if self.__current_score == None:
			score_diff = float('inf')
		else:
			score_diff = trial_score - self.__current_score 
			logging.debug("trial rows: %s" % trial_bicluster.rows())
			logging.debug("trial cols: %s" % trial_bicluster.columns())
			logging.debug("current rows: %s" % self.__current_bicluster.rows())
			logging.debug("current cols: %s" % self.__current_bicluster.columns())

		self.__score_diff_history.append( score_diff )


		logging.debug("low_score: %s current_score: %s trial_score: %s" % (self.__low_score, self.__current_score, trial_score))
		logging.debug("low_score bicluster: %s" % (self.lowscore_bicluster()))
		if( trial_score >= self.__current_score and self.__current_score != None ):
			logging.debug("bicluster does not decrease total score, test ")
			#kdrew: if no, use logistic regression to predict membership value: x
			#kdrew: p(drop|x) = math.e**(-(1-x)/T)

			if self.__temp == 0.0:
				prob = 0.0
			else:
				prob = m.exp( (-1.0*score_diff)/self.__temp )

			random_prob = self.__random_module.random()

			logging.debug("score_diff: %s, prob: %s, random_prob: %s" % (score_diff, prob,random_prob,))

			if prob > random_prob:
				#kdrew: thermal accept
				logging.debug("thermal accept")
				self.__current_bicluster = bc.Bicluster(rows=trial_bicluster.rows()[:], cols=trial_bicluster.columns()[:], random_module=self.__random_module)
				self.__current_score = trial_score
				self.__accepts += 1
				self.__thermal_accepts += 1
				self.__iterations_since_last_accept = 0

				self.__result_history.append( "thermal" )
				self.__score_history.append( trial_score ) 
				#print self.__current_bicluster.rows()

			else:
				#kdrew: reject
				logging.debug("thermal reject")
				self.__rejects += 1
				self.__iterations_since_last_accept += 1
				self.__result_history.append( "reject" )
				self.__score_history.append( trial_score )
				#print self.__current_bicluster.rows()

		else:
			logging.debug("bicluster decreases total score, automatically accept")

			if self.__low_score > trial_score or self.__low_scoring_bicluster == None:
				self.__low_scoring_bicluster = bc.Bicluster(rows=trial_bicluster.rows()[:], cols=trial_bicluster.columns()[:], random_module=self.__random_module)
				self.__low_score = trial_score
				self.__lowscore_accepts += 1

				self.__result_history.append( "lowscore" )
				self.__score_history.append( trial_score )

			else:
				self.__result_history.append( "score" )
				self.__score_history.append( trial_score )

			self.__current_bicluster = bc.Bicluster(rows=trial_bicluster.rows()[:], cols=trial_bicluster.columns()[:], random_module=self.__random_module)
			self.__current_score = trial_score
			self.__accepts += 1
			self.__score_accepts += 1

			self.__iterations_since_last_accept = 0


		self.__iterations += 1

		#print self.__current_bicluster.rows()
		#kdrew: return copy of current bicluster
		return bc.Bicluster(rows=self.__current_bicluster.rows()[:], cols=self.__current_bicluster.columns()[:], random_module=self.__random_module)
