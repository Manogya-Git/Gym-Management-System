class GymScopedMixin:
    def get_queryset(self):
        return super().get_queryset().filter(gym=self.request.gym)

    def perform_create(self, serializer):
        serializer.save(gym=self.request.gym)