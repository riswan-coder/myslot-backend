from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied

from .models import Game, Machine
from .serializers import GameSerializer, MachineSerializer
from shops.models import GamingCenter
from accounts.permissions import IsShopOwner, IsObjectOwner

class GameViewSet(viewsets.ModelViewSet):
    serializer_class = GameSerializer
    permission_classes = [IsShopOwner, IsObjectOwner]

    def get_queryset(self):
        if self.request.user.is_authenticated and self.request.user.role == 'owner':
            return Game.objects.filter(shop__owner=self.request.user)
        return Game.objects.filter(is_available=True)

    def perform_create(self, serializer):
        shop_id = self.request.data.get('shop')
        try:
            shop = GamingCenter.objects.get(id=shop_id, owner=self.request.user)
        except GamingCenter.DoesNotExist:
            raise PermissionDenied("You can only add games to your own shop.")
        serializer.save(shop=shop)

class MachineViewSet(viewsets.ModelViewSet):
    serializer_class = MachineSerializer
    permission_classes = [IsShopOwner, IsObjectOwner]

    def get_queryset(self):
        if self.request.user.is_authenticated and self.request.user.role == 'owner':
            return Machine.objects.filter(game__shop__owner=self.request.user)
        return Machine.objects.all()

    def perform_create(self, serializer):
        game_id = self.request.data.get('game')
        try:
            game = Game.objects.get(id=game_id, shop__owner=self.request.user)
        except Game.DoesNotExist:
            raise PermissionDenied("You can only add machines to your own games.")
        serializer.save(game=game)