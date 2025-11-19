from django.db import models
from django.conf import settings

# --- EXISTING MODELS ---

class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=100)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, related_name="variants", on_delete=models.CASCADE)
    size = models.CharField(max_length=50, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.product.name} - {self.size or 'No Size'}"


class Order(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("processing", "Processing"), # Added 'processing' for completeness
        ("shipped", "Shipped"),
        ("completed", "Completed"), # Added 'completed' for completeness
        ("cancelled", "Cancelled"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    total_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # 🟢 NEW: Field to track the staff member who last modified the order status
    last_modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, # Set NULL if the staff user is deleted
        null=True,
        blank=True,
        related_name="handled_orders",
        verbose_name="Last Handler"
    )

    def __str__(self):
        return f"Order #{self.pk} by {self.user}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.quantity} x {self.variant}"


class AuditLog(models.Model):
    ACTION_CHOICES = [
        ("order_create", "Order Created"),
        ("order_status_update", "Order Status Updated"), # Specific action type
        ("order_cancel", "Order Cancelled"),             # Specific action type
        ("other", "Other Action"),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, # Changed to SET_NULL for better log integrity
        null=True,
        blank=True,
        related_name="audit_logs"
    )
    action_type = models.CharField(max_length=50, choices=ACTION_CHOICES) # Increased max_length
    
    # 🟢 NEW: Link the log directly to the Order (Optional but helpful)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True, related_name="audit_entries")
    
    # Updated description to be specific
    description = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.action_type} on Order {self.order_id} at {self.created_at.strftime('%Y-%m-%d %H:%M')}"
