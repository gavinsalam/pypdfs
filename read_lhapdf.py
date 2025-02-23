#!/usr/bin/env python3
"""
Script to print out initial condition of an LHAPDF set. Usage:

    read_lhapdf.py -pdf <pdfset> [-flav <flavour>]
"""
import argparse
# for running processes
import subprocess
import yaml
import json
import numpy as np
from pdf_base import reformat, default_pdf
from yaml import load


# get the data directory as the output of lhapdf-config --datadir
data_dir = str(subprocess.check_output(['lhapdf-config', '--datadir']),encoding="utf-8").strip()

def main():

    parser = argparse.ArgumentParser(description='Read LHAPDF file and print out the initial condition')
    parser.add_argument('-pdf', type=str, default=default_pdf, dest="pdfset", help='PDF set name')
    parser.add_argument("-flav", "--flav", default=0, type=int, help="Flavour index (default of 0 prints all flavours)")
    parser.add_argument("-iQ", default=0, type=int, help="Index in Q to print in each block")
    parser.add_argument("-block", type=int, help="if present, print only the specified Q block")

    args = parser.parse_args()
    print(args.pdfset)

    pdf_dir = data_dir + '/' + args.pdfset
    print("# data_dir = ", data_dir)
    print("# pdf_dir = ", pdf_dir)

    info_file = f'{pdf_dir}/{args.pdfset}.info'
    with open(info_file, 'r') as stream:
        info = yaml.safe_load(stream)
        print("#", info.keys())

    data_file = f'{pdf_dir}/{args.pdfset}_0000.dat'    
    with open(data_file, 'r') as stream:
        
        iblock = -1
        while True:
            line = stream.readline()
            if line.strip() == "": break
            if not line.startswith("---"): continue

            iblock += 1
            if args.block is not None and iblock != args.block: continue

            # get the x, muF and flav arrays
            x_values = np.array(list(map(float, stream.readline().split())))
            if (len(x_values) == 0): break
            #print("# x_values = ", x_values)
            muF_values = np.array(list(map(float, stream.readline().split())))
            print("# muF_values = ", muF_values)
            flavs = np.array(list(map(int, stream.readline().split())))
            print("# flavs = ", flavs)

            tabulation = np.zeros((len(x_values), len(flavs), len(muF_values)))
            flavmap = dict(zip(flavs, range(len(flavs))))
            #print("# flavmap = ", flavmap)
            print("# tabulation.shape = ", tabulation.shape)
            for ix in range(len(x_values)):
                for imu in range(len(muF_values)):
                    tabulation[ix, :, imu] = np.array(list(map(float, stream.readline().split())))

            print(f"# tabulated PDF at muF={muF_values[args.iQ]}: ", end="")
            if args.flav == 0:
                print(f"x {[iflv for iflv in flavs]}")
                print(reformat(x_values, *[tabulation[:,iflv,args.iQ] for iflv in range(len(flavs))]))
            else:
                print(f"x {args.flav}")
                print(reformat(x_values, tabulation[:,flavmap[args.flav],args.iQ]))


if __name__ == '__main__':
    main()
    
