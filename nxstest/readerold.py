import h5py
import time

f = h5py.File("swmr.h5", 'r', libver='latest', swmr=True)
dset = f["data"]
while True:
    if hasattr(dset.id, "refresh"):
        dset.id.refresh()
    shape = dset.shape
    print(shape)
    print(dset.value)
    time.sleep(0.1)
