from django.core.management.base import BaseCommand
from home.models import Product, Category
from home.cache_utils import CacheManager
import time

class Command(BaseCommand):
    help = 'Test Redis cache functionality'

    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true', help='Clear all cache')
        parser.add_argument('--stats', action='store_true', help='Show cache stats')
        parser.add_argument('--test-products', action='store_true', help='Test product caching')
        parser.add_argument('--test-categories', action='store_true', help='Test category caching')

    def handle(self, *args, **options):
        if options['clear']:
            CacheManager.clear_all_cache()
            self.stdout.write(
                self.style.SUCCESS('All cache cleared successfully')
            )
            return

        if options['stats']:
            stats = CacheManager.get_cache_stats()
            self.stdout.write(
                self.style.SUCCESS(f'Cache Stats: {stats}')
            )
            return

        if options['test_products']:
            self.test_product_caching()
            return

        if options['test_categories']:
            self.test_category_caching()
            return

        # Default: run all tests
        self.stdout.write('Running cache tests...')
        self.test_product_caching()
        self.test_category_caching()

    def test_product_caching(self):
        """Test product caching functionality"""
        self.stdout.write('Testing product caching...')
        
        # Test 1: Cache products list
        start_time = time.time()
        products = Product.objects.all()
        self.stdout.write(f'Found {products.count()} products')
        
        # First call - should hit database
        cached_products = CacheManager.get_products()
        if cached_products:
            self.stdout.write(
                self.style.WARNING('Products already in cache (first call should be None)')
            )
        else:
            self.stdout.write('Products not in cache (expected for first call)')
        
        # Cache the products
        from home.serializers import ProductSerializer
        serializer = ProductSerializer(products, many=True)
        CacheManager.set_products(serializer.data)
        
        # Second call - should hit cache
        cached_products = CacheManager.get_products()
        if cached_products:
            self.stdout.write(
                self.style.SUCCESS(f'Products served from cache: {len(cached_products)} items')
            )
        else:
            self.stdout.write(
                self.style.ERROR('Failed to retrieve products from cache')
            )
        
        # Test 2: Cache individual product
        if products.exists():
            product = products.first()
            product_id = product.id
            
            # First call - should hit database
            cached_product = CacheManager.get_product_detail(product_id)
            if cached_product:
                self.stdout.write(
                    self.style.WARNING('Product already in cache')
                )
            else:
                self.stdout.write('Product not in cache (expected for first call)')
            
            # Cache the product
            serializer = ProductSerializer(product)
            CacheManager.set_product_detail(product_id, serializer.data)
            
            # Second call - should hit cache
            cached_product = CacheManager.get_product_detail(product_id)
            if cached_product:
                self.stdout.write(
                    self.style.SUCCESS(f'Product {product_id} served from cache: {cached_product["name"]}')
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f'Failed to retrieve product {product_id} from cache')
                )
        
        end_time = time.time()
        self.stdout.write(f'Product caching test completed in {end_time - start_time:.2f} seconds')

    def test_category_caching(self):
        """Test category caching functionality"""
        self.stdout.write('Testing category caching...')
        
        # Test 1: Cache categories list
        start_time = time.time()
        categories = Category.objects.all()
        self.stdout.write(f'Found {categories.count()} categories')
        
        # First call - should hit database
        cached_categories = CacheManager.get_categories()
        if cached_categories:
            self.stdout.write(
                self.style.WARNING('Categories already in cache (first call should be None)')
            )
        else:
            self.stdout.write('Categories not in cache (expected for first call)')
        
        # Cache the categories
        from home.serializers import CategorySerializer
        serializer = CategorySerializer(categories, many=True)
        CacheManager.set_categories(serializer.data)
        
        # Second call - should hit cache
        cached_categories = CacheManager.get_categories()
        if cached_categories:
            self.stdout.write(
                self.style.SUCCESS(f'Categories served from cache: {len(cached_categories)} items')
            )
        else:
            self.stdout.write(
                self.style.ERROR('Failed to retrieve categories from cache')
            )
        
        # Test 2: Cache individual category
        if categories.exists():
            category = categories.first()
            category_id = category.id
            
            # First call - should hit database
            cached_category = CacheManager.get_category_detail(category_id)
            if cached_category:
                self.stdout.write(
                    self.style.WARNING('Category already in cache')
                )
            else:
                self.stdout.write('Category not in cache (expected for first call)')
            
            # Cache the category
            serializer = CategorySerializer(category)
            CacheManager.set_category_detail(category_id, serializer.data)
            
            # Second call - should hit cache
            cached_category = CacheManager.get_category_detail(category_id)
            if cached_category:
                self.stdout.write(
                    self.style.SUCCESS(f'Category {category_id} served from cache: {cached_category["name"]}')
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f'Failed to retrieve category {category_id} from cache')
                )
        
        end_time = time.time()
        self.stdout.write(f'Category caching test completed in {end_time - start_time:.2f} seconds') 