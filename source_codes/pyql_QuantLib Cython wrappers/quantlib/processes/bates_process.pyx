"""
 Copyright (C) 2011, Enthought Inc
 Copyright (C) 2011, Patrick Henaff

 This program is distributed in the hope that it will be useful, but WITHOUT
 ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
 FOR A PARTICULAR PURPOSE.  See the license for more details.
"""

include '../types.pxi'

from cython.operator cimport dereference as deref
cimport quantlib._stochastic_process as _sp
cimport _heston_process as _hp

from quantlib.handle cimport Handle, shared_ptr
cimport quantlib.termstructures.yields._flat_forward as _ff
cimport quantlib._quote as _qt
from quantlib.quotes cimport Quote, SimpleQuote
from quantlib.termstructures.yields.flat_forward cimport YieldTermStructure
from heston_process cimport HestonProcess

cdef public enum Discretization:
        PARTIALTRUNCATION = _hp.PartialTruncation
        FULLTRUNCATION = _hp.FullTruncation
        REFLECTION = _hp.Reflection
        NONCENTRALCHISQUAREVARIANCE = _hp.NonCentralChiSquareVariance
        QUADRATICEXPONENTIAL = _hp.QuadraticExponential
        QUADRATICEXPONENTIALMARTINGALE = _hp.QuadraticExponentialMartingale

cdef class BatesProcess(HestonProcess):

    def __cinit__(self):
        pass

    def __dealloc(self):
        pass

    def __init__(self,
       YieldTermStructure risk_free_rate_ts=YieldTermStructure(),
       YieldTermStructure dividend_ts=YieldTermStructure(),
       Quote s0=None,
       Real v0=0,
       Real kappa=0,
       Real theta=0,
       Real sigma=0,
       Real rho=0,
       Real lambda_=0,
       Real nu=0,
       Real delta=0,
       Discretization d=FULLTRUNCATION):

        #create handles
        cdef Handle[_qt.Quote] s0_handle = Handle[_qt.Quote](s0._thisptr)

        self._thisptr = shared_ptr[_sp.StochasticProcess](
            new _hp.BatesProcess(
                risk_free_rate_ts._thisptr,
                dividend_ts._thisptr,
                s0_handle,
                v0, kappa, theta, sigma, rho,
                lambda_, nu, delta, d))

    def __str__(self):
        return 'Bates process\nv0: %f kappa: %f theta: %f sigma: %f\nrho: %f lambda: %f nu: %f delta: %f' % \
          (self.v0, self.kappa, self.theta, self.sigma,
           self.rho, self.Lambda, self.nu, self.delta)

    property Lambda:
        def __get__(self):
            return (<_hp.BatesProcess*> self._thisptr.get()).Lambda()

    property nu:
        def __get__(self):
            return (<_hp.BatesProcess*> self._thisptr.get()).nu()

    property delta:
        def __get__(self):
            return (<_hp.BatesProcess*> self._thisptr.get()).delta()
