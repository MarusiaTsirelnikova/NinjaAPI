from ninja import NinjaAPI, UploadedFile, File, Schema
from API.models import *
from typing import List
from django.shortcuts import get_object_or_404
from transliterate.utils import slugify
from langdetect import detect
from django.contrib.auth import authenticate, login, logout
from ninja.errors import HttpError, AuthenticationError
from django.contrib.auth.models import User


api = NinjaAPI()


class CategoryIn(Schema):
    title: str


class CategoryOut(Schema):
    id: int
    title: str
    slug: str


class CategoryForProducts(Schema):
    title: str


class ProductIn(Schema):
    title: str
    category: int
    description: str
    price: float


class ProductOut(Schema):
    id: int
    title: str
    slug: str
    category: CategoryForProducts
    description: str
    price: float


class ProductSchema(Schema):
    title: str
    price: float


class ProductSchema2(Schema):
    title: str
    description: str
    price: float


class UsersInfo(Schema):
    id: int
    username: str


class WishlistOut(Schema):
    product: ProductSchema
    count: int


class WishlistIn(Schema):
    product: int
    count: int = 1


class UserSchema(Schema):
    username: str
    is_authenticated: bool


class OrderSchema(Schema):
    id: int
    status: str
    total: float


class OrderSchemaOut(Schema):
    order: OrderSchema
    product: ProductSchema
    count: int


class UserAuthentication(Schema):
    username: str
    password: str


def is_russian(text):
    try:
        detected_language = detect(text)
        return detected_language == 'ru'
    except:
        return False


@api.post('/login')
def login_user(request, payload: UserAuthentication):
    user = authenticate(username=payload.username, password=payload.password)
    if user:
        login(request, user)
        return {payload.username: 'Пользователь вошел в систему!'}
    raise AuthenticationError()


@api.get('/user', response=UserSchema)
def is_user_authenticated(request):
    return request.user


@api.post('/logout')
def logout_user(request):
    logout(request)
    return 'Пользователь вышел из системы!'


@api.post('/categories', summary='Создать категорию')
def create_category(request, payload: CategoryIn):
    "Создание новой категории (Поле Slug заполняется автоматически)"
    if request.user.is_superuser or request.user.groups.filter(name='Менеджер'):
        if is_russian(payload.title):
            category = Category.objects.create(
                title=payload.title,
                slug=slugify(payload.title)
            )
        else:
            slugify_title = payload.title
            slugify_title = slugify_title.replace(' ', '-')
            category = Category.objects.create(
                title=payload.title,
                slug=slugify_title.lower()
            )
        return 'Категория ' + category.title + ' успешно создана'
    raise HttpError(403, 'У пользователя недостаточно прав')


@api.get('/categories', summary='Просмотреть категории', response=List[CategoryOut])
def list_of_categories(request):
    "Просмотр списка всех категорий товаров, хранящихся в базе данных"
    return Category.objects.all()


@api.post('/products', summary='Создать товар')
def create_product(request, payload: ProductIn, image: UploadedFile = File(...)):
    "Создание нового товара"
    if request.user.is_superuser or request.user.groups.filter(name='Менеджер'):
        if is_russian(payload.title):
            product = Product.objects.create(
                title=payload.title,
                slug=slugify(payload.title),
                category=get_object_or_404(Category, id=payload.category),
                description=payload.description,
                price=payload.price
            )
        else:
            slugify_title = payload.title
            slugify_title = slugify_title.replace(' ', '-')
            product = Product.objects.create(
                title=payload.title,
                slug=slugify_title.lower(),
                category=get_object_or_404(Category, id=payload.category),
                description=payload.description,
                price=payload.price
            )
        product.image.save(image.name, image)
        return 'Товар ' + product.title + ' успешно создан'
    raise HttpError(403, 'У пользователя недостаточно прав')


@api.get('/products', summary='Просмотреть товары', response=List[ProductOut])
def list_of_products(request):
    "Просмотр списка всех товаров, хранящихся в базе данных"
    return Product.objects.all()


@api.get('/categories/{category_slug}', summary='Получить категорию по slug', response=CategoryOut)
def get_category(request, category_slug: str):
    "Получение информации о конкретной категории по ее slug-полю"
    return get_object_or_404(Category, slug=category_slug)


@api.get('/products/{product_id}', summary='Получить продукт по id', response=ProductOut)
def get_product(request, product_id: int):
    "Получение информации о конкретном товаре по его id"
    return get_object_or_404(Product, id=product_id)


@api.delete('/category/{category_slug}', summary='Удалить категорию')
def delete_category(request, category_slug: str):
    "Удаление конкретной категории из базы данных по slug-полю"
    if request.user.is_superuser or request.user.groups.filter(name='Менеджер'):
        category = get_object_or_404(Category, slug=category_slug)
        category.delete()
        return {'success': 'Категория была удалена'}
    raise HttpError(403, 'У пользователя недостаточно прав')


@api.delete('/products/{product_id}', summary='Удалить продукт')
def delete_product(request, product_id: int):
    "Удаление конкретного товара из базы данных по его id"
    if request.user.is_superuser or request.user.groups.filter(name='Менеджер'):
        product = get_object_or_404(Product, id=product_id)
        product.delete()
        return {'success': 'Товар был удален'}
    raise HttpError(403, 'У пользователя недостаточно прав')


@api.put('/products/{product_id}', summary='Изменить товар')
def update_product(request, product_id: int, payload: ProductIn):
    "Изменение информации о конкретном товаре (товар находится по его id)"
    if request.user.is_superuser or request.user.groups.filter(name='Менеджер'):
        product = get_object_or_404(Product, id=product_id)
        for attribute, value in payload.dict().items():
            if attribute == 'category':
                category = get_object_or_404(Category, id=value)
                setattr(product, attribute, category)
            else:
                setattr(product, attribute, value)
        product.save()
        return {'success': 'Товар был изменен'}
    raise HttpError(403, 'У пользователя недостаточно прав')


@api.get('/filter_by_category/{category_slug}', summary='Сортировать товары по категории', response=List[ProductOut])
def products_sorted_by_category(request, category_slug: str):
    "Получение списка товаров, принадлежащих конкретной категории"
    category = get_object_or_404(Category, slug=category_slug)
    products = Product.objects.filter(category=category)
    return products


@api.get('/filter/min', summary='Сортировать по убыванию цены', response=List[ProductSchema])
def sorted_by_price_min(request):
    return Product.objects.order_by('-price')


@api.get('/filter/max', summary='Сортировать по возрастанию цены', response=List[ProductSchema])
def sorted_by_price_max(request):
    return Product.objects.order_by('price')


@api.get('/filter/name', summary='Найти по названию', response=List[ProductSchema2])
def sorted_by_name(request, name: str):
    return Product.objects.filter(title__icontains=name)


@api.get('/filter/description', summary='Найти по описанию', response=List[ProductSchema2])
def sorted_by_description(request, desc: str):
    return Product.objects.filter(description__icontains=desc)


@api.get('/users', summary='Посмотреть информацию о пользователях', response=List[UsersInfo])
def user_info(request):
    '''Информацию о пользователях может посмотреть только суперпользователь и/или суперпользователь'''
    if request.user.is_superuser or request.user.groups.filter(name='Менеджер'):
        users = User.objects.all()
        return users
    raise HttpError(403, 'У пользователя недостаточно прав')


@api.get('/wishlist', summary='Получить вишлист', response=List[WishlistOut])
def get_wishlist(request):
    '''Получить вишлист, принадлежащий вошедшемоу в систему пользователю'''
    wishlist = get_object_or_404(Wishlist, user=request.user)
    return WishlistProduct.objects.filter(wishlist=wishlist.id)


@api.post('/wishlist', summary='Добавить запись в вишлист')
def add_to_wishlist(request, payload: WishlistIn):
    '''Если вишлист существует, то функция добавляет в данный вишлист новую запись или обновляет ее, изменяя количество продукта.
    Если пользователь еще не имеет своего вишлиста, он будет автоматически создан перед добавлением/обновлением записи'''
    if not Wishlist.objects.filter(user=request.user):
        Wishlist.objects.create(user=request.user)

    products = list()

    if WishlistProduct.objects.filter(wishlist=get_object_or_404(Wishlist, user=request.user)):
        for wishlist_products in WishlistProduct.objects.filter(wishlist=get_object_or_404(Wishlist, user=request.user)):
            products.append(wishlist_products.product.id)
        if payload.product in products:
            product = WishlistProduct.objects.filter(wishlist=get_object_or_404(Wishlist, user=request.user),
                                                     product=get_object_or_404(Product, id=payload.product))
            total_count = payload.count + product.values_list('count')[0][0]
            WishlistProduct.objects.filter(wishlist=get_object_or_404(Wishlist, user=request.user),
                                           product=get_object_or_404(Product, id=payload.product)).update(count=total_count)

            return "Запись была обновлена"
        else:
            WishlistProduct.objects.create(wishlist=get_object_or_404(Wishlist, user=request.user),
                                           product=get_object_or_404(Product, id=payload.product),
                                           count=payload.count)
            return "Запись была создана"
    else:
        WishlistProduct.objects.create(wishlist=get_object_or_404(Wishlist, user=request.user),
                                       product=get_object_or_404(Product, id=payload.product),
                                       count=payload.count)
        return "Запись была создана"


@api.post('/wishlist/delete', summary='Удалить запись из вишлиста')
def remove_from_wishlist(request, payload: WishlistIn):
    '''Если '''
    products = list()

    if WishlistProduct.objects.filter(wishlist=get_object_or_404(Wishlist, user=request.user)):
        for wishlist_products in WishlistProduct.objects.filter(
                wishlist=get_object_or_404(Wishlist, user=request.user)):
            products.append(wishlist_products.product.id)
        if payload.product in products:
            product = WishlistProduct.objects.filter(wishlist=get_object_or_404(Wishlist, user=request.user),
                                                     product=get_object_or_404(Product, id=payload.product))
            if product.values_list('count')[0][0] > payload.count:
                total_count = product.values_list('count')[0][0] - payload.count
                WishlistProduct.objects.filter(wishlist=get_object_or_404(Wishlist, user=request.user),
                                               product=get_object_or_404(Product, id=payload.product)).update(count=total_count)
                return "Запись была обновлена"
            else:
                WishlistProduct.objects.filter(wishlist=get_object_or_404(Wishlist, user=request.user),
                                               product=get_object_or_404(Product, id=payload.product)).delete()
                return "Запись была удалена"


@api.get('/order', summary='', response=List[OrderSchema])
def get_order(request):
    ''''''
    if request.user.is_superuser or request.user.groups.filter(name='Менеджер'):
        return Order.objects.all()
    raise HttpError(403, 'У пользователя недостаточно прав')


@api.post('/order/add', summary='')
def add_to_order(request, payload: WishlistIn):
    ''''''
    if not Order.objects.filter(user=request.user):
        Order.objects.create(user=request.user, status='new', total=0)
        order = get_object_or_404(Order, user=request.user)
    else:
        if Order.objects.filter(user=request.user, status='new'):
            order = Order.objects.filter(user=request.user, status='new').first()
        else:
            Order.objects.create(user=request.user, status='new', total=0)
            order = Order.objects.filter(user=request.user, status='new').first()

    products = list()

    if OrderProduct.objects.filter(order=order):
        for order_products in OrderProduct.objects.filter(order=order):
            products.append(order_products.product.id)
        if payload.product in products:
            product = OrderProduct.objects.filter(order=order,
                                                  product=get_object_or_404(Product, id=payload.product))
            total_count = payload.count + product.values_list('count')[0][0]
            OrderProduct.objects.filter(order=order,
                                        product=get_object_or_404(Product, id=payload.product)).update(count=total_count)
            Order.objects.filter(user=request.user, status='new').update(total=order.get_total())
            return "Запись была обновлена"
        else:
            product_price = Product.objects.filter(id=payload.product).values_list('price')[0][0]
            OrderProduct.objects.create(order=order,
                                        product=get_object_or_404(Product, id=payload.product),
                                        price=product_price,
                                        count=payload.count)
            Order.objects.filter(user=request.user, status='new').update(total=order.get_total())
            return "Запись была создана"
    else:
        product_price = Product.objects.filter(id=payload.product).values_list('price')[0][0]
        OrderProduct.objects.create(order=order,
                                    product=get_object_or_404(Product, id=payload.product),
                                    price=product_price,
                                    count=payload.count)
        Order.objects.filter(user=request.user, status='new').update(total=order.get_total())
        return "Запись была создана"


@api.get('/order/{order_id}', summary='', response=List[OrderSchemaOut])
def get_order_id(request, order_id: int):
    ''''''
    order = get_object_or_404(Order, id=order_id)
    return OrderProduct.objects.filter(order=order.id)


@api.put('/order/{order_id}', summary='')
def update_order_status(request, order_id: int, status: str):
    ''''''
    if request.user.is_superuser or request.user.groups.filter(name='Менеджер'):
        if status in Order.STATUS:
            Order.objects.filter(id=order_id).update(status=status)
            return 'Статус заказа был изменен'
        else:
            return 'Не получилось сменить статус заказа'
    raise HttpError(403, 'У пользователя недостаточно прав')