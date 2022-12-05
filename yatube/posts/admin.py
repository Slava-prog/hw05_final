from django.contrib import admin

from .models import Post, Group


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
