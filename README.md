# hw05_final


### Описание проекта

Социальная сеть yatube с возможностью создавать посты с картинками, подписываться на авторов,
комментировать, писать посты в тематические сообщества. Проект создавался с целью поупражняться
в использовании django.shortcuts, кэширования, sorl-thumbnail, в покрытии тестами, и в целом Django.

### Зависимости
```
Django==2.2.16
mixer==7.1.2
Pillow==8.3.1
pytest==6.2.4
pytest-django==4.4.0
pytest-pythonpath==0.7.3
requests==2.26.0
six==1.16.0
sorl-thumbnail==12.7.0
Faker==12.0.1
```
### Как запустить проект:

Клонировать репозиторий и перейти в него в командной строке:

```
git clone git@github.com:elina-kanz/hw05_final.git
```

```
cd hw05_final
```

Cоздать и активировать виртуальное окружение:

```
python3 -m venv env
```

```
source env/bin/activate
```

```
python3 -m pip install --upgrade pip
```

Установить зависимости из файла requirements.txt:

```
pip install -r requirements.txt
```

Выполнить миграции:

```
python3 manage.py migrate
```

Запустить проект:

```
python3 manage.py runserver
```

```

### Об авторе
Учусь на Яндекс.Практикуме на backend разработчика, есть физико-техническое образование. До практикума преподавала математику в школе и частно.
