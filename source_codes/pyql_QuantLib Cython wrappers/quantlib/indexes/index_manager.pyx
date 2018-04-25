# cython: c_string_type=unicode, c_string_encoding=ascii
include '../types.pxi'
from libcpp.string cimport string
cimport quantlib.indexes._index_manager as _im
from quantlib.time_series cimport TimeSeries
cimport quantlib._time_series as _ts

cdef class IndexManager:
    cdef has_history(self, string name):
        _im.IndexManager.instance().hasHistory(name)

    @staticmethod
    def histories():
        return _im.IndexManager.instance().histories()

    @staticmethod
    def get_history(string name):
        cdef TimeSeries ts = TimeSeries.__new__(TimeSeries)
        ts._thisptr = _im.IndexManager.instance().getHistory(name)
        return ts

    @staticmethod
    def set_history(string name, TimeSeries ts not None):
        _im.IndexManager.instance().setHistory(name, ts._thisptr)

    @staticmethod
    def clear_history(string name):
        _im.IndexManager.instance().clearHistory(name)

    @staticmethod
    def clear_histories():
        _im.IndexManager.instance().clearHistories()
