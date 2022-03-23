# Flask OAuth

## Quick start

Clone the repository and copy .env.example file.

```console
$ cp .env.example .env
```

Don't forget to provide credentials in .env.

Create virtual environment and install dependencies.

```console
$ virtualenv env

$ source env/bin/activate

$ pip install -r requirements
```

Start application.

```console
$ python app.py
```

## Endpoints

start

![](screenshots/start.png)

index not logged in

![](screenshots/index_not_logged_in.png)

index logged in

![](screenshots/index_logged_in.png)

list/city

![](screenshots/list_city.png)

list/blabla (oops, wrong city)

![](screenshots/list_blabla.png)

list/london

![](screenshots/list_london.png)

city/date

![](screenshots/city_date.png)

london/22-03-2022

![](screenshots/london_22-03-2022.png)

about logged in

![](screenshots/about_logged_in.png)

about not logged in

![](screenshots/about_not_logged_in.png)

useragent

![](screenshots/useragent.png)