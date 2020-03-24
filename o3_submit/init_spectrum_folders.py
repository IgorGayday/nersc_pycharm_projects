#!/usr/bin/env python

import argparse
import copy
import itertools
import os
import shutil
import os.path as path
from typing import List

from SpectrumConfig import SpectrumConfig
            

def parse_command_line_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Creates a folder structure for calculations with a given config")
    parser.add_argument("-c", "--config", default="spectrumsdt.config", help="Path to configuration file")
    parser.add_argument("-rvo", "--rovib-only", action="store_true", help="Specify to generate only folders for rovibrational diagonalization")
    parser.add_argument("-J", type=int, required=False, help="J value (rotational quantum number) for current calculation")
    parser.add_argument("-K", type=int, required=False, help="Only folders for specified K value will be created")
    args = parser.parse_args()
    return args


def generate_paths(base_path: str, folder_names: List[List[str]]) -> List[str]:
    """ Generates all combinations of folders specified in folder_names. Returns a list of generated paths """
    name_combos = itertools.product(*folder_names)
    paths = list(map(lambda name_combo: path.join(base_path, *name_combo), name_combos))
    return paths


def generate_config_lines(folder_params: List[List[str]]) -> List[str]:
    """ Each folder has a specific config parameter associated with it. 
    In a similar to generate_paths fashion this function generates full combination of all params for each folder """
    param_combos = itertools.product(*folder_params)
    config_lines = list(map(lambda param_combo: "\n" + "\n".join(param_combo), param_combos))
    return config_lines


def create_paths(target_folders: List[str]):
    """ Creates all paths specified in target_folders """
    for folder in target_folders:
        if not path.exists(folder):
            os.makedirs(folder)


def multicopy_config(config_path: str, target_folders: List[str]) -> List[str]:
    """ Copies specified config file into specified list of directories. Returns a list of full paths to new configs """
    config_name = path.basename(config_path)
    new_config_paths = list(map(lambda folder: path.join(folder, config_name), target_folders))
    for new_path in new_config_paths:
        shutil.copyfile(config_path, new_path)
    return new_config_paths


def set_config_params(config_paths: List[str], config_lines: List[str]):
    """ Appends i-th config_lines to i-th config in config_paths """
    for i in range(len(config_paths)):
        with open(config_paths[i], "a") as config:
            config.write(config_lines[i])


def main():
    args = parse_command_line_args()
    config_path = path.abspath(args.config)
    base_path = path.dirname(config_path)

    config = SpectrumConfig(config_path)
    J = config.get_j()
    num_states_base = int(config.params["num_states"])
    num_states_p0 = num_states_base * (J + 1 - J % 2)
    num_states_p1 = num_states_base * (J + 1 - (J + 1) % 2)
    ncv_mult = 1.5

    folder_names = [["K_{0}"], ["even", "odd"], ["basis", "overlaps", "diagonalization", "properties"]]
    folder_params = [["K = {0}"], ["symmetry = 0", "symmetry = 1"], ["mode = basis", "mode = overlaps\nrovib_coupling = 1", "mode = diagonalization\nrovib_coupling = 0", 
        "mode = properties\nrovib_coupling = 0"]]

    folder_names_cor = [["K_all"], ["parity_0", "parity_1"], ["even", "odd"], ["diagonalization", "properties"]]
    folder_params_cor = [["K = all\nrovib_coupling = 1"], ["parity = 0\nnum_states = " + str(num_states_p0) + "\nbasis_size_arnoldi = " + str(int(num_states_p0 * ncv_mult)), 
        "parity = 1\nnum_states = " + str(num_states_p1) + "\nbasis_size_arnoldi = " + str(int(num_states_p1 * ncv_mult))], ["symmetry = 0", "symmetry = 1"], 
        ["mode = diagonalization", "mode = properties"]]

    target_folders = []
    config_lines = []
    if not args.rovib_only:
        basis_K = int(config.params["basis_K"]) if "fix_basis_jk" in config.params else -1
        K_range = range(basis_K, basis_K + 1) if "fix_basis_jk" in config.params else range(J + 1)
        for K in K_range:
            current_folder_names = copy.deepcopy(folder_names)
            current_folder_names[0][0] = current_folder_names[0][0].format(K)
            current_target_folders = generate_paths(base_path, current_folder_names)
            target_folders = target_folders + current_target_folders

            current_folder_params = copy.deepcopy(folder_params)
            current_folder_params[0][0] = current_folder_params[0][0].format(K)
            current_config_lines = generate_config_lines(current_folder_params)
            config_lines = config_lines + current_config_lines


    target_folders = target_folders + generate_paths(base_path, folder_names_cor)
    config_lines = config_lines + generate_config_lines(folder_params_cor)

    create_paths(target_folders)
    config_paths = multicopy_config(config_path, target_folders)
    set_config_params(config_paths, config_lines)


main()