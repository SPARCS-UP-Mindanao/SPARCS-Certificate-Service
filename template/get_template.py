def html_template():
    with open('../template/certificate_template.html', 'r') as template:
        content = template.read()
    return content
