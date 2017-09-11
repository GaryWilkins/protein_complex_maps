
import logging
import numpy as np
import pandas

import protein_complex_maps.normalization_util as nu
import protein_complex_maps.protein_util as pu

logging.basicConfig(level = logging.DEBUG,format='%(asctime)s %(levelname)s %(message)s')


class MSDataSet(object):

    def __init__( self ):
        self.__master_data_matrix = None
        #kdrew: holds original ids read from file and used to link other files read in, ordered by matrix rows
        self.__master_name_list = None
        self.__master_fraction_list = None
        #kdrew: holds mapping of protein ids to matrix indices, includes ids from master_name_list
        self.__id_dict = dict()
        self.__frac_dict = dict()
        self.__mappings = dict()

    def get_data_frame(self, ids=None, ignoreNonExistingIds=False, map_name=None):
        if ids == None:
            if map_name != None:
                name_list = []
                #print self.__mappings[map_name]
                for x in self.__master_name_list:
                    try:
                        i = self.__master_name_list.index(x)
                        name_list.append(self.__mappings[map_name][i])

                    except KeyError:
                        name_list.append(x)
            else:
                name_list = self.__master_name_list

            df = pandas.DataFrame( self.__master_data_matrix.transpose(), columns=name_list, index=self.__master_fraction_list )
        else:
            data_set, new_id_map = self.get_subdata_matrix(ids, ignoreNonExistingIds=ignoreNonExistingIds)
            print new_id_map
            #df = pandas.DataFrame( data_set.transpose(), columns=ids, index=self.__master_fraction_list )
            df = pandas.DataFrame( data_set.transpose(), columns=new_id_map.values(), index=self.__master_fraction_list )
        return df

    #kdrew: ortholog_map allows for concatentating ortholog fractions, should be in the form of ortholog_map[protein_id_in_file] -> protein_id_in_msds
    def load_file( self, file_handle, header=False, normalize=False, standardize=False, ortholog_map=None, fill_missing=np.zeros):
        
        data_matrix1, name_list1, fraction_list1 = read_datafile(file_handle, header=header)
        print "fraction_list1: %s" % fraction_list1

        if normalize:
            data_matrix1 = nu.normalize_by_mean(data_matrix1)

        if standardize:
            data_matrix1 = nu.standardize(data_matrix1)

        if self.__master_data_matrix == None:
            self.__master_data_matrix = data_matrix1
            self.__master_name_list = name_list1
            self.__master_fraction_list = fraction_list1
        elif ortholog_map != None:
            ortholog_list = []
            for prot_id in name_list1:
                try:
                    ortholog_list.append(ortholog_map[prot_id])
                except KeyError:
                    #kdrew: if no mapping for given prot_id, just keep the name the same
                    ortholog_list.append(prot_id)

            self.__master_data_matrix, self.__master_name_list = concat_data_matrix( self.__master_data_matrix, self.__master_name_list, data_matrix1, ortholog_list, fill_missing=fill_missing)
            self.__master_fraction_list += fraction_list1
        else:
            self.__master_data_matrix, self.__master_name_list = concat_data_matrix( self.__master_data_matrix, self.__master_name_list, data_matrix1, name_list1, fill_missing=fill_missing)
            self.__master_fraction_list += fraction_list1

        self.update_id_dict()

    #kdrew: returns a list of mapped names that correspond to this msds, so pass in worm msds with worm2human map and get list of human names
    def get_ortholog_list( self, ortholog_map):
        ortholog_list = []

        for prot_id in self.get_name_list():
            try:
                ortholog_list.append(ortholog_map[prot_id])
            except KeyError:
                #kdrew: if no mapping for given prot_id, just keep the name the same
                ortholog_list.append(prot_id)

        return ortholog_list

    #kdrew: ortholog_map allows for concatentating ortholog fractions, should be in the form of ortholog_map[protein_id_in_file] -> protein_id_in_msds
    def concat_msds( self, msds2, ortholog_map = None, fill_missing=np.zeros ):

        if ortholog_map != None:

            ortholog_list = msds2.get_ortholog_list(ortholog_map)

            #kdrew: moved to function
            #for prot_id in msds2.get_name_list():
            #   try:
            #       ortholog_list.append(ortholog_map[prot_id])
            #   except KeyError:
            #       #kdrew: if no mapping for given prot_id, just keep the name the same
            #       ortholog_list.append(prot_id)

            self.__master_data_matrix, self.__master_name_list = concat_data_matrix( self.__master_data_matrix, self.__master_name_list, msds2.get_data_matrix(), ortholog_list, fill_missing=fill_missing)
            self.__master_fraction_list += msds2.get_fraction_list()

            self.update_id_dict( reset=True )

        else:
            self.__master_data_matrix, self.__master_name_list = concat_data_matrix( self.__master_data_matrix, self.__master_name_list, msds2.get_data_matrix(), msds2.get_name_list(), fill_missing=fill_missing )
            self.__master_fraction_list += msds2.get_fraction_list()

            self.update_id_dict()

    def update_id_dict(self, reset=False):
        if reset:
            self.__id_dict = dict()
            self.__frac_dict = dict()
        #kdrew: updating id_dict with current name list
        for i, name in enumerate(self.__master_name_list):
            self.__id_dict[name] = i

        if self.__master_fraction_list != None:
            for i, frac in enumerate(self.__master_fraction_list):
                self.__frac_dict[frac] = i

    #kdrew: populate msds with peptide count dictionary
    #kdrew: dictionary should be of the form protein->fraction->peptide->count
    #kdrew: sc_mean flag will take the mean of spectral counts for all peptides
    #kdrew: threshold will require specified number of peptides to be present, otherwise set to zero
    #kdrew: ortholog_map allows for concatentating ortholog fractions, should be in the form of ortholog_map[protein_id_in_protein_counts] -> protein_id_in_msds
    def create_by_peptide_counts( self, protein_counts, sc_mean = False, threshold=1, standardize = False, ortholog_map=None, fill_missing=np.zeros ):
        #kdrew: make sure threshold is an int
        threshold = int(threshold)

        #kdrew: get a list of all proteins
        protein_list = protein_counts.keys()

        #kdrew: get a list of all fractions
        fractions = set()
        for prot in protein_list:
            fractions = fractions.union(protein_counts[prot].keys())
        fractions_list = list(fractions)
        fractions_list.sort()
        #print fractions_list

        #kdrew: create data matrix size: proteins X fractions
        dmat = np.matrix(np.zeros(shape=(len(protein_list),len(fractions_list))))

        for i, prot in enumerate(protein_list):
            for j, fraction in enumerate(fractions_list):
                peptide_count = 0
                try:
                     for peptide in protein_counts[prot][fraction]:
                        dmat[i,j] += protein_counts[prot][fraction][peptide]
                        peptide_count += 1
                except KeyError:
                    continue

                #kdrew: take the average of all the peptide counts
                if sc_mean:
                    dmat[i,j] = 1.0*dmat[i,j]/peptide_count

                #kdrew: for any protein that does not have a given number of peptides identified, set to zero
                if peptide_count < threshold:
                    print "peptide_count < threshold, setting to zero"
                    dmat[i,j] = 0.0

                print "prot: %s fraction: %s peptide_count: %s value: %s" % (prot, fraction, peptide_count, dmat[i,j])
    
        #print dmat

        if standardize:
            dmat = nu.standardize(dmat)

        if self.__master_data_matrix == None:
            self.__master_data_matrix = dmat
            self.__master_name_list = protein_list
            self.__master_fraction_list = fractions_list
        elif ortholog_map != None:
            ortholog_list = []
            for prot_id in protein_list:
                try:
                    #kdrew: append the ortholog that will match a protein id in current msds
                    ortholog_list.append(ortholog_map[prot_id])
                except KeyError:
                    #kdrew: if no mapping for given prot_id, just keep the name the same
                    ortholog_list.append(prot_id)

            self.__master_data_matrix, self.__master_name_list = concat_data_matrix( self.__master_data_matrix, self.__master_name_list, dmat, ortholog_list, fill_missing=fill_missing)
            self.__master_fraction_list += fractions_list
        else:
            self.__master_data_matrix, self.__master_name_list = concat_data_matrix( self.__master_data_matrix, self.__master_name_list, dmat, protein_list, fill_missing=fill_missing)
            self.__master_fraction_list += fractions_list

        self.update_id_dict()

    def map_remove_version( self, ):
        num_orig = len(self.__master_name_list)
        rmver_master_name_list = [x.split('.')[0] for x in self.__master_name_list]
        num_rmver = len(set(rmver_master_name_list))

        if "rmver" not in self.__mappings.keys():
            self.__mappings["rmver"] = dict()
            self.__mappings["rmver_list"] = dict()

        for i, prot_id in enumerate(self.__master_name_list):
            i = self.__master_name_list.index(prot_id)
            mapped_id = rmver_master_name_list[i]
            self.__mappings["rmver"][i] = mapped_id

            try:
                self.__mappings["rmver_list"][i].append(mapped_id)
            except KeyError:
                self.__mappings["rmver_list"][i] = [mapped_id]

        print "num_orig: %s, num_rmver: %s" % (num_orig, num_rmver)


    #kdrew: adds mappings of Uniprot ACC protein ids to matrix indices
    def map_ids_by_genename( self, organism, reviewed=False, genename_mappings=None):
        #kdrew: map master_name_list from current db_id to db_id
        #kdrew: update master_name_list and current db_id

        if genename_mappings == None:
            gene_ids = self.__master_name_list
        else:
            gene_ids = self.__mappings[genename_mappings].values()

        protids_map = pu.get_from_uniprot_by_genename( gene_ids, organism=organism, reviewed=reviewed)
        print protids_map

        if "ACC" not in self.__mappings.keys():
            self.__mappings["ACC"] = dict()
            self.__mappings["ACC_list"] = dict()

        for protid in protids_map:
            print protid
            if genename_mappings == None:
                i = self.__master_name_list.index(protid)
            else:
                i = self.__mappings[genename_mappings].keys()[self.__mappings[genename_mappings].values().index(protid)]

            for mapped_id in protids_map[protid]:
                print mapped_id
                self.__id_dict[mapped_id] = i
                self.__mappings["ACC"][i] = mapped_id

                try:
                    self.__mappings["ACC_list"][i].append(mapped_id)
                except KeyError:
                    self.__mappings["ACC_list"][i] = [mapped_id]
        
        #return self.__id_dict


    #kdrew: wrapper for adding mappings of protein ids to matrix indices
    def map_ids( self, from_id, to_id):
        #kdrew: map master_name_list from current db_id to db_id
        #kdrew: update master_name_list and current db_id

        protids_ACC_map = pu.map_protein_ids( self.__master_name_list, from_id, 'ACC', reviewed=True)
        acc_list = [protids_ACC_map[x][0] if len(protids_ACC_map[x]) > 0 else x for x in self.__master_name_list]
        protids_map = pu.map_protein_ids( acc_list, 'ACC', to_id, reviewed=True)
        full_protids_map = dict()
        for x in self.__master_name_list:
            try:
                full_protids_map[x] = protids_map[protids_ACC_map[x][0]] 
            except (KeyError, IndexError):
                full_protids_map[x] = [x]
        self.add_mapping(full_protids_map, map_name = to_id)

    #kdrew: adds mappings of protein ids to matrix indices
    def add_mapping( self, id_map, map_name ):
        #kdrew: older versions of msds did not have mappings attribute
        try:
            self.__mappings
        except AttributeError:
            self.__mappings = dict()

        self.__mappings[map_name] = dict()
        self.__mappings[map_name+"_list"] = dict()

        #kdrew: for every protein id
        for protid in id_map:
            #kdrew: find index in msds
            i = self.__master_name_list.index(protid)
            try:
                #kdrew: tests if the map has a list of ids for entries (ex. many ids mapped for a single protein)
                if isinstance(id_map[protid], list):
                    #kdrew: if list is empty
                    if len(id_map[protid]) == 0: 
                        #kdrew: there is no mapping for this identifier, map to original identifer
                        self.__mappings[map_name][i] = protid
                        self.__mappings[map_name+"_list"][i] = [protid]

                    else: 
                        #kdrew: list is not empty
                        primary_mapped_id = id_map[protid][0]
                        self.__mappings[map_name][i] = primary_mapped_id
                        self.__mappings[map_name+"_list"][i] = id_map[protid]

                        for mapped_id in id_map[protid]:
                            self.__id_dict[mapped_id] = i

                #kdrew: tests if the map has a string for an entry (ex. only one id mapped for a single protein)
                elif isinstance(id_map[protid], str):
                    mapped_id  = id_map[protid]
                    self.__id_dict[mapped_id] = i
                    self.__mappings[map_name][i] = mapped_id
                    self.__mappings[map_name+"_list"][i] = [mapped_id]
                else:
                    raise Exception, "id_map entry is neither a list or string, something wrong"

            #kdrew: this is the case where there is no protid in id_map (missing in map and is not a list) and it should default to original id
            except KeyError:
                self.__mappings[map_name][i] = protid
                self.__mappings[map_name+"_list"][i] = [protid]
        
        #return self.__id_dict

    #kdrew: function to take id_dict in msds2 and convert it to self's id_dict
    #kdrew: useful when map_ids does not grab all ids or when uniprot mapping site is down
    def transfer_map( self, msds2 ):
        self_ids = self.__id_dict
        msds_map = msds2.get_index2names()

        self_ids2 = dict()
        #kdrew: search through msds2's map for keys in self
        for key in self_ids:
            for i in msds_map:
                if key in msds_map[i]:
                    #kdrew: grab all synonomous ids 
                    for j in msds_map[i]:
                        self_ids2[j] = self_ids[key]

        self.__id_dict = self_ids2


    #kdrew: dictionary of protein ids (keys) to matrix indices
    def get_id_dict( self ):
        return self.__id_dict

    def get_mappings_dict( self ):
        return self.__mappings

    def get_mapping( self, key ):
        return self.__mappings[key]

    def get_fraction_dict( self ):
        return self.__frac_dict

    def get_fraction_list( self ):
        return self.__master_fraction_list

    def get_name_list( self ):
        return self.__master_name_list

    def set_name_list( self, name_list ):
        self.__master_name_list = name_list

    def set_id_dict( self, id_dict ):
        self.__id_dict = id_dict

    #def get_data_matrix( self, names=None, remove_zero=False ):

    #kdrew: function to move given rows and columns into top left corner (low indices)
    def reordered_data_matrix( self, rows, columns, data_matrix=None, id_map=None ):
        if data_matrix == None:
            data_matrix = self.get_data_matrix()

        new_map = dict()

        print "rows: %s" % rows
        print "columns: %s" % columns

        reordered_rows = [x for x in xrange(data_matrix.shape[0]) if x not in rows]
        #print "reordered_rows: %s" % reordered_rows
        #kdrew: reordered_rows maps between new indices and old indices
        reordered_rows = rows + reordered_rows
        reordered_columns = columns + [x for x in xrange(data_matrix.shape[1]) if x not in columns]
        reordered_matrix = data_matrix[reordered_rows,:]
        #print reordered_matrix
        reordered_matrix = reordered_matrix[:,reordered_columns]

        #print "original rows: %s" % range(data_matrix.shape[0])
        #print "original columns: %s" % range(data_matrix.shape[1])
        #print "reordered_rows: %s" % reordered_rows
        #print "reordered_columns: %s" % reordered_columns

        index2name_map = self.get_name2index()
        for i in xrange(data_matrix.shape[0]):
            if id_map == None:
                new_map[i] = index2name_map[reordered_rows[i]]
            else:
                new_map[i] = id_map[reordered_rows[i]]

        return reordered_matrix, new_map




    #kdrew: get submatrix based on protein identifiers
    def get_subdata_matrix( self, ids, ignoreNonExistingIds=False):
        matrix = self.get_data_matrix()
        id_indices = []
        new_map = dict()
        j = 0
        for i,i_d in enumerate(ids):
            #print i, i_d
            try:
                index1 = self.__id_dict[i_d]
                if index1 not in id_indices:
                    id_indices.append(index1)
                    new_map[j] = i_d
                    j += 1
            except KeyError:
                if ignoreNonExistingIds:
                    print "get_subdata_matrix ignoring: %s" % (i_d,)
                    continue
                else:
                    raise


        #print "id_indices: %s mat_shape: %s" % (id_indices, matrix.shape[1], )
        assert matrix.shape[1] > 0, "no columns in matrix" 
        if len(id_indices) > 0:
            #kdrew: set ensures no duplicates, but I lose mapping
            return matrix[np.ix_(id_indices, range(0,matrix.shape[1]))], new_map
        else:
            return None, None
        
    #kdrew: reverses id_dict dictionary but will only keep one entry
    #kdrew: function name is confusing (consider changing to get_index2name) 
    #kdrew: format is dict{1:protid, 2:protid2}
    def get_name2index( self, ):
        return {v:k for k, v in self.__id_dict.items()}
    
    #kdrew: similar to above but key is index (int) and value is list of redundant protein ids
    def get_index2names(self,):
        id_map = dict()
        id_dict = self.get_id_dict()
        for key in id_dict:
            try:
                id_map[id_dict[key]].append(key)
            except KeyError:
                id_map[id_dict[key]] = [key]

        return id_map


    def get_data_matrix( self, remove_zero=False ):
        #print "get_data_matrix"
        #print self.__master_data_matrix

        ##kdrew: might want to return new msds object because can no longer map protein ids to indices of new matrix
        #if names != None:
        #   rows = []
        #   for name in names:
        #       #print "name: %s, index: %s" % (name, self.__master_name_list.index(name))
        #       rows.append(self.__id_dict[name]))
        #
        #   cols = range(0,self.__master_data_matrix.shape[1])
        #   submatrix = self.__master_data_matrix[np.ix_(rows, cols)]
        #
        #   #kdrew: only remove zero columns
        #   if remove_zero:
        #       submatrix = nu.remove_zero(submatrix, zero_rows=False, zero_columns=True)
        #
        #   return submatrix
        
        if remove_zero:
            return nu.remove_zero(self.__master_data_matrix, zero_rows=False, zero_columns=True)

        return self.__master_data_matrix

    def set_data_matrix( self, data_matrix ):
        self.__master_data_matrix = data_matrix


def read_datafile(fhandle, header=True):
    fraction_list = None
    if header:
        #kdrew: eat header
        line = fhandle.readline()
        print "HEADER: %s" % line
        assert line.split()[1] == 'TotalCount', "Error: missing column names, check --msblender_format in msblender2elution_profile.py"
        fraction_list = line.split()[2:]
    
    data = []
    name_list = []

    for line in fhandle.readlines():
        print line
        line_data = line.split()
        name_list.append(line_data[0])
        line_array = map(float,line_data[2:])
        logging.debug(line_array)
        data.append(line_array)

    #print data

    data_matrix = np.asmatrix(data)

    return data_matrix, name_list, fraction_list

#kdrew: fill_missing is used when one matrix has names (genes) that the other matrix does not have and missing entries needs to be filled for the other matrix
#kdrew: default is np.zeros but np.nan might be useful too
def concat_data_matrix(data_matrix1, name_list1, data_matrix2, name_list2, fill_missing=np.zeros):
    
    name_set1 = set(name_list1)
    name_set2 = set(name_list2)

    dm1_num_columns = data_matrix1.shape[1]
    dm2_num_columns = data_matrix2.shape[1]

    combined_set = name_set1.union(name_set2)
    logging.debug(combined_set)

    return_mat = None
    return_name_list = []
                        
    for name in combined_set:
        logging.debug("name: %s" % (name,))
        return_name_list.append(name)
        try:
            idx1 = name_list1.index(name)
            row1 = data_matrix1[idx1]
            logging.debug("idx1: %s" % (idx1,))
            logging.debug("row1: %s" % (row1,))
        except ValueError:
            #kdrew: not in list
            row1 = fill_missing(dm1_num_columns)

        try:
            idx2 = name_list2.index(name)
            row2 = data_matrix2[idx2]
        except ValueError:
            #kdrew: not in list
            row2 = fill_missing(dm2_num_columns)

        complete_row = np.append(np.array(row1), np.array(row2))
    

        #kdrew: add complete row to full matrix
        if return_mat == None:
            return_mat = np.matrix(complete_row)
        else:
            return_mat = np.vstack([return_mat,complete_row])

    return return_mat, return_name_list
    

def fill_missing_with_nans(num_of_cols):
    a = np.empty(num_of_cols)
    a.fill(np.nan)
    return a

