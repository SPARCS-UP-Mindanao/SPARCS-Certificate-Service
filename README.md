# SPARCS Certificate Service

A serverless Certificate Service with SQS and Twillio SendGrid

## Architecture

This project follows a **Layered Serverless Architecture with Use-Case Driven Design**.

It separates responsibilities into:

- **Entry Layer** – `handler.py`, `CertEnvInit.py`
- **Business Layer** – `usecase/`
- **Domain Layer** – `model/`
- **Data Layer** – `repository/`
- **Infrastructure Layer** – `s3/`, `layers/`, `template/`
- **Support Layer** – `constants/`, `utils/`, `resources/`, `scripts/`

### Execution Flow

1. AWS Lambda receives an event (API Gateway or SQS).
2. `CertEnvInit.py` initializes environment and services.
3. `handler.py` delegates processing to a specific use case.
4. Use case executes business logic.
5. Certificate is generated → uploaded to S3 → emailed via SendGrid.

### Project Structure

├── constants/ # Application-wide constants

├── layers/ # AWS Lambda shared dependencies

├── model/ # Domain models

├── repository/ # Data access layer

├── resources/ # Static configuration/resources

├── s3/ # AWS S3 integration

├── scripts/ # Dev and deployment scripts

├── template/ # Certificate templates

├── usecase/ # Business logic

├── utils/ # Shared helpers

├── handler.py # Lambda entry point

└── CertEnvInit.py # Environment/bootstrap initialization

## Setup Local Environment

1. **Pre-requisites:**
   - Ensure Python 3.8 is installed

2. **Install pipenv:**
   ```shell
   pip install pipenv==2023.4.29 --user
   ```

3. **Install Python Dependencies:**
   ```shell
   pipenv install
   ```

4. **Activate Virtual Environment:**
   ```shell
   pipenv shell
   ```

5. **Add Environment Variables:**
    -  Add the `.env` file provided to you in the `backend` directory

## Run Locally

1. **Activate Virtual Environment:**
   ```shell
   pipenv shell
   ```

2. **Start Local Server:**
   ```shell
   uvicorn main:app --reload --log-level debug --env-file .env
   ```

## Setup AWS CLI

1. **Download and Install AWS CLI:**
   - [AWS CLI Installation Guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)

2. **Create AWS Profile:**
   ```shell
   aws configure --profile sparcs
   ```

   - **Input your AWS Access Key ID and AWS Secret Access Key provided to you.**
   - **Input `ap-southeast-1` for the default region name.**
   - **Leave blank for the default output format.**


## Setup Serverless Framework

1. **Pre-requisites:**
   - Ensure `Node 14` or later is installed

2. **Install serverless framework:**
   ```shell
   npm install -g serverless
   ```

3. **Install serverless plugins:**
   ```shell
   npm install
   ```

## Deploy to AWS
   ```shell
   serverless deploy --stage 'dev' --aws-profile 'sparcs' --verbose
   ```

## Best Practices Followed

### Architecture & Design

- Layered Architecture (separation of concerns)
- Use-case driven business logic
- Repository pattern for data access
- Thin Lambda handler
- Dedicated environment bootstrap (`CertEnvInit.py`)
- Infrastructure isolation (S3, SendGrid, SQS separated from business logic)
- No business logic inside handlers
- Environment-based configuration
- No hardcoded secrets
- Lambda layer for heavy dependencies (e.g., WeasyPrint)

### Naming Conventions

Consistency is enforced across the project.

#### Files & Folders
- Use `snake_case`
- Descriptive and responsibility-based naming

Examples:

         - generate_certificate.py
         - events_repository.py
         - s3_constants.py

#### Classes
- Use `PascalCase`
- Singular nouns
- Clear responsibility

Examples:

         - Certificate
         - EventsRepository
         - RegistrationGlobalSecondaryIndex

#### Functions
- Use `snake_case`
- Verb-based naming

Examples:

         - generate_certificate()
         - upload_file()
         - generate_presigned_url()

#### Constants
- Use `UPPER_CASE`
- Stored inside `constants/`

Examples:

         - HASH_KEY
         - REGISTRATION_ID
         - SUPER_ADMIN

## Resources

- [FastAPI](https://fastapi.tiangolo.com/)
- [Serverless Framework Documentation](https://www.serverless.com/framework/docs)
- [Clean Coder Blog](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
