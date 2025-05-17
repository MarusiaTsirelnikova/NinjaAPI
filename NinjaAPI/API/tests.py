from django.test import TestCase
from ninja_API.api import *
from .models import *

# Create your tests here.


class LoginUserTest(TestCase):
    fixtures = ['data.json']
    right_payload = {
        'username': 'admin',
        'password': 'admin',
    }

    false_payload = {
        'username': 'admin',
        'password': '123',
    }

    def test_login(self):
        response = self.client.post('/api/login',
                                    content_type='application/json',
                                    data=self.right_payload,
                                    follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), {'admin': 'Пользователь вошел в систему!'})

    def test_no_login(self):
        response = self.client.post('/api/login',
                                    content_type='application/json',
                                    data=self.false_payload,
                                    follow=True)
        self.assertEqual(response.status_code, 401)


class LogoutUserTest(TestCase):
    def test_logout(self):
        response = self.client.post('/api/logout')
        self.assertEqual(response.status_code, 200)


class UserSchemaTest(TestCase):
    def test_user_return_schema(self):
        user = User(username='admin')
        schema = UserSchema.from_orm(user)

        self.assertEqual(user.username, schema.username)
        self.assertEqual(user.is_authenticated, schema.is_authenticated)


class CategoryInSchemaTest(TestCase):
    def test_category_return_schema(self):
        category = Category(title='category', slug='category')
        schema = CategoryIn.from_orm(category)

        self.assertEqual(category.title, schema.title)


class CategoryOutSchema(TestCase):
    def test_category_out(self):
        category = Category(id=1, title='category', slug='category')
        schema = CategoryOut.from_orm(category)

        self.assertEqual(category.id, schema.id)
        self.assertEqual(category.title, schema.title)
        self.assertEqual(category.slug, schema.slug)


class ProductInSchemaTest(TestCase):
    def test_product_return_schema(self):
        category = Category(id=1, title='category', slug='category')

        product = Product(title='random product',
                          slug='random-product',
                          category=category,
                          price=10,
                          description='description of random product')
        schema = ProductIn(title=product.title,
                           category=product.category.id,
                           description=product.description,
                           price=product.price)

        self.assertEqual(product.title, schema.title)
        self.assertEqual(product.category.id, schema.category)
        self.assertEqual(product.description, schema.description)
        self.assertEqual(product.price, schema.price)


class CategoryTest(TestCase):
    fixtures = ['data.json']

    payload = {
        'title': 'Random Category'
    }

    def test_get_category(self):
        response = self.client.get('/api/categories/new-category')

        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), {
            'id': 10,
            'title': 'new Category',
            'slug': 'new-category'
        })

    def test_get_categories(self):
        response = self.client.get('/api/categories')

        self.assertEqual(response.status_code, 200)

    def test_create_category(self):
        self.client.post('/api/login',
                         content_type='application/json',
                         data={'username': 'admin',
                               'password': 'admin'},
                         follow=True)
        response = self.client.post('/api/categories',
                                    content_type='application/json',
                                    data=self.payload)

        self.assertEqual(response.status_code, 200)

    def test_create_category_no_permissions(self):
        self.client.post('/api/login',
                         content_type='application/json',
                         data={'username': 'user',
                               'password': 'user_123'},
                         follow=True)
        response = self.client.post('/api/categories',
                                    content_type='application/json',
                                    data=self.payload)

        self.assertEqual(response.status_code, 403)

    def test_create_category_no_rights(self):
        user = User.objects.get(username='user')
        response = self.client.post('/api/categories',
                                    content_type='application/json',
                                    data=self.payload,
                                    user=user)

        self.assertEqual(response.status_code, 403)

    def test_delete_category(self):
        self.client.post('/api/login',
                         content_type='application/json',
                         data={'username': 'admin',
                               'password': 'admin'},
                         follow=True)
        response = self.client.delete('/api/category/new-category')

        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), {'success': 'Категория была удалена'})

    def test_delete_category_no_permissions(self):
        self.client.post('/api/login',
                         content_type='application/json',
                         data={'username': 'user',
                               'password': 'user_123'},
                         follow=True)
        response = self.client.delete('/api/category/new-category')

        self.assertEqual(response.status_code, 403)

    def test_wrong_slug_category(self):
        response = self.client.get('/api/categories/wrong-category')

        self.assertEqual(response.status_code, 404)


class ProductTest(TestCase):
    fixtures = ['data.json']

    def test_get_product_by_id(self):
        response = self.client.get('/api/products/3')

        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), {
            'id': 3,
            'title': 'IPhone',
            'slug': 'iphone',
            'category': {
                'title': 'Сматрфон'
            },
            'description': 'A very expensive phone',
            'price': 120000.00
        })

    def test_get_product_by_slug(self):
        response = self.client.get('/api/filter_by_category/Smatrfon')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [{
            'id': 3,
            'title': 'IPhone',
            'slug': 'iphone',
            'category': {
                'title': 'Сматрфон'
            },
            'description': 'A very expensive phone',
            'price': 120000.00
        }])

    def test_get_products(self):
        response = self.client.get('/api/products')

        self.assertEqual(response.status_code, 200)

    def test_delete_product(self):
        self.client.post('/api/login',
                         content_type='application/json',
                         data={'username': 'admin',
                               'password': 'admin'},
                         follow=True)
        response = self.client.delete('/api/products/3')

        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), {'success': 'Товар был удален'})

    def test_delete_product_no_permissions(self):
        self.client.post('/api/login',
                         content_type='application/json',
                         data={'username': 'user',
                               'password': 'user_123'},
                         follow=True)
        response = self.client.delete('/api/products/3')

        self.assertEqual(response.status_code, 403)

    def test_find_product_by_name(self):
        response = self.client.get('/api/filter/name?name=Phone')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [{
            'title': 'IPhone',
            'description': 'A very expensive phone',
            'price': 120000
        }])

    def test_find_product_by_wrong_name(self):
        response = self.client.get('/api/filter/name?name=something-silly-and-not-real')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_find_product_by_description(self):
        response = self.client.get('/api/filter/description?desc=very')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [{
            'title': 'IPhone',
            'description': 'A very expensive phone',
            'price': 120000
        }])

    def test_find_product_by_wrong_description(self):
        response = self.client.get('/api/filter/description?desc=i-should-make-some-coffee')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_wrong_product_id(self):
        response = self.client.get('/api/products/1')

        self.assertEqual(response.status_code, 404)

    def test_wrong_category_slug(self):
        response = self.client.get('/api/filter_by_category/im-not-real-lol')

        self.assertEqual(response.status_code, 404)


class OrderTest(TestCase):
    fixtures = ['data.json']

    def test_get_order(self):
        self.client.post('/api/login',
                         content_type='application/json',
                         data={'username': 'admin',
                               'password': 'admin'},
                         follow=True)
        response = self.client.get('/api/order')

        self.assertEqual(response.status_code, 200)

    def test_get_order_no_permissions(self):
        self.client.post('/api/login',
                         content_type='application/json',
                         data={'username': 'user',
                               'password': 'user_123'},
                         follow=True)
        response = self.client.get('/api/order')

        self.assertEqual(response.status_code, 403)

    def test_get_order_by_id(self):
        response = self.client.get('/api/order/14')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [
            {
                "order": {
                    "id": 14,
                    "status": "new",
                    "total": 240000
                },
                "product": {
                    "title": "IPhone",
                    "price": 120000
                },
                "count": 2
            }
        ])

    def test_not_get_order_by_id(self):
        response = self.client.get('/api/order/1')

        self.assertEqual(response.status_code, 404)

    def test_update_order_status(self):
        self.client.post('/api/login',
                         content_type='application/json',
                         data={'username': 'admin',
                               'password': 'admin'},
                         follow=True)
        response = self.client.put('/api/order/14?status=delivered')

        self.assertEqual(response.status_code, 200)

    def test_update_order_status_no_permissions(self):
        self.client.post('/api/login',
                         content_type='application/json',
                         data={'username': 'user',
                               'password': 'user_123'},
                         follow=True)
        response = self.client.put('/api/order/14?status=delivered')

        self.assertEqual(response.status_code, 403)
