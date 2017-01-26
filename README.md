# fm-django
Feedmee's django based admin backend, api, and any further webapps such as advertising management pages.

## Project Structure

* Main URL routes begin in `root/urls.py`
* Auth app adds rate limited login
* Currently root is a login screen as this is an internal use only system, however that may change.
* API app contains django-rest-framework based api setup available over `/api/`
* All models in `main/models.py` for sharing with future apps such as ad management system.

***Write tests or die!***
