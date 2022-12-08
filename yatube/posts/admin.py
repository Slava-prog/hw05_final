from django.contrib import admin

from .models import Post, Group, Comment, Follow


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    '''Источник конфигурации для модели Group.'''
    list_display = (
        'title',
        'slug',
        'description',
    )
    search_fields = ('title',)
    empty_value_display = '-пусто-'


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    '''Источник конфигурации для модели Post.'''
    list_display = (
        'pk',
        'text',
        'pub_date',
        'author',
        'group',
    )
    list_editable = ('group',)
    search_fields = ('text',)
    list_filter = ('pub_date',)
    empty_value_display = '-пусто-'


@admin.register(Comment)
class PostComment(admin.ModelAdmin):
    '''Источник конфигурации для модели Comment.'''
    list_display = (
        'post',
        'text',
        'author'
    )
    search_fields = ('text',)
    empty_value_display = '-пусто-'


@admin.register(Follow)
class PostFollow(admin.ModelAdmin):
    '''Источник конфигурации для модели Comment.'''
    list_display = (
        'author',
        'user'
    )
    search_fields = ('user',)
