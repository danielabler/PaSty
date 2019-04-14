import os
from pasty.parametric_study import ParametricStudy
from pasty import config


class MyParametricStudy(ParametricStudy):

    def latex_experiment_summary(self, doc, exp_id, results):
        doc.addLine("%========================================== \n")
        doc.addLine("\\begin{frame} \n")
        doc.addLine("\\frametitle{Configuration %03d} \n" % (exp_id))
        doc.addLine("\\centering \n")
        #self.addImage(path_to_image, image_options)
        doc.addLine("Modified Template")
        doc.addLine("\\end{frame} \n")
        doc.addLine("%========================================== \n")

ps = MyParametricStudy(config.test_folder_structure_dir)
ps.reload_state()
ps.collect_results(verbose=True)
ps.create_summary_doc()