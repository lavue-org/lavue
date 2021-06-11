# Copyright (C) 2017  DESY, Notkestr. 85, D-22607 Hamburg
#
# lavue is an image viewing program for photon science imaging detectors.
# Its usual application is as a live viewer using hidra as data source.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation in  version 2
# of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor,
# Boston, MA  02110-1301, USA.
#
# Authors:
#     Jan Kotanski <jan.kotanski@desy.de>
#


""" Provides h5cpp file writer """

import math
import os
import sys
import logging
import numpy as np
from pninexus import h5cpp

from . import filewriter
# from .Types import nptype

logger = logging.getLogger("lavue")


def nptype(dtype):
    """ converts to numpy types

    :param dtype: h5 writer type type
    :type dtype: :obj:`str`
    :returns: nupy type
    :rtype: :obj:`str`
    """
    if str(dtype) in ['string', b'string']:
        return 'str'
    return dtype


if sys.version_info > (3,):
    unicode = str
    long = int
else:
    bytes = str


def _tostr(text):
    """ converts text  to str type

    :param text: text
    :type text: :obj:`bytes` or :obj:`unicode`
    :returns: text in str type
    :rtype: :obj:`str`
    """
    if isinstance(text, str):
        return text
    elif sys.version_info > (3,):
        return str(text, "utf8")
    else:
        return str(text)


def unlimited_selection(sel, shape):
    """ checks if hyperslab is unlimited

    :param sel: hyperslab selection
    :type sel: :class:`filewriter.FTHyperslab`
    :param shape: give shape
    :type shape: :obj:`list`
    :returns: if hyperslab is unlimited list
    :rtype: :obj:`list` <:obj:`bool`>
    """
    res = None
    if isinstance(sel, tuple):
        res = []
        for sl in sel:
            if hasattr(sl, "stop"):
                res.append(
                    True if sl.stop in [unlimited()]
                    else False)
            elif hasattr(sl, "count"):
                res.append(
                    True if sl.count in [unlimited()]
                    else False)
            else:
                res.append(
                    True if sl in [unlimited()]
                    else False)

    elif hasattr(sel, "count"):
        res = []
        for ct in sel.count():
            res.append(
                True if ct in [unlimited()]
                else False)
    elif isinstance(sel, slice):
        res = [True if sel.stop in [unlimited()]
               else False]

    elif sel in [unlimited()]:
        res = [True]
    lsh = len(shape)
    lct = len(res)
    ln = max(lsh, lct)
    if res and any(t is True for t in res):
        offset = [0 for _ in range(ln)]
        block = [1 for _ in range(ln)]
        stride = [1 for _ in range(ln)]
        count = list(shape)
        while lct > len(count):
            count.append(1)
        for si in range(lct):
            if res[si]:
                count[si] = h5cpp.dataspace.UNLIMITED
        # print("Hyperslab %s %s %s %s" % (offset, block, count, stride))
        return h5cpp.dataspace.Hyperslab(
            offset=offset, block=block, count=count, stride=stride)
    else:
        return None


def _slice2selection(t, shape):
    """ converts slice(s) to selection

    :param t: slice tuple
    :type t: :obj:`tuple`
    :return shape: field shape
    :type shape: :obj:`list` < :obj:`int` >
    :returns: hyperslab selection
    :rtype: :class:`h5cpp.dataspace.Hyperslab`
    """
    if t is Ellipsis:
        return None
    elif isinstance(t, filewriter.FTHyperslab):
        offset = list(t.offset or [])
        block = list(t.block or [])
        count = list(t.count or [])
        stride = list(t.stride or [])
        for dm, sz in enumerate(shape):
            if len(offset) > dm:
                if offset[dm] is None:
                    offset[dm] = 0
            else:
                offset.append(0)
            if len(block) > dm:
                if block[dm] is None:
                    block[dm] = 1
            else:
                block.append(1)
            if len(count) > dm:
                if count[dm] is None:
                    count[dm] = sz
            else:
                count.append(sz)
            if len(stride) > dm:
                if stride[dm] is None:
                    stride[dm] = 1
            else:
                stride.append(1)
        # print("Hyperslab %s %s %s %s" % (offset, block, count, stride))
        return h5cpp.dataspace.Hyperslab(
            offset=offset, block=block, count=count, stride=stride)

    elif isinstance(t, slice):
        start = t.start or 0
        stop = t.stop or shape[0]
        if start < 0:
            start == shape[0] + start
        if stop < 0:
            stop == shape[0] + stop
        if t.step in [None, 1]:
            return h5cpp.dataspace.Hyperslab(
                offset=(start,), block=((stop - start),))
        else:
            return h5cpp.dataspace.Hyperslab(
                offset=(start,),
                count=int(math.ceil((stop - start) / float(t.step))),
                stride=(t.step,))
    elif isinstance(t, (int, long)):
        return h5cpp.dataspace.Hyperslab(
            offset=(t,), block=(1,))
    elif isinstance(t, (list, tuple)):
        offset = []
        block = []
        count = []
        stride = []
        it = -1
        for tit, tel in enumerate(t):
            it += 1
            if isinstance(tel, (int, long)):
                if tel < 0:
                    offset.append(shape[it] + tel)
                else:
                    offset.append(tel)
                block.append(1)
                count.append(1)
                stride.append(1)
            elif isinstance(tel, slice):
                start = tel.start if tel.start is not None else 0
                stop = tel.stop if tel.stop is not None else shape[it]
                if start < 0:
                    start == shape[it] + start
                if stop < 0:
                    stop == shape[it] + stop
                if tel.step in [None, 1]:
                    offset.append(start)
                    block.append(stop - start)
                    count.append(1)
                    stride.append(1)
                else:
                    offset.append(start)
                    block.append(1)
                    count.append(
                        int(math.ceil(
                            (stop - start) / float(tel.step))))
                    stride.append(tel.step)
            elif tel is Ellipsis:
                esize = len(shape) - len(t) + 1
                for jt in range(esize):
                    offset.append(0)
                    block.append(shape[it])
                    count.append(1)
                    stride.append(1)
                    if jt < esize - 1:
                        it += 1
        # print("Hyperslab %s %s %s %s" % (offset, block, count, stride))
        if len(offset):
            return h5cpp.dataspace.Hyperslab(
                offset=offset, block=block, count=count, stride=stride)


pTh = {
    "long": h5cpp.datatype.Integer,
    "str": h5cpp.datatype.kVariableString,
    "unicode": h5cpp.datatype.kVariableString,
    "bool": h5cpp.datatype.kEBool,
    "int": h5cpp.datatype.kInt64,
    "int64": h5cpp.datatype.kInt64,
    "int32": h5cpp.datatype.kInt32,
    "int16": h5cpp.datatype.kInt16,
    "int8": h5cpp.datatype.kInt8,
    "uint": h5cpp.datatype.kInt64,
    "uint64": h5cpp.datatype.kUInt64,
    "uint32": h5cpp.datatype.kUInt32,
    "uint16": h5cpp.datatype.kUInt16,
    "uint8": h5cpp.datatype.kUInt8,
    "float": h5cpp.datatype.kFloat32,
    "float64": h5cpp.datatype.kFloat64,
    "float32": h5cpp.datatype.kFloat32,
    "string": h5cpp.datatype.kVariableString,
}


hTp = {
    h5cpp.datatype.Integer: "long",
    h5cpp.datatype.kVariableString: "string",
    h5cpp._datatype.Class.STRING: "string",
    h5cpp.datatype.kInt64: "int64",
    h5cpp.datatype.kInt32: "int32",
    h5cpp.datatype.kInt16: "int16",
    h5cpp.datatype.kInt8: "int8",
    h5cpp.datatype.kInt64: "uint",
    h5cpp.datatype.kUInt64: "uint64",
    h5cpp.datatype.kUInt32: "uint32",
    h5cpp.datatype.kUInt16: "uint16",
    h5cpp.datatype.kUInt8: "uint8",
    h5cpp.datatype.Float: "float",
    h5cpp.datatype.kFloat64: "float64",
    h5cpp.datatype.kFloat32: "float32",
}


def unlimited(parent=None):
    """ return dataspace UNLIMITED variable for the current writer module

    :param parent: parent object
    :type parent: :class:`FTObject`
    :returns:  dataspace UNLIMITED variable
    :rtype: :class:`h5cpp.dataspace.UNLIMITED`
    """
    return h5cpp.dataspace.UNLIMITED


def open_file(filename, readonly=False, libver=None, swmr=False):
    """ open the new file

    :param filename: file name
    :type filename: :obj:`str`
    :param readonly: readonly flag
    :type readonly: :obj:`bool`
    :param libver: library version: 'lastest' or 'earliest'
    :type libver: :obj:`str`
    :returns: file object
    :rtype: :class:`H5CppFile`
    """

    fapl = h5cpp.property.FileAccessList()
    # if hasattr(fapl, "set_close_degree"):
    #     fapl.set_close_degree(h5cpp._property.CloseDegree.STRONG)
    if readonly:
        flag = h5cpp.file.AccessFlags.READONLY
    else:
        flag = h5cpp.file.AccessFlags.READWRITE
    if swmr:
        if readonly:
            if hasattr(h5cpp.file.AccessFlags, "SWMRREAD"):
                flag = flag | h5cpp.file.AccessFlags.SWMRREAD
        else:
            if hasattr(h5cpp.file.AccessFlags, "SWMRWRITE"):
                flag = flag | h5cpp.file.AccessFlags.SWMRWRITE

    if libver is None or libver == 'lastest':
        fapl.library_version_bounds(
            h5cpp.property.LibVersion.LATEST,
            h5cpp.property.LibVersion.LATEST)
    return H5CppFile(h5cpp.file.open(filename, flag, fapl), filename)


def is_image_file_supported():
    """ provides if loading of image files are supported

    :retruns: if loading of image files are supported
    :rtype: :obj:`bool`
    """
    return hasattr(h5cpp.file, "from_buffer") and \
        hasattr(h5cpp.file, "ImageFlags")


def is_vds_supported():
    """ provides if vds are supported

    :retruns: if vds are supported
    :rtype: :obj:`bool`
    """
    return hasattr(h5cpp.property, "VirtualDataMaps") and \
        hasattr(h5cpp.property, "VirtualDataMaps")


def is_unlimited_vds_supported():
    """ provides if unlimited vds are supported

    :retruns: if unlimited vds are supported
    :rtype: :obj:`bool`
    """
    return is_vds_supported()


def load_file(membuffer, filename=None, readonly=False, **pars):
    """ load a file from memory byte buffer

    :param membuffer: memory buffer
    :type membuffer: :obj:`bytes` or :obj:`io.BytesIO`
    :param filename: file name
    :type filename: :obj:`str`
    :param readonly: readonly flag
    :type readonly: :obj:`bool`
    :param pars: parameters
    :type pars: :obj:`dict` < :obj:`str`, :obj:`str`>
    :returns: file object
    :rtype: :class:`H5PYFile`
    """
    if not is_image_file_supported():
        raise Exception(
            "Loading a file from a memory buffer not supported")
    if type(membuffer).__name__ == "ndarray":
        npdata = np.array(membuffer[:], dtype="uint8")
    else:
        if hasattr(membuffer, "getbuffer"):
            membuffer = membuffer.getbuffer()
        elif hasattr(membuffer, "getvalue"):
            membuffer = membuffer.getvalue()
        try:
            npdata = np.frombuffer(membuffer[:], dtype=np.uint8)
        except Exception:
            npdata = np.fromstring(membuffer[:], dtype=np.uint8)
    if readonly:
        flag = h5cpp.file.ImageFlags.READONLY
    else:
        flag = h5cpp.file.ImageFlags.READWRITE
    return H5CppFile(h5cpp.file.from_buffer(npdata, flag), filename)


def create_file(filename, overwrite=False, libver=None, swmr=None):
    """ create a new file

    :param filename: file name
    :type filename: :obj:`str`
    :param overwrite: overwrite flag
    :type overwrite: :obj:`bool`
    :param libver: library version: 'lastest' or 'earliest'
    :type libver: :obj:`str`
    :returns: file object
    :rtype: :class:`H5CppFile`
    """
    fcpl = h5cpp.property.FileCreationList()
    fapl = h5cpp.property.FileAccessList()
    # if hasattr(fapl, "set_close_degree"):
    #     fapl.set_close_degree(h5cpp._property.CloseDegree.STRONG)
    flag = h5cpp.file.AccessFlags.TRUNCATE if overwrite \
        else h5cpp.file.AccessFlags.EXCLUSIVE
    if libver is None or libver == 'lastest' or swmr:
        fapl.library_version_bounds(
            h5cpp.property.LibVersion.LATEST,
            h5cpp.property.LibVersion.LATEST)
    fl = h5cpp.file.create(filename, flag, fcpl, fapl)
    rt = fl.root()
    attrs = rt.attributes
    attrs.create("file_time", pTh["unicode"]).write(
        unicode(H5CppFile.currenttime()))
    hdf5ver = u""
    if hasattr(h5cpp, "current_library_version"):
        hdf5ver = h5cpp.current_library_version()
    attrs.create("HDF5_Version", pTh["unicode"]).write(hdf5ver)
    attrs.create("NX_class", pTh["unicode"]).write(u"NXroot")
    # attrs.create("NeXus_version", pTh["unicode"]).write(u"4.3.0")
    attrs.create("file_name", pTh["unicode"]).write(unicode(filename))
    attrs.create("file_update_time", pTh["unicode"]).write(
        unicode(H5CppFile.currenttime()))
    rt.close()
    return H5CppFile(fl, filename)


def link(target, parent, name):
    """ create link

    :param target: nexus path name
    :type target: :obj:`str`
    :param parent: parent object
    :type parent: :class:`FTObject`
    :param name: link name
    :type name: :obj:`str`
    :returns: link object
    :rtype: :class:`H5CppLink`
    """
    if ":/" in target:
        filename, path = target.split(":/")
    else:
        filename, path = None, target

    localfname = H5CppLink.getfilename(parent)
    if filename and \
       os.path.abspath(filename) != os.path.abspath(localfname):
        h5cpp.node.link(target_file=filename,
                        target=h5cpp.Path(path),
                        link_base=parent.h5object,
                        link_path=h5cpp.Path(name))
    else:
        h5cpp.node.link(target=h5cpp.Path(path),
                        link_base=parent.h5object,
                        link_path=h5cpp.Path(name))

    lks = parent.h5object.links
    lk = [e for e in lks if str(e.path.name) == name][0]
    el = H5CppLink(lk, parent)
    return el


def get_links(parent):
    """ get links

    :param parent: parent object
    :type parent: :class:`FTObject`
    :returns: list of link objects
    :returns: link object
    :rtype: :obj: `list` <:class:`H5CppLink`>
    """
    lks = parent.h5object.links
    links = [H5CppLink(e, parent) for e in lks]
    return links


def data_filter():
    """ create deflate filter

    :returns: deflate filter object
    :rtype: :class:`H5CppDataFilter`
    """
    return H5CppDataFilter(h5cpp.filter.Deflate())


deflate_filter = data_filter


def target_field_view(filename, fieldpath, shape,
                      dtype=None, maxshape=None):
    """ create target field view for VDS

    :param filename: file name
    :type filename: :obj:`str`
    :param fieldpath: nexus field path
    :type fieldpath: :obj:`str`
    :param shape: shape
    :type shape: :obj:`list` < :obj:`int` >
    :param dtype: attribute type
    :type dtype: :obj:`str`
    :param maxshape: shape
    :type maxshape: :obj:`list` < :obj:`int` >
    :returns: target field view object
    :rtype: :class:`H5CppTargetFieldView`
    """
    return H5CppTargetFieldView(
        filename, fieldpath, shape, dtype, maxshape)


def virtual_field_layout(shape, dtype, maxshape=None):
    """ creates a virtual field layout for a VDS file

    :param shape: shape
    :type shape: :obj:`list` < :obj:`int` >
    :param dtype: attribute type
    :type dtype: :obj:`str`
    :param maxshape: shape
    :type maxshape: :obj:`list` < :obj:`int` >
    :returns: virtual layout
    :rtype: :class:`H5CppVirtualFieldLayout`
    """
    if not is_vds_supported():
        raise Exception("VDS not supported")
    return H5CppVirtualFieldLayout(
        h5cpp.property.VirtualDataMaps(),
        shape, dtype, maxshape)


class H5CppFile(filewriter.FTFile):

    """ file tree file
    """

    def __init__(self, h5object, filename):
        """ constructor

        :param h5object: h5 object
        :type h5object: :obj:`any`
        :param filename:  file name
        :type filename: :obj:`str`
        """
        filewriter.FTFile.__init__(self, h5object, filename)
        #: (:obj:`str`) object nexus path
        self.path = None
        if hasattr(h5object, "path"):
            self.path = h5object.path

    def root(self):
        """ root object

        :returns: parent object
        :rtype: :class:`H5CppGroup`
        """
        return H5CppGroup(self._h5object.root(), self)

    def flush(self):
        """ flash the data
        """
        self._h5object.flush()

    def close(self):
        """ close file
        """
        filewriter.FTFile.close(self)
        if self._h5object.is_valid:
            self._h5object.close()

    @property
    def is_valid(self):
        """ check if file is valid

        :returns: valid flag
        :rtype: :obj:`bool`
        """
        return self._h5object.is_valid

    @property
    def readonly(self):
        """ check if file is readonly

        :returns: readonly flag
        :rtype: :obj:`bool`
        """
        try:
            flag = self._h5object.intent == h5cpp.file.AccessFlags.READONLY
            if not flag and hasattr(h5cpp.file.AccessFlags, "SWMRREAD"):
                return self._h5object.intent == \
                    h5cpp.file.AccessFlags.READONLY \
                    | h5cpp.file.AccessFlags.SWMRREAD
            else:
                return flag
        except Exception:
            return None

    def reopen(self, readonly=False, swmr=False, libver=None):
        """ reopen file

        :param readonly: readonly flag
        :type readonly: :obj:`bool`
        :param swmr: swmr flag
        :type swmr: :obj:`bool`
        :param libver:  library version, default: 'latest'
        :type libver: :obj:`str`
        """

        fapl = h5cpp.property.FileAccessList()
        # if hasattr(fapl, "set_close_degree"):
        #     fapl.set_close_degree(h5cpp._property.CloseDegree.STRONG)
        if libver is None or libver == 'lastest' or swmr:
            fapl.library_version_bounds(
                h5cpp.property.LibVersion.LATEST,
                h5cpp.property.LibVersion.LATEST)

        if swmr:
            if not hasattr(h5cpp.file.AccessFlags, "SWMRWRITE"):
                raise Exception("SWMR not supported")
            if not readonly:
                flag = h5cpp.file.AccessFlags.READWRITE \
                       | h5cpp.file.AccessFlags.SWMRWRITE
            else:
                flag = h5cpp.file.AccessFlags.READONLY \
                       | h5cpp.file.AccessFlags.SWMRREAD

        elif readonly:
            flag = h5cpp.file.AccessFlags.READONLY
        else:
            flag = h5cpp.file.AccessFlags.READWRITE
        if self.is_valid:
            self.close()
        self._h5object = h5cpp.file.open(self.name, flag, fapl)
        filewriter.FTFile.reopen(self)


class H5CppGroup(filewriter.FTGroup):

    """ file tree group
    """

    def __init__(self, h5object, tparent=None):
        """ constructor

        :param h5object: h5 object
        :type h5object: :obj:`any`
        :param tparent: tree parent
        :type tparent: :obj:`FTObject`
        """

        filewriter.FTGroup.__init__(self, h5object, tparent)
        #: (:obj:`str`) object nexus path
        self.path = u""
        #: (:obj:`str`) object name
        self.name = None
        if hasattr(h5object, "link"):
            self.name = h5object.link.path.name
            if tparent and tparent.path:
                if isinstance(tparent, H5CppFile):
                    if self.name == ".":
                        self.path = u"/"
                    else:
                        self.path = u"/" + self.name
                else:
                    if tparent.path.endswith("/"):
                        self.path = tparent.path
                    else:
                        self.path = tparent.path + u"/"
                    self.path += self.name
            if ":" not in self.name:
                if u"NX_class" in [at.name for at in h5object.attributes]:
                    clss = filewriter.first(
                        h5object.attributes["NX_class"]).read()
                else:
                    clss = ""
                if clss:
                    if isinstance(clss, (list, np.ndarray)):
                        clss = clss[0]
                if clss and clss != 'NXroot':
                    self.path += u":" + str(clss)

    def open(self, name):
        """ open a file tree element

        :param name: element name
        :type name: :obj:`str`
        :returns: file tree object
        :rtype: :class:`FTObject`
        """
        try:
            if self._h5object.has_group(h5cpp.Path(name)):
                return H5CppGroup(
                    self._h5object.get_group(h5cpp.Path(name)), self)
            elif self._h5object.has_dataset(h5cpp.Path(name)):
                return H5CppField(
                    self._h5object.get_dataset(h5cpp.Path(name)), self)
            elif self._h5object.attributes.exists(name):
                return H5CppAttribute(self._h5object.attributes[name], self)
            else:
                return H5CppLink(
                    [lk for lk in self._h5object.links
                     if lk.path.name == name][0], self)

        except Exception as e:
            logger.warning(str(e))
            # print(str(e))
            return H5CppLink(
                [lk for lk in self._h5object.links
                 if lk.path.name == name][0], self)

    def open_link(self, name):
        """ open a file tree element as link

        :param name: element name
        :type name: :obj:`str`
        :returns: file tree object
        :rtype: :class:`FTObject`
        """
        return H5CppLink(
            [lk for lk in self._h5object.links
             if lk.path.name == name][0], self)

    def create_group(self, n, nxclass=None):
        """ open a file tree element

        :param n: group name
        :type n: :obj:`str`
        :param nxclass: group type
        :type nxclass: :obj:`str`
        :returns: file tree group
        :rtype: :class:`H5CppGroup`
        """
        gr = h5cpp.node.Group(self._h5object, n)
        if nxclass is not None:
            gr.attributes.create(
                "NX_class", pTh["unicode"]).write(unicode(nxclass))
        return H5CppGroup(gr, self)

    def create_virtual_field(self, name, layout, fillvalue=0):
        """ creates a virtual filed tres element

        :param name: field name
        :type name: :obj:`str`
        :param layout: virual field layout
        :type layout: :class:`H5CppFieldLayout`
        :param fillvalue:  fill value
        :type fillvalue: :obj:`int` or :class:`np.ndarray`
        """
        if not is_vds_supported():
            raise Exception("VDS not supported")
        dcpl = h5cpp.property.DatasetCreationList()
        if fillvalue is not None:
            if hasattr(dcpl, "set_fill_value"):
                if isinstance(fillvalue, np.ndarray):
                    dcpl.set_fill_value(
                        fillvalue[0], pTh[str(fillvalue.dtype)])
                else:
                    dcpl.set_fill_value(
                        fillvalue, pTh[_tostr(layout.dtype)])
            else:
                raise Exception("VDS fill_value not supported")

        shape = layout.shape or [1]
        dataspace = h5cpp.dataspace.Simple(
            tuple(shape),
            tuple([h5cpp.dataspace.UNLIMITED] * len(shape)))
        vf = h5cpp.node.VirtualDataset(
            self._h5object, h5cpp.Path(name),
            pTh[_tostr(layout.dtype)], dataspace,
            layout._h5object, dcpl=dcpl)
        return H5CppField(vf, self)

    def create_field(self, name, type_code,
                     shape=None, chunk=None, dfilter=None):
        """ open a file tree element

        :param n: group name
        :type n: :obj:`str`
        :param type_code: nexus field type
        :type type_code: :obj:`str`
        :param shape: shape
        :type shape: :obj:`list` < :obj:`int` >
        :param chunk: chunk
        :type chunk: :obj:`list` < :obj:`int` >
        :param dfilter: filter deflater
        :type dfilter: :class:`H5CppDataFilter`
        :returns: file tree field
        :rtype: :class:`H5CppField`
        """
        dcpl = h5cpp.property.DatasetCreationList()
        if type_code in ["str", "unicode", "string"] and \
           shape is None and chunk is None:
            dataspace = h5cpp.dataspace.Scalar()
            return H5CppField(h5cpp.node.Dataset(
                self._h5object, h5cpp.Path(name),
                pTh[_tostr(type_code)], dataspace,
                dcpl=dcpl), self)
        else:
            shape = shape or [1]
            dataspace = h5cpp.dataspace.Simple(
                tuple(shape), tuple([h5cpp.dataspace.UNLIMITED] * len(shape)))
            if dfilter:
                if dfilter.filterid == 1:
                    h5object = dfilter.h5object
                    h5object.level = dfilter.rate
                else:
                    h5object = h5cpp.filter.ExternalFilter(
                        dfilter.filterid, list(dfilter.options))
                h5object(dcpl)
                if dfilter.shuffle:
                    sfilter = h5cpp.filter.Shuffle()
                    sfilter(dcpl)
            if chunk is None and shape is not None:
                chunk = [(dm if dm != 0 else 1) for dm in shape]
            dcpl.layout = h5cpp.property.DatasetLayout.CHUNKED
            dcpl.chunk = tuple(chunk)
            return H5CppField(h5cpp.node.Dataset(
                self._h5object, h5cpp.Path(name),
                pTh[_tostr(type_code)], dataspace,
                dcpl=dcpl), self)

    @property
    def size(self):
        """ group size

        :returns: group size
        :rtype: :obj:`int`
        """
        return self._h5object.links.size

    @property
    def attributes(self):
        """ return the attribute manager

        :returns: attribute manager
        :rtype: :class:`H5CppAttributeManager`
        """
        return H5CppAttributeManager(self._h5object.attributes, self)

    def close(self):
        """ close group
        """
        filewriter.FTGroup.close(self)

        if self._h5object.is_valid:
            self._h5object.close()

    def reopen(self):
        """ reopen group
        """
        if isinstance(self._tparent, H5CppFile):
            self._h5object = self._tparent.h5object.root()
        else:
            try:
                self._h5object = self._tparent.h5object.get_group(
                    h5cpp.Path(self.name))
            except Exception as e:
                logger.warning(str(e))
                # print(str(e))
                self._h5object = [lk for lk in self._tparent.h5object.links
                                  if lk.path.name == self.name][0]
        filewriter.FTGroup.reopen(self)

    def exists(self, name):
        """ if child exists

        :param name: child name
        :type name: :obj:`str`
        :returns: existing flag
        :rtype: :obj:`bool`
        """
        return name in [
            lk.path.name for lk in self._h5object.links]

    def names(self):
        """ read the child names

        :returns: h5 object
        :rtype: :obj:`list` <`str`>
        """
        return [
            lk.path.name for lk in self._h5object.links]

    class H5CppGroupIter(object):

        def __init__(self, group):
            """ constructor

            :param group: group object
            :type manager: :obj:`H5CppGroup`
            """

            self.__group = group
            self.__names = group.names()

        def __next__(self):
            """ the next attribute

            :returns: attribute object
            :rtype: :class:`FTAtribute`
            """
            if self.__names:
                return self.__group.open(self.__names.pop(0))
            else:
                raise StopIteration()

        next = __next__

        def __iter__(self):
            """ attribute iterator

            :returns: attribute iterator
            :rtype: :class:`H5CppAttrIter`
            """
            return self

    def __iter__(self):
        """ attribute iterator

        :returns: attribute iterator
        :rtype: :class:`H5CppAttrIter`
        """
        return self.H5CppGroupIter(self)

    @property
    def is_valid(self):
        """ check if field is valid

        :returns: valid flag
        :rtype: :obj:`bool`
        """
        return self._h5object.is_valid


class H5CppField(filewriter.FTField):

    """ file tree file
    """

    def __init__(self, h5object, tparent=None):
        """ constructor

        :param h5object: h5 object
        :type h5object: :obj:`any`
        :param tparent: treee parent
        :type tparent: :obj:`FTObject`
        """
        filewriter.FTField.__init__(self, h5object, tparent)
        #: (:obj:`str`) object nexus path
        self.path = ''
        #: (:obj:`str`) object name
        self.name = None
        if hasattr(h5object, "link"):
            self.name = h5object.link.path.name
            if tparent and tparent.path:
                if tparent.path == "/":
                    self.path = "/" + self.name
                else:
                    self.path = tparent.path + "/" + self.name
        #: (:obj:`bool`) bool flag
        # self.boolflag = False

    @property
    def attributes(self):
        """ return the attribute manager

        :returns: attribute manager
        :rtype: :class:`H5CppAttributeManager`
        """
        return H5CppAttributeManager(self._h5object.attributes, self)

    def close(self):
        """ close field
        """
        filewriter.FTField.close(self)
        if self._h5object.is_valid:
            self._h5object.close()

    def reopen(self):
        """ reopen field
        """
        try:
            self._h5object = self._tparent.h5object.get_dataset(
                h5cpp.Path(self.name))
        except Exception:
            self._h5object = [lk for lk in self._tparent.h5object.links
                              if lk.path.name == self.name][0]

        filewriter.FTField.reopen(self)

    def refresh(self):
        """ refresh the field

        :returns: refreshed
        :rtype: :obj:`bool`
        """
        self._h5object.refresh()
        return True

    def grow(self, dim=0, ext=1):
        """ grow the field

        :param dim: growing dimension
        :type dim: :obj:`int`
        :param dim: size of the grow
        :type dim: :obj:`int`
        """
        if self._h5object.dataspace.type != h5cpp.dataspace.Type.SCALAR:
            self._h5object.extent(dim, ext)

    def read(self):
        """ read the field value

        :returns: h5 object
        :rtype: :obj:`any`
        """
        if self.dtype in ['string', b'string']:
            # workaround for bug: h5cpp #355
            if self.size == 0:
                if self.shape:
                    v = np.empty(shape=self.shape,
                                 dtype=nptype(self.dtype))
                else:
                    v = []
            else:
                v = self._h5object.read()
            try:
                v = v.decode('UTF-8')
            except Exception:
                pass
        else:
            v = self._h5object.read()
        return v

    def write(self, o):
        """ write the field value

        :param o: h5 object
        :type o: :obj:`any`
        """
        self._h5object.write(o)

    def __setitem__(self, t, o):
        """ set value

        :param t: slice tuple
        :type t: :obj:`tuple`
        :param o: h5 object
        :type o: :obj:`any`
        """
        if self.shape == (1,) and t == 0:
            return self._h5object.write(o)
        selection = _slice2selection(t, self.shape)
        if selection is None:
            self._h5object.write(o)
        else:
            self._h5object.write(o, selection=selection)

    def __getitem__(self, t):
        """ get value

        :param t: slice tuple
        :type t: :obj:`tuple`
        :returns: h5 object
        :rtype: :obj:`any`
        """
        if self.shape == (1,) and t == 0:
            if self.dtype in ['string', b'string']:
                # workaround for bug: h5cpp #355
                if self.size == 0:
                    if self.shape:
                        v = np.empty(shape=self.shape, dtype=self.dtype)
                    else:
                        v = []
                else:
                    v = self._h5object.read()
            else:
                v = self._h5object.read()

        selection = _slice2selection(t, self.shape)
        if selection is None:
            if self.dtype in ['string', b'string']:
                # workaround for bug: h5cpp #355
                if self.size == 0:
                    if self.shape:
                        v = np.empty(shape=self.shape, dtype=self.dtype)
                    else:
                        v = []
                else:
                    v = self._h5object.read()
                try:
                    v = v.decode('UTF-8')
                except Exception:
                    pass
            else:
                v = self._h5object.read()
            return v
        v = self._h5object.read(selection=selection)
        # if hasattr(v, "shape") and hasattr(v, "reshape"):
        #     shape = [sh for sh in v.shape if sh != 1]
        #     if shape != list(v.shape):
        #         v.reshape(shape)
        if hasattr(v, "shape"):
            shape = v.shape
            if len(shape) == 3 and shape[2] == 1:
                #: problem with old numpy
                # v.reshape(shape[:2])
                v = v[:, :, 0]
                shape = v.shape
            if len(shape) == 3 and shape[1] == 1:
                # v.reshape([shape[0], shape[2]])
                v = v[:, 0, :]
                shape = v.shape
            if len(shape) == 3 and shape[0] == 1:
                # v.reshape([shape[1], shape[2]])
                v = v[0, :, :]
                shape = v.shape
            if len(shape) == 2 and shape[1] == 1:
                # v.reshape([shape[0]])
                v = v[0, :]
                shape = v.shape
            if len(shape) == 2 and shape[0] == 1:
                # v.reshape([shape[1]])
                v = v[:, 0]
                shape = v.shape
            if len(shape) == 1 and shape[0] == 1:
                v = v[0]
        if self.dtype in ['string', b'string']:
            try:
                v = v.decode('UTF-8')
            except Exception:
                pass
        return v

    @property
    def is_valid(self):
        """ check if field is valid

        :returns: valid flag
        :rtype: :obj:`bool`
        """
        return self._h5object.is_valid

    @property
    def dtype(self):
        """ field data type

        :returns: field data type
        :rtype: :obj:`str`
        """
        # if self.boolflag:
        #     return "bool"
        if str(self._h5object.datatype.type) == "FLOAT":
            if self._h5object.datatype.size == 8:
                return "float64"
            elif self._h5object.datatype.size == 4:
                return "float32"
            elif self._h5object.datatype.size == 16:
                return "float128"
            else:
                return "float"
        elif str(self._h5object.datatype.type) == "INTEGER":

            if self._h5object.datatype.size == 8:
                if self._h5object.datatype.is_signed():
                    return "int64"
                else:
                    return "uint64"
            elif self._h5object.datatype.size == 4:
                if self._h5object.datatype.is_signed():
                    return "int32"
                else:
                    return "uint32"
            elif self._h5object.datatype.size == 2:
                if self._h5object.datatype.is_signed():
                    return "int16"
                else:
                    return "uint16"
            elif self._h5object.datatype.size == 1:
                if self._h5object.datatype.is_signed():
                    return "int8"
                else:
                    return "uint8"
            elif self._h5object.datatype.size == 16:
                if self._h5object.datatype.is_signed():
                    return "int128"
                else:
                    return "uint128"
            else:
                return "int"
        elif str(self._h5object.datatype.type) == "ENUM":
            if h5cpp._datatype.is_bool(
                    h5cpp.datatype.Enum(self._h5object.datatype)):
                return "bool"
            else:
                return "int"

        return hTp[self._h5object.datatype.type]
#

    @property
    def shape(self):
        """ field shape

        :returns: field shape
        :rtype: :obj:`list` < :obj:`int` >
        """
        if hasattr(self._h5object.dataspace, "current_dimensions"):
            return self._h5object.dataspace.current_dimensions
        if self._h5object.dataspace.type == h5cpp.dataspace.Type.SCALAR:
            return ()
        else:
            return (1,)

    @property
    def size(self):
        """ field size

        :returns: field size
        :rtype: :obj:`int`
        """
        return self._h5object.dataspace.size


class H5CppLink(filewriter.FTLink):

    """ file tree link
    """

    def __init__(self, h5object, tparent=None):
        """ constructor

        :param h5object: h5 object
        :type h5object: :obj:`any`
        :param tparent: treee parent
        :type tparent: :obj:`FTObject`
        """
        filewriter.FTLink.__init__(self, h5object, tparent)
        #: (:obj:`str`) object nexus path
        self.path = ''
        #: (:obj:`str`) object name
        self.name = None
        if tparent and tparent.path:
            self.path = tparent.path
        if not self.path.endswith("/"):
            self.path += "/"
        self.name = h5object.path.name
        self.path += self.name

    @property
    def is_valid(self):
        """ check if link is valid

        :returns: valid flag
        :rtype: :obj:`bool`
        """
        try:
            return self._h5object.node.is_valid
        except Exception:
            return False

    def refresh(self):
        """ refresh the field

        :returns: refreshed
        :rtype: :obj:`bool`
        """
        self._h5object.refresh()
        return True

    @classmethod
    def getfilename(cls, obj):
        """ provides a filename from h5 node

        :param obj: h5 node
        :type obj: :class:`FTObject`
        :returns: file name
        :rtype: :obj:`str`
        """
        filename = ""
        while not filename:
            par = obj.parent
            if par is None:
                break
            if isinstance(par, H5CppFile):
                filename = par.name
                break
            else:
                obj = par
        return filename

    @property
    def target_path(self):
        """ target path

        :returns: target path
        :rtype: :obj:`str`
        """
        fpath = self._h5object.target().file_path
        opath = self._h5object.target().object_path
        if not fpath:
            fpath = self.getfilename(self)
        return "%s:/%s" % (fpath, opath)

    def reopen(self):
        """ reopen field
        """
        lks = self._tparent.h5object.links
        try:
            lk = [e for e in lks
                  if e.path.name == self.name][0]
            self._h5object = lk
        except Exception:
            self._h5object = None
        filewriter.FTLink.reopen(self)

    def close(self):
        """ close group
        """
        filewriter.FTLink.close(self)
        self._h5object = None


class H5CppDataFilter(filewriter.FTDataFilter):

    """ file tree deflate
    """


class H5CppVirtualFieldLayout(filewriter.FTVirtualFieldLayout):

    """ virtual field layout """

    def __init__(self, h5object, shape, dtype=None, maxshape=None):
        """ constructor

        :param h5object: h5 object
        :type h5object: :obj:`any`
        :param shape: shape
        :type shape: :obj:`list` < :obj:`int` >
        :param dtype: attribute type
        :type dtype: :obj:`str`
        :param maxshape: shape
        :type maxshape: :obj:`list` < :obj:`int` >
        """
        filewriter.FTVirtualFieldLayout.__init__(self, h5object)
        #: (:obj:`list` < :obj:`int` >) shape
        self.shape = shape
        # : (:obj:`str`): data type
        self.dtype = dtype
        #: (:obj:`list` < :obj:`int` >) maximal shape
        self.maxshape = maxshape

    def __setitem__(self, key, source):
        """ add target field to layout

        :param key: slide
        :type key: :obj:`tuple`
        :param source: target field view
        :type source: :class:`H5PYTargetFieldView`
        """
        self.add(key, source)

    def add(self, key, source, sourcekey=None, shape=None):
        """ add target field to layout

        :param key: slide
        :type key: :obj:`tuple`
        :param source: target field view
        :type source: :class:`H5PYTargetFieldView`
        :param sourcekey: slide or selection
        :type sourcekey: :obj:`tuple`
        :param shape: target shape in the layout
        :type shape: :obj:`tuple`
        """
        if shape is None:
            shape = list(source.shape or [])
            if hasattr(key, "__len__"):
                size = len(key)
                while len(shape) < size:
                    shape.insert(0, 1)
        lds = h5cpp.dataspace.Simple(tuple(shape))
        selection = None
        if key is not None and key != filewriter.FTHyperslab():
            selection = _slice2selection(key, shape)
            lview = h5cpp.dataspace.View(lds, selection)
        else:
            lview = h5cpp.dataspace.View(lds)
        sds = h5cpp.dataspace.Simple(tuple(shape))
        if sourcekey is not None and sourcekey != filewriter.FTHyperslab():
            srcsel = _slice2selection(sourcekey, source.shape)
            eview = h5cpp.dataspace.View(sds, srcsel)
        elif selection is not None:
            usel = unlimited_selection(selection, shape)
            if usel is not None:
                eview = h5cpp.dataspace.View(sds, usel)
            else:
                eview = h5cpp.dataspace.View(sds)
        else:
            eview = h5cpp.dataspace.View(sds)
        fname = source.filename
        path = h5cpp.Path(source.fieldpath)
        self._h5object.add(h5cpp.property.VirtualDataMap(
            lview, str(fname), path, eview))


class H5CppTargetFieldView(filewriter.FTTargetFieldView):

    """ target field for VDS """

    def __init__(self, filename, fieldpath, shape, dtype=None, maxshape=None):
        """ constructor

        :param filename: file name
        :type filename: :obj:`str`
        :param fieldpath: nexus field path
        :type fieldpath: :obj:`str`
        :param shape: shape
        :type shape: :obj:`list` < :obj:`int` >
        :param dtype: attribute type
        :type dtype: :obj:`str`
        :param maxshape: shape
        :type maxshape: :obj:`list` < :obj:`int` >
        """
        filewriter.FTTargetFieldView.__init__(self, None)
        #: (:obj:`str`) directory and file name
        self.filename = filename
        #: (:obj:`str`) nexus field path
        self.fieldpath = fieldpath
        #: (:obj:`list` < :obj:`int` >) shape
        self.shape = shape
        # : (:obj:`str`): data type
        self.dtype = dtype
        #: (:obj:`list` < :obj:`int` >) maximal shape
        self.maxshape = maxshape


class H5CppDeflate(H5CppDataFilter):

    """ deflate filter """


class H5CppAttributeManager(filewriter.FTAttributeManager):

    """ file tree attribute
    """

    def __init__(self, h5object, tparent=None):
        """ constructor

        :param h5object: h5 object
        :type h5object: :obj:`any`
        :param tparent: treee parent
        :type tparent: :obj:`FTObject`
        """
        filewriter.FTAttributeManager.__init__(self, h5object, tparent)
        #: (:obj:`str`) object nexus path
        self.path = ''
        #: (:obj:`str`) object name
        self.name = None

    def create(self, name, dtype, shape=None, overwrite=False):
        """ create a new attribute

        :param name: attribute name
        :type name: :obj:`str`
        :param dtype: attribute type
        :type dtype: :obj:`str`
        :param shape: attribute shape
        :type shape: :obj:`list` < :obj:`int` >
        :param overwrite: overwrite flag
        :type overwrite: :obj:`bool`
        :returns: attribute object
        :rtype: :class:`H5CppAtribute`
        """
        at = None
        names = [att.name for att in self._h5object]
        if name in names:
            if overwrite:
                try:
                    if str(self[name].dtype) == _tostr(dtype):
                        at = self._h5object[name]
                except Exception as e:
                    logger.warning(str(e))
                    # print(str(e))
                if at is None:
                    self._h5object.remove(name)
            else:
                raise Exception("Attribute %s exists" % name)
        shape = shape or []
        if shape:
            if at is None:
                at = self._h5object.create(name, pTh[_tostr(dtype)], shape)
            if dtype in ['string', b'string']:
                emp = np.empty(shape, dtype="unicode")
                emp[:] = ''
                at.write(emp)
            else:
                at.write(np.zeros(shape, dtype=dtype))
        else:
            if at is None:
                at = self._h5object.create(name, pTh[_tostr(dtype)])
            if dtype in ['string', b'string']:
                at.write(np.array(u"", dtype="unicode"))
            else:
                at.write(np.array(0, dtype=dtype))

        at = H5CppAttribute(at, self.parent)
        # if dtype == "bool":
        #     at.boolflag = True
        return at

    def __len__(self):
        """ number of attributes

        :returns: number of attributes
        :rtype: :obj:`int`
        """
        return self._h5object.__len__()

    def __getitem__(self, name):
        """ get value

        :param name: attribute name
        :type name: :obj:`str`
        :returns: attribute object
        :rtype: :class:`FTAtribute`
        """
        return H5CppAttribute(
            self._h5object.__getitem__(name), self.parent)

    def names(self):
        """ key values

        :returns: attribute names
        :rtype: :obj:`list` <:obj:`str`>
        """
        return [att.name for att in self._h5object]

    def close(self):
        """ close attribure manager
        """
        filewriter.FTAttributeManager.close(self)

    def reopen(self):
        """ reopen field
        """
        self._h5object = self._tparent.h5object.attributes
        filewriter.FTAttributeManager.reopen(self)

    @property
    def is_valid(self):
        """ check if link is valid

        :returns: valid flag
        :rtype: :obj:`bool`
        """
        return self._tparent.h5object.is_valid


class H5CppAttribute(filewriter.FTAttribute):

    """ file tree attribute
    """

    def __init__(self, h5object, tparent=None):
        """ constructor

        :param h5object: h5 object
        :type h5object: :obj:`any`
        :param tparent: treee parent
        :type tparent: :obj:`FTObject`
        """
        filewriter.FTAttribute.__init__(self, h5object, tparent)
        #: (:obj:`str`) object name
        self.name = h5object.name
        #: (:obj:`str`) object nexus path
        self.path = tparent.path
        self.path += "@%s" % self.name

        #: (:obj:`bool`) bool flag
        # self.boolflag = False

    def close(self):
        """ close attribute
        """
        filewriter.FTAttribute.close(self)
        if self._h5object.is_valid:
            self._h5object.close()

    def read(self):
        """ read attribute value

        :returns: python object
        :rtype: :obj:`any`
        """
        vl = self._h5object.read()
        if self.dtype in ['string', b'string']:
            try:
                vl = vl.decode('UTF-8')
            except Exception:
                pass
        return vl

    def write(self, o):
        """ write attribute value

        :param o: python object
        :type o: :obj:`any`
        """
        self._h5object.write(o)

    def __setitem__(self, t, o):
        """ write attribute value

        :param t: slice tuple
        :type t: :obj:`tuple`
        :param o: python object
        :type o: :obj:`any`
        """
        if t is Ellipsis or t == slice(None, None, None) or \
           t == (slice(None, None, None), slice(None, None, None)) or \
           (hasattr(o, "__len__") and t == slice(0, len(o), None)):
            if self.dtype in ['string', b'string']:
                if isinstance(o, str):
                    self._h5object.write(unicode(o))
                else:
                    dtype = np.unicode_
                    self._h5object.write(np.array(o, dtype=dtype))
            else:
                self._h5object.write(np.array(o, dtype=self.dtype))
        elif isinstance(t, slice):
            var = self._h5object.read()
            if self.dtype not in ['string', b'string']:
                var[t] = np.array(o, dtype=nptype(self.dtype))
            else:
                dtype = np.unicode_
                var[t] = np.array(o, dtype=dtype)
                var = var.astype(dtype)
            try:
                self._h5object.write(var)
            except Exception:
                dtype = np.unicode_
                tvar = np.array(var, dtype=dtype)
                self._h5object[0][self.name] = tvar

        elif isinstance(t, tuple):
            var = self._h5object.read()
            if self.dtype not in ['string', b'string']:
                var[t] = np.array(o, dtype=nptype(self.dtype))
            else:
                dtype = np.unicode_
                if hasattr(var, "flatten"):
                    vv = var.flatten().tolist() + \
                        np.array(o, dtype=dtype).flatten().tolist()
                    nt = np.array(vv, dtype=dtype)
                    var = np.array(var, dtype=nt.dtype)
                    var[t] = np.array(o, dtype=dtype)
                elif hasattr(var, "tolist"):
                    var = var.tolist()
                    var[t] = np.array(o, dtype=self.dtype).tolist()
                else:
                    var[t] = np.array(o, dtype=self.dtype).tolist()
                var = var.astype(dtype)
            self._h5object.write(var)
        else:
            if isinstance(o, str) or isinstance(o, unicode):
                self._h5object.write(unicode(o))
            else:
                self._h5object.write(np.array(o, dtype=self.dtype))

    def __getitem__(self, t):
        """ read attribute value

        :param t: slice tuple
        :type t: :obj:`tuple`
        :returns: python object
        :rtype: :obj:`any`
        """
        v = self._h5object.__getitem__(t)
        # if hasattr(v, "shape") and hasattr(v, "reshape"):
        #     shape = [sh for sh in v.shape if sh != 1]
        #     if shape != list(v.shape):
        #         v.reshape(shape)
        if hasattr(v, "shape"):
            shape = v.shape
            if len(shape) == 3 and shape[2] == 1:
                #: problem with old numpy
                # v.reshape(shape[:2])
                v = v[:, :, 0]
                shape = v.shape
            if len(shape) == 3 and shape[1] == 1:
                # v.reshape([shape[0], shape[2]])
                v = v[:, 0, :]
                shape = v.shape
            if len(shape) == 3 and shape[0] == 1:
                # v.reshape([shape[1], shape[2]])
                v = v[0, :, :]
                shape = v.shape
            if len(shape) == 2 and shape[1] == 1:
                # v.reshape([shape[0]])
                v = v[0, :]
                shape = v.shape
            if len(shape) == 2 and shape[0] == 1:
                # v.reshape([shape[1]])
                v = v[:, 0]
                shape = v.shape
            if len(shape) == 1 and shape[0] == 1:
                v = v[0]
        if self.dtype in ['string', b'string']:
            try:
                v = v.decode('UTF-8')
            except Exception:
                pass
        return v

    @property
    def is_valid(self):
        """ check if attribute is valid

        :returns: valid flag
        :rtype: :obj:`bool`
        """
        return self._h5object.is_valid

    @property
    def dtype(self):
        """ field data type

        :returns: field data type
        :rtype: :obj:`str`
        """
        # if self.boolflag:
        #     return "bool"
        if str(self._h5object.datatype.type) == "FLOAT":
            if self._h5object.datatype.size == 8:
                return "float64"
            elif self._h5object.datatype.size == 4:
                return "float32"
            elif self._h5object.datatype.size == 16:
                return "float128"
            else:
                return "float"
        elif str(self._h5object.datatype.type) == "INTEGER":
            if self._h5object.datatype.size == 8:
                if self._h5object.datatype.is_signed():
                    return "int64"
                else:
                    return "uint64"
            elif self._h5object.datatype.size == 4:
                if self._h5object.datatype.is_signed():
                    return "int32"
                else:
                    return "uint32"
            elif self._h5object.datatype.size == 2:
                if self._h5object.datatype.is_signed():
                    return "int16"
                else:
                    return "uint16"
            elif self._h5object.datatype.size == 1:
                if self._h5object.datatype.is_signed():
                    return "int8"
                else:
                    return "uint8"
            elif self._h5object.datatype.size == 16:
                if self._h5object.datatype.is_signed():
                    return "int128"
                else:
                    return "uint128"
            else:
                return "int"
        elif str(self._h5object.datatype.type) == "ENUM":
            if h5cpp._datatype.is_bool(
                    h5cpp.datatype.Enum(self._h5object.datatype)):
                return "bool"
            else:
                return "int"
        return hTp[self._h5object.datatype.type]

    @property
    def shape(self):
        """ attribute shape

        :returns: attribute shape
        :rtype: :obj:`list` < :obj:`int` >
        """
        if hasattr(self._h5object.dataspace, "current_dimensions"):
            return self._h5object.dataspace.current_dimensions
        if self._h5object.dataspace.type == h5cpp.dataspace.Type.SCALAR:
            return ()
        else:
            return (1,)

    def reopen(self):
        """ reopen attribute
        """
        self._h5object = self._tparent.h5object.attributes[self.name]
        filewriter.FTAttribute.reopen(self)
