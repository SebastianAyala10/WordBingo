from django.urls import path
from . import views

urlpatterns = [
   path("lobby/", views.lobby, name="lobby"),
    path("waiting-room/", views.waiting_room_view, name="waiting_room"),
    path("room/<int:room_id>/status/", views.room_status_api, name="room_status"),
    path("game/<int:room_id>/", views.game_view, name="game"),
    path("game/<int:room_id>/state/", views.game_state_api, name="game_state"),
    path("game/<int:room_id>/call/", views.call_next_word, name="call_next_word"),
    path("game/<int:room_id>/finish/", views.finish_game, name="finish_game"),
]
