#!/usr/bin/env python3
from __future__ import division
from __future__ import print_function
from builtins import range
from builtins import object
import argparse
import sys
from pdf_base import *

usage="""
  Usage:    ./pdf.py [-h] [options]

  Options
  -------

  -pdf  PDFname
  -Q    Q     
  -xmin xmin    
  -xmax xmax    
  -nx   nx
  -x-from-file FILENAME

  -flav flav1,flav2   (use PDG codes)
  -eval 'eval-string' (e.g. "flv(1)-flv(-1)" to get d-dbar)

  -a-stretch A        (default 5.0, indicates stretching of large-x region)

  -imem IMEM          just the given member
  -err                output the symm err
  -fullerr            output the full error info

  -out OUTPUT_FILE

  -info               (print info)

"""

import io
import sys
#import hfile # you may need to add ../aux to your path to get it (cf below for lhapdfPath)
import re
import numpy as np
from math import *

out = sys.stdout

a_stretch = 5.0


#----------------------------------------------------------------------        
def main():
    global a_stretch

    parser = argparse.ArgumentParser(description='Print out some aspect of a PDF')
    parser.add_argument('-pdf', type=str, default=default_pdf, help='PDF name')
    parser.add_argument('-imem', type=int, default=0, help='The member to examine')
    parser.add_argument('-err', action='store_true', help='Output the symm err')
    parser.add_argument('-fullerr', action='store_true', help='Output the full error info')
    parser.add_argument('-medianerr', action='store_true', help='use a median + interval uncertainty')

    parser.add_argument('-Q','-muF', type=float, default=100.0, help='Q')    
    parser.add_argument('-lnQ','-lnmuF', type=float, default=None, help='lnQ (overrides -Q)')
    parser.add_argument("-Qmin", type=float, default=0.0, help="Minimum Q value (if non-zero, overrides Q; typically one would then set xmin=xmax)")
    parser.add_argument("-Qmax", type=float, default=0.0, help="Maximum Q value (if non-zero, overrides Q; typically one would then set xmin=xmax)")
    
    parser.add_argument('-xmin', type=float, default=1e-4, help='xmin')
    parser.add_argument('-xmax', type=float, default=1.0, help='xmax')
    parser.add_argument('-nx', type=int, default=100, help='number of x values to print out (of Q values if used with -Qmin and -Qmax)')
    parser.add_argument('-x-from-file', type=str, default="", help='Read x values from file')
    parser.add_argument('-a-stretch', type=float, default=a_stretch, help='Stretching of large-x region')

    parser.add_argument('-flav', '-flv', type=str, default='1', 
                         help='Comma-separated list of PDG IDs of flavours to print (if the first one is negative do e.g. -flav=-1,1)')
    parser.add_argument('-eval', type=str, default="", help='Evaluation string, e.v. flv(1)+flv(-1) to get d+dbar')

    parser.add_argument('-out', type=str, default="", help='Output file (default is stdout)')
    parser.add_argument('-info', action='store_true', help='Include the contents of the PDF info file in the output')
    parser.add_argument('-prec', type=int, default=5, help='Number of digits of precision in printout (default 5)')

    # transfer arguments to local variables
    args = parser.parse_args()
    pdfname = args.pdf
    Q = args.Q
    if args.lnQ is not None: Q = exp(args.lnQ)

    if (args.Qmin == 0.0): args.Qmin = Q
    if (args.Qmax == 0.0): args.Qmax = Q

    xmin = args.xmin
    xmax = args.xmax
    nx = args.nx
    x_from_file = args.x_from_file
    #global a_stretch
    a_stretch = args.a_stretch
    imem = args.imem

    format="{{:<{}.{}g}}".format(args.prec+7,args.prec)

    flav = args.flav
    myEval = args.eval.split(',')
    if (myEval[0] != ""): 
        flavList = myEval
    else:
        flavList = flav.split(',')
        myEval = None

    print_info = args.info
    
    #-- send output to a file if requested
    if (args.out != ""):
        outName = args.out
        out = open(outName,'w')
    else:
        out = sys.stdout
    
    
    # now set up the pdf
    pdfset = lhapdf.getPDFSet(pdfname)
    #pdf=lhapdf.mkPDF(pdfname, 0)
    
    print("# "+" ".join(sys.argv), file=out)        
    
    # decide which x points to use
    if (x_from_file != ""):
        xs = get_x_from_file(x_from_file)
        nx = len(xs)
    else:
        xs=np.empty([nx])
        Qs = np.logspace(log10(args.Qmin), log10(args.Qmax), nx)
        #for ix in range(0,nx): xs[ix] = xmin*(xmax/xmin)**((1.0*ix)/(nx-1))
        zetamin=zeta_of_x(xmin)
        zetamax=zeta_of_x(xmax)
        for ix in range(0,nx): xs[ix] = x_of_zeta(zetamin + (zetamax-zetamin)*((1.0*ix)/max(1,nx-1)))
    

    if args.err:
        pdfs = pdfset.mkPDFs()
        pdf = pdfs[0]
    else:
        pdf = pdfset.mkPDF(imem)

    #-- print the header
    if args.Qmin == args.Qmax:
        print("# pdf = {}, Q = {}, alphas(Q) = {}, version = {}".format(
            pdfname,Q,pdf.alphasQ(Q), pdfset.dataversion), file=out)
        header = "# Columns: x"
    else:
        print("# pdf = {}, Qmin = {}, Qmax = {}, alphas(Qmin) = {}, version = {}".format(
            pdfname,args.Qmin,args.Qmax,pdf.alphasQ(args.Qmin), pdfset.dataversion), file=out)
        header = "# Columns: x Q"
    for flav in flavList:
        if (args.err):
            header += " x*flav({}) errsymm({})".format(flav,flav)
            if (args.fullerr): header += " bandlo({}) bandhi({})".format(flav,flav)
        else:
            header += " x*flav({})".format(flav)
    print(header, file=out)

    # and the x points
    flv = lambda iflav: pdf.xfxQ(int(iflav), xs[ix], Qs[ix])
    if (args.err):
    
        resfull=np.empty([nx,len(flavList),pdfset.size])
        if (args.fullerr):
            ncol=4
        else:
            ncol=2
        reserr=np.empty([nx,ncol*len(flavList)])
    
        for ix,x in enumerate(xs):
            for iflav,flav in enumerate(flavList):
                for ipdf,pdf in enumerate(pdfs):
                    if (myEval): resfull[ix,iflav,ipdf] = eval(myEval[iflav])
                    else:        resfull[ix,iflav,ipdf] = pdf.xfxQ(int(flav), xs[ix], Qs[ix])
                if (args.medianerr):
                    uncert = intervalUncert(resfull[ix,iflav,:])
                    reserr[ix,iflav*ncol  ] = uncert.central
                else:
                    uncert = pdfset.uncertainty(resfull[ix,iflav,:])
                    reserr[ix,iflav*ncol  ] = resfull[ix,iflav,0]
    
                reserr[ix,iflav*ncol+1] = uncert.errsymm
                if (args.fullerr):
                    reserr[ix,iflav*ncol+2] = uncert.central-abs(uncert.errminus)
                    reserr[ix,iflav*ncol+3] = uncert.central+uncert.errplus

        if args.Qmin == args.Qmax:
            print(reformat(xs, reserr, format=format), file=out)
        else:
            print(reformat(xs, Qs, reserr, format=format), file=out)   
    else:
        res=np.empty([nx,len(flavList)])
        print("", file=out)
        for ix,x in enumerate(xs):
            Q = Qs[ix]
            for iflav,flav in enumerate(flavList):
                if (myEval):
                    res[ix,iflav] = eval(myEval[iflav])
                else:
                    res[ix,iflav] = pdf.xfxQ(int(flav), x, Q)
        
        if args.Qmin == args.Qmax:
            print(reformat(xs, res, format=format), file=out)
        else:
            print(reformat(xs, Qs, res, format=format), file=out)   

    if (print_info): printInfo(pdfname)

#----------------------------------------------------------------------    
def get_x_from_file(filename):
    '''Ignores lines that start with a hash; and assumes that x values 
    are the first column
    '''
    xlist = []
    with open(filename,'r') as f:
        for line in f:
            line = line.strip()
            if (line[0] == '#' or len(line) == 0): continue
            values = line.split(' ')
            xlist.append(float(values[0]))
    return np.array(xlist)

def zeta_of_x(x):
    y = log(1.0/x)
    return  y + a_stretch*(1.0 - x)

def x_of_zeta(zeta):
    y = zeta
    eps = 1e-12
    maxiter = 100
    if (a_stretch != 0):
        for iter in range(0, maxiter+1):
            if (iter == maxiter):
                print("Could not solve x from zeta", file=sys.stderr)
                sys.exit(-1)
            x = exp(-y)
            diff_from_zero = zeta - y - a_stretch*(1.0-x)
            # we have found good solution
            if (abs(diff_from_zero) < eps): break
            deriv = -1.0  - a_stretch*x;
            y = y - diff_from_zero/deriv
          
    return exp(-y)


if __name__ == '__main__':
    main()
