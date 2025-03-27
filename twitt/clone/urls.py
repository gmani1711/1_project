from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Authentication URLs
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # Home and Feed
    path('', views.PostListView.as_view(), name='home'),
    
    # Post URLs
    path('post/<int:pk>/', views.PostDetailView.as_view(), name='post-detail'),
    path('post/new/', views.PostCreateView.as_view(), name='post-create'),
    path('post/<int:pk>/update/', views.PostUpdateView.as_view(), name='post-update'),
    path('post/<int:pk>/delete/', views.PostDeleteView.as_view(), name='post-delete'),
    path('post/<int:pk>/like/', views.like_post, name='like-post'),
    path('post/<int:pk>/comment/', views.add_comment, name='add-comment'),
    
    # Profile URLs
    path('profile/<str:username>/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit-profile'),
    path('profile/<str:username>/follow/', views.follow_toggle, name='follow-toggle'),
    
    # Story URLs
    path('story/new/', views.create_story, name='create-story'),
    path('story/<str:username>/', views.view_story, name='view-story'),
    
    # Direct Message URLs
    path('messages/', views.direct_messages, name='direct-messages'),
    path('messages/<str:username>/', views.conversation, name='conversation'),
]

