from django.shortcuts import render, redirect
import os
import stripe
from django.conf import settings
from django.views.decorators.http import require_POST

stripe.api_key = settings.STRIPE_SECRET_KEY


@require_POST
def create_checkout_session(request):
    domain = 'http://127.0.0.1:8001'
    try:
        checkout_session = stripe.checkout.Session.create(
            line_items=[
                {
                    # Provide the exact Price ID (for example, pr_1234) of the product you want to sell
                    'price': '{{PRICE_ID}}',
                    'quantity': 1,
                },
            ],
            mode='payment',
            success_url=domain + '/success.html',
            cancel_url=domain + '/cancel.html',
        )
    except Exception as e:
        return str(e)

    return redirect(checkout_session.url, code=303)