import time
import warnings
from collections import defaultdict
import os
import h5py
import numpy as np
from tqdm.autonotebook import tqdm

import larpix.format.rawhdf5format as rh5
import larpix.format.hdf5format as h5
import larpix.format.hdf5format_direct as h5_direct
from larpix.format.pacman_msg_format import parse
from larpix import PacketCollection

class FileParser(object):
    max_read = 256000

    def __init__(self, temp_dir, sampling, max_msgs, clean_up_interval, use_numba=False):
        self.sampling = sampling
        self.max_msgs = max_msgs
        self.clean_up_interval = clean_up_interval
        self.temp_dir = temp_dir
        self.use_numba = use_numba

        self._curr_index = defaultdict(int)
        self._last_updated = defaultdict(lambda : time.time())

    def __call__(self, datafiles):
        datafile_fh = list()
        for file in tqdm(datafiles, desc='Loading file...'):
            try:
                datafile_fh.append(self._load_raw_hdf5(file))
            except Exception as e:
                warnings.warn('could not load {} as raw hdf5! \nError: {}'.format(file, e), RuntimeWarning)
                datafile_fh.append(dict(packets=np.empty((0,))))

            self._last_updated[file] = time.time()

        self._clean_up()

        return datafile_fh

    def clean_up_temp_files(self, datafiles):
        for file in datafiles:
            try:
                self._remove_temp_file(file)
            except Exception as e:
                warnings.warning('could not clear temp file for {} \nError: {}'.format(file, e), RuntimeWarning)

    def _load_raw_hdf5(self, filename):
        length = rh5.len_rawfile(filename)

        start_idx = self._curr_index[filename]
        end_idx = min(length, self.max_msgs+self._curr_index[filename]) if self.max_msgs > 0 else length
        for start in range(start_idx, end_idx, self.max_read):
            end = min(start+self.max_read, end_idx)

            rd = rh5.from_rawfile(filename, start=start, end=end)

            if self.use_numba:
                h5_direct.to_file_direct(self._temp_filename(filename),
                                         rd['msgs'], rd['msg_headers']['io_groups'])
            else:
                pkts = list()
                for io_group,msg in zip(rd['msg_headers']['io_groups'], rd['msgs']):
                    pkts.extend(parse(msg, io_group=io_group))
                h5.to_file(self._temp_filename(filename), pkts, workers=2)

            self._curr_index[filename] = end

            if start > start_idx:
                print('\tloaded {}/{}...'.format(end-start_idx,end_idx-start_idx), end='\r')

        if self.sampling:
            self._curr_index[filename] = length

        return h5py.File(self._temp_filename(filename), 'r')

    def _temp_filename(self, filename):
        return os.path.join(self.temp_dir,'{}.dqm.h5'.format(os.path.basename(filename[:-3])))

    def _remove_temp_file(self, filename):
        if os.path.exists(self._temp_filename(filename)):
            os.remove(self._temp_filename(filename))

    def _clean_up(self):
        to_clean = []
        for filename,last in self._last_updated.items():
            if time.time() > last + self.clean_up_interval:
                to_clean.append(filename)
        for filename in to_clean:
            del self._last_updated[filename]
            if filename in self._curr_index:
                del self._curr_index[filename]

