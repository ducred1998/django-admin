from django.contrib import admin
from django.shortcuts import render
from sample_app.models import *
import csv
from datetime import datetime, timedelta
from django.utils.html import format_html
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.models import User, Group
from django.contrib.admin import AdminSite

# Custom Filters
class QuestionPublishedListFilter(admin.SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = ('Published questions')
    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'pub_date'
    def lookups(self, request, model_admin):
        return (
            ('Published', ('Published questions')),
            ('Unpublished', ('Unpublished questions')),
        )

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        if self.value() == 'Published':
            return queryset.filter(pub_date__lt=datetime.now())
        if self.value() == 'Unpublished':
            return queryset.filter(pub_date__gte=datetime.now())

class QuestionInline(admin.TabularInline):
    model = Question

class AuthorAdmin(admin.ModelAdmin):
    fieldsets = [
        ("Author information", {'fields': ['name','createdDate','updatedDate']}),
    ]
    empty_value_display = 'Unknown'
    list_display = ('name','createdDate','updatedDate',)
    search_fields = ('name',)
    inlines = [QuestionInline,]
    readonly_fields = ('createdDate','updatedDate',)

    def save_model(self, request, obj, form, change):
        print("Author saved by user %s" %request.user)
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        qs = super(AuthorAdmin, self).get_queryset(request)
        return qs.filter(name__startswith='j')

class QuestionAdmin(admin.ModelAdmin):
    fieldsets = [
        ("Question information", {
            'fields': ('question_text',)
        }),
        ("Date", {
            'fields': ('pub_date',)
        }),
        ('The author', {
            'classes': ('collapse',),
            'fields': ('refAuthor',),
        }),
    ]
    list_display = ('question_text','goToChoices','refAuthor',
                    'has_been_published','pub_date','createdDate', 
                    'updatedDate',)
    list_display_links = ('refAuthor',)
    
    list_editable = ('question_text',)
    # ordering = ('-pub_date',)
    # ordering = ('pub_date',)
    # ordering = ('-pub_date', 'createdDate',)
    date_hierarchy = 'pub_date'
    list_filter = (QuestionPublishedListFilter,'refAuthor',)
    search_fields = ('question_text','refAuthor__name',)
    list_select_related = ('refAuthor',)
    autocomplete_fields = ['refAuthor']
    #Search for ID
    # raw_id_fields = ['refAuthor']
    
    def has_been_published(self, obj):
        present = datetime.now()
        return obj.pub_date.date() < present.date()
    has_been_published.boolean = True
    has_been_published.short_description = 'Published?'

    # def colored_question_text(self, obj):
    #     return format_html('<span style="color: #{};">{}</span>', "ff5733", obj.question_text, )

    # colored_question_text.short_description = 'question text'

    def goToChoices(self, obj):
        return format_html('<a class="button" href="/admin/sample_app/choice/?question__id__exact=%s" target="blank">Choices</a>&nbsp;'% obj.pk)
    goToChoices.short_description = 'Choices'
    goToChoices.allow_tags = True

    def make_published(modeladmin, request, queryset):
        queryset.update(pub_date=datetime.now()- timedelta(days=1))
    make_published.short_description = "Mark selected questions as published"
    
    
    # Export to csv
    def export_to_csv(modeladmin, request, queryset):
        opts = modeladmin.model._meta
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; \
            filename={}.csv'.format(opts.verbose_name)
        writer = csv.writer(response)
        fields = [field for field in opts.get_fields() 
                    if not field.many_to_many and not field.one_to_many]
        # Write a first row with header information
        writer.writerow([field.verbose_name for field in fields])
        # Write data rows
        for obj in queryset:
            data_row = []
            for field in fields:
                value = getattr(obj, field.name)
                if isinstance(value, datetime):
                    value = value.strftime('%d/%m/%Y %H:%M')
                data_row.append(value)
            writer.writerow(data_row)
        return response
    
    export_to_csv.short_description = 'Export to CSV'

    # Intermediate page
    def make_published_custom(self, request, queryset):
        if 'apply' in request.POST:
            queryset.update(pub_date=datetime.now()- timedelta(days=1))
            self.message_user(request,
                "Changed to published on {} questions".format(queryset.count()))
            return HttpResponseRedirect(request.get_full_path())
        return render(request, 'admin/custom_makepublished.html', context={'questions':queryset})
    
    # ACTIONS
    actions = [make_published, export_to_csv, make_published_custom]

class ChoiceAdmin(admin.ModelAdmin):

    fieldsets = [
        ("Choice information", {
            "fields": ('choice_text',),
        }),
        ("Question", {
            "fields": ('question',),
        }),
        ("Votes", {
            "fields": ('votes',),
        }),
    ]
    
    list_display = ('question', 'choice_text', 'votes', 'createdDate', 'updatedDate',)
    list_display_links = ('question',)
    list_filter = ('question__refAuthor',)
    search_fields = ('choice_text','question__refAuthor__name','question__question_text',)
    list_select_related = ('question','question__refAuthor',)

class AuthorCloneAdmin(admin.ModelAdmin):
    fieldsets = [
        ("Author information", {'fields': ['name','createdDate','updatedDate']}),
    ]
    list_display = ('name','createdDate','updatedDate',)
    search_fields = ('name',)

# Register your models here.
# admin.site.register(Author, AuthorAdmin)
# admin.site.register(Question, QuestionAdmin)
# admin.site.register(Choice, ChoiceAdmin)
# admin.site.register(AuthorClone, AuthorCloneAdmin)

# Design customization
# admin.site.site_header = "Django Admin Ultimate Guide"
# admin.site.site_title = "Django Admin Title"
# admin.site.index_title = "Welcome to Ultimate Guide"

## Custom admin site
class MyUltimateAdminSite(AdminSite):
    site_header = 'My Django Admin Ultimate Guide'
    site_title = 'My Django Admin Ultimate Guide Administration'
    index_title = 'Welcome to my "sample_app"'

site = MyUltimateAdminSite()

admin.site.unregister(User)
admin.site.unregister(Group)

site.register(Author, AuthorAdmin)
site.register(Question, QuestionAdmin)
site.register(Choice, ChoiceAdmin)
site.register(AuthorClone, AuthorCloneAdmin)