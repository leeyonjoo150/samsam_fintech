from django.urls import path
from .views import my_stock_holdings, add_stock_holding, add_stock_account, search_data
from .views import geoguessr_game

app_name = 'financial_data'

urlpatterns = [
    path('', my_stock_holdings, name='my_stock_holdings'),
    path('add/', add_stock_holding, name='add_stock_holding'),
    path('add_stock_account/', add_stock_account, name='add_stock_account'),
    path('search/', search_data, name='search_data'),
    path("geoguessr/", geoguessr_game, name='geoguessr_game'),
]