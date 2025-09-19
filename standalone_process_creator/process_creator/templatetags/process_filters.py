from django import template
import re
import os

register = template.Library()

@register.filter
def markdown_to_html(text):
    """Convert basic Markdown formatting to HTML"""
    if not text:
        return ""
    
    # Convert headers
    text = re.sub(r'^### (.+)$', r'<h3>\1</h3>', text, flags=re.MULTILINE)
    text = re.sub(r'^## (.+)$', r'<h2>\1</h2>', text, flags=re.MULTILINE)
    text = re.sub(r'^# (.+)$', r'<h1>\1</h1>', text, flags=re.MULTILINE)
    
    # Convert bold text
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    
    # Convert italic text
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    
    # Convert bullet points
    text = re.sub(r'^\* (.+)$', r'<li>\1</li>', text, flags=re.MULTILINE)
    text = re.sub(r'^- (.+)$', r'<li>\1</li>', text, flags=re.MULTILINE)
    
    # Convert numbered lists
    text = re.sub(r'^(\d+)\. (.+)$', r'<li>\2</li>', text, flags=re.MULTILINE)
    
    # Wrap consecutive list items in ul/ol tags
    lines = text.split('\n')
    result = []
    in_list = False
    list_type = 'ul'
    
    for line in lines:
        if line.strip().startswith('<li>'):
            if not in_list:
                in_list = True
                list_type = 'ul' if line.strip().startswith('<li>') else 'ol'
                result.append(f'<{list_type}>')
            result.append(line)
        else:
            if in_list:
                result.append(f'</{list_type}>')
                in_list = False
            result.append(line)
    
    if in_list:
        result.append(f'</{list_type}>')
    
    text = '\n'.join(result)
    
    # Convert line breaks
    text = re.sub(r'\n', '<br>', text)
    
    return text

@register.filter
def basename(value):
    """Extract just the filename from a path"""
    if not value:
        return ""
    return os.path.basename(value)
