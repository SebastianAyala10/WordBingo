from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import Room, BingoCard, GameState


# Página de inicio (landing del bingo)
def home(request):
    return render(request, "bingo/home.html")


# Lobby al que se redirige después de login / registro
@login_required
def lobby(request):
    return render(request, "bingo/lobby.html")


# Sala de espera con contador
@login_required
def waiting_room_view(request):
    room = Room.get_default_room()

    # Si la partida está corriendo, mandamos directo al juego
    if room.status == "running":
        return redirect("bingo:game", room.id)

    # Si la partida terminó o el contador de la ronda anterior ya pasó,
    # preparamos una nueva ronda
    if room.status == "finished" or room.remaining_seconds() == 0:
        room.status = "waiting"
        room.wait_end_time = timezone.now() + timedelta(seconds=30)
        room.players.clear()
        room.save()
        # Limpiar estado de la ronda anterior
        BingoCard.objects.filter(room=room).delete()
        GameState.objects.filter(room=room).delete()

    # Añadimos al jugador actual a la sala de esta ronda
    room.players.add(request.user)

    return render(request, "bingo/waiting_room.html", {"room": room})


# API que usa la sala de espera (contador + lista de jugadores)
@login_required
def room_status_api(request, room_id):
    room = get_object_or_404(Room, pk=room_id)

    remaining = room.remaining_seconds()

    # Cuando el contador llega a 0 por primera vez, arranca la partida
    if remaining == 0 and room.status == "waiting":
        room.status = "running"
        room.save()

        # Crear un estado de juego nuevo para esta ronda
        game_state = GameState.start_new_for_room(room)

        # Crear cartones 5x5 para cada jugador
        for player in room.players.all():
            BingoCard.objects.get_or_create(
                user=player,
                room=room,
                defaults={"words": BingoCard.generate_words()},
            )

        # Asegurarnos de tener ya la primera palabra cantada
        game_state.call_next()

    players = list(room.players.values_list("username", flat=True))

    return JsonResponse(
        {
            "status": room.status,
            "remaining_seconds": remaining,
            "players": players,
        }
    )


# Vista de la partida (cartón + UI del juego)
@login_required
def game_view(request, room_id):
    room = get_object_or_404(Room, pk=room_id)

    # Si por alguna razón el usuario entra sin cartón, se le genera uno
    card, _ = BingoCard.objects.get_or_create(
        user=request.user,
        room=room,
        defaults={"words": BingoCard.generate_words()},
    )

    game_state, _ = GameState.objects.get_or_create(room=room)
    # Si aún no hay palabras cantadas, sacamos la primera
    if not game_state.called_words:
        game_state.call_next()

    return render(
        request,
        "bingo/game.html",
        {
            "room": room,
            "card": card,
            "game": game_state,
        },
    )


# API para que el front sepa palabra actual y lista de palabras
@login_required
def game_state_api(request, room_id):
    room = get_object_or_404(Room, pk=room_id)
    game_state, _ = GameState.objects.get_or_create(room=room)

    last_word = game_state.called_words[-1] if game_state.called_words else None

    return JsonResponse(
        {
            "status": room.status,
            "last_word": last_word,
            "called_words": game_state.called_words,
        }
    )


# API del botón "Siguiente palabra"
@login_required
@require_POST
def call_next_word(request, room_id):
    room = get_object_or_404(Room, pk=room_id)
    game_state, _ = GameState.objects.get_or_create(room=room)

    word = game_state.call_next()
    finished = word is None

    return JsonResponse(
        {
            "finished": finished,
            "word": word,
            "called_words": game_state.called_words,
        }
    )


# Marcar partida como terminada (para poder empezar una nueva ronda luego)
@login_required
def finish_game(request, room_id):
    room = get_object_or_404(Room, pk=room_id)
    room.status = "finished"
    room.save()
    return redirect("bingo:lobby")
