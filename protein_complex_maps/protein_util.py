
#kdrew: this file is for utilities for querying features about proteins

import urllib, urllib2 

#kdrew: queries uniprot for protein sequence length
def get_length_uniprot( protein_id ):
	length_dict = dict()
	report_query = "http://www.uniprot.org/uniprot/?format=tab&query=accession:%s&columns=id,length" % (protein_id,)
	f = urllib2.urlopen(report_query)
	for line in f.readlines():
		if protein_id == line.split()[0]:
			return int(line.split()[1])
	return None


#kdrew: uses uniprot webservice to map ids
#kdrew: from_id and to_id are abbreviations of dbid names which can be found: http://www.uniprot.org/faq/28
def map_protein_ids( id_list, from_id, to_id ):
	url = 'http://www.uniprot.org/mapping/'

	params = {
		'from':'%s' % (from_id,),
		'to':'%s' % (to_id,),
		'format':'tab',
		'query':' '.join(id_list)
	}

	data = urllib.urlencode(params)
	request = urllib2.Request(url, data)
	contact = "kdrew@utexas.edu" 
	request.add_header('User-Agent', 'Python %s' % contact)
	response = urllib2.urlopen(request)

    #kdrew: put resulting map into dictionary of lists (one to many)
	return_dict = {}
	for line in response.readlines():
		if line.split()[0] != "From":
			try:
				return_dict[line.split()[0]].append(line.split()[1])
			except:
				return_dict[line.split()[0]] = [line.split()[1],] 

	return return_dict

