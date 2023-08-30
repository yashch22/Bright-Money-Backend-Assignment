# Bright-Money-Backend-Assignment






<img src="https://www.sherpalo.com/static/e2e31bb6a086dbce5418180ac1a6c646/logo_bright-colour.png" alt="Image Alt Text" width="200">


## Table of Contents
- [Tech Stack](#tech-stack)
- [Installation](#installation)
- [Data Model](#DataModel)
- [Project Structure](#project-structure)
- [API Endpoint](#api-endpoint)



---

## Tech Stack

![Django](https://static.djangoproject.com/img/logos/django-logo-negative.1d528e2cb5fb.png) <img src="https://blog.knoldus.com/wp-content/uploads/2019/05/rabbitmq.png" alt="RabbitMq Logo" height="48">![Sqlite](https://upload.wikimedia.org/wikipedia/commons/thumb/3/38/SQLite370.svg/2560px-SQLite370.svg.png) 


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


