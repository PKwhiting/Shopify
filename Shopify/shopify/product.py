"""
Product Class

Simplified interface for dealing with individual Shopify products.
Provides classmethods for factory operations and instance methods for product operations.
"""

from typing import Dict, Any, Optional, List, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from .client import ShopifyClient


class Product:
    """
    Simplified Product class representing an individual Shopify product.

    Provides classmethods for operations like search, get, create and
    instance methods for operations like publish, save, delete.
    """

    # Web publication ID for publish/unpublish operations (deprecated - use dynamic lookup)
    WEB_PUBLICATION_ID = "gid://shopify/Publication/1"

    # Cache for store publications to avoid repeated queries
    _publications_cache = {}

    def __init__(self, client: "ShopifyClient", data: Dict[str, Any]):
        """
        Initialize a Product instance.

        Args:
            client: ShopifyClient instance
            data: Product data from GraphQL response
        """
        self.client = client
        # Map descriptionHtml to description for SDK consistency
        mapped_data = data.copy()
        if "descriptionHtml" in mapped_data:
            mapped_data["description"] = mapped_data["descriptionHtml"]
        self._data = mapped_data
        self._original_data = mapped_data.copy()
        self._dirty = False

    def _get_store_publications(self) -> List[Dict[str, Any]]:
        """
        Get all available publications for the store.

        Returns:
            List of publication dictionaries with id and name

        Raises:
            ValueError: If query fails
        """
        # Use shop URL as cache key to handle multiple stores
        cache_key = getattr(self.client, "shop_url", "default")

        # Return cached result if available
        if cache_key in self._publications_cache:
            return self._publications_cache[cache_key]

        try:
            query = """
            query getPublications($first: Int!) {
                publications(first: $first) {
                    edges {
                        node {
                            id
                            name
                            supportsFuturePublishing
                        }
                    }
                    pageInfo {
                        hasNextPage
                    }
                }
            }
            """

            variables = {"first": 50}  # Should be enough for most stores
            result = self.client.execute_query(query, variables)

            publications = []
            if result and "publications" in result:
                for edge in result["publications"]["edges"]:
                    publications.append(edge["node"])

            # Cache the result
            self._publications_cache[cache_key] = publications
            return publications
        except Exception:
            # If publications query fails, return empty list
            # This allows fallback to static ID
            self._publications_cache[cache_key] = []
            return []

    def _get_default_publication(self) -> Optional[Dict[str, Any]]:
        """
        Get the default web publication for the store.

        Returns:
            Publication dictionary or None if not found
        """
        publications = self._get_store_publications()

        # Look for web-related publication first
        for pub in publications:
            name = pub.get("name", "").lower()
            if "web" in name or "online" in name:
                return pub

        # If no web publication found, return the first one
        if publications:
            return publications[0]

        return None

    @property
    def id(self) -> Optional[str]:
        """Get product ID."""
        return self._data.get("id")

    @property
    def title(self) -> Optional[str]:
        """Get product title."""
        return self._data.get("title")

    @title.setter
    def title(self, value: str):
        """Set product title."""
        self._data["title"] = value
        self._dirty = True

    @property
    def handle(self) -> Optional[str]:
        """Get product handle."""
        return self._data.get("handle")

    @handle.setter
    def handle(self, value: str):
        """Set product handle."""
        self._data["handle"] = value
        self._dirty = True

    @property
    def status(self) -> Optional[str]:
        """Get product status."""
        return self._data.get("status")

    @property
    def description(self) -> Optional[str]:
        """Get product description."""
        return self._data.get("description")

    @description.setter
    def description(self, value: str):
        """Set product description."""
        self._data["description"] = value
        self._dirty = True

    @property
    def product_type(self) -> Optional[str]:
        """Get product type."""
        return self._data.get("productType")

    @product_type.setter
    def product_type(self, value: str):
        """Set product type."""
        self._data["productType"] = value
        self._dirty = True

    @property
    def vendor(self) -> Optional[str]:
        """Get product vendor."""
        return self._data.get("vendor")

    @vendor.setter
    def vendor(self, value: str):
        """Set product vendor."""
        self._data["vendor"] = value
        self._dirty = True

    @property
    def tags(self) -> Optional[List[str]]:
        """Get product tags."""
        return self._data.get("tags", [])

    @tags.setter
    def tags(self, value: List[str]):
        """Set product tags."""
        self._data["tags"] = value
        self._dirty = True

    @property
    def created_at(self) -> Optional[str]:
        """Get product creation timestamp."""
        return self._data.get("createdAt")

    @property
    def updated_at(self) -> Optional[str]:
        """Get product update timestamp."""
        return self._data.get("updatedAt")

    @property
    def is_published(self) -> bool:
        """Check if product is published."""
        return self.status == "ACTIVE"

    @property
    def variants(self) -> List[Dict[str, Any]]:
        """Get product variants."""
        variants_data = self._data.get("variants", {})
        if isinstance(variants_data, dict) and "edges" in variants_data:
            return [edge["node"] for edge in variants_data["edges"]]
        return variants_data if isinstance(variants_data, list) else []

    @property
    def images(self) -> List[Dict[str, Any]]:
        """Get product images."""
        images_data = self._data.get("images", {})
        if isinstance(images_data, dict) and "edges" in images_data:
            return [edge["node"] for edge in images_data["edges"]]
        return images_data if isinstance(images_data, list) else []

    # Class methods for factory operations
    @classmethod
    def search(
        cls,
        query: str = "",
        first: int = 10,
        after: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        client: Optional["ShopifyClient"] = None,
    ) -> List["Product"]:
        """
        Search for products.

        Args:
            query: Search query string
            first: Number of products to fetch (max 250)
            after: Cursor for pagination
            filters: Additional filters (product_type, vendor, etc.)
            client: ShopifyClient instance. If None, will be created from environment variables.

        Returns:
            List of Product instances

        Raises:
            ValueError: If parameters are invalid or environment variables are not properly set
        """
        if client is None:
            from .client import create_client_from_environment
            client = create_client_from_environment()
            
        if not isinstance(first, int) or first < 1:
            raise ValueError("'first' parameter must be a positive integer")
        if first > 250:
            raise ValueError("'first' parameter cannot exceed 250")

        # Build the query string with filters
        query_parts = []
        if query:
            query_parts.append(query)

        if filters:
            for key, value in filters.items():
                if key == "product_type" and value:
                    query_parts.append(f"product_type:{value}")
                elif key == "vendor" and value:
                    query_parts.append(f"vendor:{value}")
                elif key == "status" and value:
                    query_parts.append(f"status:{value}")
                elif key == "tag" and value:
                    query_parts.append(f"tag:{value}")

        search_query = " AND ".join(query_parts) if query_parts else ""

        graphql_query = """
        query searchProducts($query: String, $first: Int!, $after: String) {
            products(query: $query, first: $first, after: $after) {
                pageInfo {
                    hasNextPage
                    endCursor
                }
                edges {
                    node {
                        id
                        title
                        handle
                        status
                        createdAt
                        updatedAt
                        productType
                        vendor
                        tags
                        description
                        variants(first: 10) {
                            edges {
                                node {
                                    id
                                    title
                                    sku
                                    price
                                    inventoryQuantity
                                }
                            }
                        }
                        images(first: 5) {
                            edges {
                                node {
                                    id
                                    src
                                    altText
                                }
                            }
                        }
                    }
                }
            }
        }
        """

        variables = {"first": first}
        if search_query:
            variables["query"] = search_query
        if after:
            variables["after"] = after

        result = client.execute_query(graphql_query, variables)

        # Shopify returns mutation/query result directly (no top-level 'data' key)
        products_data = result.get("products") if result else None
        products = []
        if products_data and "edges" in products_data:
            for edge in products_data["edges"]:
                products.append(cls(client, edge["node"]))
        return products

    @classmethod
    def get(cls, client_or_product_id: Union["ShopifyClient", str], product_id: Optional[str] = None) -> Optional["Product"]:
        """
        Get a product by ID.

        Args:
            client_or_product_id: ShopifyClient instance OR product ID (when using environment variables)
            product_id: Product ID (when client is provided as first arg)

        Returns:
            Product instance or None if not found

        Raises:
            ValueError: If product_id is invalid or environment variables are not properly set
        """
        # Handle both call patterns:
        # 1. Product.get(client, product_id) - traditional
        # 2. Product.get(product_id) - new environment variable style
        
        if isinstance(client_or_product_id, str) and product_id is None:
            # New style: Product.get(product_id)
            product_id = client_or_product_id
            from .client import create_client_from_environment
            client = create_client_from_environment()
        else:
            # Traditional style: Product.get(client, product_id)
            client = client_or_product_id
            if not product_id:
                raise ValueError("Product ID must be provided")
                
        if not product_id or not isinstance(product_id, str):
            raise ValueError("Product ID must be a non-empty string")

        query = """
        query getProduct($id: ID!) {
            product(id: $id) {
                id
                title
                handle
                status
                createdAt
                updatedAt
                productType
                vendor
                tags
                description
                variants(first: 250) {
                    edges {
                        node {
                            id
                            title
                            sku
                            price
                            inventoryQuantity
                        }
                    }
                }
                images(first: 10) {
                    edges {
                        node {
                            id
                            src
                            altText
                            width
                            height
                        }
                    }
                }
            }
        }
        """

        variables = {"id": product_id}

        result = client.execute_query(query, variables)

        # Shopify returns mutation/query result directly (no top-level 'data' key)
        product_data = result.get("product") if result else None
        if product_data:
            return cls(client, product_data)
        return None

    @classmethod
    def get_by_handle(cls, client_or_handle: Union["ShopifyClient", str], handle: Optional[str] = None) -> Optional["Product"]:
        """
        Get a product by handle.

        Args:
            client_or_handle: ShopifyClient instance OR product handle (when using environment variables)
            handle: Product handle (when client is provided as first arg)

        Returns:
            Product instance or None if not found

        Raises:
            ValueError: If handle is invalid or environment variables are not properly set
        """
        # Handle both call patterns:
        # 1. Product.get_by_handle(client, handle) - traditional
        # 2. Product.get_by_handle(handle) - new environment variable style
        
        if isinstance(client_or_handle, str) and handle is None:
            # New style: Product.get_by_handle(handle)
            handle = client_or_handle
            from .client import create_client_from_environment
            client = create_client_from_environment()
        else:
            # Traditional style: Product.get_by_handle(client, handle)
            client = client_or_handle
            if not handle:
                raise ValueError("Product handle must be provided")
                
        if not handle or not isinstance(handle, str):
            raise ValueError("Product handle must be a non-empty string")

        query = """
        query getProductByHandle($handle: String!) {
            productByHandle(handle: $handle) {
                id
                title
                handle
                status
                createdAt
                updatedAt
                productType
                vendor
                tags
                description
                variants(first: 250) {
                    edges {
                        node {
                            id
                            title
                            sku
                            price
                            inventoryQuantity
                        }
                    }
                }
                images(first: 10) {
                    edges {
                        node {
                            id
                            src
                            altText
                            width
                            height
                        }
                    }
                }
            }
        }
        """

        variables = {"handle": handle}
        result = client.execute_query(query, variables)

        # Shopify returns mutation/query result directly (no top-level 'data' key)
        product_data = result.get("productByHandle") if result else None
        if product_data:
            return cls(client, product_data)
        return None

    @classmethod
    def create(cls, client_or_product_data: Union["ShopifyClient", Dict[str, Any]], product_data: Optional[Dict[str, Any]] = None) -> "Product":
        """
        Create a new product.

        Args:
            client_or_product_data: ShopifyClient instance OR product data (when using environment variables)
            product_data: Product data for creation (when client is provided as first arg)

        Returns:
            Created Product instance

        Raises:
            ValueError: If product_data is invalid, operation fails, or environment variables are not properly set
        """
        # Handle both call patterns:
        # 1. Product.create(client, product_data) - traditional
        # 2. Product.create(product_data) - new environment variable style
        
        if isinstance(client_or_product_data, dict) and product_data is None:
            # New style: Product.create(product_data)
            product_data = client_or_product_data
            from .client import create_client_from_environment
            client = create_client_from_environment()
        else:
            # Traditional style: Product.create(client, product_data)
            client = client_or_product_data
            if not product_data:
                raise ValueError("Product data must be provided")
                
        if not isinstance(product_data, dict):
            raise ValueError("Product data must be a dictionary")
        if not product_data:
            raise ValueError("Product data cannot be empty")

        mutation = """
        mutation productCreate($input: ProductInput!) {
            productCreate(input: $input) {
                product {
                    id
                    title
                    handle
                    status
                    createdAt
                    updatedAt
                    productType
                    vendor
                    tags
                    descriptionHtml
                }
                userErrors {
                    field
                    message
                }
            }
        }
        """

        variables = {"input": product_data}
        result = client.execute_mutation(mutation, variables)

        # Shopify returns mutation/query result directly (no top-level 'data' key)
        product_create = result.get("productCreate") if result else None
        if product_create:
            if product_create.get("userErrors"):
                error_messages = []
                for error in product_create["userErrors"]:
                    field = error.get("field", ["unknown"])
                    message = error.get("message", "Unknown error")
                    if isinstance(field, list):
                        field_str = ".".join(field)
                    else:
                        field_str = str(field)
                    error_messages.append(f"{field_str}: {message}")
                print("[DEBUG] Product.create userErrors:", product_create["userErrors"])
                raise ValueError(f"Product creation failed: {'; '.join(error_messages)}")

            if product_create.get("product"):
                return cls(client, product_create["product"])

        print("[DEBUG] Product.create mutation response:", result)
        raise ValueError("Product creation failed: No product data returned")

    # Instance methods for product operations
    def save(self) -> "Product":
        """
        Save changes to the product.

        Returns:
            Updated Product instance

        Raises:
            ValueError: If product has no ID or operation fails
        """
        if not self.id:
            raise ValueError("Cannot save product without ID")

        if not self._dirty:
            return self  # No changes to save

        # Extract only the changed fields
        update_data = {"id": self.id}

        # Add changed fields
        for key in ["title", "handle", "description", "productType", "vendor", "tags"]:
            if key in self._data and self._data.get(key) != self._original_data.get(key):
                # Map 'description' to 'descriptionHtml' for Shopify API
                if key == "description":
                    update_data["descriptionHtml"] = self._data["description"]
                else:
                    update_data[key] = self._data[key]

        mutation = """
        mutation productUpdate($input: ProductInput!) {
            productUpdate(input: $input) {
                product {
                    id
                    title
                    handle
                    status
                    updatedAt
                    productType
                    vendor
                    tags
                    descriptionHtml
                }
                userErrors {
                    field
                    message
                }
            }
        }
        """

        variables = {"input": update_data}
        result = self.client.execute_mutation(mutation, variables)

        # Handle user errors (expect top-level 'productUpdate' in response)
        product_update = result.get("productUpdate") if result else None
        if product_update:
            if product_update.get("userErrors"):
                error_messages = []
                for error in product_update["userErrors"]:
                    field = error.get("field", ["unknown"])
                    message = error.get("message", "Unknown error")
                    if isinstance(field, list):
                        field_str = ".".join(field)
                    else:
                        field_str = str(field)
                    error_messages.append(f"{field_str}: {message}")
                raise ValueError(f"Product update failed: {'; '.join(error_messages)}")

            if product_update.get("product"):
                # Update our data with the response
                self._data.update(product_update["product"])
                self._original_data = self._data.copy()
                self._dirty = False
                return self

        raise ValueError("Product update failed: No product data returned")

    def delete(self) -> bool:
        """
        Delete the product.

        Returns:
            True if deletion was successful

        Raises:
            ValueError: If product has no ID or operation fails
        """
        if not self.id:
            raise ValueError("Cannot delete product without ID")

        mutation = """
        mutation productDelete($input: ProductDeleteInput!) {
            productDelete(input: $input) {
                deletedProductId
                userErrors {
                    field
                    message
                }
            }
        }
        """

        variables = {"input": {"id": self.id}}
        result = self.client.execute_mutation(mutation, variables)

        # Shopify returns mutation/query result directly (no top-level 'data' key)
        product_delete = result.get("productDelete") if result else None
        if product_delete:
            if product_delete.get("userErrors"):
                error_messages = []
                for error in product_delete["userErrors"]:
                    field = error.get("field", ["unknown"])
                    message = error.get("message", "Unknown error")
                    if isinstance(field, list):
                        field_str = ".".join(field)
                    else:
                        field_str = str(field)
                    error_messages.append(f"{field_str}: {message}")
                raise ValueError(f"Product deletion failed: {'; '.join(error_messages)}")

            return bool(product_delete.get("deletedProductId"))

        raise ValueError("Product deletion failed")

    def publish(self, publications: Optional[List[Dict[str, Any]]] = None) -> "Product":
        """
        Publish the product.

        Args:
            publications: List of publication targets (optional)

        Returns:
            Updated Product instance

        Raises:
            ValueError: If product has no ID or operation fails
        """
        if not self.id:
            raise ValueError("Cannot publish product without ID")

        # Default to publishing to web if no publications specified
        if publications is None:
            default_pub = self._get_default_publication()
            if default_pub:
                publications = [{"publicationId": default_pub["id"]}]
            else:
                # Fallback to the old static ID for backward compatibility
                publications = [{"publicationId": self.WEB_PUBLICATION_ID}]

        mutation = """
        mutation publishablePublish($id: ID!, $input: [PublicationInput!]!) {
            publishablePublish(id: $id, input: $input) {
                publishable {
                    ... on Product {
                        id
                        status
                        publishedAt
                    }
                }
                userErrors {
                    field
                    message
                }
            }
        }
        """

        variables = {"id": self.id, "input": publications}
        result = self.client.execute_mutation(mutation, variables)

        # Handle user errors (support both with and without 'data' wrapper)
        publish_result = None
        if result:
            if "data" in result and isinstance(result["data"], dict):
                publish_result = result["data"].get("publishablePublish")
            else:
                publish_result = result.get("publishablePublish")

        if publish_result:
            if publish_result.get("userErrors"):
                error_messages = []
                for error in publish_result["userErrors"]:
                    field = error.get("field", ["unknown"])
                    message = error.get("message", "Unknown error")
                    if isinstance(field, list):
                        field_str = ".".join(field)
                    else:
                        field_str = str(field)
                    error_messages.append(f"{field_str}: {message}")
                raise ValueError(f"Product publish failed: {'; '.join(error_messages)}")

            if publish_result.get("publishable"):
                self._data["status"] = "ACTIVE"
                return self

        raise ValueError("Product publish failed")

    def unpublish(self, publications: Optional[List[Dict[str, Any]]] = None) -> "Product":
        """
        Unpublish the product.

        Args:
            publications: List of publication targets (optional)

        Returns:
            Updated Product instance

        Raises:
            ValueError: If product has no ID or operation fails
        """
        if not self.id:
            raise ValueError("Cannot unpublish product without ID")

        # Default to unpublishing from web if no publications specified
        if publications is None:
            default_pub = self._get_default_publication()
            if default_pub:
                publications = [{"publicationId": default_pub["id"]}]
            else:
                # Fallback to the old static ID for backward compatibility
                publications = [{"publicationId": self.WEB_PUBLICATION_ID}]

        mutation = """
        mutation publishableUnpublish($id: ID!, $input: [PublicationInput!]!) {
            publishableUnpublish(id: $id, input: $input) {
                publishable {
                    ... on Product {
                        id
                        status
                    }
                }
                userErrors {
                    field
                    message
                }
            }
        }
        """

        variables = {"id": self.id, "input": publications}
        result = self.client.execute_mutation(mutation, variables)

        # Handle user errors (support both with and without 'data' wrapper)
        unpublish_result = None
        if result:
            if "data" in result and isinstance(result["data"], dict):
                unpublish_result = result["data"].get("publishableUnpublish")
            else:
                unpublish_result = result.get("publishableUnpublish")

        if unpublish_result:
            if unpublish_result.get("userErrors"):
                error_messages = []
                for error in unpublish_result["userErrors"]:
                    field = error.get("field", ["unknown"])
                    message = error.get("message", "Unknown error")
                    if isinstance(field, list):
                        field_str = ".".join(field)
                    else:
                        field_str = str(field)
                    error_messages.append(f"{field_str}: {message}")
                raise ValueError(f"Product unpublish failed: {'; '.join(error_messages)}")

            if unpublish_result.get("publishable"):
                self._data["status"] = "DRAFT"
                return self

        raise ValueError("Product unpublish failed")

    def duplicate(self, new_title: Optional[str] = None) -> "Product":
        """
        Duplicate the product.

        Args:
            new_title: Title for the duplicated product (optional)

        Returns:
            New Product instance representing the duplicate

        Raises:
            ValueError: If product has no ID or operation fails
        """
        if not self.id:
            raise ValueError("Cannot duplicate product without ID")

        mutation = """
        mutation productDuplicate(
            $productId: ID!,
            $newTitle: String,
            $newStatus: ProductStatus,
            $includeImages: Boolean
        ) {
            productDuplicate(
                productId: $productId,
                newTitle: $newTitle,
                newStatus: $newStatus,
                includeImages: $includeImages
            ) {
                newProduct {
                    id
                    title
                    handle
                    status
                    createdAt
                    updatedAt
                    productType
                    vendor
                    tags
                    description
                }
                userErrors {
                    field
                    message
                }
            }
        }
        """

        variables = {"productId": self.id, "newStatus": "DRAFT", "includeImages": True}

        if new_title:
            variables["newTitle"] = new_title

        result = self.client.execute_mutation(mutation, variables)

        # Handle user errors
        if result and "data" in result and "productDuplicate" in result["data"]:
            duplicate_result = result["data"]["productDuplicate"]
            if duplicate_result.get("userErrors"):
                error_messages = []
                for error in duplicate_result["userErrors"]:
                    field = error.get("field", ["unknown"])
                    message = error.get("message", "Unknown error")
                    if isinstance(field, list):
                        field_str = ".".join(field)
                    else:
                        field_str = str(field)
                    error_messages.append(f"{field_str}: {message}")
                raise ValueError(f"Product duplication failed: {'; '.join(error_messages)}")

            if duplicate_result.get("newProduct"):
                return Product(self.client, duplicate_result["newProduct"])

        raise ValueError("Product duplication failed")

    def __str__(self) -> str:
        """String representation of the product."""
        return f"Product(id={self.id}, title='{self.title}', status={self.status})"

    def __repr__(self) -> str:
        """Developer representation of the product."""
        return (
            f"Product(id='{self.id}', title='{self.title}', "
            f"handle='{self.handle}', status='{self.status}')"
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert product to dictionary."""
        return self._data.copy()
