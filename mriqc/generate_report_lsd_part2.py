from glob import glob
from correlation import get_similarity_distribution
from motion import get_mean_frame_displacement_disttribution
from volumes import get_median_distribution
from reports import create_report, read_dists, check
import pandas as pd
from nipype.pipeline.engine import Workflow, Node
from nipype.interfaces.utility import Function, IdentityInterface
from nipype.interfaces.io import SelectFiles


if __name__ == '__main__':
    data_dir = "/afs/cbs.mpg.de/projects/mar004_lsd-lemon-preproc/"
    out_dir= "/afs/cbs.mpg.de/projects/mar004_lsd-lemon-preproc/results/reports/lsd/"
    fs_dir= "/afs/cbs.mpg.de/projects/mar004_lsd-lemon-preproc/freesurfer/"
    
    subjects_file = '/afs/cbs.mpg.de/projects/mar004_lsd-lemon-preproc/documents/all_lsd_%s_new.txt'
    stats_file = out_dir+"%s_summary.csv"
    check_file = out_dir+'checklist_%s.txt'
    
    scans = ['rest1a'] #, 'rest1b', 'rest2a', 'rest2b']
    
        
    wf = Workflow("reports_part2")
    wf.base_dir = "/scr/ilz3/LEMON_LSD/wd_reports_julia/"
    wf.config['execution']['crashdump_dir'] = wf.base_dir + "crash_files/"

    with open(subjects_file%scans[0], 'r') as f: # can be made dependent on scan
        subjects = [line.strip() for line in f]
    subjects.sort()
    #subjects.remove('26858')
    #subjects.remove('26435')
    #subjects.remove('27062')
    
    with open(check_file%scans[0], 'r') as cf:
        done = [line.strip() for line in cf]
    done.sort()
    
    subjects = [x for x in subjects if x not in done]
    
    scan_infosource = Node(IdentityInterface(fields=['scan_id']), 
                              name='scan_infosource')
    scan_infosource.iterables=('scan_id', scans)
    
    
    def make_stats(template, scan_id):
        return template%scan_id
    
    make_statsfile = Node(Function(input_names=['template', 'scan_id'],
                                    output_names=['fname'],
                                    function=make_stats),
                           name='make_statsfile')
    make_statsfile.inputs.template = stats_file
    
    
    read_distributions = Node(Function(input_names=['csv_file'],
                                       output_names=['similarity_distribution',
                                                     'mean_FD_distribution',
                                                     'tsnr_distributions'],
                                       function=read_dists),
                              name='read_distributions')
    
    
    subject_infosource = Node(IdentityInterface(fields=['subject_id']), 
                              name='subject_infosource')
    subject_infosource.iterables=('subject_id', subjects)
    
    
    # select files
    templates={'stats_file' : "results/reports/lsd/{scan_id}_summary.csv",
                'tsnr_file' : "probands/{subject_id}/preprocessed/lsd_resting/{scan_id}/realign/rest_realigned_tsnr.nii.gz",
                'timeseries_file' : "probands/{subject_id}/preprocessed/lsd_resting/{scan_id}/rest_preprocessed.nii.gz",
                'realignment_parameters_file' : "probands/{subject_id}/preprocessed/lsd_resting/{scan_id}/realign/rest_realigned.par",
                'wm_file' : "probands/{subject_id}/preprocessed/anat/T1_brain_wmedge.nii.gz",
                'mean_epi_file' : "probands/{subject_id}/preprocessed/lsd_resting/{scan_id}/coregister/rest_mean2fmap_unwarped.nii.gz",
                'mean_epi_uncorrected_file' :"probands/{subject_id}/preprocessed/lsd_resting/{scan_id}/coregister/rest_mean2fmap.nii.gz",
                'mask_file' : "probands/{subject_id}/preprocessed/lsd_resting/{scan_id}/denoise/mask/T1_brain_mask2epi.nii.gz",
                'reg_file' : "probands/{subject_id}/preprocessed/lsd_resting/{scan_id}/coregister/transforms2anat/rest2anat.dat",
                'mincost_file' : "probands/{subject_id}/preprocessed/lsd_resting/{scan_id}/coregister/rest2anat.dat.mincost"         
               }
    selectfiles = Node(SelectFiles(templates, base_directory=data_dir),
                       name="selectfiles")
    
    
    
    def make_out(out_dir, subject_id, scan_id):
        f = out_dir+"%s_%s_report.pdf"%(subject_id, scan_id)
        return f
    
    
    make_outfile = Node(Function(input_names=['out_dir',
                                              'subject_id',
                                              'scan_id'],
                                 output_names=['output_file'], 
                                 function = make_out),
                        name='make_outfile')
    make_outfile.inputs.out_dir = out_dir
    
        
    report = Node(Function(input_names=['subject_id', 
                                         'tsnr_file', 
                                         'realignment_parameters_file', 
                                         'parameter_source',
                                         'mean_epi_file',
                                         'mean_epi_uncorrected_file',
                                         'wm_file', 
                                         'mask_file', 
                                         'reg_file', 
                                         'fssubjects_dir', 
                                         'similarity_distribution', 
                                         'mean_FD_distribution', 
                                         'tsnr_distributions', 
                                         'output_file'], 
                            output_names=['out', 'subject_id'],
                            function = create_report), name="report")
    report.inputs.parameter_source = 'FSL'
    report.inputs.fssubjects_dir = fs_dir
    
    check_report = Node(Function(input_names=['subject_id', 'scan_id', 'checklist'],
                                 output_names=['checklist'],
                                 function=check),
                        name='check_report')
    check_report.inputs.checklist = check_file
    
    
    
    wf.connect([(scan_infosource, selectfiles, [('scan_id', 'scan_id')]),
                (scan_infosource, make_statsfile, [('scan_id', 'scan_id')]),
                (scan_infosource, make_outfile, [('scan_id', 'scan_id')]),
                (scan_infosource, check_report, [('scan_id', 'scan_id')]),
                (subject_infosource, selectfiles, [('subject_id', 'subject_id')]),
                (subject_infosource, make_outfile, [('subject_id', 'subject_id')]),
                (subject_infosource, report, [('subject_id', 'subject_id')]),
                (selectfiles, report, [('tsnr_file', 'tsnr_file'),
                                        ('realignment_parameters_file', 'realignment_parameters_file'),
                                        ('mean_epi_file', 'mean_epi_file'),
                                        ('mean_epi_uncorrected_file', 'mean_epi_uncorrected_file'),
                                        ('wm_file', 'wm_file'),
                                        ('mask_file', 'mask_file'),
                                        ('reg_file', 'reg_file')]),
                (make_statsfile, read_distributions, [('fname', 'csv_file')]),
                (read_distributions, report, [('similarity_distribution', 'similarity_distribution'),
                                              ('mean_FD_distribution', 'mean_FD_distribution'),
                                              ('tsnr_distributions', 'tsnr_distributions')]),
                (make_outfile, report, [('output_file', 'output_file')]),
                (report, check_report, [('subject_id', 'subject_id')])
                ])
                
    wf.run() #plugin='MultiProc', plugin_args={'n_procs' : 20})
         
