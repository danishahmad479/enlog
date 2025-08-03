from django.core.cache import cache
from django.conf import settings
import json
from typing import List, Dict, Any, Optional

class CacheManager:
    """Cache manager for products and categories"""
    
    # Cache keys
    PRODUCTS_CACHE_KEY = 'products_list'
    PRODUCT_DETAIL_CACHE_KEY = 'product_detail_{}'
    CATEGORIES_CACHE_KEY = 'categories_list'
    CATEGORY_DETAIL_CACHE_KEY = 'category_detail_{}'
    PRODUCTS_BY_CATEGORY_CACHE_KEY = 'products_by_category_{}'
    
    # Cache timeout (1 hour)
    CACHE_TIMEOUT = 3600
    
    @classmethod
    def get_products_cache_key(cls, filters: Dict[str, Any] = None) -> str:
        """Generate cache key for products with filters"""
        if not filters:
            return cls.PRODUCTS_CACHE_KEY
        
        # Create a sorted string of filters for consistent cache keys
        filter_str = '_'.join([f"{k}_{v}" for k, v in sorted(filters.items()) if v])
        return f"{cls.PRODUCTS_CACHE_KEY}_{filter_str}"
    
    @classmethod
    def get_products(cls, filters: Dict[str, Any] = None) -> Optional[List[Dict]]:
        """Get products from cache"""
        cache_key = cls.get_products_cache_key(filters)
        return cache.get(cache_key)
    
    @classmethod
    def set_products(cls, products: List[Dict], filters: Dict[str, Any] = None) -> None:
        """Cache products"""
        cache_key = cls.get_products_cache_key(filters)
        cache.set(cache_key, products, cls.CACHE_TIMEOUT)
        print(f"Cached products with key: {cache_key}")
    
    @classmethod
    def get_product_detail(cls, product_id: int) -> Optional[Dict]:
        """Get product detail from cache"""
        cache_key = cls.PRODUCT_DETAIL_CACHE_KEY.format(product_id)
        return cache.get(cache_key)
    
    @classmethod
    def set_product_detail(cls, product_id: int, product_data: Dict) -> None:
        """Cache product detail"""
        cache_key = cls.PRODUCT_DETAIL_CACHE_KEY.format(product_id)
        cache.set(cache_key, product_data, cls.CACHE_TIMEOUT)
        print(f"Cached product detail with key: {cache_key}")
    
    @classmethod
    def get_categories(cls) -> Optional[List[Dict]]:
        """Get categories from cache"""
        return cache.get(cls.CATEGORIES_CACHE_KEY)
    
    @classmethod
    def set_categories(cls, categories: List[Dict]) -> None:
        """Cache categories"""
        cache.set(cls.CATEGORIES_CACHE_KEY, categories, cls.CACHE_TIMEOUT)
        print(f"Cached categories with key: {cls.CATEGORIES_CACHE_KEY}")
    
    @classmethod
    def get_category_detail(cls, category_id: int) -> Optional[Dict]:
        """Get category detail from cache"""
        cache_key = cls.CATEGORY_DETAIL_CACHE_KEY.format(category_id)
        return cache.get(cache_key)
    
    @classmethod
    def set_category_detail(cls, category_id: int, category_data: Dict) -> None:
        """Cache category detail"""
        cache_key = cls.CATEGORY_DETAIL_CACHE_KEY.format(category_id)
        cache.set(cache_key, category_data, cls.CACHE_TIMEOUT)
        print(f"Cached category detail with key: {cache_key}")
    
    @classmethod
    def get_products_by_category(cls, category_id: int) -> Optional[List[Dict]]:
        """Get products by category from cache"""
        cache_key = cls.PRODUCTS_BY_CATEGORY_CACHE_KEY.format(category_id)
        return cache.get(cache_key)
    
    @classmethod
    def set_products_by_category(cls, category_id: int, products: List[Dict]) -> None:
        """Cache products by category"""
        cache_key = cls.PRODUCTS_BY_CATEGORY_CACHE_KEY.format(category_id)
        cache.set(cache_key, products, cls.CACHE_TIMEOUT)
        print(f"Cached products by category with key: {cache_key}")
    
    @classmethod
    def invalidate_product_cache(cls, product_id: int = None) -> None:
        """Invalidate product-related cache"""
        if product_id:
            # Invalidate specific product cache
            cache_key = cls.PRODUCT_DETAIL_CACHE_KEY.format(product_id)
            cache.delete(cache_key)
            print(f"Invalidated product detail cache: {cache_key}")
        
        # Invalidate all products list cache (with and without filters)
        cache.delete(cls.PRODUCTS_CACHE_KEY)
        
        # Invalidate products by category cache
        from .models import Product
        if product_id:
            try:
                product = Product.objects.get(id=product_id)
                category_cache_key = cls.PRODUCTS_BY_CATEGORY_CACHE_KEY.format(product.category.id)
                cache.delete(category_cache_key)
                print(f"Invalidated products by category cache: {category_cache_key}")
            except Product.DoesNotExist:
                pass
        
        # Clear common filter patterns manually
        common_filters = [
            {'category': '1'}, {'category': '2'}, {'category': '3'},
            {'min_price': '100'}, {'max_price': '500'},
            {'category': '1', 'min_price': '100'}, {'category': '1', 'max_price': '500'},
            {'min_price': '100', 'max_price': '500'}
        ]
        
        for filters in common_filters:
            cache_key = cls.get_products_cache_key(filters)
            cache.delete(cache_key)
        
        print("Invalidated all product-related cache")
    
    @classmethod
    def invalidate_category_cache(cls, category_id: int = None) -> None:
        """Invalidate category-related cache"""
        if category_id:
            # Invalidate specific category cache
            cache_key = cls.CATEGORY_DETAIL_CACHE_KEY.format(category_id)
            cache.delete(cache_key)
            print(f"Invalidated category detail cache: {cache_key}")
            
            # Invalidate products by this category
            category_products_key = cls.PRODUCTS_BY_CATEGORY_CACHE_KEY.format(category_id)
            cache.delete(category_products_key)
            print(f"Invalidated products by category cache: {category_products_key}")
        
        # Invalidate all categories list cache
        cache.delete(cls.CATEGORIES_CACHE_KEY)
        
        # Invalidate all product cache since category changes affect products
        cls.invalidate_product_cache()
        
        print("Invalidated all category-related cache")
    
    @classmethod
    def clear_all_cache(cls) -> None:
        """Clear all cache"""
        cache.clear()
        print("Cleared all cache")
    
    @classmethod
    def get_cache_stats(cls) -> Dict[str, Any]:
        """Get cache statistics"""
        # This is a simple implementation - in production you might want more detailed stats
        return {
            'cache_backend': settings.CACHES['default']['BACKEND'],
            'cache_timeout': cls.CACHE_TIMEOUT,
            'cache_prefix': settings.CACHES['default']['KEY_PREFIX']
        } 