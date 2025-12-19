### School Management System

In Production
Parent login redirected to http://localhost:8000/children/my-children/
Admin Login to Dashboard http://localhost:8000/admin/login/?next=/admin/
All other user roles login at http://localhost:8000/accounts/login/

## Environment Setup
Clone main to local computer.
set up `.venv` or `venv` virtual enviroment using `py -m venv .venv` in cloned folder besides project folder.
Activate virtual env `.venv\Scripts\activate`
`cd` to project folder `DMS`
run `py -m pip install -r requirements.txt` to install project dependencies
run `py manange.py runserver to start development sever`

#### TroubleShoot
Set Execution Policies to remotesigned 

