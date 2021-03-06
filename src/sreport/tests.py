# Copyright  2012 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public
# License as published by the Free Software Foundation; either version
# 2 of the License (GPLv2) or (at your option) any later version.
# There is NO WARRANTY for this software, express or implied,
# including the implied warranties of MERCHANTABILITY,
# NON-INFRINGEMENT, or FITNESS FOR A PARTICULAR PURPOSE. You should
# have received a copy of GPLv2 along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.


"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from mongoengine.connection import connect, disconnect
from django.conf import settings
from logging import getLogger
from sreport.models import ReportData, MyQuerySet
from rhic_serve.rhic_rest.models import RHIC, Account
from mongoengine.queryset import QuerySet
from mongoengine import Document, StringField, ListField, DateTimeField, IntField
from datetime import datetime, timedelta
from common.products import Product_Def
from common.utils import datespan


LOG = getLogger(__name__)
hr_fmt = "%m%d%Y:%H"

'''
Currently the unit tests required that the rhic_serve database has been populated w/ the sample-load.py script
This can be found @rhic_serve/playpen/sample-load.py
Example: python sample-load.py Splice-RHIC-Sample-Data.csv Splice-Product-Definitions.csv

Although the product usage data from the is not used from the splice-server's generate_usage_data.py script, the generated RHIC's are used.
It is also a current requirement to load RHIC's.
This script can be found @splice-server/playpen/generate_usage_data.py
Example: PYTHONPATH=~/workspace/rhic_serve/ DJANGO_SETTINGS_MODULE='dev.settings' ./generate_usage_data.py -n 1

Example of running these unit tests from $checkout/src
#python manage.py test sreport --settings=dev.settings -v 3

'''

class ReportData(ReportData):
    db_name = settings.MONGO_DATABASE_NAME_RESULTS
    meta = {'queryset_class': MyQuerySet}

class Product(Document):

    support_level_choices = {
        'l1-l3': 'L1-L3',
        'l3': 'L3-only',
        'ss': 'SS',
    }

    sla_choices = {
        'std': 'Standard',
        'prem': 'Premium',
        'na': 'N/A',
    }

    # Product name
    name = StringField(required=True)
    # Unique product identifier
    engineering_ids = ListField(required=True)
    # Quantity 
    quantity = IntField(required=True)
    # Product support level
    support_level = StringField(required=True, choices=support_level_choices.keys())
    # Product sla
    sla = StringField(required=True, choices=sla_choices.keys())
    


class SimpleTest(TestCase):
    def test_basic_addition(self):
        """
        Tests that 1 + 1 always equals 2.
        """
        self.assertEqual(1 + 1, 2)
    def test_basic_addition_false(self):
        self.assertNotEquals(1 + 1, 3)

class MongoTestCase(TestCase):
    """
    TestCase class that clear the collection between the tests
    """
    db_name = settings.MONGO_DATABASE_NAME_RESULTS
    def __init__(self, methodName='runtest'):
        super(MongoTestCase, self).__init__(methodName)
        disconnect()
        self.db = connect(self.db_name)
        self.drop_database_and_reconnect()
    
    def _post_teardown(self):
        super(MongoTestCase, self)._post_teardown()
        self.drop_database_and_reconnect(reconnect=False)

    def drop_database_and_reconnect(self, reconnect=True):
        disconnect()
        self.db.drop_database(self.db_name)
        # Mongoengine sometimes doesn't recreate unique indexes
        # in between test runs, adding the below 'reset' to fix this
        # https://github.com/hmarr/mongoengine/issues/422
        QuerySet._reset_already_indexed()
        if reconnect:
            self.db = connect(self.db_name)
    
class MongoTestsTestCase(MongoTestCase):

    def test_mongo_cleanup_is_working(self):
        class MongoTestEntry(Document):
            uuid = StringField(required=True, unique=True)
        m = MongoTestEntry(uuid="new_entry")
        m.save()
        lookup = MongoTestEntry.objects()
        self.assertEqual(len(lookup), 1)
        self.drop_database_and_reconnect()
        lookup = MongoTestEntry.objects()
        self.assertEqual(len(lookup), 0)
        

            
RHEL = "RHEL Server"
HA = "RHEL HA"
EUS = "RHEL EUS"
LB = "RHEL LB"
JBoss = "JBoss EAP"
EDU = "RHEL Server for Education"
UNLIMITED = "RHEL Server 2-socket Unlimited Guest"
GEAR = "OpenShift Gear"

products_dict={
                 RHEL: (["69"], '8d401b5e-2fa5-4cb6-be64-5f57386fda86', "rhel-server-1190457-3116649-prem-l1-l3"), 
                 HA: (["83"], 'fbbd06c6-ebed-4892-87a3-2bf17c864444', 'rhel-ha-1190457-3874444-na-standard'),
                 EUS: (["70"],'fbbd06c6-ebed-4892-87a3-2bf17c865555', 'rhel-eus-1190457-3874444-prem-l1-l3'),
                 LB: (["85"], 'fbbd06c6-ebed-4892-87a3-2bf17c866666', 'rhel-lb-1190457-3874444-prem-l1-l3'),
                 JBoss: (["183"],'ee5c9aaa-a40c-1111-80a6-ef731076bbe8', 'jboss-1111730-4582732-prem-l1-l3'),
                 EDU: (["69"], 'fbbd06c6-ebed-4892-87a3-2bf17c86e610', 'rhel-server-education-1190457-3879847-na-ss'),
                 UNLIMITED: (["69"], 'fbbd06c6-ebed-4892-87a3-2bf17c867777', 'rhel-2socket_unlimited-1190457-3874444-prem-l1-l3'),
                 GEAR: (["69", "183"], 'b0e7bd8a-0b23-4b35-86d7-52a87311a5c2', 'openshift-gear-3485301-4582732-prem-l1-l3')
                }
 
class TestData():
    
    @staticmethod
    def create_entry(product, memhigh=True, date=None):
        if not date:
            date = datetime.now()
        this_hour = date.strftime(hr_fmt)
            
        row = ReportData(
                                instance_identifier = "12:31:3D:08:49:00",
                                date =  date,

                                
                                hour = this_hour,
                                memtotal = 16048360,
                                cpu_sockets = 4,
                                environment = "us-east-1",
                                splice_server = "splice-server-1.spliceproject.org"
                                )
        
        for key, value in products_dict.items():
            if product == key:
                rhic = RHIC.objects.filter(uuid=value[1])[0]
                row['product_name']=key
                row['product']=value[0]
                row['consumer_uuid']=value[1]
                row['consumer']=value[2]
                row['contract_id']=rhic.contract
                row['sla']=rhic.sla
                row['support']=rhic.support_level
                row['contract_use']="20"
                
        
        if memhigh:
            row['memtotal'] = 16048360
            return row
        else:
            row['memtotal'] = 640
            return row
       
        
    
    @staticmethod    
    def create_products():
        
        for key, value in products_dict.items():
            #print('create_product', key)
            rhic = RHIC.objects.filter(uuid=value[1])[0]
            contract_num = rhic.contract
            #print('contract_num', contract_num)
            #print('account_id', rhic.account_id)
            contract_list = Account.objects.filter(account_id=rhic.account_id)[0].contracts
            for contract in contract_list:
                if contract.contract_id == contract_num:
                    list_of_products = contract.products
                    for p in list_of_products:
                        #print p.name
                        if p.name == key:
                            row = Product(
                                          quantity = p.quantity,
                                          support_level = p.support_level,
                                          sla = p.sla,
                                          name=p.name,
                                          engineering_ids=p.engineering_ids
                                          )
                            row.save()
            
    @staticmethod
    def create_rhic():
        rhic = {
                    'uuid': '1001',
                    'name': 'test_rhic',
                    'account_id': '1001',
                    'contract': '1',
                    'support_level': 'l1-l3',
                    'sla': 'prem',
                    'products': [RHEL, HA, EDU, EUS, LB, JBoss, GEAR ],
                    'engineering_ids': ["69", "83", "70", "85", "183"]
                    }
                    
        RHIC.objects.get_or_create(rhic)
        
    
class ReportTestCase(TestCase):
    def setUp(self):
        db_name = settings.MONGO_DATABASE_NAME_RESULTS
        self.db = connect(db_name)
        ReportData.drop_collection()
        rhel_product = TestData.create_products()
        rhel_entry = TestData.create_entry(RHEL, memhigh=True)
        rhel_entry.save()

        
         
    def test_report_data(self):
        self.setUp()
        lookup = ReportData.objects.all()
        self.assertEqual(len(lookup), 1)
     
    def test_rhel_basic_results(self):
        
        delta=timedelta(days=1)
        start = datetime.now() - delta
        end = datetime.now() + delta
        contract_num = "3116649"
        environment = "us-east-1"
        
        lookup = ReportData.objects.all()
        self.assertEqual(len(lookup), 1)
        #test perfect match
        p = Product.objects.filter(name="RHEL Server")[0]
        rhic = RHIC.objects.filter(uuid="8d401b5e-2fa5-4cb6-be64-5f57386fda86")[0]
        results_dicts = Product_Def.get_product_match(p, rhic, start, end, contract_num, environment)
        self.assertEqual(len(results_dicts), 1)
        
        #test result not found if name does not match
        test_object = Product.objects.filter(name="RHEL Server")[0]
        test_object.name = "fail"
        results_dicts = Product_Def.get_product_match(test_object, rhic, start, end, contract_num, environment)
        self.assertFalse(results_dicts, 'no results returned')
        
        # test result not found where rhic uuid does not match
        test_object =  RHIC.objects.filter(uuid="8d401b5e-2fa5-4cb6-be64-5f57386fda86")[0]
        test_object.uuid = "1234"
        results_dicts = Product_Def.get_product_match(p, test_object, start, end, contract_num, environment)
        self.assertFalse(results_dicts, 'no results returned')
        
        # test no results are found if usage date is not in range
        test_object = datetime.now()
        results_dicts = Product_Def.get_product_match(p, rhic, test_object, end, contract_num, environment)
        self.assertFalse(results_dicts, 'no results returned')
        
        test_object = start
        results_dicts = Product_Def.get_product_match(p, rhic, start, test_object, contract_num, environment)
        self.assertFalse(results_dicts, 'no results returned')
        
        #test if contract number is not a match
        test_object = "1234"
        results_dicts = Product_Def.get_product_match(p, rhic, start, end, test_object, environment)
        self.assertFalse(results_dicts, 'no results returned')
        
        #test if environment is not a match
        test_object = "env_hell"
        results_dicts = Product_Def.get_product_match(p, rhic, start, end, contract_num, test_object)
        self.assertFalse(results_dicts, 'no results returned')
        
        
    def test_rhel_data_range_results(self):
        contract_num = "3116649"
        environment = "us-east-1"
        search_date_start = datetime.now() - timedelta(days=11)
        search_date_end = datetime.now()
                                                     
        delta = timedelta(days=10)
        rhel = TestData.create_entry(RHEL, memhigh=True, date=(datetime.now() - delta))
        rhel.save()
        
        lookup = ReportData.objects.all()
        self.assertEqual(len(lookup), 2)
        
        #test that there are now two objects in the database
        p = Product.objects.filter(name="RHEL Server")[0]
        rhic = RHIC.objects.filter(uuid="8d401b5e-2fa5-4cb6-be64-5f57386fda86")[0]
        results_dicts = Product_Def.get_product_match(p, rhic, search_date_start, search_date_end, contract_num, environment)
        #lenth of list should be one per product
        self.assertEqual(len(results_dicts), 1)
        #dictionary should contain the count of checkins
        self.assertEqual(results_dicts[0]['count'], 2)
        
    def test_rhel_memory_results(self):
        contract_num = "3116649"
        environment = "us-east-1"
        end = datetime.now()
        delta=timedelta(days=1)
        start = datetime.now() - delta
        
        p = Product.objects.filter(name="RHEL Server")[0]
        rhic = RHIC.objects.filter(uuid="8d401b5e-2fa5-4cb6-be64-5f57386fda86")[0]
        results_dicts = Product_Def.get_product_match(p, rhic, start, end, contract_num, environment)
        self.assertTrue('> ' in results_dicts[0]['facts'], ' > 8GB found')
        
        rhel02 = TestData.create_entry(RHEL, memhigh=False)
        rhel02.save()
        end = datetime.now()
        
        #verify two items in db
        lookup = ReportData.objects.all()
        self.assertEqual(len(lookup), 2)
        #RHEL w/ > 8GB and < 8GB memory are considered two different products
        #The result dict should have two items in the list (2 products, 1 count each)
        results_dicts = Product_Def.get_product_match(p, rhic, start, end, contract_num, environment)
        self.assertEqual(len(results_dicts), 2)
        
    
    def test_find_each_product(self):
        ReportData.drop_collection()
        count = 0
        for key, value in products_dict.items():
            count += 1
            entry = TestData.create_entry(key, memhigh=True)
            entry.save(safe=True)
            lookup = len(ReportData.objects.all())
            self.assertEqual(lookup, count)
            
            
        end = datetime.now()
        delta=timedelta(days=1)
        start = datetime.now() - delta
        
        for key, value in products_dict.items():
            print(key)
            p = Product.objects.filter(name=key)[0]
            print(p.name)

            rhic = RHIC.objects.filter(uuid=value[1])[0]
            print(rhic.uuid)
            print(rhic.contract)
            results_dicts = Product_Def.get_product_match(p, rhic, start, end, rhic.contract, "us-east-1")
            self.assertEqual(len(results_dicts), 1)
    
    
    
    
    