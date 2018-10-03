from pninexus import h5cpp
import time

readonly = True
libver = None
filename = "swmr.h5"

fapl = h5cpp.property.FileAccessList()
# fapl.set_close_degree(h5cpp._property.CloseDegree.STRONG)
flag = h5cpp.file.AccessFlags.READONLY | h5cpp.file.AccessFlags.SWMRREAD
if libver is None or libver == 'lastest':
    fapl.library_version_bounds(
        h5cpp.property.LibVersion.LATEST,
        h5cpp.property.LibVersion.LATEST)
f = h5cpp.file.open(filename, flag, fapl)
rt = f.root()
dset = rt.get_dataset(h5cpp.Path("data"))
# import h5py
while True:
    if hasattr(dset, "refresh"):
        dset.refresh()
        shape = dset.dataspace.current_dimensions
        print(shape)
        # print(dset.read())
        time.sleep(0.1)

# f = h5py.File("swmr.h5", 'r', libver='latest', swmr=True)
# dset = f["data"]
f.close()
