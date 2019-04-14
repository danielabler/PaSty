from pasty import images_to_latex as itl
import pathlib as pl

from pasty import config

p_doc = pl.Path(config.output_dir).joinpath('latex_doc', 'test_doc.tex')
#p_doc.mkdir(parents=True, exist_ok=True)

doc = itl.LatexDoc()
doc.addTitlePage()
doc.writeDoc(p_doc)
doc.compile()