# Payment/admin_views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from .models import Payment
from .serializers import PaymentSerializer

@api_view(["GET"])
@permission_classes([IsAdminUser])
def list_payments(request):
    """
    List all payments, with optional filtering by status.
    """
    status_filter = request.query_params.get("status")
    
    # FIX: Changed 'order__customer' to 'order__user'
    queryset = Payment.objects.all().select_related("order", "order__user") 

    if status_filter:
        queryset = queryset.filter(status=status_filter)

    serializer = PaymentSerializer(queryset, many=True)
    return Response(serializer.data)

@api_view(["GET"])
@permission_classes([IsAdminUser])
def payment_detail(request, payment_id):
    """
    View details of a single payment.
    """
    try:
        # FIX: Changed 'order__customer' to 'order__user'
        payment = Payment.objects.select_related("order", "order__user").get(id=payment_id)
    except Payment.DoesNotExist:
        return Response({"error": "Payment not found"}, status=status.HTTP_404_NOT_FOUND)

    serializer = PaymentSerializer(payment)
    return Response(serializer.data)

@api_view(["POST"])
@permission_classes([IsAdminUser])
def reconcile_payment(request, payment_id):
    """
    Manually mark a payment as Success/Failed and update related order.
    Useful if callback failed.
    """
    try:
        payment = Payment.objects.get(id=payment_id)
    except Payment.DoesNotExist:
        return Response({"error": "Payment not found"}, status=status.HTTP_404_NOT_FOUND)

    new_status = request.data.get("status")
    if new_status not in ["Success", "Failed"]:
        return Response({"error": "Invalid status"}, status=status.HTTP_400_BAD_REQUEST)

    payment.status = new_status
    payment.save()

    # NOTE: It's good practice to ensure 'Success'/'Failed' match case if model choices are strict
    if new_status == "Success":
        payment.order.status = "Processing"
        payment.order.save()
    elif new_status == "Failed":
        payment.order.status = "Pending Payment"
        payment.order.save()

    return Response({"message": f"Payment {payment_id} updated to {new_status}."})