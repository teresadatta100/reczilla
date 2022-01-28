#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

@author: Simone Boglio
"""

import os
import numpy as np
import Data_manager.Utility as ut
import scipy.sparse as sps

from Data_manager.Gowalla.GowallaReader import GowallaReader as GowallaReader_DataManager
from Data_manager.split_functions.split_train_validation import split_train_validation_test_negative_leave_one_out_user_wise
from Data_manager.split_functions.split_train_validation import split_train_validation_leave_one_out_user_wise
from Data_manager.split_functions.split_data_on_timestamp import split_data_on_timestamp

from Data_manager.IncrementalSparseMatrix import IncrementalSparseMatrix
from Data_manager.load_and_save_data import save_data_dict_zip, load_data_dict_zip
from Data_manager.Utility import filter_urm
from Conferences.IJCAI.ConvNCF_github.Dataset import Dataset as Dataset_github



class GowallaReader:

    DATASET_NAME = "Gowalla"
    DATASET_URL = "https://polimi365-my.sharepoint.com/:u:/g/personal/10322330_polimi_it/EbAK6lYNM6NMh-b5tDUDC-kBxGLQkLmQYm0dXWuHaykQrQ?e=IOzbTW"

    URM_DICT = {}
    ICM_DICT = {}

    def __init__(self, pre_splitted_path):

        pre_splitted_path += "data_split/"
        pre_splitted_filename = "splitted_data_"

        # If directory does not exist, create
        if not os.path.exists(pre_splitted_path):
            os.makedirs(pre_splitted_path)

        try:
            print("Dataset_{}: Attempting to load pre-splitted data".format(self.DATASET_NAME))

            for attrib_name, attrib_object in load_data_dict_zip(pre_splitted_path, pre_splitted_filename).items():
                self.__setattr__(attrib_name, attrib_object)


        except FileNotFoundError:


            print("Dataset_{}: Pre-splitted data not found, building new one".format(self.DATASET_NAME))

            compressed_file_folder = "Conferences/IJCAI/ConvNCF_github/Data/"
            decompressed_file_folder = "Data_manager_split_datasets/Gowalla/"

            # compressed_file = tarfile.open(compressed_file_folder + "gowalla.test.negative.gz", "r:gz")
            # compressed_file.extract("yelp.test.negative", path=decompressed_file_folder + "decompressed/")
            # compressed_file.close()
            #
            # compressed_file = tarfile.open(compressed_file_folder + "gowalla.test.rating.gz", "r:gz")
            # compressed_file.extract("yelp.test.rating", path=decompressed_file_folder + "decompressed/")
            # compressed_file.close()
            #
            # compressed_file = tarfile.open(compressed_file_folder + "gowalla.train.rating.gz", "r:gz")
            # compressed_file.extract("yelp.train.rating", path=decompressed_file_folder + "decompressed/")
            # compressed_file.close()



            # if original:

            Dataset_github.load_rating_file_as_list = Dataset_github.load_training_file_as_matrix

            try:
                dataset = Dataset_github(compressed_file_folder + "gowalla")

            except FileNotFoundError as exc:

                print("Dataset_{}: Gowalla files not found, please download them and put them in this folder '{}', url: {}".format(self.DATASET_NAME, compressed_file_folder, self.DATASET_URL))
                print("Dataset_{}: Uncompressed files not found, please manually decompress the *.gz files in this folder: '{}'".format(self.DATASET_NAME, compressed_file_folder))

                raise exc


            URM_train_original, URM_test = dataset.trainMatrix, dataset.testRatings

            n_users = max(URM_train_original.shape[0], URM_test.shape[0])
            n_items = max(URM_train_original.shape[1], URM_test.shape[1])

            URM_train_original = sps.csr_matrix(URM_train_original, shape=(n_users, n_items))
            URM_test = sps.csr_matrix(URM_test, shape=(n_users, n_items))

            URM_train_original.data = np.ones_like(URM_train_original.data)
            URM_test.data = np.ones_like(URM_test.data)

            URM_test_negatives_builder = IncrementalSparseMatrix(n_rows=n_users, n_cols=n_items)

            n_negative_samples = 999
            for user_index in range(len(dataset.testNegatives)):
                user_test_items = dataset.testNegatives[user_index]
                if len(user_test_items) != n_negative_samples:
                    print("user id: {} has {} negative items instead {}".format(user_index, len(user_test_items), n_negative_samples))
                URM_test_negatives_builder.add_single_row(user_index, user_test_items, data=1.0)

            URM_test_negative = URM_test_negatives_builder.get_SparseMatrix().tocsr()
            URM_test_negative.data = np.ones_like(URM_test_negative.data)

            URM_train, URM_validation = split_train_validation_leave_one_out_user_wise(URM_train_original.copy(), verbose=False)


            #
            #
            # # NOT USED
            # # elif not time_split: #create from full dataset with random leave one out from LINKED dateset in the article since timestamp is not present.
            # #
            # #     data_reader = GowallaGithubReader_DataManager()
            # #     loaded_dataset = data_reader.load_data()
            # #
            # #     URM_all = loaded_dataset.get_URM_all()
            # #
            # #     URM_all.eliminate_zeros()
            # #
            # #     URM_all.data = np.ones_like(URM_all.data)
            # #
            # #     #use this function 2 time because the order could change slightly the number of final interactions
            # #     #with this order we get the same number of interactions as in the paper
            # #     URM_all = filter_urm(URM_all, user_min_number_ratings=0, item_min_number_ratings=10)
            # #     URM_all = filter_urm(URM_all, user_min_number_ratings=2, item_min_number_ratings=0)
            # #
            # #     URM_train, URM_validation, URM_test, URM_negative = split_train_validation_test_negative_leave_one_out_user_wise(URM_all, negative_items_per_positive=999,
            # #                                                                                                                                          at_least_n_train_items_test=0, at_least_n_train_items_validation=0,
            # #                                                                                                                                          verbose=True)
            # #     URM_timestamp = sps.csc_matrix(([],([],[])), shape=URM_train.shape)
            #
            # else: # create from full dataset with leave out one time wise from ORIGINAL full dateset
            #     data_reader = GowallaReader_DataManager()
            #     loaded_dataset = data_reader.load_data()
            #
            #     URM_all = loaded_dataset.get_URM_all()
            #
            #     # use this function 2 time because the order could change slightly the number of final interactions
            #     # with this order we get the same number of interactions as in the paper
            #     URM_all = filter_urm(URM_all, user_min_number_ratings=0, item_min_number_ratings=10)
            #     URM_all = filter_urm(URM_all, user_min_number_ratings=2, item_min_number_ratings=0)
            #
            #     URM_timestamp = URM_all.copy()
            #     URM_all.data = np.ones_like(URM_all.data)
            #
            #     URM_train, URM_validation, URM_test, URM_negative = split_data_on_timestamp(URM_all, URM_timestamp, negative_items_per_positive=999)
            #     URM_train = URM_train + URM_validation
            #     URM_train, URM_validation = split_train_validation_leave_one_out_user_wise(URM_train, verbose=False)


            self.URM_DICT = {
                "URM_train": URM_train,
                "URM_test": URM_test,
                "URM_validation": URM_validation,
                "URM_test_negative": URM_test_negative,
            }

            save_data_dict_zip(self.URM_DICT, self.ICM_DICT, pre_splitted_path, pre_splitted_filename)


        print("{}: Dataset loaded".format(self.DATASET_NAME))

        ut.print_stat_datareader(self)
