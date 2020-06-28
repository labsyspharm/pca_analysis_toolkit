from __future__ import print_function, division
import warnings
import sys
import os
import re
import io
import struct
import itertools
import uuid
import multiprocessing
import concurrent.futures
import numpy as np
import skimage.io
import tifffile
import skimage.transform
import pytiff


def preduce(coords, img_in, img_out):
    (iy1, ix1), (iy2, ix2) = coords
    (oy1, ox1), (oy2, ox2) = np.array(coords) // 2
    tile = img_in[iy1:iy2, ix1:ix2]
    tile = skimage.transform.pyramid_reduce(tile, multichannel=False)
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore', 'Possible precision loss')
        tile = skimage.util.dtype.convert(tile, img_out.dtype)
    img_out[oy1:oy2, ox1:ox2] = tile


def imsave(path, img, tile_size, **kwargs):
    tifffile.imsave(
        path, img, bigtiff=True, append=True, tile=(tile_size, tile_size),
        metadata=None, **kwargs
    )


def format_shape(shape):
    return "%dx%d" % (shape[1], shape[0])


def construct_xml(filename, shapes, num_channels, dtype, pixel_size=1,
        channel_name_list=None):
    if channel_name_list is None:
        channel_name_list = ['Channel {}'.format(i) for i in range(num_channels)]

    img_uuid = uuid.uuid4().urn
    if dtype == np.uint16:
        ome_dtype = 'uint16'
    elif dtype == np.uint8:
        ome_dtype = 'uint8'
    else:
        raise ValueError("can't handle dtype: %s" % dtype)
    ifd = 0
    xml = io.StringIO()
    xml.write(u'<?xml version="1.0" encoding="UTF-8"?>')
    xml.write(
        (u'<OME xmlns="http://www.openmicroscopy.org/Schemas/OME/2016-06"'
         ' xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"'
         ' UUID="{uuid}"'
         ' xsi:schemaLocation="http://www.openmicroscopy.org/Schemas/OME/2016-06'
         ' http://www.openmicroscopy.org/Schemas/OME/2016-06/ome.xsd">')
        .format(uuid=img_uuid)
    )
    for level, shape in enumerate(shapes):
        if level == 0:
            psize_xml = (
                u'PhysicalSizeX="{0}" PhysicalSizeXUnit="\u00b5m"'
                u' PhysicalSizeY="{0}" PhysicalSizeYUnit="\u00b5m"'
                .format(pixel_size)
            )
        else:
            psize_xml = u''
        xml.write(u'<Image ID="Image:{}">'.format(level))
        xml.write(
            (u'<Pixels BigEndian="false" DimensionOrder="XYZCT"'
             ' ID="Pixels:{level}" {psize_xml} SizeC="{num_channels}" SizeT="1"'
             ' SizeX="{sizex}" SizeY="{sizey}" SizeZ="1" Type="{ome_dtype}">')
            .format(
                level=level, psize_xml=psize_xml, num_channels=num_channels,
                sizex=shape[1], sizey=shape[0], ome_dtype=ome_dtype
            )
        )
        for channel, channel_name in zip(range(num_channels), channel_name_list):
            xml.write(
                (u'<Channel ID="Channel:{level}:{channel}"'
                 + (u' Name="{channel_name}"' if level == 0 else u'')
                 + u' SamplesPerPixel="1"><LightPath/></Channel>')
                .format(level=level, channel=channel, channel_name=channel_name)
            )
        for channel in range(num_channels):
            xml.write(
                (u'<TiffData FirstC="{channel}" FirstT="0" FirstZ="0"'
                 ' IFD="{ifd}" PlaneCount="1">'
                 '<UUID FileName="{filename}">{uuid}</UUID>'
                 '</TiffData>')
                .format(
                    channel=channel, ifd=ifd, filename=filename, uuid=img_uuid
                )
            )
            ifd += 1
        if level == 0:
            for channel in range(num_channels):
                xml.write(
                    u'<Plane TheC="{channel}" TheT="0" TheZ="0"/>'
                    .format(channel=channel)
                )
        xml.write(u'</Pixels>')
        xml.write(u'</Image>')
    xml.write(u'</OME>')
    xml_bytes = xml.getvalue().encode('utf-8') + b'\x00'
    return xml_bytes


def patch_ometiff_xml(path, xml_bytes):
    with open(path, 'rb+') as f:
        f.seek(0, io.SEEK_END)
        xml_offset = f.tell()
        f.write(xml_bytes)
        f.seek(0)
        ifd_block = f.read(500)
        match = re.search(b'!!xml!!\x00', ifd_block)
        if match is None:
            raise RuntimeError("Did not find placeholder string in IFD")
        f.seek(match.start() - 8)
        f.write(struct.pack('<Q', len(xml_bytes)))
        f.write(struct.pack('<Q', xml_offset))


def main(array_list, channel_name_list=None, out_path=None, tile_size=1024):
    if hasattr(os, 'sched_getaffinity'):
        num_workers = len(os.sched_getaffinity(0))
    else:
        num_workers = multiprocessing.cpu_count()

    if channel_name_list is None:
        channel_name_list = [str(i+1) for i in range(len(array_list))]

    if out_path is None:
        out_path = './out.ome.tif'

    if os.path.exists(out_path):
        print("%s already exists, aborting" % out_path)
        sys.exit(1)

    print("Appending input images")
    for i, img_in in enumerate(array_list):
        print("    %d: %s" % (i + 1, channel_name_list[i]))
        if i == 0:
            base_shape = img_in.shape
            dtype = img_in.dtype
            kwargs = {
                'description': '!!xml!!',
                'software': 'Glencoe/Faas pyramid'
            }
        else:
            if img_in.shape != base_shape:
                print(
                    "%s: expected shape %s, got %s"
                    % (channel_name_list[i], base_shape, img_in.shape)
                )
                sys.exit(1)
            if img_in.dtype != dtype:
                print(
                    "%s: expected dtype %s, got %s"
                    % (channel_name_list[i], dtype, img_in.dtype)
                )
                sys.exit(1)
            kwargs = {}
        imsave(out_path, img_in, tile_size, **kwargs)
    print()

    num_channels = len(channel_name_list)
    num_levels = np.ceil(np.log2(max(base_shape) / tile_size)) + 1
    factors = 2 ** np.arange(num_levels)
    shapes = (np.ceil(np.array(base_shape) / factors[:,None])).astype(int)

    print("Pyramid level sizes:")
    for i, shape in enumerate(shapes):
        print("    level %d: %s" % (i + 1, format_shape(shape)), end="")
        if i == 0:
            print(" (original size)", end="")
        print()
    print()

    executor = concurrent.futures.ThreadPoolExecutor(num_workers)

    shape_pairs = zip(shapes[:-1], shapes[1:])
    for level, (shape_in, shape_out) in enumerate(shape_pairs):

        print(
            "Resizing images for level %d (%s -> %s)"
            % (level + 2, format_shape(shape_in), format_shape(shape_out))
        )

        ty = np.array(range(0, shape_in[0], tile_size))
        tx = np.array(range(0, shape_in[1], tile_size))
        coords = list(zip(
            itertools.product(ty, tx),
            itertools.product(ty + tile_size, tx + tile_size)
        ))
        img_in = pytiff.Tiff(out_path)
        img_out = np.empty(shape_out, dtype)

        for c in range(num_channels):

            page = level * num_channels + c
            img_in.set_page(page)
            for i, _ in enumerate(executor.map(
                preduce, coords,
                itertools.repeat(img_in), itertools.repeat(img_out)
            )):
                percent = int((i + 1) / len(coords) * 100)
                if i % 20 == 0 or percent == 100:
                    print("\r    %d: %d%%" % (c + 1, percent), end='')
                    sys.stdout.flush()
            imsave(out_path, img_out, tile_size)
            print()

        img_in.close()
        print()

    xml = construct_xml(os.path.basename(out_path), shapes, num_channels, dtype, 0.325,
            channel_name_list=channel_name_list)
    patch_ometiff_xml(out_path, xml)

