#!/usr/bin/env python3
"""Fix web_app.py formatting"""

with open('web_app.py', 'r') as f:
    content = f.read()

# Fix the literal \n that was introduced
content = content.replace(r'render_template(\n        "index.html",', 'render_template(\n        "index.html",')

with open('web_app.py', 'w') as f:
    f.write(content)

print('web_app.py fixed')
