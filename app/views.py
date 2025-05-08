from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages

from django.contrib.auth import authenticate, login , logout
import pandas as pd
from django.http import JsonResponse


import os

def home(request):
   df = pd.read_csv('data/smartphones.csv')
   phones = df.to_dict('records')
   return render(request, 'main.html', {'phones': phones})

def home(request):
   if request.user.is_anonymous:
       redirect('login/')
   return render(request,'main.html')



def signup(request):        
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if not password or not confirm_password:
            return render(request, 'signup.html', {'message': 'Password fields cannot be empty'})


        if password != confirm_password:
            return render(request, 'signup.html', {'message': 'Passwords do not match'})

        if User.objects.filter(username=email).exists():
            return render(request, 'signup.html', {'message': 'Email already registered'})

        
        user = User.objects.create_user(username=email, email=email, password=password, first_name=name)
        user.save()

        return redirect('login_')  
    return render(request, 'signup.html')

def login_(request):
    if request.method == 'POST':
        username = request.POST.get('username')  # use 'username' to match your form
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('home')  # use name="home" from urls.py
        else:
            return render(request, 'login.html', {'message': 'Invalid credentials'})
    return render(request, 'login.html')



def logoutuser(request):
    logout(request)
    return redirect('login_')


def recommend_phones(request):
    recommendations = None
    error = None

    if request.method == 'POST':
        try:
            # Get form inputs
            brand = request.POST.get('brand', '').strip().lower()
            max_price = float(request.POST.get('max_price', 999999))
            min_ram = float(request.POST.get('min_ram', 0))
            min_storage = float(request.POST.get('min_storage', 0))

            # Load CSV file
            df = pd.read_csv('data/smartphones.csv')  

            # Clean and preprocess data
            df['ram'] = df['ram'].astype(str)
            df['storage'] = df['storage'].astype(str)
            df['price'] = df['price'].astype(str)

            df['RAM_GB'] = df['ram'].str.extract(r'(\d+)').astype(float)
            df['Storage_GB'] = df['storage'].str.extract(r'(\d+)').astype(float)
            df['Price_INR'] = df['price'].str.replace('₹', '', regex=False).str.replace(',', '', regex=False).astype(float)

            # Apply filters
            if brand and brand != "any":
                filtered = df[
                    (df['Price_INR'] <= max_price) &
                    (df['RAM_GB'] >= min_ram) &
                    (df['Storage_GB'] >= min_storage) &
                    (df['name'].str.lower().str.contains(brand))
                ].copy()
            else:
                filtered = df[
                    (df['Price_INR'] <= max_price) &
                    (df['RAM_GB'] >= min_ram) &
                    (df['Storage_GB'] >= min_storage)
                ].copy()

            # Scoring logic
            def compute_score(row, alpha=2, beta=1.5, gamma=0.02):
                return (alpha * row['RAM_GB']) + (beta * row['Storage_GB']) - (gamma * row['Price_INR'])

            filtered['Score'] = filtered.apply(compute_score, axis=1)
            top_10 = filtered.sort_values(by='Score', ascending=False).head(6)

            #  Convert to dicts for template use
            recommendations = top_10.to_dict('records')

        except Exception as e:
            error = f"Error: {str(e)}"

    return render(request, 'main.html', {
        'recommendations': recommendations,
        'error': error
    })

def phone_detail_view(request, model_slug):
    df = pd.read_csv('data/smartphones.csv')

    # Create slug from model field
    df['slug'] = df['model'].str.lower().str.replace(' ', '-')

    # Filter by the model_slug
    phone_data = df[df['slug'] == model_slug]

    if phone_data.empty:
        return render(request, 'error.html', {'error': 'Phone not found'})

    phone = phone_data.iloc[0].to_dict()
    return render(request, 'phone_detail.html', {'phone': phone})

smartphones_df = pd.read_csv('data/smartphones.csv')

# Create model_slug column
smartphones_df['model_slug'] = smartphones_df['model'].str.lower().str.replace(' ', '-').str.replace(r'[^a-z0-9\-]', '', regex=True)

def search_suggestions(request):
    query = request.GET.get('q', '')
    suggestions = []
    if query:
        matches = smartphones_df[
            (smartphones_df['model'].str.contains(query, case=False, na=False) |
             smartphones_df['name'].str.contains(query, case=False, na=False))
        ]
        suggestions = matches['model'].head(5).tolist()
    return JsonResponse(suggestions, safe=False)

def search_results(request):
    query = request.GET.get('q', '')
    results = []
    if query:
        matches = smartphones_df[
            (smartphones_df['model'].str.contains(query, case=False, na=False) |
             smartphones_df['name'].str.contains(query, case=False, na=False))
            &
            smartphones_df['model_slug'].notnull() &
            (smartphones_df['model_slug'] != '')
        ]
        results = matches.to_dict('records')
    return render(request, 'search_results.html', {'query': query, 'results': results})


df = pd.read_csv('data/smartphones.csv')

df.columns = df.columns.str.lower()  # make sure all column names are lower case
df['full_name'] = df['name'].str.lower() + ' ' + df['model'].str.lower()  # add combined search column

def compare(request):
    comparison = {}
    if request.method == 'POST':
        phone1_query = request.POST.get('phone1', '').lower().strip()
        phone2_query = request.POST.get('phone2', '').lower().strip()

        phone1_data = df[df['full_name'].str.contains(phone1_query, na=False)].head(1)
        phone2_data = df[df['full_name'].str.contains(phone2_query, na=False)].head(1)

        if not phone1_data.empty and not phone2_data.empty:
            phone1 = phone1_data.iloc[0]
            phone2 = phone2_data.iloc[0]

            comparison = {
                'phone1': {
                    'name': f"{phone1['name']} {phone1['model']}",
                    'ram': phone1['ram'],
                    'storage': phone1['storage'],
                    'battery': phone1['battery'],
                    'camera': phone1['primary_camera'],
                    'processor': phone1['processor']
                },
                'phone2': {
                    'name': f"{phone2['name']} {phone2['model']}",
                    'ram': phone2['ram'],
                    'storage': phone2['storage'],
                    'battery': phone2['battery'],
                    'camera': phone2['primary_camera'],
                    'processor': phone2['processor']
                },
                'better': decide_better(phone1, phone2)
            }
        else:
            comparison['error'] = "One or both smartphones not found!"

    return render(request, 'compare.html', {'comparison': comparison})

def search_phones(request):
    query = request.GET.get('term', '').lower()
    matches = df[df['full_name'].str.contains(query, na=False)]['full_name'].head(10).tolist()
    return JsonResponse(matches, safe=False)

def decide_better(phone1, phone2):
    score1 = (phone1['ram'] or 0) + (phone1['storage'] or 0) + (phone1['battery'] or 0) + (phone1['primary_camera'] or 0)
    score2 = (phone2['ram'] or 0) + (phone2['storage'] or 0) + (phone2['battery'] or 0) + (phone2['primary_camera'] or 0)
    if score1 > score2:
        return f"{phone1['name']} {phone1['model']}"
    elif score2 > score1:
        return f"{phone2['name']} {phone2['model']}"
    else:
        return "Both are equally good"

