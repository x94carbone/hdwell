#!/usr/bin/env python3

__author__ = "Matthew R. Carbone & Marco Baity-Jesi"
__maintainer__ = "Matthew R. Carbone & Marco Baity-Jesi"
__email__ = "x94carbone@gmail.com"
__status__ = "Prototype"


import os
import pickle
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import logging
from cycler import cycler

from .aux import order_of_magnitude, hxw
from .templates import PLOTTING_INFO_TEMPLATE, PLOTTING_PROTOCOL_MAP

from . import logger  # noqa
lg = logging.getLogger(__name__)

# Custom color cycle.
mpl.rcParams['axes.prop_cycle'] = cycler('color', ['b', 'c', '#ffdb00',
                                                   'mediumseagreen', '#ffa904',
                                                   'pink', '#ee7b06',
                                                   '#a12424', '#400b0b', 'r'])

AVAILABLE_PLOTTING_PARAMETERS = [1]


def plot_actual(run_path, params, df):
    plotting_params = params['plot']

    if plotting_params['protocol'] not in AVAILABLE_PLOTTING_PARAMETERS:
        raise RuntimeError("Unsupported plotting protocol %i"
                           % plotting_params['protocol'])

    p = PLOTTING_PROTOCOL_MAP[plotting_params['protocol']]
    dpi = plotting_params['dpi']

    # First step: read in all data corresponding to the four observables in
    # question: avg e, psi basin/config and the memory function.
    # TODO: memory function
    df = df.sort_values(by=[p['group_by'], p['to_plot']])

    if p['plot_maxes']:
        df = df.query('nmc == "%s" and nvec == "%s"'
                      % (str(np.max(df.nmc.unique())),
                         str(np.max(df.nvec.unique()))))

    groups = df[p['group_by']].unique()
    zfill_index = order_of_magnitude(1 + np.max(df['loc'].unique())) + 1

    # Clear past figures and initialize a new one.
    # Average energy ----------------------------------------------------------
    plt.clf()
    plt.figure(figsize=(8.5, 11))

    lg.info("Average Energy...")
    for ii, g in enumerate(groups):
        lg.info("%i // %i" % (ii, g))

        plt.gca().set_prop_cycle(None)  # Reset colormap
        ax = plt.subplot(len(groups), 1, ii + 1)

        # For each group, plot 'to_plot'.
        df_temp = df.query('%s == "%s"' % (p['group_by'], g))

        for index, row in df_temp.iterrows():
            # Load in the average energies.
            loc_str = str(row['loc']).zfill(zfill_index)
            energy_path = os.path.join(run_path, loc_str, 'avg_e.pkl')
            sample_e_path = os.path.join(run_path, loc_str, 'sample_e.pkl')
            avg_e = pickle.load(open(energy_path, 'rb'))
            sample_e = pickle.load(open(sample_e_path, 'rb'))
            if ii == 0:
                label = "%s" % row['beta']
            else:
                label = None
            if p['avg_e_scale'] == 'log':
                plt.semilogx(sample_e, avg_e, 'o', markersize=0.5, label=label)
            else:
                plt.plot(sample_e, avg_e, 'o', markersize=0.5, label=label)
            plt.ylabel(r"$\langle E \rangle(t)$")

            if index == len(df_temp.index) - 1:
                plt.xlabel(r"$t$")

        plt.text(0.5, 0.05, "%s = %i" % (p['group_by'], g),
                 ha='center', va='top', transform=ax.transAxes, fontsize=14)

        if p['avg_e_scale'] == 'log':
            # This is not efficient. TODO: refactor.

            sample_e_log = np.log10(sample_e)
            last_n = p['last_n_points']

            plt.gca().set_prop_cycle(None)  # Reset colormap
            for index, row in df_temp.iterrows():
                loc_str = str(row['loc']).zfill(zfill_index)
                energy_path = os.path.join(run_path, loc_str, 'avg_e.pkl')
                sample_e_path = os.path.join(run_path, loc_str, 'sample_e.pkl')
                sample_e = pickle.load(open(sample_e_path, 'rb'))
                avg_e = pickle.load(open(energy_path, 'rb'))
                m = np.polyfit(sample_e_log[-last_n:], avg_e[-last_n:], deg=1)
                best_fit = np.polyval(m, sample_e_log)
                plt.semilogx(sample_e, best_fit, '--', alpha=0.5,
                             label="y = %.02f * x + %.02f" % (m[0], m[1]))

        plt.ylim(top=0.0)

        # Only need one legend.
        plt.legend(title="%s" % p['to_plot'], fontsize=6)

        if ii != len(groups) - 1:
            plt.tick_params(labelbottom=False)

    plt.subplots_adjust(hspace=0.05)

    plt.savefig(os.path.join(run_path, 'avg_e.pdf'), dpi=dpi,
                bbox_inches='tight')

    # Psi config --------------------------------------------------------------
    plt.clf()
    plt.figure(figsize=(8.5, 11))

    lg.info("Psi Config...")
    for ii, g in enumerate(groups):
        lg.info("%i // %i" % (ii, g))

        plt.gca().set_prop_cycle(None)  # Reset colormap
        ax = plt.subplot(len(groups), 1, ii + 1)
        ax.tick_params(axis='both', which='minor')

        # For each group, plot 'to_plot'.
        df_temp = df.query('%s == "%s"' % (p['group_by'], g))

        for index, row in df_temp.iterrows():
            # Load in the average energies.
            loc_str = str(row['loc']).zfill(zfill_index)
            psi_config_path = os.path.join(run_path, loc_str, 'psi_config.pkl')
            psi_config = pickle.load(open(psi_config_path, 'rb'))

            xgrid = []
            ygrid = []
            for key, value in psi_config.items():
                xgrid.append(2**key)
                ygrid.append(value)

            xgrid = np.array(xgrid)
            ygrid = np.array(ygrid)
            ygrid = ygrid / np.max(ygrid)

            if index == len(df_temp.index) - 1:
                plt.xlabel(r"$\tau$")

            if ii == 0:
                label = "%s" % row['beta']
            else:
                label = None

            if xgrid == []:
                continue

            plt.loglog(xgrid, ygrid, 'o', markersize=5, label=label)

            plt.ylabel(r"$\psi_C(t)$")
            ax.tick_params(axis='both', which='minor')

        plt.text(0.5, 0.05, "%s = %i" % (p['group_by'], g),
                 ha='center', va='top', transform=ax.transAxes, fontsize=14)

        last_n = p['last_n_points']

        # Add best fit lines
        plt.gca().set_prop_cycle(None)  # Reset colormap
        for index, row in df_temp.iterrows():

            loc_str = str(row['loc']).zfill(zfill_index)
            psi_config_path = os.path.join(run_path, loc_str, 'psi_config.pkl')
            psi_config = pickle.load(open(psi_config_path, 'rb'))

            xgrid = []
            ygrid_ = []
            for key, value in psi_config.items():
                xgrid.append(2**key)
                ygrid_.append(value)

            xgrid = np.array(xgrid[:-2])
            ygrid = np.array(ygrid_[:-2])
            ygrid = ygrid / np.max(ygrid_)

            logx = np.log10(xgrid)
            logy = np.log10(ygrid)
            m = np.polyfit(logx, logy, deg=1)
            poly = np.poly1d(m)

            def yfit(x):
                return 10.0**(poly(np.log10(x)))

            plt.plot(xgrid, yfit(xgrid), '--', alpha=0.5,
                     label="y = %.02f * x + %.02f" % (m[0], m[1]))

        plt.ylim(bottom=0.0)

        # Only need one legend.
        plt.legend(title="%s" % p['to_plot'], fontsize=6)

        if ii != len(groups) - 1:
            plt.tick_params(labelbottom=False)

    plt.subplots_adjust(hspace=0.05)

    plt.savefig(os.path.join(run_path, 'psi_config.pdf'), dpi=dpi,
                bbox_inches='tight')

    # Psi basin ---------------------------------------------------------------
    plt.clf()
    plt.figure(figsize=(8.5, 11))

    lg.info("Psi Basin...")
    for ii, g in enumerate(groups):
        lg.info("%i // %i" % (ii, g))

        plt.gca().set_prop_cycle(None)  # Reset colormap
        ax = plt.subplot(len(groups), 1, ii + 1)
        ax.tick_params(axis='both', which='minor')

        # For each group, plot 'to_plot'.
        df_temp = df.query('%s == "%s"' % (p['group_by'], g))

        for index, row in df_temp.iterrows():
            # Load in the average energies.
            loc_str = str(row['loc']).zfill(zfill_index)
            psi_basin_path = os.path.join(run_path, loc_str, 'psi_basin.pkl')
            psi_basin = pickle.load(open(psi_basin_path, 'rb'))

            xgrid = []
            ygrid = []
            for key, value in psi_basin.items():
                xgrid.append(2**key)
                ygrid.append(value)

            if index == len(df_temp.index) - 1:
                plt.xlabel(r"$\tau$")

            if ii == 0:
                label = "%s" % row['beta']
            else:
                label = None

            if xgrid == []:
                continue

            xgrid = np.array(xgrid)
            ygrid = np.array(ygrid)
            ygrid = ygrid / np.max(ygrid)

            plt.loglog(xgrid, ygrid, 'o', markersize=5, label=label)
            ax.tick_params(axis='both', which='minor')

            plt.ylabel(r"$\psi_B(t)$")

        plt.text(0.5, 0.05, "%s = %i" % (p['group_by'], g),
                 ha='center', va='top', transform=ax.transAxes, fontsize=14)

        last_n = p['last_n_points']

        plt.gca().set_prop_cycle(None)  # Reset colormap
        for index, row in df_temp.iterrows():

            loc_str = str(row['loc']).zfill(zfill_index)
            psi_basin_path = os.path.join(run_path, loc_str, 'psi_basin.pkl')
            psi_basin = pickle.load(open(psi_basin_path, 'rb'))

            xgrid_ = []
            ygrid_ = []
            for key, value in psi_basin.items():
                xgrid_.append(2**key)
                ygrid_.append(value)

            if xgrid_ == []:
                continue

            xgrid = np.array(xgrid_[4:-2])
            ygrid = np.array(ygrid_[4:-2])

            try:
                ygrid = ygrid / np.max(ygrid_)
            except ValueError:
                xgrid = np.array(xgrid_[:-1])
                ygrid = np.array(ygrid_[:-1])
                ygrid = ygrid / np.max(ygrid_)

            logx = np.log10(xgrid)
            logy = np.log10(ygrid)
            m = np.polyfit(logx, logy, deg=1)
            poly = np.poly1d(m)

            def yfit(x):
                return 10.0**(poly(np.log10(x)))

            plt.plot(xgrid, yfit(xgrid), '--', alpha=0.5,
                     label="y = %.02f * x + %.02f" % (m[0], m[1]))

        plt.ylim(bottom=0.0)

        # Only need one legend.
        plt.legend(title="%s" % p['to_plot'], fontsize=6)

        if ii != len(groups) - 1:
            plt.tick_params(labelbottom=False)

    plt.subplots_adjust(hspace=0.05)

    plt.savefig(os.path.join(run_path, 'psi_basin.pdf'), dpi=dpi,
                bbox_inches='tight')

    # Memory config -----------------------------------------------------------
    plt.clf()
    plt.figure(figsize=(8.5, 11))

    lg.info("Pi Config...")
    for ii, g in enumerate(groups):
        lg.info("%i // %i" % (ii, g))

        plt.gca().set_prop_cycle(None)  # Reset colormap
        ax = plt.subplot(len(groups), 1, ii + 1)
        ax.tick_params(axis='both', which='minor')

        # For each group, plot 'to_plot'.
        df_temp = df.query('%s == "%s"' % (p['group_by'], g))

        for index, row in df_temp.iterrows():
            # Load in the average energies.
            loc_str = str(row['loc']).zfill(zfill_index)
            pi_basin_path = os.path.join(run_path, loc_str,
                                         'memory_config.pkl')
            pi_basin = pickle.load(open(pi_basin_path, 'rb'))
            ygrid = pi_basin[0]
            xgrid = pi_basin[1]
            delta = pi_basin[2]

            if index == len(df_temp.index) - 1:
                plt.xlabel(r"$\tau$")

            if ii == 0:
                label = "%s" % row['beta']
            else:
                label = None

            if xgrid == []:
                continue

            xgrid = np.array(xgrid)
            ygrid = np.array(ygrid)
            ygrid = ygrid / row['nvec']

            plt.loglog(xgrid, ygrid, 'o', markersize=5, label=label)
            ax.tick_params(axis='both', which='minor')

            plt.ylabel(r"$\Pi_C(t_w, t_w + %.02f t_w)$" % delta)

        plt.text(0.5, 0.05, "%s = %i" % (p['group_by'], g),
                 ha='center', va='top', transform=ax.transAxes, fontsize=14)

        plt.ylim(bottom=0.0)

        # Only need one legend.
        plt.legend(title="%s" % p['to_plot'], fontsize=6)

        if ii != len(groups) - 1:
            plt.tick_params(labelbottom=False)

    plt.subplots_adjust(hspace=0.05)

    plt.savefig(os.path.join(run_path, 'memory_config.pdf'), dpi=dpi,
                bbox_inches='tight')

    # Memory basin ------------------------------------------------------------
    plt.clf()
    plt.figure(figsize=(8.5, 11))

    lg.info("Pi Basin...")
    for ii, g in enumerate(groups):
        lg.info("%i // %i" % (ii, g))

        plt.gca().set_prop_cycle(None)  # Reset colormap
        ax = plt.subplot(len(groups), 1, ii + 1)
        ax.tick_params(axis='both', which='minor')

        # For each group, plot 'to_plot'.
        df_temp = df.query('%s == "%s"' % (p['group_by'], g))

        for index, row in df_temp.iterrows():
            # Load in the average energies.
            loc_str = str(row['loc']).zfill(zfill_index)
            pi_basin_path = os.path.join(run_path, loc_str,
                                         'memory_basin.pkl')
            pi_basin = pickle.load(open(pi_basin_path, 'rb'))
            ygrid = pi_basin[0]
            xgrid = pi_basin[1]
            delta = pi_basin[2]

            if index == len(df_temp.index) - 1:
                plt.xlabel(r"$\tau$")

            if xgrid == []:
                continue

            xgrid = np.array(xgrid)
            ygrid = np.array(ygrid)
            ygrid = ygrid / row['nvec']

            plt.loglog(xgrid, ygrid, 'o', markersize=5)
            ax.tick_params(axis='both', which='minor')

            plt.ylabel(r"$\Pi_B(t_w, t_w + %.02f t_w)$" % delta)

        plt.text(0.5, 0.05, "%s = %i" % (p['group_by'], g),
                 ha='center', va='top', transform=ax.transAxes, fontsize=14)

        plt.gca().set_prop_cycle(None)  # Reset colormap
        for index, row in df_temp.iterrows():

            loc_str = str(row['loc']).zfill(zfill_index)
            pi_basin_path = os.path.join(run_path, loc_str,
                                         'memory_basin.pkl')
            pi_basin = pickle.load(open(pi_basin_path, 'rb'))

            xgrid = pi_basin[1]
            delta = pi_basin[2]

            xgrid = np.array(xgrid)

            if ii == 0:
                label = "%s" % row['beta']
            else:
                label = None

            hxw_ = hxw(2.0 - row['beta'] / row['lambda_prime'], delta)
            if hxw_ < 1e-14:
                hxw_ *= -1  # ignore
                label = None
            line = [hxw_ for __ in range(len(xgrid))]

            if label is not None:
                label = label + r" ($H_x(w) = %.02f$)" % hxw_

            plt.loglog(xgrid, line, '--', alpha=0.5, label=label)

        plt.ylim(bottom=0.0)

        # Only need one legend.
        plt.legend(title="%s" % p['to_plot'], fontsize=6)

        if ii != len(groups) - 1:
            plt.tick_params(labelbottom=False)

    plt.subplots_adjust(hspace=0.05)

    plt.savefig(os.path.join(run_path, 'memory_basin.pdf'), dpi=dpi,
                bbox_inches='tight')


def plotting_tool(data_path, plotting_params, prompt=True):
    """Plots all data available in the `DATA_hdwell` directory."""

    all_dirs = os.listdir(data_path)  # List all run directories.

    for directory in all_dirs:
        run_path = os.path.join(data_path, directory)
        param_path = os.path.join(run_path, 'params.csv')
        df = pd.read_csv(param_path)

        if prompt:
            x_ = PLOTTING_INFO_TEMPLATE.format(directory=run_path,
                                               beta=df.beta.unique(),
                                               dims=df.N.unique(),
                                               nmc=df.nmc.unique(),
                                               nvec=df.nvec.unique(),
                                               betac=df.lambda_prime.unique(),
                                               ptype=df.ptype.unique(),
                                               protocol=df.protocol.unique())

            if input(x_) != 'y':
                print("Skipping.")
                continue
            else:
                print("Plotting...")

        plot_actual(run_path, plotting_params, df)
