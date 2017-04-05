from glob import glob
from correlation import get_similarity_distribution
from motion import get_mean_frame_displacement_disttribution
from volumes import get_median_distribution
from reports import create_report
import pandas as pd
from nipype.pipeline.engine import Workflow, Node
from nipype.interfaces.utility import Function


if __name__ == '__main__':
    data_dir = "/afs/cbs.mpg.de/projects/mar004_lsd-lemon-preproc/probands/"
    out_dir= "/afs/cbs.mpg.de/projects/mar004_lsd-lemon-preproc/results/reports/lsd_new/"
    fs_dir= "/afs/cbs.mpg.de/projects/mar004_lsd-lemon-preproc/freesurfer/"
    
    
    scans = ['rest1a', 'rest1b', 'rest2a', 'rest2b']

#   wf = Workflow("reports")
#   wf.base_dir = "/nobackup/ilz2/LEMON_LSD/rescue_julia/working_dir/"
#   wf.config['execution']['crashdump_dir'] = wf.base_dir + "crash_files/"
    
    
    for scan in scans:
        print scan
        
        subjects = list(pd.read_csv('/home/raid3/huntenburg/workspace/lsd_data_paper/lsd_preproc.csv', dtype='str')['ID'])
        subjects.sort()
        
        if scan == 'rest1a':
            pass
        elif scan == 'rest1b':
            subjects.remove('')
        elif scan == 'rest2a':
            subjects.remove('')
            subjects.remove('')
        elif scan == 'rest2b':
            subjects.remove('')
            subjects.remove('')
            subjects.remove('')
            subjects.remove('')
            subjects.remove('')
            
               
        #generating distributions
        print 'generating similarity'
        mincost_files = [data_dir + "%s/preprocessed/lsd_resting/%s/coregister/rest2anat.dat.mincost"%(subject, scan) for subject in subjects]
        similarity_distribution = get_similarity_distribution(mincost_files)
        
        print 'generating mean fd'
        realignment_parameters_files = [data_dir + "%s/preprocessed/lsd_resting/%s/realign/rest_realigned.par"%(subject, scan) for subject in subjects]
        mean_FD_distribution, max_FD_distribution = get_mean_frame_displacement_disttribution(realignment_parameters_files, 'FSL')
          
        print 'generating tsnr'
        tsnr_files = [glob(data_dir + "%s/preprocessed/lsd_resting/%s/realign/*tsnr.nii.gz"%(subject, scan))[0] for subject in subjects]
        mask_files = [data_dir + "%s/preprocessed/lsd_resting/%s/denoise/mask/T1_brain_mask2epi.nii.gz"%(subject, scan) for subject in subjects]
        tsnr_distributions = get_median_distribution(tsnr_files, mask_files)
         
        df = pd.DataFrame(zip(subjects, similarity_distribution, mean_FD_distribution, max_FD_distribution, tsnr_distributions), 
                          columns = ["subject_id", "coregistration dissimilarity", "Mean FD", "Max FD", "Median tSNR"])
        df.to_csv(out_dir+"%s_summary.csv"%(scan))
        
#         similarity_distribution = dict(zip(subjects, similarity_distribution))
#         
#         for subject in subjects:
#             print subject
#             #setting paths for this subject
#             tsnr_file = glob(data_dir + "%s/preprocessed/lsd_resting/%s/realign/*tsnr.nii.gz"%(subject, scan))[0]
#             
#             timeseries_file = data_dir + "%s/preprocessed/lsd_resting/%s/rest_preprocessed.nii.gz"%(subject, scan)
#             realignment_parameters_file = data_dir + "%s/preprocessed/lsd_resting/%s/realign/rest_realigned.par"%(subject, scan)
#             
#             wm_file = data_dir + "%s/preprocessed/anat/T1_brain_wmedge.nii.gz"%(subject)
#             mean_epi_file = data_dir + "%s/preprocessed/lsd_resting/%s/coregister/rest_mean2fmap_unwarped.nii.gz"%(subject, scan)
#             mean_epi_uncorrected_file = data_dir + "%s/preprocessed/lsd_resting/%s/coregister/rest_mean2fmap.nii.gz"%(subject, scan)
#             mask_file = data_dir + "%s/preprocessed/lsd_resting/%s/denoise/mask/T1_brain_mask2epi.nii.gz"%(subject, scan)
#             reg_file = data_dir + "%s/preprocessed/lsd_resting/%s/coregister/transforms2anat/rest2anat.dat"%(subject, scan)
#             fssubjects_dir = fs_dir
#             
#             mincost_file = data_dir + "%s/preprocessed/lsd_resting/%s/coregister/rest2anat.dat.mincost"%(subject, scan)
#             
#             output_file = out_dir+"%s_%s_report.pdf"%(subject, scan)
#             
#             report = Node(Function(input_names=['subject_id', 
#                                                  'tsnr_file', 
#                                                  'realignment_parameters_file', 
#                                                  'parameter_source',
#                                                  'mean_epi_file',
#                                                  'mean_epi_uncorrected_file',
#                                                  'wm_file', 
#                                                  'mask_file', 
#                                                  'reg_file', 
#                                                  'fssubjects_dir', 
#                                                  'similarity_distribution', 
#                                                  'mean_FD_distribution', 
#                                                  'tsnr_distributions', 
#                                                  'output_file'], 
#                                     output_names=['out'],
#                                     function = create_report), name="report_%s_%s"%(scan,subject))
#             report.inputs.subject_id = subject
#             report.inputs.tsnr_file = tsnr_file
#             report.inputs.realignment_parameters_file = realignment_parameters_file
#             report.inputs.parameter_source = 'FSL'
#             report.inputs.mean_epi_file = mean_epi_file
#             report.inputs.mean_epi_uncorrected_file = mean_epi_uncorrected_file
#             report.inputs.wm_file = wm_file
#             report.inputs.mask_file = mask_file
#             report.inputs.reg_file = reg_file
#             report.inputs.fssubjects_dir = fssubjects_dir
#             report.inputs.similarity_distribution = similarity_distribution
#             report.inputs.mean_FD_distribution = mean_FD_distribution
#             report.inputs.tsnr_distributions = tsnr_distributions
#             report.inputs.output_file = output_file
#             report.plugin_args={'override_specs': 'request_memory = 8000'}
#             wf.add_nodes([report])
              
    #wf.run(plugin='MultiProc', plugin_args={'n_procs' : 10})
    #wf.run()
         
