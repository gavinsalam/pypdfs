#!/usr/bin/env python3

import argparse
from pdf_base import *
import lumi

def main():
    parser = argparse.ArgumentParser(description='Print the lumi-derived rapidity distribution')
    parser.add_argument('-pdf', type=str, default=default_pdf, help='PDF name')
    parser.add_argument('-err', action='store_true', help='Output the symm err')
    parser.add_argument('-imem', type=int, default=0, help='The member to examine')

    parser.add_argument("-rts", type=float, default=default_rts, help='Centre of mass energy (rts), in GeV')
    parser.add_argument("-mass", type=float, default=100.0, help='mass of system being produced')
    parser.add_argument("-flav1", "-flv1", type=int, default= 1, help="flavour from proton with +ve pz")
    parser.add_argument("-flav2", "-flv2", type=int, default=-1, help="flavour from proton with -ve pz")
    parser.add_argument("-eval", type=str, help="a string such as g1*g2 or sigma1*g or qqbar=2*(d1*dbar2+u1*ubar2+...)")

    parser.add_argument('-out', '-o', type=str, dest="out", default="", help='Output file (default is stdout)')
    parser.add_argument('-prec', type=int, default=5, help='Number of digits of precision in printout (default 5)')

    args = parser.parse_args()

    pdfname = args.pdf
    pdfset = lhapdf.getPDFSet(pdfname)
    if args.err:
        pdfs = pdfset.mkPDFs()
        pdf = pdfs[0]
    else:
        pdf = pdfset.mkPDF(args.imem)


    if (args.out != ""):
        outName = args.out
        out = open(outName,'w')
    else:
        out = sys.stdout
    format="{{:<{}.{}g}}".format(args.prec+7,args.prec)


    print("#", " ".join(sys.argv), file=out)
    print(f"# pdf = {pdfname}, imem = {args.imem}, rts = {args.rts}, mass = {args.mass}, pdf_version = {pdfset.dataversion}", file=out)
    print(f"# rapidity", lumi.lumi_description(args.flav1,args.flav2,args.eval), file=out)

    lumi_res = lumi.lumi(pdf, args.mass, args.rts, args.flav1, args.flav2, args.eval, return_Lumi=True)
    print(reformat(lumi_res.yvals[::-1], lumi_res.dlumi[::-1], format=format), file=out)


if __name__ == '__main__': main()