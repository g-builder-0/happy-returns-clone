from django.test import TestCase #QUESTION: what are the important methods defined in TestCase?
from django.contrib.auth.models import User
from rest_framework.test import APITestCase, APIClient
from rest_framework.authtoken.models import Token
from rest_framework import status
from .models import Merchant, Consumer, Return, ReturnItem


class MerchantModelTest(TestCase):
    """Test Merchant model"""

    def setUp(self):
        self.merchant = Merchant.objects.create(
            name="Test Store",
            email="test@store.com",
            api_key="test123"
        )

    def test_merchant_creation(self):
        """Test merchant is created correctly"""
        self.assertEqual(self.merchant.name, "Test Store")
        self.assertEqual(self.merchant.email, "test@store.com")
        self.assertTrue(self.merchant.is_active) #QUESTION: this is true by default?

    def test_merchant_str(self):
        """Test merchant string representation"""
        self.assertEqual(str(self.merchant), "Test Store")


class ConsumerModelTest(TestCase):
    """Test Consumer model"""

    def setUp(self):
        self.consumer = Consumer.objects.create(
            email="customer@example.com",
            first_name="John",
            last_name="Doe"
        )

    def test_consumer_creation(self):
        """Test consumer is created correctly"""
        self.assertEqual(self.consumer.email, "customer@example.com")
        self.assertEqual(self.consumer.first_name, "John")

    def test_consumer_str(self):
        """Test consumer string representation"""
        self.assertEqual(str(self.consumer), "John Doe (customer@example.com)") #QUESTION: How does python know to concatenate first_name and last_name and email (along with parentheses)


class ReturnModelTest(TestCase):
    """Test Return model with nested items"""

    def setUp(self): #QUESTION: Why do we need to create a new Merchant and Consumer for every test case? Why can't we just use the one we already have?
        self.merchant = Merchant.objects.create(
            name="Test Store",
            email="test@store.com"
        )
        self.consumer = Consumer.objects.create(
            email="customer@example.com",
            first_name="John",
            last_name="Doe"
        )
        self.return_obj = Return.objects.create(
            merchant=self.merchant,
            consumer=self.consumer,
            order_number="ORD-12345",
            authorization_code="RET-ABC123",
            refund_amount=99.99,
            status=Return.STATUS_INITIATED
        )

    def test_return_creation(self):
        """Test return is created correctly"""
        self.assertEqual(self.return_obj.order_number, "ORD-12345") #QUESTION: why do we keep pretentiously using .assertEqual() rather than just '='?
        self.assertEqual(self.return_obj.status, Return.STATUS_INITIATED)
        self.assertEqual(self.return_obj.refund_amount, 99.99)

    def test_return_with_items(self):
        """Test return with nested items"""
        item = ReturnItem.objects.create(
            return_obj=self.return_obj, #QUESTION: Why are we creating a variable return_obj to reference its own return_obj attribute?
            product_name="Test Product",
            product_sku="SKU-123",
            quantity=2,
            unit_price=49.99,
            return_reason=ReturnItem.REASON_UNWANTED
        )
        self.assertEqual(self.return_obj.items.count(), 1) #QUESTION: Why are we asking if the quantity is 1 when we know it's 2?
        self.assertEqual(item.product_name, "Test Product")


class MerchantAPITest(APITestCase): #QUESTION: What is the point of using APITestCase rather than TestCase? What are the attributes of an instance of APITestCase?
    """Test Merchant API endpoints"""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.token = Token.objects.create(user=self.user)
        self.client = APIClient() #QUESTION: What is APIClient()? Isn't this name overly generic when we are testing the MerchantAPI() specifically? Why do we need to instantiate it?
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key) #QUESTION: what is token.key and what are the other attributes of token? In which class is the credentials() method defined and is it part of DRF?

    def test_create_merchant(self):
        """Test creating merchant via API"""
        data = {
            'name': 'New Store',
            'email': 'new@store.com',
            'is_active': True
        }
        response = self.client.post('/api/merchants/', data, format='json') #QUESTION: What is the purpose of the post() function and when is it commonly used?
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Merchant.objects.count(), 1) #QUESTION: Why do we want the number of merchants in the database to be 1?
        self.assertEqual(Merchant.objects.get().name, 'New Store')

    def test_list_merchants(self):
        """Test listing merchants"""
        Merchant.objects.create(name='Store 1', email='store1@test.com', api_key='test_key_1')
        Merchant.objects.create(name='Store 2', email='store2@test.com', api_key='test_key_2')

        response = self.client.get('/api/merchants/') #QUESTION: Are we calling the /api/merchants endpoint with the HTTP GET method, hoping to get a list of merchants in JSON format?
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2) #QUESTION: why does the length of the response need to be 2 characters? Does len() refer to the number of characters, number of items in a list or number of values in a dictionary?


class ConsumerAPITest(APITestCase):
    """Test Consumer API endpoints"""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.token = Token.objects.create(user=self.user)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

    def test_create_consumer(self):
        """Test creating consumer via API"""
        data = {
            'email': 'customer@test.com',
            'first_name': 'Jane',
            'last_name': 'Smith'
        }
        response = self.client.post('/api/consumers/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Consumer.objects.count(), 1)


class ReturnAPITest(APITestCase):
    """Test Return API endpoints"""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass') #QUESTION: create_user() is a method defined in the User class?
        self.token = Token.objects.create(user=self.user)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

        self.merchant = Merchant.objects.create(name='Test Store', email='test@store.com')
        self.consumer = Consumer.objects.create(
            email='customer@test.com',
            first_name='John',
            last_name='Doe'
        )

    def test_create_return_with_items(self):
        """Test creating return with nested items"""
        data = {
            'merchant': self.merchant.id,
            'consumer': self.consumer.id,
            'order_number': 'ORD-123',
            'authorization_code': 'RET-XYZ',
            'refund_amount': '150.00',
            'items': [ #QUESTION: Where is it specified that items in a return are to be listed as a value in a dictionary which contains a list of dictionaries?
                {
                    'product_name': 'Product 1',
                    'product_sku': 'SKU-001',
                    'quantity': 1,
                    'unit_price': '75.00',
                    'return_reason': 'UNWANTED'
                },
                {
                    'product_name': 'Product 2',
                    'product_sku': 'SKU-002',
                    'quantity': 1,
                    'unit_price': '75.00',
                    'return_reason': 'DEFECTIVE'
                }
            ]
        }
        response = self.client.post('/api/returns/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Return.objects.count(), 1) #QUESTION: Why is it important to verify that we only have 1 record in the Return table? Do we anticipate that another record was secretly added without our knowledge?
        self.assertEqual(Return.objects.get().items.count(), 2)

    def test_filter_returns_by_status(self):
        """Test filtering returns by status"""
        Return.objects.create(
            merchant=self.merchant,
            consumer=self.consumer,
            order_number='ORD-1',
            authorization_code='RET-1',
            refund_amount=50.00,
            status=Return.STATUS_INITIATED
        )
        Return.objects.create(
            merchant=self.merchant,
            consumer=self.consumer,
            order_number='ORD-2',
            authorization_code='RET-2',
            refund_amount=75.00,
            status=Return.STATUS_COMPLETED
        )

        response = self.client.get('/api/returns/?status=INITIATED')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_approve_return(self):
        """Test approve action"""
        return_obj = Return.objects.create(
            merchant=self.merchant,
            consumer=self.consumer,
            order_number='ORD-1',
            authorization_code='RET-1',
            refund_amount=50.00,
            status=Return.STATUS_INITIATED
        )

        response = self.client.post(f'/api/returns/{return_obj.id}/approve/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return_obj.refresh_from_db() #QUESTION: What does .refresh_from_db() do? Don't we want to keep the database as it is so that we can test if the status=STATUS_AUTHORIZED?
        self.assertEqual(return_obj.status, Return.STATUS_AUTHORIZED) #QUESTION: Do we expect this to succeed because we already ran this line response = self.client.post(f'/api/returns/{return_obj.id}/approve/')?

    def test_cancel_return(self):
        """Test cancel action"""
        return_obj = Return.objects.create(
            merchant=self.merchant,
            consumer=self.consumer,
            order_number='ORD-1',
            authorization_code='RET-1',
            refund_amount=50.00,
            status=Return.STATUS_INITIATED
        )

        response = self.client.post(f'/api/returns/{return_obj.id}/cancel/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return_obj.refresh_from_db()
        self.assertEqual(return_obj.status, Return.STATUS_CANCELLED) #QUESTION: So if a return gets cancelled, it doesn't get deleted? It just sits in the database with a status of STATUS_CANCELLED?