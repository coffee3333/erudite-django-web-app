import django_filters
from django.db.models import Q
from django.core.exceptions import ValidationError
from core.models.course_model import Course
from django.contrib.auth import get_user_model


class CourseFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method='filter_search')
    title = django_filters.CharFilter(field_name='title', lookup_expr='icontains')
    owner_username = django_filters.CharFilter(method='filter_owner_username')
    level = django_filters.CharFilter(field_name='level', lookup_expr='iexact')
    status = django_filters.CharFilter(field_name='status', lookup_expr='iexact')
    sort_by = django_filters.CharFilter(method='filter_sort_by')

    class Meta:
        model = Course
        fields = ['search', 'title', 'owner_username', 'owner_id', 'level', 'status', 'sort_by']

    def filter_search(self, queryset, name, value):
        if value:
            return queryset.filter(
                Q(title__icontains=value) |
                Q(description__icontains=value) |
                Q(owner__username__icontains=value)
            ).distinct()
        return queryset

    def filter_owner_username(self, queryset, name, value):
        User = get_user_model()
        if value:
            user_exists = User.objects.filter(username__iexact=value).exists()
            if not user_exists:
                raise ValidationError(f"User with username '{value}' does not exist.")
            return queryset.filter(owner__username__iexact=value)
        return queryset

    def filter_sort_by(self, queryset, name, value):
        valid_sorts = {
            'newest': '-created_at',
            'oldest': 'created_at',
            'title_asc': 'title',
            'title_desc': '-title',
        }
        if value in valid_sorts:
            return queryset.order_by(valid_sorts[value])
        raise ValidationError({"sort_by": f"Invalid sorting option. Choose one of: {', '.join(valid_sorts.keys())}"})
