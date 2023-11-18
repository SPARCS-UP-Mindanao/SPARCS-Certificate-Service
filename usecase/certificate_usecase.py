import logging
import os
import tempfile
from typing import List

import jinja2
import pdfkit
import fitz  

from template.get_template import html_template


class CertificateUsecase:
    def __init__(self):
        self.logger = logging.getLogger()

    def generate_certificate_html(self, template_img: str, name: str):
        j2 = jinja2.Environment()
        template = html_template()
        htmlTemplate = j2.from_string(template)
        return htmlTemplate.render(template_img=template_img, name=name)

    def generate_certficates(self, template_img: str, names: List[str], event_name: str):
        try:
            for name in names:
                with tempfile.TemporaryDirectory() as tmpdir
                    html_out = self.generate_certificate_html(template_img=template_img, name=name)
                    html_filename = 'certificate.html'
                    output_path = os.path.join(tmpdir, html_filename)
                    with open(output_path, 'w') as file:
                        file.write(html_out)

                    certificate_name = f'{event_name}_{name}.pdf'
                    certificate_path = os.path.join(tmpdir, certificate_name)
                    options = {
                        'page-size': 'A4',
                        'orientation': 'Landscape',
                        'margin-top': '0mm',
                        'margin-right': '0mm',
                        'margin-bottom': '0mm',
                        'margin-left': '0mm',
                    }
                    pdfkit.from_string(input=html_out, output_path=certificate_path, options=options)

                    certificate_doc = fitz.open(certificate_path)

                    first_page = certificate_doc.load_page(0)  # 0 is the index of the first page

                    # Create a new PDF to store the first page
                    doc_first_page = fitz.open()
                    doc_first_page.insert_pdf(certificate_doc, from_page=0, to_page=0)

                    # Save the new PDF
                    doc_first_page.save(certificate_path)
                    doc_first_page.close()
                    
                    # TODO: upload to S3
                    
                    # TODO: Convert to png
                    # Render the page to a pixmap (an image)
                    pix = first_page.get_pixmap()

                    # Save the image
                    image_path = os.path.join(tmpdir, f'{certificate_name}.png')
                    pix.save(image_path)
                    
                    # TODO: upload to S3

                    certificate_doc.close()

        except Exception as e:
            self.logger.error(e)
            return
