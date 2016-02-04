from __future__ import division
import os
import math
import random
import tempfile
import copper
import numpy as np
import pandas as pd

from nose.tools import raises
from copper.tests.utils import eq_


# -----------------------------------------------------------------------------
#                               Properties

def test_create_empty():
    # Checks empty Dataframes
    ds = copper.Dataset()
    eq_(ds.role, pd.Series())
    eq_(ds.type, pd.Series())
    eq_(ds.frame.empty, True)
    eq_(ds.metadata.empty, True)


def test_create_noempty():
    df = pd.DataFrame(np.random.rand(10, 5))
    ds = copper.Dataset(df)
    eq_(ds.frame, df)
    eq_(len(ds), 10)
    eq_(len(ds), len(df))
    eq_(len(ds.role), 5)
    eq_(len(ds.type), 5)
    eq_(len(ds.metadata), 5)
    eq_(ds.metadata['Role'], ds.role)
    eq_(ds.metadata['Type'], ds.type)
    eq_(ds.index, df.index)
    eq_(ds.columns, df.columns)
    eq_(str(ds), str(ds.metadata))


def test_create_empty_and_set():
    df = pd.DataFrame(np.random.rand(10, 5))
    ds = copper.Dataset()
    eq_(ds.role, pd.Series())
    eq_(ds.type, pd.Series())
    eq_(ds.metadata.empty, True)
    eq_(ds.frame.empty, True)

    ds.frame = df.copy()
    eq_(ds.frame, df)
    eq_(len(ds), 10)
    eq_(len(ds), len(df))
    eq_(len(ds.role), 5)
    eq_(len(ds.type), 5)
    eq_(len(ds.metadata), 5)
    eq_(ds.metadata['Role'], ds.role)
    eq_(ds.metadata['Type'], ds.type)
    eq_(ds.index, df.index)
    eq_(ds.columns, df.columns)
    eq_(str(ds), str(ds.metadata))
    eq_(unicode(ds), unicode(ds.metadata))


def test_set_frame_different_length_same_cols():
    # Tests that the metadata is mantained if columns are the same
    df1 = pd.DataFrame(np.random.rand(5, 5))
    ds = copper.Dataset(df1.copy())
    ds.role[[2, 4]] = ds.TARGET
    ds.type[[1, 2]] = ds.CATEGORY
    meta_old = ds.metadata.copy()

    df2 = pd.DataFrame(np.random.rand(10, 5))
    ds.frame = df2
    eq_(ds.metadata, meta_old)


@raises(AssertionError)
def test_set_frame_different_length_same_cols_fail():
    # By failing is testing that the default metadata is not in place
    df1 = pd.DataFrame(np.random.rand(5, 5))
    ds = copper.Dataset(df1.copy())
    default_meta = ds.metadata.copy()
    ds.role[[2, 4]] = ds.TARGET
    ds.type[[1, 2]] = ds.CATEGORY

    df2 = pd.DataFrame(np.random.rand(10, 5))
    ds.frame = df2
    eq_(ds.metadata, default_meta)


def test_set_frame_different_cols():
    # Checks default metadata is placed
    df1 = pd.DataFrame(np.random.rand(5, 5))
    ds = copper.Dataset(df1)
    ds.role[[2, 4]] = ds.TARGET
    ds.type[[1, 2]] = ds.CATEGORY

    df2 = pd.DataFrame(np.random.rand(10, 10))
    ds.frame = df2
    eq_(ds.role[2], ds.INPUT)
    eq_(ds.role[4], ds.INPUT)
    eq_(ds.type[1], ds.NUMBER)
    eq_(ds.type[2], ds.NUMBER)


@raises(AssertionError)
def test_set_frame_different_cols_fail():
    # By failing it checks that the metadata is different == was recreated
    df1 = pd.DataFrame(np.random.rand(5, 5))
    ds = copper.Dataset(df1)
    meta_old = ds.metadata.copy()

    df2 = pd.DataFrame(np.random.rand(10, 10))
    ds.frame = df2
    eq_(ds.metadata, meta_old)


def test_default_type():
    df = pd.DataFrame(np.random.rand(5, 20))
    rand_col = math.floor(random.random() * 20)
    rand_col2 = math.floor(random.random() * 20)
    df[rand_col] = df[rand_col].apply(lambda x: str(x))
    df[rand_col2] = df[rand_col].apply(lambda x: str(x))
    ds = copper.Dataset(df)

    eq_(ds.type[rand_col], ds.CATEGORY)
    for col in ds.columns:
        if col not in (rand_col, rand_col2):
            eq_(ds.type[col], ds.NUMBER)


def test_set_metadata():
    df = pd.DataFrame(np.random.rand(5, 5))
    ds = copper.Dataset(df)

    rand_col = math.floor(random.random() * 5)
    meta = ds.metadata.copy()
    meta['Role'][rand_col] = ds.TARGET
    eq_(ds.role[rand_col], ds.INPUT)  # Not changes until reasigment
    ds.metadata = meta
    eq_(ds.role[rand_col], ds.TARGET)  # Change

    for i in range(5):
        rand_col = math.floor(random.random() * 5)
        meta = ds.metadata.copy()
        meta['Role'][rand_col] = ds.TARGET
        ds.metadata = meta
        eq_(ds.role[rand_col], ds.TARGET)

    rand_col = math.floor(random.random() * 5)
    meta = ds.metadata.copy()
    meta['Type'][rand_col] = ds.CATEGORY
    eq_(ds.type[rand_col], ds.NUMBER)  # Not changes until reasigment
    ds.metadata = meta
    eq_(ds.type[rand_col], ds.CATEGORY)  # Change

    for i in range(5):
        rand_col = math.floor(random.random() * 5)
        meta = ds.metadata.copy()
        meta['Type'][rand_col] = ds.CATEGORY
        ds.metadata = meta
        eq_(ds.type[rand_col], ds.CATEGORY)


@raises(AssertionError)
def test_set_metadata_fail_length():
    df = pd.DataFrame(np.random.rand(5, 5))
    ds = copper.Dataset(df)

    meta = ds.metadata.copy()
    meta = meta.drop(0)
    ds.metadata = meta


@raises(AssertionError)
def test_set_metadata_fail_index():
    df = pd.DataFrame(np.random.rand(5, 5))
    ds = copper.Dataset(df)

    meta = ds.metadata.copy()
    meta = meta.reindex([11, 1, 2, 3, 4])
    ds.metadata = meta


def test_save_load_metadata():
    tempdir = tempfile.gettempdir()
    # Save
    df = pd.DataFrame(np.random.rand(5, 10))
    ds = copper.Dataset(df)
    ds.role[2] = ds.TARGET
    ds.role[7] = ds.IGNORE
    ds.type[1] = ds.CATEGORY
    ds.type[5] = ds.CATEGORY
    ds.metadata.to_csv(os.path.join(tempdir, 'metadata.csv'))
    # Load
    ds2 = copper.Dataset(df)
    loaded_meta = pd.read_csv(os.path.join(tempdir, 'metadata.csv'))
    loaded_meta = loaded_meta.set_index('Columns')
    ds2.metadata = loaded_meta
    eq_(ds2.role[2], ds.TARGET)
    eq_(ds2.role[7], ds.IGNORE)
    eq_(ds2.type[1], ds.CATEGORY)
    eq_(ds2.type[5], ds.CATEGORY)


def test_copy_metadata():
    cols = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j']
    df1 = pd.DataFrame(np.random.rand(5, 10), columns=cols)
    ds1 = copper.Dataset(df1)
    ds1.role[['c', 'd', 'h', 'i']] = ds1.TARGET
    ds1.type[['b', 'c', 'g', 'i']] = ds1.CATEGORY
    # meta_old = ds1.metadata.copy()

    df2 = pd.DataFrame(np.random.rand(5, 10), columns=cols)
    ds2 = copper.Dataset(df2)
    ds2.copy_metadata(ds1.metadata)
    eq_(ds2.metadata, ds1.metadata)


def test_copy_metadata_ignore_true():
    cols = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j']
    df1 = pd.DataFrame(np.random.rand(5, 10), columns=cols)
    ds1 = copper.Dataset(df1)
    ds1.role[['a', 'd', 'h', 'i']] = ds1.TARGET
    ds1.type[['b', 'd', 'g', 'i']] = ds1.CATEGORY

    cols = ['z', 'y', 'f', 'a', 'b', 'd', 'e']
    df2 = pd.DataFrame(np.random.rand(5, 7), columns=cols)
    ds2 = copper.Dataset(df2)
    ds2.copy_metadata(ds1.metadata)
    eq_(ds2.role['z'], ds1.INPUT)
    eq_(ds2.role['y'], ds1.INPUT)
    eq_(ds2.role['a'], ds1.TARGET)
    eq_(ds2.role['b'], ds1.INPUT)
    eq_(ds2.role['d'], ds1.TARGET)
    eq_(ds2.role['e'], ds1.INPUT)

    eq_(ds2.type['z'], ds1.NUMBER)
    eq_(ds2.type['y'], ds1.NUMBER)
    eq_(ds2.type['a'], ds1.NUMBER)
    eq_(ds2.type['b'], ds1.CATEGORY)
    eq_(ds2.type['d'], ds1.CATEGORY)
    eq_(ds2.type['e'], ds1.NUMBER)


def test_copy_metadata_ignore_false():
    cols = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j']
    df1 = pd.DataFrame(np.random.rand(5, 10), columns=cols)
    ds1 = copper.Dataset(df1)
    ds1.role[['a', 'd', 'h', 'i']] = ds1.TARGET
    ds1.type[['b', 'd', 'g', 'i']] = ds1.CATEGORY

    cols = ['z', 'y', 'f', 'a', 'b', 'd', 'e']
    df2 = pd.DataFrame(np.random.rand(5, 7), columns=cols)
    ds2 = copper.Dataset(df2)
    ds2.copy_metadata(ds1.metadata, ignoreMissing=False)
    eq_(ds2.role['z'], ds1.IGNORE)
    eq_(ds2.role['y'], ds1.IGNORE)
    eq_(ds2.role['a'], ds1.TARGET)
    eq_(ds2.role['b'], ds1.INPUT)
    eq_(ds2.role['d'], ds1.TARGET)
    eq_(ds2.role['e'], ds1.INPUT)

    eq_(ds2.type['z'], ds1.NUMBER)
    eq_(ds2.type['y'], ds1.NUMBER)
    eq_(ds2.type['a'], ds1.NUMBER)
    eq_(ds2.type['b'], ds1.CATEGORY)
    eq_(ds2.type['d'], ds1.CATEGORY)
    eq_(ds2.type['e'], ds1.NUMBER)


# -----------------------------------------------------------------------------
#                            Functions

def test_update_cat_to_num_int():
    sol = np.arange(100)
    strings = np.array(['a(%f)' % d for d in sol])
    df = pd.DataFrame(strings)
    ds = copper.Dataset(df)
    ds.type[0] = ds.NUMBER
    ds.update()
    eq_(sol, ds[0].values)


def test_update_cat_to_num_float():
    sol = np.arange(100) / 100
    strings = np.array(['a(%f)' % d for d in sol])
    df = pd.DataFrame(strings)
    ds = copper.Dataset(df)
    ds.type[0] = ds.NUMBER
    ds.update()
    eq_(sol, ds[0].values)


def test_filter_role():
    df = pd.DataFrame(np.random.rand(5, 10))
    ds = copper.Dataset(df)
    ds.role[[0, 2, 4, 5, 9]] = ds.IGNORE
    eq_(ds.filter(role=ds.INPUT), ds[[1, 3, 6, 7, 8]])

    ds.role[:] = ds.IGNORE
    ds.role[[1, 3, 4, 6, 8]] = ds.INPUT
    eq_(ds.filter(role=ds.INPUT), ds[[1, 3, 4, 6, 8]])

    ds.role[[2, 9]] = ds.TARGET
    eq_(ds.filter(role=ds.TARGET), ds[[2, 9]])

    eq_(ds.filter(role=[ds.INPUT, ds.TARGET]), ds[[1, 2, 3, 4, 6, 8, 9]])

    eq_(ds.filter(), df)


def test_filter_type():
    df = pd.DataFrame(np.random.rand(5, 10))
    ds = copper.Dataset(df)
    ds.type[[0, 2, 4, 5, 9]] = ds.CATEGORY
    eq_(ds.filter(type=ds.CATEGORY), ds[[0, 2, 4, 5, 9]])

    ds.type[:] = ds.CATEGORY
    ds.type[[1, 3, 6, 7, 9]] = ds.NUMBER
    eq_(ds.filter(type=ds.NUMBER), ds[[1, 3, 6, 7, 9]])

    eq_(ds.filter(type=[ds.NUMBER, ds.CATEGORY]), df)

    eq_(ds.filter(), df)


def test_filter_role_and_type():
    df = pd.DataFrame(np.random.rand(5, 5))
    ds = copper.Dataset(df)
    ds.role[:] = ds.IGNORE

    ds.role[2] = ds.INPUT
    ds.type[2] = ds.CATEGORY
    eq_(ds.filter(role=ds.INPUT, type=ds.CATEGORY), df[[2]])

    ds.role[4] = ds.INPUT
    ds.type[4] = ds.CATEGORY
    eq_(ds.filter(role=ds.INPUT, type=ds.CATEGORY), df[[2, 4]])

    eq_(ds.filter(role=ds.IGNORE, type=ds.NUMBER), df[[0, 1, 3]])

    ds.role[4] = ds.IGNORE
    eq_(ds.filter(role=ds.INPUT, type=ds.CATEGORY), df[[2]])

    eq_(ds.filter(), df)


# -----------------------------------------------------------------------------
#                            Pandas API

def test_get_column():
    df = pd.DataFrame(np.random.rand(5, 10))
    ds = copper.Dataset(df)
    eq_(ds[0], df[0])
    eq_(ds[5], df[5])
    eq_(ds[9], df[9])


def test_set_column():
    df = pd.DataFrame(np.random.rand(5, 10))
    ds = copper.Dataset(df)
    new_col = np.random.rand(5, 1)
    eq_(ds[3].values, df[3].values)
    ds[3] = new_col
    eq_(ds[[3]].values, new_col)


def test_head():
    df = pd.DataFrame(np.random.rand(5, 10))
    ds = copper.Dataset(df.copy())
    l = math.floor(random.random() * 10)
    eq_(ds.head(l), df.head(l))


def test_tail():
    df = pd.DataFrame(np.random.rand(5, 10))
    ds = copper.Dataset(df.copy())
    l = math.floor(random.random() * 10)
    eq_(ds.head(l), df.head(l))

if __name__ == '__main__':
    import nose
    nose.runmodule(argv=[__file__, '-vs', '--nologcapture'], exit=False)
