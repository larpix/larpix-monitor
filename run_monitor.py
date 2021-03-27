#!/usr/bin/env python3
import argparse
import json
import os
import datetime

from monitor.file_watcher import FileWatcher
from monitor.file_parser import FileParser
from monitor.plotter import Plotter
from monitor.plotting_functions import available_plots

def main(**kwargs):

    fw = FileWatcher(
        directory=kwargs.get('in_directory','./'),
        interval=kwargs.get('interval')
        )
    fp = FileParser(
        clean_up_interval=kwargs.get('flush_interval')
        )
    p  = Plotter(
        plots=kwargs.get('plots'),
        clean_up_interval=kwargs.get('flush_interval')
        )

    while True:
        if kwargs.get('once',None):
            datafiles = [kwargs['once']]
        else:
            datafiles = fw()
            print(datetime.datetime.now(), end='\r')

        if not datafiles: continue
        print('',end='\n')
        print('\tnew data in',datafiles)

        datafile_packets = fp(datafiles)
        print('\tgot',sum(map(lambda fh: len(fh['packets']),datafile_packets)),'packets')

        datafile_figs = p(zip(datafiles, datafile_packets))
        print('\tgenerated',sum(map(len,datafile_figs)),'plots')

        for filename,figs in zip(datafiles,datafile_figs):
            dir_name = os.path.join(kwargs.get('out_directory'), os.path.basename(filename[:-3]) + '_dqm')
            for fig_name, fig in figs.items():
                os.makedirs(dir_name, exist_ok=True)
                fig.savefig(os.path.join(
                    dir_name, fig_name + kwargs.get('ext')
                    ))
            print('\tdone writing to',dir_name)

        if kwargs.get('once',None):
            break

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run the LArPix data quality monitor')
    parser.add_argument('-i','--in_directory', type=str, required=False, default='./', help='''
        Directory to watch (default=%(default)s)
        ''')
    parser.add_argument('-o','--out_directory', type=str, required=False, default='./', help='''
        Directory to save plots (default=%(default)s)
        ''')
    parser.add_argument('--interval', type=float, required=False, default=30., help='''
        File update interval [s] (default=%(default)s)
        ''')
    parser.add_argument('--once', type=str, required=False, help='''
        Run once on passed file and then exit, otherwise continously monitor for new data
        ''')
    parser.add_argument('--flush_interval', type=float, required=False, default=1800., help='''
        Memory cleaning interval [s] (default=%(default)s)
        ''')
    parser.add_argument('--ext', type=str, required=False, default='.png', help='''
        File extension to save plots as (default=%(default)s)
        ''')
    parser.add_argument('--plots', nargs='+', type=str, required=False, default=available_plots, help='''
        Plot names to generate (default=%(default)s)
        ''')
    args = parser.parse_args()
    main(**vars(args))
