адрес сервера http://myfoodrecipes.ddns.net/recipes
логин и пароль администратора vasea01 vasea011
# FoodGram Project

FoodGram - это веб-приложение для обмена рецептами и создания списка покупок. Пользователи могут создавать рецепты, добавлять их в избранное, а также составлять список ингредиентов для покупок.

## Запуск проекта

1. Перейдите в директорию проекта:

cd backend

2. Установите зависимости из файла `requirements.txt`:

pip install -r requirements.txt

3. Примените миграции:

python manage.py migrate

4. Запустите сервер разработки:

python manage.py runserver

## Примеры запросов

- Получить список всех рецептов:

GET /api/recipes/

- Создать новый рецепт:

POST /api/recipes/

- Добавить рецепт в избранное:

POST /api/recipes/<recipe_id>/favorite/

## Использованные технологии

- Python
- Django
- Django REST Framework
- PostgreSQL
- Gunicorn
- Docker

## Автор

Проект разработан [Василе](https://github.com/EVA666999).
