PyPDFs
======

A package to help with extraction of information about PDFs in text format. 

It requires an installation of LHAPDF, including its python package.

To view a specific pdf flavour and its uncertainty for a fixed
factorisation scale (Q), as a function of x:

```
./pdf.py -pdf MSHT20nnlo_as118 -flav 4 -err -Q 200.0
```

To view a partonic luminosity (u*ubar) as a function of the invariant
mass of the produced system:

```
./lumi.py -pdf MSHT20nnlo_as118 -eval '2*u1*ubar2' -rts 13600
```

Note that this uses a non-standard definition of the luminosity (m^2/s
times the usual one).

To view the momentum carried by the gluon as a function of the
factorisation scale Q

```
./mom.py -pdf MSHT20nnlo_as118 -flav 21
```
