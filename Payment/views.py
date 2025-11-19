from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import JsonResponse

from .models import Payment
from .services.mpesa_service import MPesaService
from .services.airtel_service import AirtelMoneyService
from Shop.models import Order, OrderItem
from .serializers import PaymentSerializer


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def initiate_payment(request):
    """Initiate payment for an order"""
    payment_method = request.data.get('payment_method')  # 'mpesa' or 'airtel'
    phone_number = request.data.get('phone_number')
    cart_items = request.data.get('cart_items', [])  # [{variant_id, quantity}, ...]
    
    if not all([payment_method, phone_number, cart_items]):
        return Response(
            {"error": "payment_method, phone_number, and cart_items are required"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Create order
        order = Order.objects.create(
            user=request.user,
            status='pending',
            total_price=0
        )
        
        total = 0
        for item in cart_items:
            from Shop.models import ProductVariant
            variant = ProductVariant.objects.get(id=item['variant_id'])
            quantity = int(item['quantity'])
            
            # Check stock
            if variant.stock < quantity:
                order.delete()
                return Response(
                    {"error": f"Not enough stock for {variant.product.name}"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create order item
            OrderItem.objects.create(
                order=order,
                variant=variant,
                quantity=quantity
            )
            
            total += variant.price * quantity
        
        # Update order total
        order.total_price = total
        order.save()
        
        # Create payment record
        payment = Payment.objects.create(
            order=order,
            user=request.user,
            payment_method=payment_method,
            phone_number=phone_number,
            amount=total,
            status='pending'
        )
        
        # Initiate payment based on method
        if payment_method == 'mpesa':
            mpesa = MPesaService()
            result = mpesa.stk_push(
                phone_number=phone_number,
                amount=total,
                account_reference=f"Order-{order.id}",
                transaction_desc=f"Payment for Order #{order.id}"
            )
            
            if result.get('ResponseCode') == '0':
                payment.merchant_request_id = result.get('MerchantRequestID')
                payment.checkout_request_id = result.get('CheckoutRequestID')
                payment.save()
                
                return Response({
                    "success": True,
                    "message": "STK push sent. Check your phone",
                    "order_id": order.id,
                    "payment_id": payment.id
                })
            else:
                payment.status = 'failed'
                payment.result_desc = result.get('errorMessage', 'Payment initiation failed')
                payment.save()
                return Response(
                    {"error": result.get('errorMessage', 'Payment failed')},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        elif payment_method == 'airtel':
            airtel = AirtelMoneyService()
            result = airtel.initiate_payment(
                phone_number=phone_number,
                amount=total,
                reference=f"Order-{order.id}",
                transaction_id=f"TXN-{payment.id}"
            )
            
            if result.get('status', {}).get('success'):
                payment.transaction_id = result.get('data', {}).get('transaction', {}).get('id')
                payment.save()
                
                return Response({
                    "success": True,
                    "message": "Payment request sent. Check your phone",
                    "order_id": order.id,
                    "payment_id": payment.id
                })
            else:
                payment.status = 'failed'
                payment.result_desc = result.get('status', {}).get('message', 'Payment failed')
                payment.save()
                return Response(
                    {"error": "Airtel payment initiation failed"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        else:
            return Response(
                {"error": "Invalid payment method"},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@csrf_exempt
@api_view(['POST'])
def mpesa_callback(request):
    """Handle M-Pesa callback"""
    data = request.data
    
    try:
        result_code = data['Body']['stkCallback']['ResultCode']
        checkout_request_id = data['Body']['stkCallback']['CheckoutRequestID']
        
        payment = Payment.objects.get(checkout_request_id=checkout_request_id)
        
        if result_code == 0:
            # Payment successful
            callback_metadata = data['Body']['stkCallback']['CallbackMetadata']['Item']
            
            for item in callback_metadata:
                if item['Name'] == 'MpesaReceiptNumber':
                    payment.transaction_id = item['Value']
            
            payment.status = 'completed'
            payment.result_desc = 'Payment successful'
            payment.save()
            
            # Update order status
            payment.order.status = 'paid'
            payment.order.save()
            
        else:
            # Payment failed
            payment.status = 'failed'
            payment.result_desc = data['Body']['stkCallback'].get('ResultDesc', 'Payment failed')
            payment.save()
        
        return JsonResponse({"ResultCode": 0, "ResultDesc": "Accepted"})
    
    except Exception as e:
        return JsonResponse({"ResultCode": 1, "ResultDesc": str(e)})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_payment_status(request, payment_id):
    """Check payment status"""
    try:
        payment = Payment.objects.get(id=payment_id, user=request.user)
        serializer = PaymentSerializer(payment)
        return Response(serializer.data)
    except Payment.DoesNotExist:
        return Response(
            {"error": "Payment not found"},
            status=status.HTTP_404_NOT_FOUND
        )