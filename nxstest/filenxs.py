import pni.io.nx.h5 as nexus
import numpy
import time

nx = 1024
ny = 2048
dshapemn = [nx, ny]
shapemn = [0, nx, ny]
chunkmn = [1, nx, ny]
fpath = "/tmp/pcotest_00750/pco4000"
prefix = "mypcoscan_"
postfix = ".h5"
start = 0
last = 13


file2 = nexus.create_file("file2.nxs", True)
root = file2.root()
en = root.create_group("entry", "NXentry")
ins = en.create_group("instrument", "NXinstrument")
de = ins.create_group("detector", "NXdetector")
datamn = de.create_field("data", "uint32", shape=shapemn, chunk=chunkmn)
for i in range(50):
    amn = numpy.ones(shape=dshapemn)
    amn.fill(i)
    datamn.grow()
    print(datamn.shape)
    print(amn.shape)
    datamn[i, :, :] = amn
    file2.flush()
    time.sleep(1)
file2.close()
