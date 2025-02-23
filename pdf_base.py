import subprocess
import sys
# figure out where lhapdf's python package is hiding
lhapdfPath = str(subprocess.Popen(["lhapdf-config", "--prefix"],
                            stdout=subprocess.PIPE).communicate()[0].rstrip())
lhapdfPath += "/lib/python{}.{}/site-packages".format(sys.version_info[0],sys.version_info[1])
# include it in the python path
sys.path = [lhapdfPath] + sys.path
#sys.path.append(lhapdfPath)
import io
import lhapdf

default_pdf = "MSHT20nnlo_as118"
default_rts = 13600.0

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


#----------------------------------------------------------------------
def printInfo(pdfname):
    # find out location of data
    lhapdfData = subprocess.Popen(["lhapdf-config", "--datadir"],
                                  stdout=subprocess.PIPE).communicate()[0].decode('utf-8').rstrip()
    # read and print the file
    with open("{0}/{1}/{1}.info".format(str(lhapdfData),pdfname),'r') as ff:
        contents = ff.read()
        print(contents)


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

