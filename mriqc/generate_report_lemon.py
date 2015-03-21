from glob import glob
from correlation import get_similarity_distribution
from motion import get_mean_frame_displacement_disttribution
from volumes import get_median_distribution
from reports import create_report
import pandas as pd
from nipype.pipeline.engine import Workflow, Node
from nipype.interfaces.utility import Function


if __name__ == '__main__':
    data_dir = "/scr/ilz2/LEMON_LSD/"
    out_dir= "/scr/ilz2/LEMON_LSD/reports/lemon/"
    
    scans=['rest']
    wf = Workflow("reports")
    wf.base_dir = data_dir+'working_dir_reports_lemon/'

    with open('/scr/ilz2/LEMON_LSD/list_reports_lemon.txt', 'r') as f:
        subjects = [line.strip() for line in f]
    
    subjects.sort()
     
    #generating distributions
    mincost_files = [data_dir + "%s/preprocessed/lemon_resting/coregister/rest2anat.dat.mincost"%(subject) for subject in subjects]
    similarity_distribution = get_similarity_distribution(mincost_files)
    
      
    realignment_parameters_files = [data_dir + "%s/preprocessed/lemon_resting/realign/rest_realigned.par"%(subject) for subject in subjects]
    mean_FD_distribution, max_FD_distribution = get_mean_frame_displacement_disttribution(realignment_parameters_files)
      
    tsnr_files = [data_dir + "%s/preprocessed/lemon_resting/realign/rest_realigned_tsnr.nii.gz"%(subject) for subject in subjects]
    mask_files = [data_dir + "%s/preprocessed/lemon_resting/denoise/mask/T1_brain_mask2epi.nii.gz"%(subject) for subject in subjects]
    tsnr_distributions = get_median_distribution(tsnr_files, mask_files)
     
    df = pd.DataFrame(zip(subjects, similarity_distribution, mean_FD_distribution, max_FD_distribution, tsnr_distributions), columns = ["subject_id", "coregistration quality", "Mean FD", "Max FD", "Median tSNR"])
    df.to_csv(out_dir+"rest_summary.csv")
    
    similarity_distribution = dict(zip(subjects, similarity_distribution))
    
    for subject in subjects:
        #setting paths for this subject
        tsnr_file = data_dir + "%s/preprocessed/lemon_resting/realign/rest_realigned_tsnr.nii.gz"%(subject)
        
        timeseries_file = data_dir + "%s/preprocessed/lemon_resting/rest_preprocessed.nii.gz"%(subject)
        realignment_parameters_file = data_dir + "%s/preprocessed/lemon_resting/realign/rest_realigned.par"%(subject)

        wm_file = data_dir + "%s/preprocessed/anat/T1_brain_wmedge.nii.gz"%(subject)
        mean_epi_file = data_dir + "%s/preprocessed/lemon_resting/coregister/rest_mean2fmap_unwarped.nii.gz"%(subject)
        mean_epi_uncorrected_file = data_dir + "%s/preprocessed/lemon_resting/coregister/rest_mean2fmap.nii.gz"%(subject)
        mask_file = data_dir + "%s/preprocessed/lemon_resting/denoise/mask/T1_brain_mask2epi.nii.gz"%(subject)
        reg_file = data_dir + "%s/preprocessed/lemon_resting/coregister/transforms2anat/rest2anat.dat"%(subject)
        fssubjects_dir = data_dir + "freesurfer/"

        mincost_file = data_dir + "%s/preprocessed/lemon_resting/coregister/rest2anat.dat.mincost"%(subject)
        
        output_file = out_dir+"%s_rest_report.pdf"%(subject)
        
        report = Node(Function(input_names=['subject_id', 
                                             'tsnr_file', 
                                             'realignment_parameters_file', 
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
                                output_names=['out'],
                                function = create_report), name="report_%s"%(subject))
        report.inputs.subject_id = subject
        report.inputs.tsnr_file = tsnr_file
        report.inputs.realignment_parameters_file = realignment_parameters_file
        report.inputs.mean_epi_file = mean_epi_file
        report.inputs.mean_epi_uncorrected_file = mean_epi_uncorrected_file
        report.inputs.wm_file = wm_file
        report.inputs.mask_file = mask_file
        report.inputs.reg_file = reg_file
        report.inputs.fssubjects_dir = fssubjects_dir
        report.inputs.similarity_distribution = similarity_distribution
        report.inputs.mean_FD_distribution = mean_FD_distribution
        report.inputs.tsnr_distributions = tsnr_distributions
        report.inputs.output_file = output_file
        report.plugin_args={'override_specs': 'request_memory = 4000'}
        wf.add_nodes([report])
              
    wf.run(plugin='MultiProc')
         
