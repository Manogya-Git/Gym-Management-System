from django.db import transaction

from .models import Gym, GymStaff


@transaction.atomic
def create_gym(*, owner, **gym_data):
    gym = Gym.objects.create(
        owner=owner,
        **gym_data
    )

    GymStaff.objects.create(
        user=owner,
        gym=gym,
        role=GymStaff.Role.OWNER
    )

    return gym