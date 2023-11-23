from usecase.certificate_usecase import CertificateUsecase


def generate_cert_test():
    cert = CertificateUsecase()
    cert.generate_certficates('string')


if __name__ == '__main__':
    generate_cert_test()
