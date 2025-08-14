"""
Product Class

Simplified interface for dealing with individual Shopify products.
Provides classmethods for factory operations and instance methods for product operations.
"""

from typing import Dict, Any, Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from .client import ShopifyClient


class Product:
    """
    Simplified Product class representing an individual Shopify product.

    Provides classmethods for operations like search, get, create and
    instance methods for operations like publish, save, delete.
    """

    def __init__(self, client: "ShopifyClient", data: Dict[str, Any]):
        """
        Initialize a Product instance.

        Args:
            client: ShopifyClient instance
            data: Product data from GraphQL response
        """
        self.client = client
        self._data = data
        self._original_data = data.copy()
        self._dirty = False

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
        client: "ShopifyClient",
        query: str = "",
        first: int = 10,
        after: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List["Product"]:
        """
        Search for products.

        Args:
            client: ShopifyClient instance
            query: Search query string
            first: Number of products to fetch (max 250)
            after: Cursor for pagination
            filters: Additional filters (product_type, vendor, etc.)

        Returns:
            List of Product instances

        Raises:
            ValueError: If parameters are invalid
        """
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

        products = []
        if result and "data" in result and "products" in result["data"]:
            for edge in result["data"]["products"]["edges"]:
                products.append(cls(client, edge["node"]))

        return products

    @classmethod
    def get(cls, client: "ShopifyClient", product_id: str) -> Optional["Product"]:
        """
        Get a product by ID.

        Args:
            client: ShopifyClient instance
            product_id: Product ID

        Returns:
            Product instance or None if not found

        Raises:
            ValueError: If product_id is invalid
        """
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
                            weight
                            weightUnit
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

        if (
            result
            and "data" in result
            and "product" in result["data"]
            and result["data"]["product"]
        ):
            return cls(client, result["data"]["product"])

        return None

    @classmethod
    def get_by_handle(cls, client: "ShopifyClient", handle: str) -> Optional["Product"]:
        """
        Get a product by handle.

        Args:
            client: ShopifyClient instance
            handle: Product handle

        Returns:
            Product instance or None if not found

        Raises:
            ValueError: If handle is invalid
        """
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
                            weight
                            weightUnit
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

        if (
            result
            and "data" in result
            and "productByHandle" in result["data"]
            and result["data"]["productByHandle"]
        ):
            return cls(client, result["data"]["productByHandle"])

        return None

    @classmethod
    def create(cls, client: "ShopifyClient", product_data: Dict[str, Any]) -> "Product":
        """
        Create a new product.

        Args:
            client: ShopifyClient instance
            product_data: Product data for creation

        Returns:
            Created Product instance

        Raises:
            ValueError: If product_data is invalid or operation fails
        """
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
                    description
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

        # Handle user errors
        if result and "data" in result and "productCreate" in result["data"]:
            product_create = result["data"]["productCreate"]
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
                raise ValueError(f"Product creation failed: {'; '.join(error_messages)}")

            if product_create.get("product"):
                return cls(client, product_create["product"])

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
                    description
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

        # Handle user errors
        if result and "data" in result and "productUpdate" in result["data"]:
            product_update = result["data"]["productUpdate"]
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

        # Handle user errors
        if result and "data" in result and "productDelete" in result["data"]:
            product_delete = result["data"]["productDelete"]
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
            publications = [{"publicationId": "gid://shopify/Publication/1"}]  # Web publication

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

        # Handle user errors
        if result and "data" in result and "publishablePublish" in result["data"]:
            publish_result = result["data"]["publishablePublish"]
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
                # Update our status
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
            publications = [{"publicationId": self.WEB_PUBLICATION_ID}]  # Web publication

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

        # Handle user errors
        if result and "data" in result and "publishableUnpublish" in result["data"]:
            unpublish_result = result["data"]["publishableUnpublish"]
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
                # Update our status
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
