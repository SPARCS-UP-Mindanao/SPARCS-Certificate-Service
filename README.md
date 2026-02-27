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

## Development Setup

1. **Prerequisites:**
   - Visual Studio Code
   - VS Code Dev Containers extension
   - Docker Desktop
   - AWS CLI configured on host machine (`aws configure`)

2. **Clone and Open Project**
   ```shell
   git clone https://github.com/SPARCS-UP-Mindanao/SPARCS-Certificate-Service.git 
   cd SPARCS-Certificate-Service
   ```
   
   Open the folder in VS Code. VS Code will detect the dev container configuration and show a notification:
   
   **"Folder contains a Dev Container configuration file. Reopen folder to develop in a container"**
   
   Click **Reopen in Container** or manually open with `Ctrl` + `Shift` + `P` → `Dev Containers: Reopen in Container`

   The dev container will automatically:
   
   - Build the container environment
   - Install all dependencies
   - Configure AWS CLI with your host credentials

## Local Development

1. **Install Python Dependencies:**
   ```shell
   pipenv install
   ```

2. **Activate Virtual Environment:**
   ```shell
   pipenv shell
   ```

## Setup AWS SSO

1. **Configure AWS SSO Profile:**
   ```shell
   aws configure sso
   ```

   **You will be prompted for:**
   - **SSO Start URL** (provided by your organization)
   - **SSO Region** → `ap-southeast-1`
   - **CLI default client Region** → `ap-southeast-1`
   - **CLI default output format** → `json`
   - **CLI profile name** → `sparcs`

   After entering SSO details, authenticate in your browser and select your AWS account and role.

2. **Login via SSO:**
   ```shell
   aws sso login --profile sparcs
   ```

3. **Verify Identity:**
   ```shell
   aws sts get-caller-identity --profile sparcs
   ```

## Deploy to AWS

1. **Install serverless plugins:**
   ```shell
   npm install
   ```

2. **Deploy:**
   ```shell
   npx serverless deploy --stage dev --aws-profile sparcs --verbose
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
