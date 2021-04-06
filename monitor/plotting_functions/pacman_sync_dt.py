'''Plot the time differences in the PACMAN SYNC timestamps relative to the
PPS.

A. Mastbaum <mastbaum@physics.rutgers.edu>, 2021/04/02
'''

import matplotlib.pyplot as plt
import numpy as np
import os

class PacmanSyncHistograms(object):
    def __call__(self, filename, fh, fig=None):
        p = fh['packets']
        
        # Extract sync packets by IO group
        # Type 6 = SyncPacket and chr(83) = 'S' = SYNC
        sync_mask = ((p['packet_type'] == 6)&(p['trigger_type'] == 83))
        groups = p['io_group']
        syncs = [ (g, p[sync_mask&(groups==g)]) for g in np.unique(groups) ]
        
        # Plot
        if fig is None:
            fig = plt.figure(figsize=(8, 6))

        gs = fig.add_gridspec(1, 2,  width_ratios=(2,1), height_ratios=(1,),
                              left=0.1, right=0.9, bottom=0.1, top=0.9,
                              wspace=0.05, hspace=0.05)

        ax0 = fig.add_subplot(gs[0,1])
        ax1 = fig.add_subplot(gs[0,0], sharey=ax0)

        for group, sync in syncs:
            ts = sync['timestamp'] - 1e7
            mu, std = np.mean(ts), np.std(ts)
            vmin, vmax = np.min(ts) - 1, np.max(ts) + 1
            bins = np.arange(vmin, vmax)

            # Time series plot of Delta ts
            label = r'io_group %i: $\Delta t=%1.2f\pm%1.2f$' % (group, mu, std)
            ax1.plot(ts, '.', label=label)

            # Sideways histogram of Delta ts
            ax0.hist(ts, bins=bins, histtype='step', lw=2, orientation='horizontal')

        ax0.tick_params(axis="y", labelleft=False)
        ax1.legend(loc='best')
        ax1.set_ylabel('timestamp - 1E7')
        ax1.set_xlabel('Timestamp packet')
        ax0.set_xlabel('# Packets')
        fig.suptitle(r'Sync packet $\Delta t$: %s' % filename.split(os.sep)[-1])

        return fig

