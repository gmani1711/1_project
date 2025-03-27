from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from .models import Profile, Post, Comment, Like, Story, DirectMessage
from .forms import UserRegisterForm, UserUpdateForm, ProfileUpdateForm, PostForm, CommentForm, StoryForm, MessageForm

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! You can now log in.')
            return redirect('login')
    else:
        form = UserRegisterForm()
    return render(request, 'signup.html', {'form': form})

@login_required
def home(request):
    # Get users that the current user follows
    following_users = User.objects.filter(profile__followers=request.user)
    
    # Get posts from those users and the current user
    posts = Post.objects.filter(user__in=list(following_users) + [request.user])
    
    # Get active stories from users the current user follows
    active_stories = Story.objects.filter(
        user__in=following_users,
        expires_at__gt=timezone.now()
    ).order_by('user', '-created_at').distinct('user')
    
    context = {
        'posts': posts,
        'active_stories': active_stories,
    }
    return render(request, 'home.html', context)

class PostListView(LoginRequiredMixin, ListView):
    model = Post
    template_name = 'home.html'
    context_object_name = 'posts'
    
    def get_queryset(self):
        # Get users that the current user follows
        following_users = User.objects.filter(profile__followers=self.request.user)
        # Get posts from those users and the current user
        return Post.objects.filter(user__in=list(following_users) + [self.request.user])
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get active stories from users the current user follows
        following_users = User.objects.filter(profile__followers=self.request.user)
        context['active_stories'] = Story.objects.filter(
            user__in=following_users,
            expires_at__gt=timezone.now()
        ).select_related('user').order_by('user__username').distinct('user__username')
        return context

class PostDetailView(LoginRequiredMixin, DetailView):
    model = Post
    template_name = 'post_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comments'] = Comment.objects.filter(post=self.object)
        context['comment_form'] = CommentForm()
        context['liked'] = Like.objects.filter(post=self.object, user=self.request.user).exists()
        return context

class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'post_form.html'
    success_url = reverse_lazy('home')
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'post_form.html'
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)
    
    def test_func(self):
        post = self.get_object()
        return self.request.user == post.user

class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Post
    template_name = 'post_confirm_delete.html'
    success_url = reverse_lazy('home')
    
    def test_func(self):
        post = self.get_object()
        return self.request.user == post.user

@login_required
def like_post(request, pk):
    post = get_object_or_404(Post, pk=pk)
    like, created = Like.objects.get_or_create(post=post, user=request.user)
    
    if not created:
        # User already liked the post, so unlike it
        like.delete()
        liked = False
    else:
        liked = True
    
    if request.is_ajax():
        return JsonResponse({
            'liked': liked,
            'likes_count': post.get_likes_count()
        })
    
    return HttpResponseRedirect(reverse('post-detail', args=[pk]))

@login_required
def add_comment(request, pk):
    post = get_object_or_404(Post, pk=pk)
    
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.user = request.user
            comment.save()
            messages.success(request, 'Comment added successfully!')
            
            if request.is_ajax():
                return JsonResponse({
                    'success': True,
                    'comment_id': comment.id,
                    'username': comment.user.username,
                    'text': comment.text,
                    'created_at': comment.created_at.strftime('%b %d, %Y, %I:%M %p')
                })
    
    return HttpResponseRedirect(reverse('post-detail', args=[pk]))

@login_required
def profile(request, username):
    user = get_object_or_404(User, username=username)
    posts = Post.objects.filter(user=user)
    
    # Check if the current user follows this profile
    is_following = False
    if request.user.is_authenticated:
        is_following = user.profile.followers.filter(id=request.user.id).exists()
    
    context = {
        'user_profile': user,
        'posts': posts,
        'is_following': is_following,
        'followers_count': user.profile.get_followers_count(),
        'following_count': user.profile.get_following_count(),
        'posts_count': posts.count(),
    }
    return render(request, 'profile.html', context)

@login_required
def edit_profile(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('profile', username=request.user.username)
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)
    
    context = {
        'u_form': u_form,
        'p_form': p_form
    }
    return render(request, 'edit_profile.html', context)

@login_required
def follow_toggle(request, username):
    user_to_follow = get_object_or_404(User, username=username)
    
    if request.user == user_to_follow:
        messages.warning(request, 'You cannot follow yourself.')
    else:
        if request.user in user_to_follow.profile.followers.all():
            # Unfollow
            user_to_follow.profile.followers.remove(request.user)
            messages.success(request, f'You have unfollowed {username}.')
        else:
            # Follow
            user_to_follow.profile.followers.add(request.user)
            messages.success(request, f'You are now following {username}.')
    
    return redirect('profile', username=username)

@login_required
def create_story(request):
    if request.method == 'POST':
        form = StoryForm(request.POST, request.FILES)
        if form.is_valid():
            story = form.save(commit=False)
            story.user = request.user
            story.save()
            messages.success(request, 'Your story has been created!')
            return redirect('home')
    else:
        form = StoryForm()
    
    return render(request, 'story_form.html', {'form': form})

@login_required
def view_story(request, username):
    user = get_object_or_404(User, username=username)
    stories = Story.objects.filter(
        user=user,
        expires_at__gt=timezone.now()
    ).order_by('created_at')
    
    if not stories:
        messages.warning(request, f'{username} has no active stories.')
        return redirect('home')
    
    context = {
        'stories': stories,
        'story_user': user
    }
    return render(request, 'story_view.html', context)

@login_required
def direct_messages(request):
    # Get all conversations where the user is either sender or receiver
    conversations = User.objects.filter(
        models.Q(sent_messages__receiver=request.user) | 
        models.Q(received_messages__sender=request.user)
    ).distinct()
    
    context = {
        'conversations': conversations
    }
    return render(request, 'direct_messages.html', context)

@login_required
def conversation(request, username):
    other_user = get_object_or_404(User, username=username)
    
    # Get all messages between the current user and the other user
    messages = DirectMessage.objects.filter(
        (models.Q(sender=request.user) & models.Q(receiver=other_user)) |
        (models.Q(sender=other_user) & models.Q(receiver=request.user))
    ).order_by('created_at')
    
    # Mark messages as read
    unread_messages = messages.filter(is_read=False, receiver=request.user)
    unread_messages.update(is_read=True)
    
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user
            message.receiver = other_user
            message.save()
            return redirect('conversation', username=username)
    else:
        form = MessageForm()
    
    context = {
        'messages': messages,
        'other_user': other_user,
        'form': form
    }
    return render(request, 'conversation.html', context)

