include '../types.pxi'

from libcpp cimport bool


cimport quantlib.math._array as _arr
cdef extern from 'ql/math/optimization/method.hpp' namespace 'QuantLib':

    cdef cppclass OptimizationMethod:
        pass


cdef extern from 'ql/math/optimization/levenbergmarquardt.hpp' namespace 'QuantLib':

    cdef cppclass LevenbergMarquardt(OptimizationMethod):
        LevenbergMarquardt(
            Real epsfcn,
            Real xtol,
            Real gtol
        )

cdef extern from 'ql/math/optimization/endcriteria.hpp' namespace 'QuantLib':

    cdef cppclass EndCriteria:
        EndCriteria(
            Size maxIterations,
            Size maxStationaryStateIterations,
            Real rootEpsilon,
            Real functionEpsilon,
            Real gradientEpsilon
        )

cdef extern from 'ql/math/optimization/endcriteria.hpp' namespace 'QuantLib::EndCriteria':
    ctypedef enum Type:
        No "None"
        MaxIterations
        StationaryPoint
        StationaryFunctionValue
        StationaryFunctionAccuracy
        ZeroGradientNorm
        Unknown


cdef extern from 'ql/math/optimization/constraint.hpp' namespace 'QuantLib':

    cdef cppclass Constraint:
        Constraint()
        bool test(_arr.Array& a)
