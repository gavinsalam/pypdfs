#!/usr/bin/env python
from __future__ import division
from __future__ import print_function
from builtins import range
from builtins import object
import argparse

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
import subprocess
#import hfile # you may need to add ../aux to your path to get it (cf below for lhapdfPath)
import re
import numpy as np
import cmdline
from math import *
# figure out where lhapdf's python package is hiding
lhapdfPath = str(subprocess.Popen(["lhapdf-config", "--prefix"],
                            stdout=subprocess.PIPE).communicate()[0].rstrip())
lhapdfPath += "/lib/python{}.{}/site-packages".format(sys.version_info[0],sys.version_info[1])
# include it in the python path
sys.path = [lhapdfPath] + sys.path
#sys.path.append(lhapdfPath)
import lhapdf

out = sys.stdout

names = {
    1 : r"$d$",
    2 : r"$u$",
    3 : r"$s$",
    4 : r"$c$",
    5 : r"$b$",
    6 : r"$t$",
   -1 : r"$\bar d$",
   -2 : r"$\bar u$",
   -3 : r"$\bar s$",
   -4 : r"$\bar c$",
   -5 : r"$\bar b$",
   -6 : r"$\bar t$",
   21 : r"$g$",
   22 : r"$\gamma$"
    }

a_stretch = 5.0
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

#----------------------------------------------------------------------
# a set of routines for getting percentile-based estimates -- not
# optimally efficient because median and errsym both do a sort...
def percentile(perc, sorted_values):
    n = len(sorted_values) - 1
    loc = n*perc
    iloc = int(n*perc)
    w2 = (loc-iloc)
    w1 = 1.0 - w2
    return sorted_values[iloc] * w1 + sorted_values[iloc + 1] * w2


class intervalUncert(object):
    """\
    A structure that mirrors the PDFUncertainty class from LHAPDF, but using
    interval-based uncertainties
    """
    def __init__(self,values):
        n = len(values)
        sorted_values = np.sort(values[1:])
        self.central = percentile(0.50, sorted_values)
        onesigma = 0.682689492137
        percentile_lo = (1 - onesigma)/2.0
        percentile_hi = 1 - percentile_lo
        self.errplus  = percentile(percentile_hi, sorted_values) - self.central
        # apparently errminus is defined as positive in LHAPDF...
        self.errminus = self.central - percentile(percentile_lo, sorted_values)
        self.errsymm  = 0.5 * (self.errplus + abs(self.errminus))

#----------------------------------------------------------------------
def reformat(*columns, **keyw):
  """returns a string containing each of the columns placed
      side by side. If instead of columns, 2d numpy arrays
      are supplied, then these are output sensibly too

      For now, it assumes that columns are numpy arrays,
      but this could in principle be relaxed.

      Among the keyword arguments, the only one currently supported is
      "format", which should be a string used to format the output

  """

  ncol = len(columns)
  shapes = []
  ncols  = []
  for i in range(ncol):
    shapes.append(columns[i].shape)
    if    (len(shapes[i]) == 1): ncols.append(0)
    elif  (len(shapes[i]) == 2): ncols.append(shapes[i][1])
    else: raise Error(" a 'column' appears not to be 1 or 2-dimensional" )

  # lazily assume that all lengths are the same
  nlines = shapes[0][0]

  #output = io.BytesIO()
  output = io.StringIO()
  if ("format" in keyw):
    frm=keyw["format"]

    for i in range(nlines) :
      for j in range(ncol):
        if (ncols[j] == 0): print(frm.format(columns[j][i]), end=' ', file=output)    # trailing comma kills newline
        else: 
          for k in range (ncols[j]):
            print(frm.format(columns[j][i,k]), end=' ', file=output)
      print(file=output)
  else:
    for i in range(nlines) :
      for j in range(ncol):
        if (ncols[j] == 0): print(columns[j][i], end=' ', file=output)    # trailing comma kills newline
        else: 
          for k in range (ncols[j]):
            print(columns[j][i,k], end=' ', file=output)
      print(file=output)
      
  return output.getvalue()

#----------------------------------------------------------------------        
def main():
    global a_stretch

    parser = argparse.ArgumentParser(description='Print out some aspect of a PDF')
    parser.add_argument('-pdf', type=str, default="MSHT20nnlo_as118", help='PDF name')

    parser.add_argument('-Q', type=float, default=100.0, help='Q')    
    parser.add_argument('-xmin', type=float, default=1e-4, help='xmin')
    parser.add_argument('-xmax', type=float, default=1.0, help='xmax')
    parser.add_argument('-nx', type=int, default=100, help='number of x values to print out (of Q values if used with -Qmin and -Qmax)')
    parser.add_argument('-x-from-file', type=str, default="", help='Read x values from file')

    parser.add_argument("-Qmin", type=float, default=0.0, help="Minimum Q value (if non-zero, overrides Q; typically one would then set xmin=xmax)")
    parser.add_argument("-Qmax", type=float, default=0.0, help="Maximum Q value (if non-zero, overrides Q; typically one would then set xmin=xmax)")

    parser.add_argument('-flav', '-flv', type=str, default='1', 
                         help='Comma-separated list of PDG IDs of flavours to print (if the first one is negative do e.g. -flav=-1,1)')
    parser.add_argument('-eval', type=str, default="", help='Evaluation string, e.v. flv(1)+flv(-1) to get d+dbar')
    parser.add_argument('-a-stretch', type=float, default=a_stretch, help='Stretching of large-x region')
    parser.add_argument('-imem', type=int, default=0, help='The member to examine')
    parser.add_argument('-err', action='store_true', help='Output the symm err')
    parser.add_argument('-fullerr', action='store_true', help='Output the full error info')
    parser.add_argument('-medianerr', action='store_true', help='use a median + interval uncertainty')
    parser.add_argument('-out', type=str, default="", help='Output file (default is stdout)')
    parser.add_argument('-info', action='store_true', help='Include the contents of the PDF info file in the output')
    parser.add_argument('-prec', type=int, default=5, help='Number of digits of precision in printout (default 5)')

    # transfer arguments to local variables
    args = parser.parse_args()
    pdfname = args.pdf
    Q = args.Q

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

    # if (cmdline.present("-h")):
    #     print(usage)
    #     sys.exit(0)
    
    #-- send output to a file if requested
    if (args.out != ""):
        outName = cmdline.value("-out")
        out = open(outName,'w')
    else:
        out = sys.stdout
    
    
    # now set up the pdf
    pdfset = lhapdf.getPDFSet(pdfname)
    #pdf=lhapdf.mkPDF(pdfname, 0)
    
    print("# "+cmdline.cmdline(), file=out)        
    
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
    '''
    xlist = []
    with open(filename,'r') as f:
        for line in f:
            line = line.strip()
            if (line[0] == '#' or len(line) == 0): continue
            values = line.split(' ')
            xlist.append(float(values[0]))
    return np.array(xlist)

#----------------------------------------------------------------------
def printInfo(pdfname):
    # find out location of data
    lhapdfData = subprocess.Popen(["lhapdf-config", "--datadir"],
                                  stdout=subprocess.PIPE).communicate()[0].decode('utf-8').rstrip()
    # read and print the file
    with open("{0}/{1}/{1}.info".format(str(lhapdfData),pdfname),'r') as ff:
        contents = ff.read()
        print(contents)


if __name__ == '__main__':
    main()
