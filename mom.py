#!/usr/bin/env python3
#
# Usage:
#
#   ./mom.py [-pdf PDF] [-flav iflv]  [-Q-lo LO] [-Q-hi HI] [-nQ N] \
#            [{-err | -fullerr} [-do-latex]] [-out OUT]
#
# 
from __future__ import division
from __future__ import print_function
from builtins import range
import sys
import subprocess
#import hfile # you may need to add ../aux to your path to get it (cf below for lhapdfPath)
import re
import numpy as np
import cmdline
from math import *
# figure out where lhapdf's python package is hiding
#lhapdfPath = subprocess.Popen(["lhapdf-config", "--prefix"],
#                            stdout=subprocess.PIPE).communicate()[0].rstrip()
#lhapdfPath += "/lib/python{}.{}/site-packages".format(sys.version_info[0],sys.version_info[1])
# include it in the python path
#sys.path = [lhapdfPath] + sys.path
#sys.path.append(lhapdfPath)
import lhapdf
import pdf as mypdf

out = sys.stdout

myEval= cmdline.value("-eval","")


#----------------------------------------------------------------------
def mom(pdf, Q, iflav, xmin = None):
    if (xmin is None):
        ymax = -log(pdf.xMin)
    else:
        ymax = -log(xmin)
    # these settings should be accurate enough for most
    # purposes
    dy_min = 0.1
    ny_min = 100
    ny = max(ny_min, int(ymax/dy_min))
    dy = ymax/ny
    flv = lambda iflav: pdf.xfxQ(int(iflav), x, Q)
    
    x_pdf = np.zeros(ny+1)
    for iy in range(0,ny+1):
        x = exp(-dy*iy)
        if (myEval): x_pdf[iy] = x * eval(myEval)
        else:        x_pdf[iy] = x * pdf.xfxQ(iflav, x, Q)
        
    mom = x_pdf.sum() * dy
    return mom
    
#-- send output to a file if requested
if (cmdline.present("-out")):
    outName = cmdline.value("-out")
    out = open(outName,'w')

#-- get basic parameters
pdfname = cmdline.value("-pdf","MSHT20nnlo_as118")
#flav=cmdline.value("-flav",21)
Q_lo = cmdline.value("-Q-lo",10.0)
Q_hi = cmdline.value("-Q-hi",10000.0)
nQ = cmdline.value("-nQ",50)

doLaTeX=cmdline.present("-do-latex")

if (cmdline.present("-xmin")): xmin = cmdline.value("-xmin", return_type = float)
else                         : xmin = None

#nx=cmdline.value("-nx",100)
#Q=cmdline.value("-Q", 100.0)
flavList=cmdline.value("-flav",'1').split(',')
for iflav,flav in enumerate(flavList):
    flavList[iflav] = int(flav)
fullerr = cmdline.present("-fullerr")
err = cmdline.present("-err") or fullerr
if (not err):
    imem = cmdline.value("-imem",0)
else        :
    imem = 0
    medianerr = cmdline.present("-medianerr")

print_info=cmdline.present("-info")

divide_by_M2 = cmdline.present("-divide-by-M2")

mu = None
if (cmdline.present("-mu")): mu = cmdline.value("-mu", return_type=float)

cmdline.assert_all_options_used()

# now set up the pdf
pdfset = lhapdf.getPDFSet(pdfname)

# make sure our lumi mass range is in the PDF range
QMin = sqrt(pdfset.mkPDF(imem).q2Min)
Q_lo = max(Q_lo, QMin)


#======================================================================
# now start with the output
print("# "+cmdline.cmdline(), file=out)        

# generate the Qvals
Qvals=Q_lo*(Q_hi/Q_lo)**((1.0*np.arange(0,nQ))/(max(1,nQ-1)))


if (err):

    resfull=np.empty([nQ,len(flavList),pdfset.size])
    if (fullerr):
        ncol=4
    else:
        ncol=2
    reserr=np.empty([nQ,ncol*len(flavList)])

    pdfs = pdfset.mkPDFs()
    for iQ,Q in enumerate(Qvals):
        for iflav,flav in enumerate(flavList):
            for ipdf,pdf in enumerate(pdfs):
                resfull[iQ,iflav,ipdf] = mom(pdf, Q, flav, xmin)
            if (medianerr):
                uncert = mypdf.intervalUncert(resfull[iQ,iflav,:])
            else:
                uncert = pdfset.uncertainty(resfull[iQ,iflav,:])

            reserr[iQ,iflav*ncol+0] = uncert.central
            reserr[iQ,iflav*ncol+1] = uncert.errsymm
            if (fullerr):
                reserr[iQ,iflav*ncol+2] = uncert.central-abs(uncert.errminus)
                reserr[iQ,iflav*ncol+3] = uncert.central+uncert.errplus

    print("# pdf = {}, version = {}".format(pdfname, pdfset.dataversion), file=out)
    header = "# Columns: Q"
    for flav in flavList:
        header += " mom({}) errsymm({})".format(flav,flav)
        if (fullerr): header += " bandlo({}) bandhi({})".format(flav,flav)
    if (fullerr): header += " bandlo bandhi"
    print(header, file=out)
    print(mypdf.reformat(Qvals, reserr, format='{:<12.5g}'), file=out)

    if (doLaTeX):
        print("{:8s}".format("Q [GeV]"), end=' ', file=out)
        for iflav,flav in enumerate(flavList):
            print("& {:17s}".format(mypdf.names[flav]), end=' ', file=out)
        print(r"\\", file=out)
        for iQ,Q in enumerate(Qvals):
            print("{:8.1f}".format(Q), end=' ', file=out)
            for iflav,flav in enumerate(flavList):
                print(r"& ${:5.2f} \pm {:5.2f}$".format(100*reserr[iQ,iflav*ncol+0],
                                                              100*reserr[iQ,iflav*ncol+1]), end=' ', file=out)
            print(r"\\", file=out)
    
else:
    pdf=pdfset.mkPDF(imem)
    res=np.empty([nQ,len(flavList)])
    for iQ,Q in enumerate(Qvals):
        for iflav,flav in enumerate(flavList):
            res[iQ,iflav] = mom(pdf, Q, flav, xmin)
    
    print("# pdf = {}, imem = {}, version = {}".format(pdfname,imem, pdfset.dataversion), file=out)
    header = "# Columns: Q"
    for flav in flavList:
        header += " mom({}): central".format(flav)
    print(header, file=out)
    print(mypdf.reformat(Qvals, res, format='{:<12.5g}'), file=out)


def printInfo():
    # find out location of data
    lhapdfData = subprocess.Popen(["lhapdf-config", "--datadir"],
                                  stdout=subprocess.PIPE).communicate()[0].rstrip()
    print(subprocess.Popen(["cat", "{0}/{1}/{1}.info".format(lhapdfData,pdfname)],
                                  stdout=subprocess.PIPE).communicate()[0], file=out)

if (print_info): printInfo()

