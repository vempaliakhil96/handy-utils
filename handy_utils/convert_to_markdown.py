from traitlets.config import Config
from nbconvert.exporters import MarkdownExporter
from nbconvert.preprocessors import TagRemovePreprocessor
import nbformat
from pathlib import Path


c = Config()

c.TagRemovePreprocessor.remove_cell_tags = ("remove_cell", "skip")
c.TagRemovePreprocessor.remove_all_outputs_tags = ("remove_output",)
c.TagRemovePreprocessor.remove_input_tags = ("remove_input",)
c.TagRemovePreprocessor.enabled = True

exporter = MarkdownExporter(config=c)
exporter.register_preprocessor(TagRemovePreprocessor(config=c), True)


def convert_to_markdown(notebook_path: str, output_path: str) -> str:
    notebook_path = Path(notebook_path)
    output_path = Path(output_path)

    with open(notebook_path) as f:
        nb = nbformat.read(f, as_version=4)
    
    for cell in nb.cells:
        if cell.source.startswith("#|nb_tag:"):
            c = cell.source.split('\n')[0]; cell.source = cell.source.replace(c, '').strip()
            tag_name = c.replace('#|nb_tag:', '').strip()
            if 'tags' not in cell.metadata: cell.metadata['tags'] = []
            cell.metadata['tags'].append(tag_name); cell.metadata['tags'] = list(set(cell.metadata['tags']))

    output = exporter.from_notebook_node(nb)
    
    if output_path.is_dir(): output_path = output_path / notebook_path.name.replace('.ipynb', '.md')
    
    with open(output_path, "w") as f: f.write(output[0])
    
    return output_path


if __name__ == "__main__":
    convert_to_markdown("/Users/avempali/Documents/repos/devai-issue-scoping/notebooks/avempali-16-finetuning.ipynb", "test.md")
