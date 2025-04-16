from bs4 import BeautifulSoup
from bs4.element import NavigableString, Tag
from typing import Union, Dict, Optional, cast

def html_to_asf(el: Union[BeautifulSoup, NavigableString, Tag, str], 
                ctx: Optional[Dict] = None) -> str:
    """Convert HTML (bs4) element to Atlassian Storage Format `el`"""
    if ctx is None: ctx = {}
    
    # Handle string nodes
    if isinstance(el, (str, NavigableString)):
        return str(el)
    
    # Get tag name and attributes
    tag = el.name if isinstance(el, (Tag, BeautifulSoup)) else None
    attrs = el.attrs if isinstance(el, (Tag, BeautifulSoup)) else {}
    
    # Process children first
    inner = ''.join(html_to_asf(cast(Union[BeautifulSoup, NavigableString, Tag, str], c), ctx) 
                    for c in el.children) if hasattr(el, 'children') else ''
    
    # Handle different HTML elements
    if tag is None:
        return inner
        
    elif tag == 'p':
        style = cast(str, attrs.get('style', ''))
        align = style.replace('text-align: ', '') if 'style' in attrs else ''
        if align in ('center', 'right'):
            return f'<p style="text-align: {align}">{inner}</p>'
        return f'<p>{inner}</p>'
        
    elif tag in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
        return f'<{tag}>{inner}</{tag}>'
        
    elif tag == 'strong' or tag == 'b':
        return f'<strong>{inner}</strong>'
        
    elif tag == 'em' or tag == 'i':
        return f'<em>{inner}</em>'
        
    elif tag == 'u':
        return f'<u>{inner}</u>'
        
    elif tag == 'strike' or tag == 's':
        return f'<span style="text-decoration: line-through;">{inner}</span>'
        
    elif tag == 'sup':
        return f'<sup>{inner}</sup>'
        
    elif tag == 'sub':
        return f'<sub>{inner}</sub>'
        
    elif tag == 'code':
        return f'<code>{inner}</code>'
        
    elif tag == 'pre':
        return f'<pre>{inner}</pre>'
        
    elif tag == 'blockquote':
        return f'<blockquote><p>{inner}</p></blockquote>'
        
    elif tag == 'small':
        return f'<small>{inner}</small>'
        
    elif tag == 'big':
        return f'<big>{inner}</big>'
        
    elif tag == 'br':
        return '<br />'
        
    elif tag == 'hr':
        return '<hr />'
        
    elif tag == 'ul':
        return f'<ul>{inner}</ul>'
        
    elif tag == 'ol':
        return f'<ol>{inner}</ol>'
        
    elif tag == 'li':
        return f'<li>{inner}</li>'
        
    elif tag == 'a':
        href = cast(str, attrs.get('href', ''))
        if inner=='¶': return ''
        if href.startswith('http'): return f'<a href="{href}">{inner}</a>'
        return f'<ac:link><ri:page ri:content-title="{href}"/><ac:plain-text-link-body><![CDATA[{inner}]]></ac:plain-text-link-body></ac:link>'
        
    elif tag == 'img':
        src = cast(str, attrs.get('src', ''))
        if src.startswith('http'): return f'<ac:image><ri:url ri:value="{src}"/></ac:image>'
        return f'<ac:image><ri:attachment ri:filename="{src}"/></ac:image>'
        
    elif tag == 'span':
        style = cast(str, attrs.get('style', ''))
        if 'color:' in style:
            color = style.split('color:')[1].split(';')[0].strip()
            return f'<span style="color: {color}">{inner}</span>'
        return inner
        
    # Default case - pass through unchanged
    return inner

def convert_html_str_to_asf(html_str: str) -> str:
    """Convert HTML string to Atlassian Storage Format string"""
    soup = BeautifulSoup(html_str, 'html.parser')
    return html_to_asf(soup) 