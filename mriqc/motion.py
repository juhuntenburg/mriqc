import numpy as np
import pylab as plt
import seaborn as sns
from misc import plot_vline
from matplotlib.figure import Figure
from matplotlib.backends.backend_pdf import FigureCanvasPdf as FigureCanvas
from matplotlib.gridspec import GridSpec

def calc_frame_dispalcement(realignment_parameters_file, parameter_source):
    lines = open(realignment_parameters_file, 'r').readlines()
    rows = [[float(x) for x in line.split()] for line in lines]
    cols = np.array([list(col) for col in zip(*rows)])

    # Assuming a 50 mm radius to convert rotation to displacement on a sphere
    # from https://github.com/poldrack/fmriqa/blob/master/compute_fd.py :
    # Circumference of the sphere is pi*2*radius. Multiply that circumference 
    # by (degree rotation/360) or (radians rotation/2*pi) to get the length of 
    # the arc produced by a rotation.   
    
    headradius=50
    
    if parameter_source == 'AFNI':
        translations = np.transpose(np.abs(np.diff(cols[0:3, :])))
        rotations = np.transpose(np.abs(np.diff(cols[3:6, :])))
        # afni returns rotation in degrees
        arc = 2 * np.pi * headradius * (rotations/360.)
    
    elif parameter_source == 'FSL':
        translations = np.transpose(np.abs(np.diff(cols[3:6, :])))
        rotations = np.transpose(np.abs(np.diff(cols[0:3, :])))
        # mcflirt returns rotation in radians
        # arc = 2 * np.pi * headradius * (rotations/2*np.pi) --> drop the 2pi
        arc = headradius * rotations

    FD_power = np.sum(translations, axis = 1) + np.sum(arc, axis =1)
    #FD is zero for the first time point
    FD_power = np.insert(FD_power, 0, 0)
    
    return FD_power


def get_mean_frame_displacement_disttribution(realignment_parameters_files, parameter_source):
    mean_FDs = []
    max_FDs = []
    for realignment_parameters_file in realignment_parameters_files:
        FD_power = calc_frame_dispalcement(realignment_parameters_file, parameter_source)
        mean_FDs.append(FD_power.mean())
        max_FDs.append(FD_power.max())
        
    return mean_FDs, max_FDs

def plot_frame_displacement(realignment_parameters_file, parameter_source, mean_FD_distribution=None, figsize=(11.7,8.3)):

    FD_power = calc_frame_dispalcement(realignment_parameters_file, parameter_source)

    fig = Figure(figsize=figsize)
    FigureCanvas(fig)
    
    if mean_FD_distribution:
        grid = GridSpec(2, 4)
    else:
        grid = GridSpec(1, 4)
    
    ax = fig.add_subplot(grid[0,:-1])
    ax.plot(FD_power)
    ax.set_xlim((0, len(FD_power)))
    ax.set_ylabel("Frame Displacement [mm]")
    ax.set_xlabel("Frame number")
    ylim = ax.get_ylim()
    
    ax = fig.add_subplot(grid[0,-1])
    sns.distplot(FD_power, vertical=True, ax=ax)
    ax.set_ylim(ylim)
    
    if mean_FD_distribution:
        ax = fig.add_subplot(grid[1,:])
        sns.distplot(mean_FD_distribution, ax=ax)
        ax.set_xlabel("Mean Frame Displacement (over all subjects) [mm]")
        MeanFD = FD_power.mean()
        label = "MeanFD = %g"%MeanFD
        plot_vline(MeanFD, label, ax=ax)
        
    fig.suptitle('motion', fontsize='14')
        
    return fig