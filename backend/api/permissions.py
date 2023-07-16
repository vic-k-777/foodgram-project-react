from rest_framework import permissions


class IsAuthorOrReadOnly(permissions.BasePermission):
    """Ограничим права пользователю, наложив запрет на удаление
    или редактирование чужих публикации. Запрашивать список
    всех публикаций или отдельную публикацию может любой пользователь.
    Создавать новую публикацию может только
    аутентифицированный пользователь."""
    def has_permission(self, request, view):
        return (request.method in permissions.SAFE_METHODS
                or request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        return (request.method in permissions.SAFE_METHODS
                or obj.author == request.user)


class IsAuthenticatedOrAdmin(permissions.BasePermission):
    """Проверим, что пользователь авторизован или является Админом."""
    def has_permission(self, request, view):
        return request.user.is_authenticated or request.user.is_staff
