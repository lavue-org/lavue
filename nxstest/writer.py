import h5py
import numpy as np
import time

f = h5py.File("swmr.h5", 'w', libver='latest')
arr = np.array([1, 2, 3, 4])
dset = f.create_dataset("data", chunks=(2,), maxshape=(None,), data=arr)
f.swmr_mode = True
# Now it is safe for the reader to open the swmr.h5 file
for i in range(50):
    new_shape = ((i+1) * len(arr), )
    dset.resize(new_shape)
    dset[i*len(arr):] = arr
    dset.flush()
    time.sleep(1)
    # Notify the reader process that new data has been written
