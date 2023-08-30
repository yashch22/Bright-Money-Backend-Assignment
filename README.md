# Bright-Money-Backend-Assignment






<img src="https://www.sherpalo.com/static/e2e31bb6a086dbce5418180ac1a6c646/logo_bright-colour.png" alt="Bright Money logo" width="200">


## Table of Contents
- [Tech Stack](#tech-stack)
- [Installation](#installation)
- [Data Model](#DataModel)
- [Project Structure](#project-structure)
- [API Endpoint](#api-endpoint)
- [Future Scope](#future-improvements)



---

## Tech Stack

<img src="https://static.djangoproject.com/img/logos/django-logo-negative.1d528e2cb5fb.png" alt="Django logo" width="200">
<img src="https://blog.knoldus.com/wp-content/uploads/2019/05/rabbitmq.png" alt="RabbitMq Logo" width="200">
<img src="https://upload.wikimedia.org/wikipedia/commons/thumb/3/38/SQLite370.svg/2560px-SQLite370.svg.png" alt="Django logo" width="200">



## Installation


To get started with the project, follow these steps:

1. Clone the repository:
   ```
   https://github.com/yashch22/Bright-Money-Backend-Assignment.git
   ```
   
2. Set up a virtual environment:
   ``` 
   python3 -m venv venv  # Create a virtual environment
   source venv/bin/activate  # Activate the virtual environment (on macOS/Linux)

   ```


3. Install Dependencies from requirements.txt:
   ``` 
   pip3 install -r requirements.txt

   ```
4. Setup and run rabbitmq:
   On mac
   ``` 
   brew install rabbitmq
   export PATH=$PATH:/usr/local/opt/rabbitmq/sbin
   brew services start rabbitmq
   ```

5. Apply Migrations and run the server:
   ``` 
   python3 manage.py makemigrations
   python3 manage.py migrate
   python3 manage.py runserver

   ```
## Data Model
<img src="loan_management_system/assets/<Models.svg" alt="Bright Money logo" width="200">


## Project Structure
The project structure is organized as follows:
```
loan_management_system/
├── loan_app/
│   ├── migrations/
│   ├── tasks.py
│   ├── templates/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── tests.py
│   └── views.py
├── loan_management_system/
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   ├── celer.py
│   └── wsgi.py
└── manage.py
         
```

## API Endpoint
The backend exposes the following API endpoints:
- **POST /register-user**: Register a new user,
- **POST /apply-loan/**: Loan application for existing user.
- **POST /make-payment/**: Make a payment against existing loan
- **GET /get-statement/**: Retrieve a specific form by its ID.

## Future Scope

1. **Enhanced User Authentication**: We plan to introduce a robust authentication system that allows users to create passwords, enhancing account security and providing a more personalized experience.
2. **Streamlined Authentication with JWT**: Our roadmap includes implementing JSON Web Tokens (JWT) for authentication. This not only improves security but also reduces payload size, leading to faster and smoother authentication processes.
3. **Dockerization for Ease of Deployment**: We're exploring the Dockerization of our system to simplify deployment across different environments. Docker containers will ensure consistency and easy scaling, making the platform more accessible and manageable.
4. **Microservices Architecture**: Moving towards a microservices architecture, where different components of the system, such as user registration, loan applications, payments, and statements, will be developed and deployed as individual microservices. This decoupled structure allows us to isolate functionalities and scale them as needed.
