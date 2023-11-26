import os
import tempfile
from http import HTTPStatus

import fitz
import jinja2
import pdfkit

from model.registrations.registration import RegistrationIn
from repository.events_repository import EventsRepository
from repository.registrations_repository import RegistrationsRepository
from s3.data_store import S3DataStore
from template.get_template import html_template
from utils.logger import logger


class CertificateUsecase:
    def __init__(self):
        self.__s3_data_store = S3DataStore()
        self.__registrations_repository = RegistrationsRepository()
        self.__events_repository = EventsRepository()

    def generate_certificate_html(self, template_img: str, name: str):
        j2 = jinja2.Environment()
        template = html_template()
        htmlTemplate = j2.from_string(template)
        return htmlTemplate.render(template_img=template_img, name=name)

    def generate_certficates(self, event_id: str):
        logger.info(f"Generating certificates for event: {event_id}")

        # Get Events Data
        status, event, message = self.__events_repository.query_events(event_id=event_id)
        if status != HTTPStatus.OK:
            logger.error(message)
            return

        template_img = event.certificateTemplate

        # Get Registration Data
        status, registrations, message = self.__registrations_repository.query_registrations(event_id=event_id)
        if status != HTTPStatus.OK:
            logger.error(message)
            return

        html_filename = 'certificate.html'
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                template_img_path = os.path.join(tmpdir, 'template_img.png')
                self.__s3_data_store.download_file(object_name=template_img, file_name=template_img_path)

                for registration in registrations:
                    logger.info(
                        f"Generating certificates for event: {event_id} registration: {registration.registrationId}"
                    )

                    # Generate Certificate HTML--------------------------------------------------------------------------------------------
                    name = f'{registration.firstName} {registration.lastName}'
                    certificate_name = f'{event_id}_{name}'
                    html_out = self.generate_certificate_html(template_img=template_img_path, name=name)
                    output_path = os.path.join(tmpdir, html_filename)
                    with open(output_path, 'w') as file:
                        file.write(html_out)

                    # Convert HTML to PDF-------------------------------------------------------------------------------------------------
                    certificate_name_pdf = f'{certificate_name}.pdf'
                    certificate_path = os.path.join(tmpdir, certificate_name_pdf)
                    options = {
                        'page-size': 'A4',
                        'orientation': 'Landscape',
                        'margin-top': '0mm',
                        'margin-right': '0mm',
                        'margin-bottom': '0mm',
                        'margin-left': '0mm',
                        "enable-local-file-access": "",
                    }
                    PATH_WKHTMLTOPDF = '/opt/bin/wkhtmltopdf'
                    PDFKIT_CONFIG = pdfkit.configuration(wkhtmltopdf=PATH_WKHTMLTOPDF)
                    pdfkit.from_string(
                        input=html_out, output_path=certificate_path, options=options, configuration=PDFKIT_CONFIG
                    )

                    # Get only the first page of the PDF----------------------------------------------------------------------------------
                    certificate_doc = fitz.open(certificate_path)
                    first_page_index = 0
                    first_page = certificate_doc.load_page(first_page_index)

                    # Create a new PDF to store the first page
                    doc_first_page = fitz.open()
                    doc_first_page.insert_pdf(certificate_doc, from_page=0, to_page=0)

                    # Save the new PDF
                    doc_first_page.save(certificate_path)
                    doc_first_page.close()

                    # Upload to S3-------------------------------------------------------------------------------------------------------
                    certificate_pdf_object_key = f'certificates/{event_id}/{name}/{certificate_name_pdf}'
                    self.__s3_data_store.upload_file(file_name=certificate_path, object_name=certificate_pdf_object_key)

                    # Convert to png-----------------------------------------------------------------------------------------------------
                    zoom = 4
                    mat = fitz.Matrix(zoom, zoom)
                    pix = first_page.get_pixmap(matrix=mat)

                    # Save the image-----------------------------------------------------------------------------------------------------
                    image_certificate_name = f'{certificate_name}.png'
                    image_path = os.path.join(tmpdir, image_certificate_name)
                    pix.save(image_path)

                    # upload to S3-------------------------------------------------------------------------------------------------------
                    certificate_img_object_key = f'certificates/{event_id}/{name}/{image_certificate_name}'
                    self.__s3_data_store.upload_file(file_name=image_path, object_name=certificate_img_object_key)
                    certificate_doc.close()

                    # Update Registration Entry-------------------------------------------------------------------------------------------
                    self.__registrations_repository.update_registration(
                        registration_entry=registration,
                        registration_in=RegistrationIn(
                            certificateImgObjectKey=certificate_img_object_key,
                            certificatePdfObjectKey=certificate_pdf_object_key,
                        ),
                    )

                    logger.info(
                        f"Success Generating certificates for event: {event_id} registration: {registration.registrationId}"
                    )

        except Exception as e:
            logger.error(f'Error Generating Certificate: {e}')
            return
