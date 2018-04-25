include '../../types.pxi'
cimport cython
from libcpp.string cimport string
from quantlib.indexes.swap_index cimport SwapIndex
cimport quantlib._index as _in
cimport quantlib.indexes._swap_index as _si
cimport _swap_spread_index as _ssi
from quantlib.handle cimport shared_ptr, static_pointer_cast, dynamic_pointer_cast

@cython.final
cdef class SwapSpreadIndex(InterestRateIndex):
    def __init__(self, string family_name, SwapIndex swap_index1,
                 SwapIndex swap_index2, Real gearing1=1.,
                 Real gearing2=2.):
        self._thisptr = shared_ptr[_in.Index](
            new _ssi.SwapSpreadIndex(family_name,
                                     static_pointer_cast[_si.SwapIndex](swap_index1._thisptr),
                                     static_pointer_cast[_si.SwapIndex](swap_index2._thisptr),
                                     gearing1,
                                     gearing2))

    @property
    def gearing1(self):
        cdef shared_ptr[_ssi.SwapSpreadIndex] swap_spread_index = \
            dynamic_pointer_cast[_ssi.SwapSpreadIndex](self._thisptr)
        return swap_spread_index.get().gearing1()

    @property
    def gearing2(self):
        cdef shared_ptr[_ssi.SwapSpreadIndex] swap_spread_index = \
            dynamic_pointer_cast[_ssi.SwapSpreadIndex](self._thisptr)
        return swap_spread_index.get().gearing2()
