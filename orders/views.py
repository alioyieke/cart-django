from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from carts.models import CartItem
from .forms import OrderForm
from .models import Order, Payment, OrderProduct
import datetime, json
from store.models import Product
from django.template.loader import render_to_string
from django.core.mail import EmailMessage

# Create your views here.
def payments(request, order_number):
    # pay pal
    # body = json.loads(request.body)
    order = Order.objects.get(user = request.user, is_ordered = False, order_number = order_number)
    # Store transaction details
    # generate payment id
    yr = int(datetime.date.today().strftime('%Y'))
    dt = int(datetime.date.today().strftime('%d'))
    mt = int(datetime.date.today().strftime('%m'))
    d = datetime.date(yr, mt, dt)
    current_date = d.strftime("%Y%m%d")
    payment_id = current_date + str(order.id)
            
    payment = Payment(
        user           = request.user,
        payment_id     = payment_id,
        payment_method = 'NULL',
        amount_paid    = order.order_total,
        status         = 'COMPLETED',
    )
    payment.save()
    order.payment = payment
    order.is_ordered = True
    order.status     = 'COMPLETED'
    order.save()

    #Move the cart items to Order Product table
    cart_items = CartItem.objects.filter(user = request.user)
    payment    = Payment.objects.get(payment_id = payment_id)
    for item in cart_items:
        order_product = OrderProduct()
        order_product.payment       = payment
        order_product.user          = request.user
        order_product.product       = item.product
        order_product.quantity      = item.quantity
        order_product.product_price = item.product.price
        order_product.ordered       = True
        order_product.order         = order
        order_product.save()

        #save product variations
        cart_item = CartItem.objects.get(id = item.id)
        product_variation = cart_item.variations.all()
        orderproduct = OrderProduct.objects.get(id = order_product.id)
        orderproduct.variation.set(product_variation)
        orderproduct.save()

        #Reduce quantity of the sold products
        product = Product.objects.get(id = item.product.id)
        product.stock -= item.quantity
        product.save()
    
    #clear cart
    CartItem.objects.filter(user = request.user).delete()

    #send order received email to customer
    mail_subject = 'Thank you for your order!'
    message      = render_to_string('orders/order_received_email.html', {
        'user' : request.user,
        'order' : order,
    })
    to_email  = request.user.email
    send_mail = EmailMessage(mail_subject, message, to=[to_email])
    send_mail.send()

    #send order number and transaction id back to sendData() via JsonResponse
    #data = {
    #     'order_number': order.order_number,
    #     'transID': payment.payment_id,
    # }
    # return JsonResponse(data)

    return redirect('order_complete', order.order_number, payment_id)

def place_order(request, total = 0, quantity = 0):
    current_user = request.user
    cart_items   = CartItem.objects.filter(user = current_user)
    cart_count   = cart_items.count()
    if cart_count <= 0:
        return redirect('store')
    
    grand_total = 0
    tax = 0
    for cart_item in cart_items:
        total += (cart_item.product.price * cart_item.quantity)
        quantity += cart_item.quantity

    tax         = (2 * total)/100
    grand_total = total + tax
    
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            # store shipping information
            data = Order()
            data.user       = current_user
            data.first_name = form.cleaned_data['first_name']
            data.last_name  = form.cleaned_data['last_name']
            data.phone      = form.cleaned_data['phone']
            data.email      = form.cleaned_data['email']
            data.county     = form.cleaned_data['county']
            data.town       = form.cleaned_data['town']
            data.address    = form.cleaned_data['address']
            data.order_note = form.cleaned_data['order_note']
            data.order_total = grand_total
            data.tax         = tax
            data.ip          = request.META.get('REMOTE_ADDR')
            data.save()

            # generate order number
            yr = int(datetime.date.today().strftime('%Y'))
            dt = int(datetime.date.today().strftime('%d'))
            mt = int(datetime.date.today().strftime('%m'))
            d = datetime.date(yr, mt, dt)
            current_date = d.strftime("%Y%m%d")
            order_number = current_date + str(data.id)
            data.order_number = order_number
            data.save()

            order = Order.objects.get(user = current_user, is_ordered = False, order_number = order_number)
            context = {
                'order': order,
                'cart_items': cart_items,
                'total': total,
                'tax': tax,
                'grand_total': grand_total,
            }
            return render(request, 'orders/payments.html', context)
    else:
        return redirect('checkout')

def order_complete(request, order_number, payment_id):
    # order_number = request.GET.get('order_number')
    # transID      = request.GET.get('payment-id')

    try:
        order = Order.objects.get(order_number = order_number, is_ordered = True)
        ordered_products = OrderProduct.objects.filter(order_id = order.id)
        payment = Payment.objects.get(payment_id = payment_id)

        subtotal = 0
        for i in ordered_products:
            subtotal += i.product_price * i.quantity

        context = {
            'order': order,
            'ordered_products': ordered_products,
            'order_number': order.order_number,
            'transID': payment.payment_id,
            'payment': payment,
            'subtotal': subtotal,
        }
        return render(request, 'orders/order_complete.html', context)
    except(Payment.DoesNotExist, Order.DoesNotExist):
        return redirect('home')
