from django.shortcuts import render, redirect, get_object_or_404
from store.models import Product, Variation
from carts.models import Cart, CartItem
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required


# Private function to capture session key
def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart

# Add product to cart
def add_cart(request, product_id):
    current_user = request.user
    product = Product.objects.get(id = product_id) # get the product
    
    # user is authenticated
    if current_user.is_authenticated:
        # Handle product variations
        product_variation = []
        if request.method == 'POST':
            for item in request.POST:
                key = item
                value = request.POST[key]
                try:
                    variation = Variation.objects.get(product = product, variation_category__iexact = key, variation_value__iexact = value)
                    product_variation.append(variation)
                except:
                    pass

        # save cart items
        is_cart_item_exists = CartItem.objects.filter(product = product, user = current_user).exists()
        if is_cart_item_exists:
            # Update existing cart item
            cart_item = CartItem.objects.filter(product = product, user = current_user)
            ex_var_list = []
            id = []
            # Save existing product variation in a list
            for item in cart_item:
                existing_variation = item.variations.all()
                ex_var_list.append(list(existing_variation))
                id.append(item.id)

            if product_variation in ex_var_list:
                # Increase the cart item quantity
                index   = ex_var_list.index(product_variation)
                item_id = id[index]
                item    = CartItem.objects.get(product = product, id = item_id)
                item.quantity += 1
                item.save()
            else:
                # Add item to cart with new variation
                item = CartItem.objects.create(product = product, quantity = 1, user = current_user)
                if len(product_variation) > 0:
                    item.variations.clear()
                    item.variations.add(*product_variation)
                item.save()

        else:
            # Add new cart item
            cart_item = CartItem.objects.create(
                product  = product,
                user     = current_user,
                quantity = 1,
            )
            if len(product_variation) > 0:
                cart_item.variations.clear()
                cart_item.variations.add(*product_variation)
            cart_item.save()

        return redirect('cart')
    # user is a guest
    else:
        # Handle product variations
        product_variation = []
        if request.method == 'POST':
            for item in request.POST:
                key = item
                value = request.POST[key]
                try:
                    variation = Variation.objects.get(product = product, variation_category__iexact = key, variation_value__iexact = value)
                    product_variation.append(variation)
                except:
                    pass

        # get the cart using the cart_id present in the session
        try:
            cart = Cart.objects.get(cart_id = _cart_id(request)) 
        except Cart.DoesNotExist:
            cart = Cart.objects.create(
                cart_id = _cart_id(request)
            )
        cart.save()

        # save cart items
        is_cart_item_exists = CartItem.objects.filter(product = product, cart = cart).exists()
        if is_cart_item_exists:
            # Update existing cart item
            cart_item = CartItem.objects.filter(product = product, cart = cart)
            ex_var_list = []
            id = []
            # Save existing product variation in a list
            for item in cart_item:
                existing_variation = item.variations.all()
                ex_var_list.append(list(existing_variation))
                id.append(item.id)

            if product_variation in ex_var_list:
                # Increase the cart item quantity
                index   = ex_var_list.index(product_variation)
                item_id = id[index]
                item    = CartItem.objects.get(product = product, id = item_id)
                item.quantity += 1
                item.save()
            else:
                # Add item to cart with new variation
                item = CartItem.objects.create(product = product, quantity = 1, cart = cart)
                if len(product_variation) > 0:
                    item.variations.clear()
                    item.variations.add(*product_variation)
                item.save()

        else:
            # Add new cart item
            cart_item = CartItem.objects.create(
                product  = product,
                cart     = cart,
                quantity = 1,
            )
            if len(product_variation) > 0:
                cart_item.variations.clear()
                cart_item.variations.add(*product_variation)
            cart_item.save()

        return redirect('cart')

# Decrease quantity of a cart item
def remove_cart(request, product_id, cart_item_id):
    product   = get_object_or_404(Product, id = product_id)
    try:
        if request.user.is_authenticated:
            cart_item = CartItem.objects.get(product = product, user = request.user, id = cart_item_id)
        else:
            cart = Cart.objects.get(cart_id = _cart_id(request))
            cart_item = CartItem.objects.get(product = product, cart = cart, id = cart_item_id)
        if cart_item.quantity > 1:
            cart_item.quantity -=1
            cart_item.save()
        else:
            cart_item.delete()
    except:
        pass

    return redirect('cart')

# Remove item from cart
def remove_cart_item(request, product_id, cart_item_id):
    product   = get_object_or_404(Product, id = product_id)
    if request.user.is_authenticated:
        cart_item = CartItem.objects.get(product = product, user = request.user, id = cart_item_id)
    else:
        cart = Cart.objects.get(cart_id = _cart_id(request))
        cart_item = CartItem.objects.get(product = product, cart = cart, id = cart_item_id)
    cart_item.delete()
    return redirect('cart')

# Display cart content
def cart(request, total = 0, quantity = 0, cart_items = None):
    try:
        tax = 0
        grand_total = 0
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user = request.user, is_active = True)
        else:
            cart       = Cart.objects.get(cart_id = _cart_id(request))
            cart_items = CartItem.objects.filter(cart = cart, is_active = True)
            
        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity

        tax         = (2 * total)/100
        grand_total = total + tax
    except ObjectDoesNotExist:
        pass 

    context = {
        'tax' : tax,
        'total' : total,
        'quantity' : quantity,
        'cart_items' : cart_items,
        'grand_total' : grand_total,
    }
    return render(request, 'store/cart.html', context)

# Checkout
@login_required(login_url='login')
def checkout(request, total=0, quantity=0, cart_items=None):
    try:
        tax = 0
        grand_total = 0
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user = request.user, is_active = True)
        else:
            cart       = Cart.objects.get(cart_id = _cart_id(request))
            cart_items = CartItem.objects.filter(cart = cart, is_active = True)
            
        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity

        tax         = (2 * total)/100
        grand_total = total + tax
    except ObjectDoesNotExist:
        pass 

    context = {
        'tax' : tax,
        'total' : total,
        'quantity' : quantity,
        'cart_items' : cart_items,
        'grand_total' : grand_total,
    }
    return render(request, 'store/checkout.html', context)
