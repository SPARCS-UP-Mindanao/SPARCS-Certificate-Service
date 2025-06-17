FROM public.ecr.aws/lambda/python:3.8


ARG FUNCTION_DIR="/var/task"
RUN mkdir -p ${FUNCTION_DIR}

RUN pip install pipenv
RUN yum install -y pango

COPY Pipfile ${LAMBDA_TASK_ROOT}
COPY Pipfile.lock ${LAMBDA_TASK_ROOT}

RUN pipenv install --system --deploy --ignore-pipfile

COPY . ${LAMBDA_TASK_ROOT}

CMD [ "handler.generate_certificate_handler" ]
