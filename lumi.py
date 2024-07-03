#!/usr/bin/env python3
#
# Usage:
#
#   ./lumi.py [-pdf PDF] [-flav1 F1] [-flav2 F2] [-eval STRING] [-mass-lo LO] [-mass-hi HI] \
#             [-rts RTS] [-mu mu] [-err | -fullerr] [-out OUT]
#
# If F1/=F2, then the lumi includes a factor of 2 (i.e. 2*F1*F2)
#
# If "-eval STRING" is provided then STRING can contain expressions like
#    
#    u1 * dbar2
#    g1 * sigma2 (photon * all quarks)
#    y1 * y2     (photon * photon)
#
# The script imports python3 division, so 4/9 will be treated as floating point division
#
from __future__ import division
from __future__ import print_function
from builtins import range
import sys
import subprocess
import re
import numpy as np
import cmdline
from math import *
import pdf as mypdf
import lhapdf

class Lumi(object):
    def __init__(self):
        self.dy     = None
        self.dlumi  = None
        self.x1vals = None
        self.x2vals = None
        self.yvals  = None
        self.lumi   = None

#----------------------------------------------------------------------
def lumi(pdf, M, rts, iflav1, iflav2, flv_string=None, mu=None, dy_min = 0.1, ny_min = 100, return_Lumi=False):
    if (mu is None): mu = M
    tau = (M/rts)**2
    ymax = -log(tau)
    # these settings should be accurate enough for most
    # purposes
    ny = max(ny_min, int(ymax/dy_min))
    dy = ymax / ny

    ll = Lumi()
    ll.dy = dy
    ll.x1vals = np.exp(-dy*np.arange(0,ny+1))
    ll.x2vals = np.exp(-dy*(ny-np.arange(0,ny+1)))


    if (flv_string is None):
        pdf1 = np.zeros(ny+1)
        pdf2 = np.zeros(ny+1)
        for iy in range(0,ny+1):
            x = exp(-dy*iy)
            pdf1[iy] = pdf.xfxQ(iflav1, x, mu)
            pdf2[iy] = pdf.xfxQ(iflav2, x, mu)
            
        ll.dlumi = pdf1[:] * pdf2[ny::-1]
        if (iflav1 != iflav2): ll.dlumi *= 2
        ll.lumi = ll.dlumi.sum() * dy
        #lumi = (pdf1[:] * pdf2[ny::-1]).sum() * dy
            
        # if the two flavours are not identical
        # then we need a factor of two to account for
        # f_{f1/p1} * f_{f2/p2} + f_{f2/p1} * f_{f1/p2}
    else:
        # define a range of shorthands
        flv1 = lambda iflv: pdf.xfxQ(iflv, x1, mu)
        flv2 = lambda iflv: pdf.xfxQ(iflv, x2, mu)

        g1    = lambda : flv1(21)
        y1    = lambda : flv1(22)
        d1    = lambda : flv1(1)
        u1    = lambda : flv1(2)
        s1    = lambda : flv1(3)
        c1    = lambda : flv1(4)
        b1    = lambda : flv1(5)
        t1    = lambda : flv1(6)
        dbar1 = lambda : flv1(-1)
        ubar1 = lambda : flv1(-2)
        sbar1 = lambda : flv1(-3)
        cbar1 = lambda : flv1(-4)
        bbar1 = lambda : flv1(-5)
        tbar1 = lambda : flv1(-6)

        g2    = lambda : flv2(21)
        y2    = lambda : flv2(22)
        d2    = lambda : flv2(1)
        u2    = lambda : flv2(2)
        s2    = lambda : flv2(3)
        c2    = lambda : flv2(4)
        b2    = lambda : flv2(5)
        t2    = lambda : flv2(6)
        dbar2 = lambda : flv2(-1)
        ubar2 = lambda : flv2(-2)
        sbar2 = lambda : flv2(-3)
        cbar2 = lambda : flv2(-4)
        bbar2 = lambda : flv2(-5)
        tbar2 = lambda : flv2(-6)

        sigma1 = lambda : sum([flv1(i) + flv1(-i) for i in range(1,7)])
        sigma2 = lambda : sum([flv2(i) + flv2(-i) for i in range(1,7)])
        qqbar = lambda : 2*sum([flv1(i) * flv2(-i) for i in range(1,7)])
        #d1()*dbar2() + u1()*ubar2() + s1()*sbar2() + c1()*cbar2() + b1()*bbar2() + t1()*tbar2()
        
        # arrange string to allow us to use the above without "()"
        flv_string_sub = re.sub(r'([aduscbtgyr][12])',r'\1()',flv_string)
        flv_string_sub = re.sub(r'(qqbar)',r'\1()',flv_string_sub)
        flv_string_obj = compile(flv_string_sub, '/dev/stderr', mode='eval')
    
        lumi = 0
        ll.dlumi = np.zeros(ny+1)
        for iy in range(0,ny+1):
            x1 = ll.x1vals[iy]
            x2 = ll.x2vals[iy]
            ll.dlumi[iy] = eval(flv_string_obj)
            #lumi = lumi + eval(flv_string_obj)

        ll.lumi = ll.dlumi.sum() * dy            
        #lumi *= dy
        
    if return_Lumi: return ll
    else          : return ll.lumi
    #return lumi

#----------------------------------------------------------------------
def lumi_description(flav1,flav2,flv_string):
    if (flv_string is None):
        return 'lumi({}*{})'.format(flav1,flav2)
    else:
        return 'lumi({})'.format(flv_string)


def main():

    #-- send output to a file if requested
    out = sys.stdout
    if (cmdline.present("-out")):
        outName = cmdline.value("-out")
        out = open(outName,'w')

    #-- get basic parameters
    pdfname = cmdline.value("-pdf","MSHT20nnlo_as118")
    flav1=cmdline.value("-flav1",21)
    flav2=cmdline.value("-flav2",21)
    flv_string = None
    if (cmdline.present("-eval")): flv_string = cmdline.value("-eval")
    rts =cmdline.value("-rts",13000)
    mass_lo = cmdline.value("-mass-lo",125.0)
    mass_hi = cmdline.value("-mass-hi",rts/2.0)
    nmass = cmdline.value("-nmass",50)
    dy_min = cmdline.value("-dy-min",0.1)

    #nx=cmdline.value("-nx",100)
    #Q=cmdline.value("-Q", 100.0)
    #flavList=cmdline.value("-flav",'1').split(',')
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
    xMin = pdfset.mkPDF(imem).xMin
    mass_lo = max(mass_lo, sqrt(xMin) * rts)


    #======================================================================
    # now start with the output
    print("# "+cmdline.cmdline(), file=out)        

    # generate the masses
    masses=mass_lo*(mass_hi/mass_lo)**((1.0*np.arange(0,nmass))/(nmass-1))
    if (divide_by_M2): norm = 1/masses**2
    else             : norm = masses**0



    if (err):

        resfull=np.empty([nmass,pdfset.size])
        if (fullerr):
            ncol=4
        else:
            ncol=2
        reserr=np.empty([nmass,ncol])

        pdfs = pdfset.mkPDFs()
        for im,mass in enumerate(masses):
            for ipdf,pdf in enumerate(pdfs):
                resfull[im,ipdf] = norm[im] * lumi(pdf, mass, rts, flav1, flav2, flv_string, mu, dy_min)
            if (medianerr):
                uncert = mypdf.intervalUncert(resfull[im,:])
            else:
                uncert = pdfset.uncertainty(resfull[im,:])

            # print(np.array2string(resfull[im,:],separator=','))
            # print(np.average(resfull[im,1:]), resfull[im,0])

            reserr[im,0] = uncert.central
            reserr[im,1] = uncert.errsymm
            if (fullerr):
                reserr[im,2] = uncert.central-abs(uncert.errminus)
                reserr[im,3] = uncert.central+uncert.errplus

        print("# pdf = {}, version = {}, rts = {}".format(pdfname, pdfset.dataversion, rts), file=out)
        header = "# Columns: mass"
        header += " "+lumi_description(flav1,flav2,flv_string)+" : mean_or_median errsymm".format(flav1,flav2)
        if (fullerr): header += " bandlo bandhi"
        print(header, file=out)
        print(mypdf.reformat(masses, reserr, format='{:<13.6g}'), file=out)

    else:
        pdf=pdfset.mkPDF(imem)
        res=np.empty([nmass])
        for im,mass in enumerate(masses):
            res[im] = norm[im] * lumi(pdf, mass, rts, flav1, flav2, flv_string, mu, dy_min)

        print("# pdf = {}, imem = {}, version = {}, rts = {}".format(pdfname,imem, pdfset.dataversion, rts), file=out)
        header = "# Columns: mass"
        header += " "+lumi_description(flav1,flav2,flv_string)+": central"
        print(header, file=out)
        print(mypdf.reformat(masses, res, format='{:<13.6g}'), file=out)

    if (print_info): printInfo()

def printInfo():
    # find out location of data
    lhapdfData = subprocess.Popen(["lhapdf-config", "--datadir"],
                                    stdout=subprocess.PIPE).communicate()[0].rstrip()
    print(subprocess.Popen(["cat", "{0}/{1}/{1}.info".format(lhapdfData,pdfname)],
                                    stdout=subprocess.PIPE).communicate()[0], file=out)

if __name__ == '__main__': main()

