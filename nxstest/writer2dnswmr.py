import h5py
import numpy as np
import time
import sys

if sys.version_info > (3,):
    unicode = str

# f = h5py.File("swmr.h5", 'w', libver='latest')
f = h5py.File("swmr.h5", 'w')

arr = np.array([[1, 2, 3], [4, 5, 6]])
dset = f.create_dataset(
    "data", shape=(0, 2, 3), chunks=(1, 2, 3), dtype="int64",
    maxshape=(None, None, None))

# f.swmr_mode = True

for i in range(50):
    new_shape = ((i+1), 2, 3)
    dset.resize(new_shape)
    dset[i, :, :] = arr + i
    dset.flush()
    time.sleep(1)
dset.attrs.create("units", "mm")
dset = f.create_dataset(
    "endtime", shape=[1], chunks=None, dtype=h5py.special_dtype(vlen=unicode),
    maxshape=(None,), data=str(time.time))
