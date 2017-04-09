# fm-django
Feedmee's django based admin backend, api, and any further webapps such as advertising management pages.

## Project Structure

* Main URL routes begin in `root/urls.py`
* Auth app adds rate limited login
* Currently root is a login screen as this is an internal use only system, however that may change.
* API app contains django-rest-framework based api setup available over `/api/`
* All models in `main/models.py` for sharing with future apps such as ad management system.

## Local Environment Setup

### Homebrew

Homebrew is a package manager for macOS and the easiest way to install dependencies.

`$ /usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"`

### Python 3.4 Runtime

```bash
$ brew tap 20015jjw/python34
$ brew install python34
```

### Postgis server via Docker

Install Docker from https://www.docker.com

Then start a Postgis container with the following command:

`$ docker run --name fm-postgis -e POSTGRES_PASSWORD=mysecretpassword -d mdillon/postgis -p 5436:5432`

This builds a docker image from the `dmillon/postgis` image, calls the instance `fm-postgis`, and maps `127.0.0.1:5436` to port `5432` inside the container.

Congrats you now have a Postgis server!

### Postgis dependencies

Install the following libraries via brew:

```bash
$ brew install gdal
$ brew install libgeoip
```

### Virtualenv

Install [virtualenv](https://www.dabapps.com/blog/introduction-to-pip-and-virtualenv-python/) to create an isolated python environment for the project.

```bash
$ cd ~/fm-django
$ pip install virtualenv
$ virtualenv env -p python34
$ source env/bin/activate
(env) $ pip install -r requirements.txt
```

### Environment Variables

fm-django uses several environment variables to control server behaviour and access resources without checking keys into source control.

First we need to open the environment activation script for modification.

```bash
$ vim env/bin/activate
```

Within the `deactivate` function definition find `unset VIRTUALENV` and add the following lines immediately _before_ it:

```bash
unset RDS_DB_NAME
unset RDS_USERNAME
unset RDS_PASSWORD
unset RDS_HOSTNAME
unset RDS_PORT
unset DEPLOYMENET
unset DJANGO_SECRET_KEY
unset AWS_S3_STATIC_KEY
unset AWS_S3_STATIC_ID
```

Next find the following code:

```bash
_OLD_VIRTUAL_PATH="$PATH"
PATH="$VIRTUAL_ENV/bin:$PATH"
export PATH
```

_After_ it add this:

```bash
export RDS_DB_NAME="postgres"
export RDS_USERNAME="postgres"
export RDS_PASSWORD=""
export RDS_HOSTNAME="localhost"
export RDS_PORT="5436"
export DEPLOYMENT="LOCAL"
export DJANGO_SECRET_KEY="@-tybl$e2m#9od*@%g$cr1)y#h6y&@-d!r!2sq)8ixvq+&sb(e"
export AWS_S3_STATIC_KEY="kJGEvPxtm9aeQnrG0zyG6iJlL3FbTYBY5KpEJe2z"
export AWS_S3_STATIC_ID="AKIAIUW5JZYOGAZBWA5Q"
```

Now rerun `$ source env/bin/activate` to apply these environment variables before continuing.

### Build database schema

Run the following command to apply database schema to your new postgis database.

`$ python manage.py migrate`

### Dummy Data

Load dummy data via the following commands:

```bash
$ python manage.py loaddata fixtures/blogs.json
$ python manage.py loaddata fixtures/cuisines.json
$ python manage.py loaddata fixtures/highlights.json
$ python manage.py loaddata fixtures/keywords.json
$ python manage.py loaddata fixtures/dishes_restaurants_subsets.json
$ python manage.py loaddata fixtures/opening_times.json
```

### Hoorah!

Now you can start the webserver by running `$ python manage.py runserver`.

If you docker container stops, start it up again with `$ docker start fm-postgis`.

## Change Management
Changes to the software is managed with Github Issues.  All changes should be documented with an associated Github issue.  The Issue should state the general goal of the change, the UI design and any other considerations.  

Each commit comment associated with a change should have #34 issue number so there is a record of why a source code change was made.  

## Github Workflow

We are using the `branch` feature of git to manage our change workflow. Further a general discussion of GitHub [workflows](http://blog.endpoint.com/2014/05/git-workflows-that-work.html) .   

Our basic development process is:

1. The developer creates a branch associated with a feature or a specific issue or bug.
2. The developer commit's changes to the branch locally frequently during the day and pushes changes to the feature branch to the server at lease once a work day.
3. Once the developer is satisfied that the feature is complete or issue is resolved. He submits a pull request to merge the changes into the develop branch.
4. Another responsible team member reviews the changes and approves of the pull request.
5. The develop branch is continuously deployed to our [dev server](http://fm-webserver-dev.us-west-2.elasticbeanstalk.com/).
6. When ready for general release it is tagged and merged into the master branch, where it is tested and deployed to [production server](https://use.feedmeeapp.com/).

### master branch
The master branch is the source code for the code currently running on production server.

### develop branch
The develop branch contains the currently completed work of the development team running on the development server.

### release branches
Additional branches can be created to allow general development to continue while a specific release is stabilized and prepared for general release. Release branches will have descriptive branches like release_1_0

### feature or issue branches
These branches are where developers spend most of their time.  The name should be a short but meaningful name.   For example 14_Android_Session, which would be issue 14, which deals with implementing the session logic for the Android platform.
