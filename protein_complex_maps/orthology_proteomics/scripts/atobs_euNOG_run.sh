
PROJECT_DIR=/project/cmcwhite/protein_complex_maps/protein_complex_maps/orthology_proteomics/

#Downsampling neg to match pos


#Done in command line in /corum folder
#sort -R nonredundant_allComplexesCore_mammals_euNOG_merged06.neg_train_ppis.txt | head -12679 > nonredundant_allComplexesCore_mammals_euNOG_merged06.neg_train_ppis_12679.txt
#sort -R nonredundant_allComplexesCore_mammals_euNOG_merged06.neg_ppis.txt | head -12679 > nonredundant_allComplexesCore_mammals_euNOG_merged06.neg_ppis_12679.txt

#This produces a file at this the same size as $PROJECT_DIR/interaction_network/atobs_euNOG_corum_train_labeled.txt
#claire: add label train

#ALREADY RUN
#python /project/cmcwhite/protein_complex_maps/protein_complex_maps/features/add_label.py --input_feature_matrix $PROJECT_DIR/correlation_elutions/atobs_pval_euNOG_feature_matrix.txt --input_positives $PROJECT_DIR/corum/nonredundant_allComplexesCore_mammals_euNOG_merged06.train_ppis.txt --input_negatives $PROJECT_DIR/corum/nonredundant_allComplexesCore_mammals_euNOG_merged06.neg_train_ppis_12679.txt --id_columns ID1 ID2 --output_file $PROJECT_DIR/interaction_network/atobs_euNOG_corum_train_downsamp_labeled.txt --fillna 0.0 --sep ,

echo "Label added"

#claire: add label test
#This is probably unused
#python /project/cmcwhite/protein_complex_maps/protein_complex_maps/features/add_label.py --input_feature_matrix $PROJECT_DIR/correlation_elutions/atobs_pval_euNOG_feature_matrix.txt --input_positives  $PROJECT_DIR/corum/nonredundant_allComplexesCore_mammals_euNOG_merged06.ppis.txt --input_negatives  $PROJECT_DIR/corum/nonredundant_allComplexesCore_mammals_euNOG_merged06.neg_ppis_12679.txt --id_columns ID1 ID2 --output_file $PROJECT_DIR/interaction_network/atobs_euNOG_corum_downsamp_labeled.txt --fillna 0.0 --sep ,

python /project/cmcwhite/protein_complex_maps/protein_complex_maps/features/feature2libsvm.py --input_feature_matrix $PROJECT_DIR/interaction_network/atobs_euNOG_corum_train_downsamp_labeled.txt --output_file $PROJECT_DIR/interaction_network/atobs_euNOG_corum_train_downsamp_labeled.libsvm1.txt --features pvalcorrmin10_atobs_long_euNOG_concat.txt_ln_pairs pvalcorrmin1_atobs_long_euNOG_concat_ln_pairs pvalcorrmin2_atobs_long_euNOG_concat_ln_pairs pvalcorrmin3_atobs_long_euNOG_concat_ln_pairs pvalcorrmin4_atobs_long_euNOG_concat_ln_pairs pvalcorrmin5_atobs_long_euNOG_concat_ln_pairs pvalcorrmin6_atobs_long_euNOG_concat_ln_pairs pvalcorrmin7_atobs_long_euNOG_concat_ln_pairs pvalcorrmin8_atobs_long_euNOG_concat_ln_pairs pvalcorrmin9_atobs_long_euNOG_concat_ln_pairs arath_euNOG_concat.txt.corr_poisson atobs_euNOG_concat.txt.corr_poisson At_Col_0_indark_201505_raw_wide_elution_arath_euNOG.txt.corr_poisson At_Col_0_indark_fraction_201504_raw_wide_elution_arath_euNOG.txt.corr_poisson At_Col_0_leaf_fraction_2014_raw_wide_elution_arath_euNOG.txt.corr_poisson At_Col_0_leaf_fraction_2015_raw_wide_elution_arath_euNOG.txt.corr_poisson braol_euNOG_concat.txt.corr_poisson BroccoliNE_WWC_raw_wide_elution_braol_euNOG.txt.corr_poisson Broccolinuclei_6-2016_raw_wide_elution_braol_euNOG.txt.corr_poisson OP_SelaginellaSEC_20160309_raw_wide_elution_selml_euNOG.txt.corr_poisson orsyj_RiceL_IEX_raw_wide_elution_orysj_euNOG.csv_concat.txt.corr_poisson Rice_201505_uniprot_raw_wide_elution_orysj_euNOG.txt.corr_poisson RiceL_IEX_raw_wide_elution_orysj_euNOG.txt.corr_poisson selaginella_WWC_raw_wide_elution_selml_euNOG.txt.corr_poisson selml_euNOG_concat.txt.corr_poisson traes_euNOG_concat.txt.corr_poisson wgIEF_raw_wide_elution_traes_euNOG.txt.corr_poisson wgSEC1_raw_wide_elution_traes_euNOG.txt.corr_poisson wheatgermIEX_raw_wide_elution_traes_euNOG.txt.corr_poisson WheatGermSEC_07-2015_raw_wide_elution_traes_euNOG.txt.corr_poisson --label_column label --keep_labels -1 1 --sep ,




#claire: convert to libsvm format unlabeled set and test set

python -u /project/cmcwhite/protein_complex_maps/protein_complex_maps/features/feature2libsvm.py --input_feature_matrix $PROJECT_DIR/interaction_network/atobs_euNOG_corum_train_downsamp_labeled.txt --output_file $PROJECT_DIR/interaction_network/atobs_euNOG_corum_train_downsamp_labeled.libsvm0.txt --features pvalcorrmin10_atobs_long_euNOG_concat.txt_ln_pairs pvalcorrmin1_atobs_long_euNOG_concat_ln_pairs pvalcorrmin2_atobs_long_euNOG_concat_ln_pairs pvalcorrmin3_atobs_long_euNOG_concat_ln_pairs pvalcorrmin4_atobs_long_euNOG_concat_ln_pairs pvalcorrmin5_atobs_long_euNOG_concat_ln_pairs pvalcorrmin6_atobs_long_euNOG_concat_ln_pairs pvalcorrmin7_atobs_long_euNOG_concat_ln_pairs pvalcorrmin8_atobs_long_euNOG_concat_ln_pairs pvalcorrmin9_atobs_long_euNOG_concat_ln_pairs arath_euNOG_concat.txt.corr_poisson atobs_euNOG_concat.txt.corr_poisson At_Col_0_indark_201505_raw_wide_elution_arath_euNOG.txt.corr_poisson At_Col_0_indark_fraction_201504_raw_wide_elution_arath_euNOG.txt.corr_poisson At_Col_0_leaf_fraction_2014_raw_wide_elution_arath_euNOG.txt.corr_poisson At_Col_0_leaf_fraction_2015_raw_wide_elution_arath_euNOG.txt.corr_poisson braol_euNOG_concat.txt.corr_poisson BroccoliNE_WWC_raw_wide_elution_braol_euNOG.txt.corr_poisson Broccolinuclei_6-2016_raw_wide_elution_braol_euNOG.txt.corr_poisson OP_SelaginellaSEC_20160309_raw_wide_elution_selml_euNOG.txt.corr_poisson orsyj_RiceL_IEX_raw_wide_elution_orysj_euNOG.csv_concat.txt.corr_poisson Rice_201505_uniprot_raw_wide_elution_orysj_euNOG.txt.corr_poisson RiceL_IEX_raw_wide_elution_orysj_euNOG.txt.corr_poisson selaginella_WWC_raw_wide_elution_selml_euNOG.txt.corr_poisson selml_euNOG_concat.txt.corr_poisson traes_euNOG_concat.txt.corr_poisson wgIEF_raw_wide_elution_traes_euNOG.txt.corr_poisson wgSEC1_raw_wide_elution_traes_euNOG.txt.corr_poisson wheatgermIEX_raw_wide_elution_traes_euNOG.txt.corr_poisson WheatGermSEC_07-2015_raw_wide_elution_traes_euNOG.txt.corr_poisson --label_column label --keep_labels 0 --sep ,



#Next two in parallel too
#claire: scale training
/home/kdrew/programs/libsvm-3.20/svm-scale -s $PROJECT_DIR/interaction_network/atobs_euNOG_corum_train_downsamp_labeled.libsvm1.scale_parameters $PROJECT_DIR/interaction_network/atobs_euNOG_corum_train_downsamp_labeled.libsvm1.txt > $PROJECT_DIR/interaction_network/atobs_euNOG_corum_train_downsamp_labeled.libsvm1.scale.txt

#claire: scale unlabeled (w/ test set) by trainâscale parameters
/home/kdrew/programs/libsvm-3.20/svm-scale -r $PROJECT_DIR/interaction_network/atobs_euNOG_corum_train_downsamp_labeled.libsvm1.scale_parameters $PROJECT_DIR/interaction_network/atobs_euNOG_corum_train_downsamp_labeled.libsvm0.txt > $PROJECT_DIR/interaction_network/atobs_euNOG_corum_train_downsamp_labeled.libsvm0.scaleByTrain.txt


##claire: parameter sweep using training set
python /home/kdrew/programs/libsvm-3.20/tools/grid.py $PROJECT_DIR/interaction_network/atobs_euNOG_corum_train_downsamp_labeled.libsvm1.scale.txt

