from usecase.certificate_usecase import CertificateUsecase


def generate_cert_test():
    cert = CertificateUsecase()
    cert.generate_certficates(
        template_img='https://dimaker.online/cdn/img/template/redactor/zqq5spi68qc30urxtw4yf5vk1scr18urcjstuyegkweor5jm2f.jpg',
        names=['Arnel Jan Sarmiento'],
        event_name='Career Talks 2023',
    )


if __name__ == '__main__':
    generate_cert_test()
