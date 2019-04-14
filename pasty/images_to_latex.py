# -*- coding: utf-8 -*-

import os, subprocess


def getFileExtension(path_to_file):
    # need to test for existence of '.'
    # return None of component has no file extension
    file_name = os.path.split(path_to_file)[-1]
    file_name_split = file_name.split(".")     
    if file_name_split[-1]==file_name:
        # there is no '.' in file_name
        return None
    else:
        return file_name_split[-1]
        
def ensureDirExists(path):
    if getFileExtension(path)==None:
        # assume that 'path' is directory, add trailing '/'
        path = path +'/'
    if os.path.exists(os.path.dirname(path)):
        return True
    else:
        os.makedirs(os.path.dirname(path))
        return False
        

def runCommand(cmd, stdout = None, stderr = None, cwd = None, ignoredRetCodes = []):
    ''' Runs the command and returns an appropriate string '''
    assert isinstance(ignoredRetCodes, list), "ignoredRetCodes should be a list"
    try:
      retcode = subprocess.call(cmd, stdout = stdout, stderr = stderr, cwd = cwd)
      if retcode == 0 or retcode in ignoredRetCodes:
          message = "OK"
      else:
          message = "failed (retcode: %s)" % retcode
    except OSError:
        message = "failed"
    return(message)
    


class LatexDoc():
    
    def __init__(self, document_prop_dict=None):
        self.config = {"document_class" : "beamer",
                       "class_options"  : "xcolor={x11names,svgnames,dvipsnames,table}, trans, 11pt",
                       "compile_command" : "pdflatex"}
        document_props = {"title"    : "Generated Presentation",
                          "subtitle" : "-- change by setting document props --",
                          "author"   : "Daniel Abler",
                          "date"     : "\\today",
                          "institute": ""}
        if document_prop_dict is not None:
            document_props.update(document_prop_dict)
        self.document_props = document_props
        self.content = []

    def addTitlePage(self):
        self.addLine("%========================================== \n")
        self.addLine("\\begin{frame}[noframenumbering] \n")
        self.addLine("\\titlepage \n")
        self.addLine("\\end{frame} \n")
        self.addLine("%========================================== \n")
        
    def addLine(self, string_line):
        self.content.append(string_line)
        
    def addImage(self, path_to_image, image_options=None):
        if image_options == None:
            command_string = "\\includegraphics{%s}"%(path_to_image)
        else: 
            command_string = "\\includegraphics[%s]{%s}"%(image_options, path_to_image)
        self.addLine(command_string)


        
    def addFrameWithSingleImage(self, title, path_to_image, image_options=None):
        self.addLine("%========================================== \n")
        self.addLine("\\begin{frame} \n")
        self.addLine("\\frametitle{%s} \n"%(title))
        self.addLine("\\centering \n")
        self.addImage(path_to_image, image_options)
        self.addLine("\\end{frame} \n")
        self.addLine("%========================================== \n")

    def writeDoc(self, path_to_document):
        path_to_document.parent.mkdir(parents=True, exist_ok=True)
        with path_to_document.open('w') as file:
            # Preamble
            file.write("\\documentclass[%s]{%s} \n"%(self.config['class_options'], self.config['document_class']))
            file.write("\\usepackage{booktabs} \n")
            # title page info
            if "title" in self.document_props.keys():
                file.write("\\title{%s} \n"%(self.document_props["title"]))
            if "author" in self.document_props.keys():
                file.write("\\author{%s} \n"%(self.document_props["author"]))
            if "institute" in self.document_props.keys():
                file.write("\\institute{%s} \n"%(self.document_props["institute"]))
            if "date" in self.document_props.keys():
                file.write("\\date{%s} \n"%(self.document_props["date"]))
            if "subtitle" in self.document_props.keys():
                file.write("\\subtitle{%s} \n"%(self.document_props["subtitle"]))
            # document
            file.write("\\begin{document} \n")
            for line in self.content:
                file.write("%s \n"%(line))
            file.write("\\end{document} \n")
        self.path_to_tex = path_to_document

    def compile(self, log_file=None):
        ''' Run pdflatex on the resulting tex file '''
        if hasattr(self, 'path_to_tex'):
            # if log_file is None:
            #     log_file = self.path_to_tex.parent.joinpath('compile.log')
            latex_cmd = self.config['compile_command']
            compile_cmd = (latex_cmd, "-shell-escape", "-interaction=nonstopmode", self.path_to_tex.as_posix())
            print("Running pdflatex: %s" % runCommand(compile_cmd, stdout=log_file, ignoredRetCodes=[1],
                                                      cwd=self.path_to_tex.parent.as_posix()))

