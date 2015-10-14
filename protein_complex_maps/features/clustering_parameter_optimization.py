
import os
import argparse
import pickle
import random
import numpy as np
import pandas as pd
import itertools as it
import subprocess as sp
import multiprocessing as mp
import tempfile as tf

import protein_complex_maps.complex_comparison as cc

def main():

    parser = argparse.ArgumentParser(description="Finds optimal parameters for clustering of ppi network")
    parser.add_argument("--input_network", action="store", dest="input_network", required=True, 
                                    help="Filename of ppi network with optional edge weights (format: id\tid\tweight)")
    parser.add_argument("--gold_standard", action="store", dest="gold_standard_filename", required=True, 
                                    help="Filename of gold standard complexes, one cluster per line, ids tab-separated")
    parser.add_argument("--output_file", action="store", dest="output_file", required=False, default=None,
                                    help="Filename of output clusters for best set of parameters")
    parser.add_argument("--random_seed", action="store", type=int, dest="random_seed", required=False, default=None,
                                    help="Sets random seed (int), default=None")
    parser.add_argument("--bootstrap_iter", action="store", type=int, dest="bootstrap_iter", required=False, default=10,
                                    help="Number of bootstrap iterations (int, default=10)")
    parser.add_argument("--bootstrap_fraction", action="store", type=float, dest="bootstrap_fraction", required=False, default=0.5,
                                    help="Fraction of edges to sample for bootstrapping, default=0.5")
    parser.add_argument("--clusterone", action="store", dest="clustone_jar", required=False, 
                                    default="/home/kdrew/programs/clusterone/cluster_one-1.0.jar",
                                    help="Location of cluster_one jar file, default= /home/kdrew/programs/clusterone/cluster_one-1.0.jar")
    parser.add_argument("--clusterone_size", action="store", dest="clusterone_size", nargs='+', required=False, 
                                    default=[2,],
                                    help="ClusterOne Size parameter sweep, default = 2")
    parser.add_argument("--clusterone_density", action="store", dest="clusterone_density", nargs='+', required=False, 
                                    default=[.1,.25,.3,.35,], 
                                    help="ClusterOne Density parameter sweep, default = .1 .25 .3 .35")
    parser.add_argument("--clusterone_max_overlap", action="store", dest="clusterone_max_overlap", nargs='+', required=False, 
                                    default=[0.5,0.75,0.9], 
                                    help="ClusterOne max-overlap parameter sweep, default = 0.5 0.75 0.9")
    parser.add_argument("--clusterone_seed_method", action="store", dest="clusterone_seed_method", nargs='+', required=False, 
                                    default=['nodes'], 
                                    help="ClusterOne seed method parameter sweep (nodes, cliques, unused_nodes, edges, default = nodes")
    parser.add_argument("--ppi_fraction", action="store", dest="ppi_fraction", nargs='+', required=False, 
                                    default=[0.005,0.01,0.05,.1,.25,.5,.75,1.0], 
                                    help="Use top fraction for further clustering, default = 0.005 0.01 0.05 .1 .25 .5 .75 1.0")
    parser.add_argument("--eval_metric", action="store", dest="eval_metric", required=False, default='mmr',
                                    help="Evaluation metric used to determine best set of parameters (mmr, acc, sensitivity, ppv), default=mmr")
    parser.add_argument("--procs", action="store", type=int, dest="procs", required=False, default=1,
                                    help="Number processors to use (int), default=1)")

    args = parser.parse_args()

    #kdrew: read gold standard into list
    gstd_file = open(args.gold_standard_filename,"rb")
    gold_standard_complexes = []
    for line in gstd_file.readlines():
        gold_standard_complexes.append(line.split())


    #kdrew: original commandline for clusterone
    #java -jar ~/programs/clusterone/cluster_one-1.0.jar blake_bioplex_merge_wkeys_deduped_corum_train_labeled.libsvm0.scaleByTrain.resultWprob_pairs_noself_nodups_wprob.txt > blake_bioplex_merge_wkeys_deduped_corum_train_labeled.libsvm0.scaleByTrain.resultWprob_pairs_noself_nodups_wprob.txt.clusterone

    #kdrew: read in the input network into a string
    with open (args.input_network, "r") as input_network_file:
        #data=input_network_file.read().replace('\n', '')
        #input_network_str = input_network_file.read()
        input_network_list = input_network_file.readlines()

    random.seed(args.random_seed)
    #for i in range(args.bootstrap_iter):

    #kdrew: size and density are clusterOne parameters
    #size_sweep = [2,]
    #density_sweep=[.1,.25,.3,.35,]
    #kdrew: fraction is the fraction of top ppis to include
    #fraction_sweep=[0.005,0.01,0.05,.1,.25,.5,.75,1.0]

    size_sweep = args.clusterone_size
    overlap_sweep = args.clusterone_max_overlap
    seed_method_sweep = args.clusterone_seed_method
    density_sweep = args.clusterone_density
    fraction_sweep = args.ppi_fraction

    best_size = None
    best_density = None
    best_fraction = None
    best_overlap = None
    best_seed_method = None
    best_eval = None

    p = mp.Pool(args.procs)
    for size, density, fraction, overlap, seed_method in it.product(size_sweep, density_sweep, fraction_sweep, overlap_sweep, seed_method_sweep ):

        #kdrew: only take the topN ppis, assumes already sorted network (probably stupidly)
        sizeOfTopNetwork = int(len(input_network_list)*float(fraction))
        network_list = input_network_list[0:sizeOfTopNetwork]

        #kdrew: cluster network_list
        multiproc_input = (network_list, args, str(size), str(density), str(overlap), str(seed_method), 0)
        cluster_prediction, ii = cluster_helper( multiproc_input )
        
        #kdrew: compare gold standard vs predicted clusters
        cplx_comparison = cc.ComplexComparison(gold_standard_complexes, cluster_prediction) 

        metric_dict = dict()
        #metric_dict['acc'] = np.mean([result.acc() for result in cplx_comparisons])
        #metric_dict['sensitivity'] = np.mean([result.sensitivity() for result in cplx_comparisons])
        #metric_dict['ppv'] = np.mean([result.ppv() for result in cplx_comparisons])
        #metric_dict['mmr'] = np.mean([result.mmr() for result in cplx_comparisons])
        metric_dict['acc'] = cplx_comparison.acc() 
        metric_dict['sensitivity'] = cplx_comparison.sensitivity() 
        metric_dict['ppv'] = cplx_comparison.ppv() 
        metric_dict['mmr'] = cplx_comparison.mmr() 
        print "size %s, density %s, overlap %s, seed_method %s, fraction %s, acc %s, sensitivity %s, ppv %s, mmr %s" % (size, density, overlap, seed_method, fraction, metric_dict['acc'], metric_dict['sensitivity'], metric_dict['ppv'], metric_dict['mmr'])



        #kdrew: bootstrap by resampling portions of network
        sizeOfBootstrap = int(len(network_list)*args.bootstrap_fraction)
        #bootstrapped_networks = [random.sample(network_list,sizeOfBootstrap) for i in range(args.bootstrap_iter)]
        #kdrew: generate k shuffled networks
        shuffled_networks = [ sorted( network_list, key=lambda k: random.random() ) for i in range(args.bootstrap_iter)]
        #kdrew: split shuffled networks into partitions based on size of bootstrap
        bootstrapped_networks = [ sn[:sizeOfBootstrap] for sn in shuffled_networks ]
        bootstrapped_test_networks = [ sn[sizeOfBootstrap:] for sn in shuffled_networks ]

        multiproc_input = [(boot_net, args, str(size), str(density), str(overlap), str(seed_method), i) for i, boot_net in enumerate(bootstrapped_networks)]
        bootstrapped_cluster_predictions = p.map(cluster_helper, multiproc_input)

        #kdrew: compare full clustered set vs bootstrapped clusters
        multiproc_input = [(cluster_prediction, predicted_clusters, bootstrapped_test_networks[i]) for predicted_clusters, i in bootstrapped_cluster_predictions]
        bootstrap_cplx_cmp_metrics = p.map(comparison_helper, multiproc_input) 
        for boot_cmp in bootstrap_cplx_cmp_metrics:
            print "bootstrapped: size %s, density %s, overlap %s, seed_method %s, fraction %s, acc %s, sensitivity %s, ppv %s, mmr %s, ppi_recovered %s" % (size, density, overlap, seed_method, fraction, boot_cmp['acc'], boot_cmp['sensitivity'], boot_cmp['ppv'], boot_cmp['mmr'], boot_cmp['percent_ppi_recovered'])


        #kdrew: keeping track of the best parameter set
        if best_eval == None or best_eval < metric_dict[args.eval_metric]: 
            best_eval = metric_dict[args.eval_metric]
            best_size = size
            best_density = density
            best_overlap = overlap
            best_seed_method = seed_method
            best_fraction = fraction




    #kdrew: only take the topN ppis, assumes already sorted network (probably stupidly)
    sizeOfTopNetwork_best = int(len(input_network_list)*float(best_fraction))
    network_list_best = input_network_list[0:sizeOfTopNetwork_best]

    #kdrew: cluster network_list
    multiproc_input_best = (network_list_best, args, str(best_size), str(best_density), str(best_overlap), str(best_seed_method), 0)
    cluster_prediction_best, ii = cluster_helper( multiproc_input_best )

    
    if args.output_file != None:
        with open (args.output_file, "w") as output_file:
            for cluster in cluster_prediction_best:
                output_file.write(' '.join(cluster))
                output_file.write("\n")

        
    p.close()
    p.join()



#kdrew: helper function that compares two sets of complexes/clusters, for use in multiprocessor
#kdrew: first parameter in tuple is the gold standard and second is the predicted clusters
def comparison_helper(parameter_tuple):

    gold_std = parameter_tuple[0]
    pred_clst = parameter_tuple[1]
    #kdrew: test_net is the other half of the bootstrap which is used for testing
    test_net = parameter_tuple[2]
    ppi_recovered_count = 0
    for ppi in test_net:
        prot1 = ppi.split()[0]
        prot2 = ppi.split()[1]
        for clst in pred_clst:
            if prot1 in clst and prot2 in clst:
                ppi_recovered_count += 1
                #kdrew: only count the ppi once if found in cluster
                break

    cplx_cmp = cc.ComplexComparison(gold_std, pred_clst) 
    d = dict()
    d['acc'] = cplx_cmp.acc()
    d['sensitivity'] = cplx_cmp.sensitivity()
    d['ppv'] = cplx_cmp.ppv()
    d['mmr'] = cplx_cmp.mmr()
    d['percent_ppi_recovered'] = (1.0*ppi_recovered_count) / len(ppi)

    return d

def cluster_helper(parameter_tuple):
    input_network_list = parameter_tuple[0]
    args = parameter_tuple[1]
    size = parameter_tuple[2]
    density = parameter_tuple[3]
    overlap = parameter_tuple[4]
    seed_method = parameter_tuple[5]
    i = parameter_tuple[6]

    #kdrew: create temp file for bootstrapped input network, clusterone requires a file input
    fileTemp = tf.NamedTemporaryFile(delete=False)
    try:
        #kdrew: write input_network or bootstrapped input network to temp file
        #fileTemp.write(input_network_str)
        for bstrap_ppi in input_network_list:
            fileTemp.write(bstrap_ppi)
        fileTemp.close()

        #kdrew: run clustering
        proc = sp.Popen(['java', '-jar', args.clustone_jar, fileTemp.name, '-s', size, '-d', density, '--max-overlap', overlap, '--seed-method', seed_method], stdout=sp.PIPE, stderr=sp.PIPE)
        clustone_out, err = proc.communicate()

    finally:
        os.remove(fileTemp.name)

    #kdrew: take output of cluster one (predicted clusters) and store them into list
    predicted_clusters = []
    for line in clustone_out.split('\n'):
        if len(line.split() ) > 0:
            predicted_clusters.append(line.split())


    return predicted_clusters, i


if __name__ == "__main__":
    main()

