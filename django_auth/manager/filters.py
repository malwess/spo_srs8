from rest_framework.filters import SearchFilter


class UnicodeSearchFilter(SearchFilter):
    """Поиск ?search=… без учёта регистра и для русских букв.

    SQLite сравнивает без учёта регистра только латиницу, поэтому стандартный
    SearchFilter не находит «Базы данных» по запросу «базы». Здесь строки
    сравниваются в Python через casefold(), а результат снова становится QuerySet.
    """

    def filter_queryset(self, request, queryset, view):
        terms = [t.casefold() for t in self.get_search_terms(request)]
        fields = getattr(view, 'search_fields', None)
        if not terms or not fields:
            return queryset

        def text(obj):
            values = []
            for field in fields:
                value = obj
                for part in field.split('__'):
                    value = getattr(value, part, '')
                values.append(str(value or ''))
            return ' '.join(values).casefold()

        ids = [obj.pk for obj in queryset if all(term in text(obj) for term in terms)]
        return queryset.filter(pk__in=ids)
