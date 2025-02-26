from traitlets.config import Config
from nbconvert.exporters import HTMLExporter
from nbconvert.preprocessors import TagRemovePreprocessor
import nbformat
from pathlib import Path
from atlassian import Confluence
from handy_utils.configuration import load_configuration
import tempfile
import os

config = load_configuration()

c = Config()

# Configure the exporter to use our custom template
template_path = os.path.join(os.path.dirname(__file__), 'templates')
c.HTMLExporter.extra_template_paths = [template_path]
c.HTMLExporter.template_file = 'atlassian_template.tpl'
c.HTMLExporter.exclude_input_prompt = True
c.HTMLExporter.exclude_output_prompt = True

c.TagRemovePreprocessor.remove_cell_tags = ("remove_cell", "skip")
c.TagRemovePreprocessor.remove_all_outputs_tags = ("remove_output",)
c.TagRemovePreprocessor.remove_input_tags = ("remove_input",)
c.TagRemovePreprocessor.enabled = True

exporter = HTMLExporter(config=c)
exporter.register_preprocessor(TagRemovePreprocessor(config=c), True)

def upload_to_confluence(output_path: str) -> str:
    
    with open(output_path) as f: text = f.read()

    page_name = output_path.name.replace('.html', '').replace('_', ' ').replace('-', ' ').replace('.', ' ').title()

    confluence = Confluence(url=f'https://{config.confluence_domain}/', 
                        cloud=True, 
                        username=config.confluence_username, 
                        password=config.confluence_api_key)
    
    print(f'Uploading {output_path} to Confluence')

    # Try to find existing page first
    existing_page = confluence.get_page_by_title(
        space=config.confluence_space_key,
        title=page_name
    )

    if existing_page:
        # Update existing page
        confluence.update_page(
            page_id=existing_page['id'],
            title=page_name,
            body=text,
            type='page',
            representation='storage',
            full_width=False,
        )
    else:
        # Create new page
        confluence.create_page(
            space=config.confluence_space_key,
            title=page_name,
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
        tmp_dir = Path(tempfile.mkdtemp())
        output_path = tmp_dir / notebook_path.name.replace('.ipynb', '.html')
        with open(output_path, "w") as f: f.write(output[0])
    if not dry_run: upload_to_confluence(output_path)
    
    return output_path
