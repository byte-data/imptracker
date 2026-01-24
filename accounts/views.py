from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import Group
from django.contrib.auth.models import Permission
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from .models import User, Cluster
import json

def is_user_manager(user):
    """Check if user has User Manager role"""
    return user.is_superuser or user.groups.filter(name='User Manager').exists()

def is_system_admin(user):
    """Check if user is System Admin"""
    return user.is_superuser or user.groups.filter(name='System Admin').exists()

@login_required
@user_passes_test(is_user_manager)
def user_list(request):
    """List all users with search and filter"""
    query = request.GET.get('q', '')
    role = request.GET.get('role', '')
    cluster = request.GET.get('cluster', '')
    
    users = User.objects.all().prefetch_related('groups', 'clusters').order_by('username')
    
    if query:
        users = users.filter(
            Q(username__icontains=query) | 
            Q(first_name__icontains=query) | 
            Q(last_name__icontains=query) |
            Q(email__icontains=query)
        )
    
    if role:
        users = users.filter(groups__name=role)
    
    if cluster:
        users = users.filter(clusters__id=cluster)
    
    roles = Group.objects.all().order_by('name')
    clusters = Cluster.objects.all().order_by('short_name')
    
    context = {
        'users': users,
        'roles': roles,
        'clusters': clusters,
        'query': query,
        'selected_role': role,
        'selected_cluster': cluster,
    }
    return render(request, 'accounts/user_list.html', context)

@login_required
@user_passes_test(is_user_manager)
def user_create(request):
    """Create a new user"""
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        password = request.POST.get('password')
        is_active = request.POST.get('is_active') == 'on'
        
        # Validate
        if User.objects.filter(username=username).exists():
            messages.error(request, f'Username "{username}" already exists.')
            return redirect('accounts:user_create')
        
        if not username or not password:
            messages.error(request, 'Username and password are required.')
            return redirect('accounts:user_create')
        
        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=password,
            is_active=is_active
        )
        
        # Assign roles
        role_ids = request.POST.getlist('roles')
        if role_ids:
            user.groups.set(Group.objects.filter(id__in=role_ids))
        
        # Assign clusters
        cluster_ids = request.POST.getlist('clusters')
        if cluster_ids:
            user.clusters.set(Cluster.objects.filter(id__in=cluster_ids))
        
        messages.success(request, f'User "{username}" created successfully.')
        return redirect('accounts:user_list')
    
    roles = Group.objects.all().order_by('name')
    clusters = Cluster.objects.all().order_by('short_name')
    context = {
        'roles': roles,
        'clusters': clusters,
    }
    return render(request, 'accounts/user_form.html', context)

@login_required
@user_passes_test(is_user_manager)
def user_edit(request, pk):
    """Edit an existing user"""
    user = get_object_or_404(User, pk=pk)
    
    if request.method == 'POST':
        user.username = request.POST.get('username')
        user.email = request.POST.get('email')
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.is_active = request.POST.get('is_active') == 'on'
        
        # Assign roles
        role_ids = request.POST.getlist('roles')
        user.groups.set(Group.objects.filter(id__in=role_ids))
        
        # Assign clusters
        cluster_ids = request.POST.getlist('clusters')
        user.clusters.set(Cluster.objects.filter(id__in=cluster_ids))
        
        user.save()
        
        messages.success(request, f'User "{user.username}" updated successfully.')
        return redirect('accounts:user_list')
    
    roles = Group.objects.all().order_by('name')
    clusters = Cluster.objects.all().order_by('short_name')
    user_role_ids = list(user.groups.values_list('id', flat=True))
    user_cluster_ids = list(user.clusters.values_list('id', flat=True))
    
    context = {
        'user_obj': user,
        'roles': roles,
        'clusters': clusters,
        'user_role_ids': user_role_ids,
        'user_cluster_ids': user_cluster_ids,
        'is_edit': True,
    }
    return render(request, 'accounts/user_form.html', context)

@login_required
@user_passes_test(is_user_manager)
def user_reset_password(request, pk):
    """Reset user password"""
    if request.method == 'POST':
        user = get_object_or_404(User, pk=pk)
        new_password = request.POST.get('new_password')
        
        if not new_password:
            return JsonResponse({'success': False, 'error': 'Password is required'})
        
        user.set_password(new_password)
        user.save()
        
        return JsonResponse({'success': True, 'message': f'Password reset for {user.username}'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
@user_passes_test(is_user_manager)
def user_delete(request, pk):
    """Delete a user (or deactivate)"""
    if request.method == 'POST':
        user = get_object_or_404(User, pk=pk)
        username = user.username
        
        # Safer to deactivate instead of delete
        user.is_active = False
        user.save()
        
        messages.success(request, f'User "{username}" has been deactivated.')
        return redirect('accounts:user_list')
    
    return redirect('accounts:user_list')


# --------- Group / Role Management (staff or superuser only) ---------
def is_staff_or_superuser(user):
    return user.is_staff or user.is_superuser


@login_required
@user_passes_test(is_staff_or_superuser)
def group_list(request):
    """List all groups (roles)"""
    query = request.GET.get('q', '')
    groups = Group.objects.all().prefetch_related('permissions', 'permissions__content_type').order_by('name')
    if query:
        groups = groups.filter(name__icontains=query)

    context = {'groups': groups, 'query': query}
    return render(request, 'accounts/group_list.html', context)


@login_required
@user_passes_test(is_staff_or_superuser)
def group_create(request):
    """Create a new group/role and assign permissions"""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        perm_ids = request.POST.getlist('permissions')

        if not name:
            messages.error(request, 'Name is required.')
            return redirect('accounts:group_create')

        if Group.objects.filter(name=name).exists():
            messages.error(request, f'Role "{name}" already exists.')
            return redirect('accounts:group_create')

        group = Group.objects.create(name=name)
        if perm_ids:
            perms = Permission.objects.filter(id__in=perm_ids)
            group.permissions.set(perms)

        messages.success(request, f'Role "{name}" created.')
        return redirect('accounts:group_list')

    permissions = Permission.objects.select_related('content_type').order_by('content_type__app_label', 'codename')
    context = {'permissions': permissions}
    return render(request, 'accounts/group_form.html', context)


@login_required
@user_passes_test(is_staff_or_superuser)
def group_edit(request, pk):
    group = get_object_or_404(Group, pk=pk)
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        perm_ids = request.POST.getlist('permissions')

        if not name:
            messages.error(request, 'Name is required.')
            return redirect('accounts:group_edit', pk=pk)

        # Prevent changing name to an existing group's name
        if Group.objects.exclude(pk=pk).filter(name=name).exists():
            messages.error(request, 'Another role with that name already exists.')
            return redirect('accounts:group_edit', pk=pk)

        group.name = name
        group.save()
        perms = Permission.objects.filter(id__in=perm_ids)
        group.permissions.set(perms)

        messages.success(request, f'Role "{group.name}" updated.')
        return redirect('accounts:group_list')

    permissions = Permission.objects.select_related('content_type').order_by('content_type__app_label', 'codename')
    group_perm_ids = list(group.permissions.values_list('id', flat=True))
    context = {'group': group, 'permissions': permissions, 'group_perm_ids': group_perm_ids, 'is_edit': True}
    return render(request, 'accounts/group_form.html', context)


@login_required
@user_passes_test(is_staff_or_superuser)
def group_delete(request, pk):
    if request.method == 'POST':
        group = get_object_or_404(Group, pk=pk)
        name = group.name
        group.delete()
        messages.success(request, f'Role "{name}" deleted.')
    return redirect('accounts:group_list')


# ============= PROFILE MANAGEMENT =============
@login_required
def profile_view(request):
    """View logged-in user's profile (read-only)"""
    user = request.user
    context = {'user_obj': user}
    return render(request, 'accounts/profile_view.html', context)


@login_required
def profile_edit(request):
    """Allow logged-in user to edit their own profile"""
    user = request.user
    
    if request.method == 'POST':
        user.first_name = request.POST.get('first_name', '').strip()
        user.last_name = request.POST.get('last_name', '').strip()
        user.email = request.POST.get('email', '').strip()
        
        user.save()
        messages.success(request, 'Your profile has been updated successfully.')
        return redirect('accounts:profile_view')
    
    context = {'user_obj': user}
    return render(request, 'accounts/profile_edit.html', context)


@login_required
def change_password(request):
    """Allow logged-in user to change their password"""
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        # Verify current password
        if not request.user.check_password(current_password):
            messages.error(request, 'Current password is incorrect.')
            return redirect('accounts:change_password')
        
        # Validate new password
        if len(new_password) < 8:
            messages.error(request, 'New password must be at least 8 characters long.')
            return redirect('accounts:change_password')
        
        if new_password != confirm_password:
            messages.error(request, 'New passwords do not match.')
            return redirect('accounts:change_password')
        
        # Update password
        request.user.set_password(new_password)
        request.user.save()
        
        # Keep user logged in after password change
        from django.contrib.auth import update_session_auth_hash
        update_session_auth_hash(request, request.user)
        
        messages.success(request, 'Your password has been changed successfully.')
        return redirect('dashboards:dashboard')
    
    return render(request, 'accounts/change_password.html')
