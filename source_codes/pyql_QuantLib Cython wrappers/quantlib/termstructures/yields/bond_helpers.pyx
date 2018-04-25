include '../../types.pxi'

from cython.operator cimport dereference as deref
from libcpp.vector cimport vector

from quantlib.handle cimport shared_ptr, Handle

cimport quantlib.instruments._bonds as _bonds
cimport quantlib.time._calendar as _calendar
cimport quantlib._quote as _qt
cimport _bond_helpers as _bh

from quantlib.instruments.bonds cimport Bond
from quantlib.quotes cimport Quote
from quantlib.time.date cimport Date
from quantlib.time.schedule cimport Schedule
from quantlib.time.daycounter cimport DayCounter
from quantlib.time._businessdayconvention cimport Following
from quantlib.termstructures.yields.rate_helpers cimport RateHelper


cdef class BondHelper(RateHelper):

    def __init__(self, Quote clean_price, Bond bond):

        # Create quote handle.
        cdef Handle[_qt.Quote] price_handle = Handle[_qt.Quote](
            clean_price._thisptr
        )

        self._thisptr = shared_ptr[_bh.RateHelper](
            new _bh.BondHelper(
                price_handle,
                deref(<shared_ptr[_bonds.Bond]*> bond._thisptr)
            ))


cdef class FixedRateBondHelper(BondHelper):

    def __init__(self, Quote clean_price, Natural settlement_days,
                 Real face_amount, Schedule schedule not None,
                 vector[Rate] coupons,
                 DayCounter day_counter not None, int payment_conv=Following,
                 Real redemption=100.0, Date issue_date=Date()):

        # Create handles.
        cdef Handle[_qt.Quote] price_handle = \
                Handle[_qt.Quote](clean_price._thisptr)

        self._thisptr = shared_ptr[_bh.RateHelper](
            new _bh.FixedRateBondHelper(
                price_handle,
                settlement_days,
                face_amount,
                deref(schedule._thisptr),
                coupons,
                deref(day_counter._thisptr),
                <_calendar.BusinessDayConvention> payment_conv,
                redemption,
                deref(issue_date._thisptr)
            ))
