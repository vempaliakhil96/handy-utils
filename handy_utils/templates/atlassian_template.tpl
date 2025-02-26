{% extends "full.tpl" %}

{# Remove prompt area #}
{% block in_prompt %}{% endblock in_prompt %}
{% block output_prompt %}{% endblock output_prompt %}

{# Custom CSS #}
{% block header %}
<style type="text/css">
    .jupyter-notebook .code {
        margin: 10px 0;
        padding: 10px;
        background-color: #f4f5f7;
        border-radius: 3px;
    }
    .jupyter-notebook .output_area {
        margin: 10px 0;
        padding: 10px;
        background-color: #ffffff;
        border: 1px solid #dfe1e6;
        border-radius: 3px;
    }
</style>
{% endblock header %}

{# Format code cells as Python code blocks #}
{% block input %}
<ac:structured-macro ac:name="code">
    <ac:parameter ac:name="language">python</ac:parameter>
    <ac:plain-text-body><![CDATA[{{ cell.source | indent(4) }}]]></ac:plain-text-body>
</ac:structured-macro>
{% endblock input %}

{# Format output cells #}
{% block output %}
<div class="output_area">
    {{ super() }}
</div>
{% endblock output %}

{# Format markdown cells #}
{% block markdowncell %}
{{ cell.source | markdown2html }}
{% endblock markdowncell %}

{# Format stdout output with preformatted text #}
{% block stream_stdout %}
<ac:structured-macro ac:name="code">
    <ac:parameter ac:name="language">text</ac:parameter>
    <ac:plain-text-body><![CDATA[{{ output.text | indent(4) }}]]></ac:plain-text-body>
</ac:structured-macro>
{% endblock stream_stdout %}
{# Format text/plain output with preformatted text #}
{% block data_text %}
<ac:structured-macro ac:name="code">
    <ac:parameter ac:name="language">text</ac:parameter>
    <ac:plain-text-body><![CDATA[{{ output.data['text/plain'] | indent(4) }}]]></ac:plain-text-body>
</ac:structured-macro>
{% endblock data_text %}

