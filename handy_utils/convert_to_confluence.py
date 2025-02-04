from traitlets.config import Config
from nbconvert.exporters import HTMLExporter
from nbconvert.preprocessors import TagRemovePreprocessor
import nbformat
from pathlib import Path
from atlassian import Confluence
from handy_utils.configuration import load_configuration
import tempfile

config = load_configuration()

c = Config()

c.TagRemovePreprocessor.remove_cell_tags = ("remove_cell", "skip")
c.TagRemovePreprocessor.remove_all_outputs_tags = ("remove_output",)
c.TagRemovePreprocessor.remove_input_tags = ("remove_input",)
c.TagRemovePreprocessor.enabled = True

exporter = HTMLExporter(config=c)
exporter.register_preprocessor(TagRemovePreprocessor(config=c), True)

def upload_to_confluence(output_path: str) -> str:
    
    with open(output_path) as f: text = f.read()

    confluence = Confluence(url=f'https://{config.confluence_domain}/', 
                        cloud=True, 
                        username=config.confluence_username, 
                        password=config.confluence_api_key)
    
    print(f'Uploading {output_path} to Confluence')

    confluence.create_page(
        space=config.confluence_space_key,
        title=output_path.name,
        body=text,
        type='page',
        representation='storage',
        full_width=False,
        editor='v2'
    )

    print(f'Uploaded {output_path} to Confluence')

def convert_to_confluence(notebook_path: str, output_path: str, dry_run: bool = False) -> str:
    notebook_path = Path(notebook_path)
    output_path = Path(output_path) if output_path else None

    with open(notebook_path) as f:
        nb = nbformat.read(f, as_version=4)
    
    for cell in nb.cells:
        if cell.source.startswith("#|nb_tag:"):
            c = cell.source.split('\n')[0]; cell.source = cell.source.replace(c, '').strip()
            tag_name = c.replace('#|nb_tag:', '').strip()
            if 'tags' not in cell.metadata: cell.metadata['tags'] = []
            cell.metadata['tags'].append(tag_name); cell.metadata['tags'] = list(set(cell.metadata['tags']))

    output = exporter.from_notebook_node(nb)
    
    if output_path and output_path.is_dir(): output_path = output_path / notebook_path.name.replace('.ipynb', '.html')
    
    if output_path:
        with open(output_path, "w") as f: f.write(output[0])
    else:
        output_path = Path(tempfile.mktemp()) / notebook_path.name.replace('.ipynb', '.html')

    if not dry_run: upload_to_confluence(output_path)
    
    return output_path
