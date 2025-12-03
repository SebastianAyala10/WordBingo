from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from django.db import models
from django.contrib.auth.models import User
import random

class Room(models.Model):
    name = models.CharField(max_length=50, default="Sala 1")
    status = models.CharField(
        max_length=60,
        choices=[
            ("waiting", "Waiting"),
            ("running", "Running"),
            ("finished", "Finished"),
        ],
        default="waiting",
    )
    wait_end_time = models.DateTimeField()
    players = models.ManyToManyField(User, related_name="rooms", blank=True)

    @classmethod
    def get_default_room(cls, wait_seconds=30):
        room, created = cls.objects.get_or_create(
            pk=1,
            defaults={
                "name": "Sala 1",
                "wait_end_time": timezone.now() + timedelta(seconds=wait_seconds),
            },
        )
        return room

    def remaining_seconds(self):
        now = timezone.now()
        return max(0, int((self.wait_end_time - now).total_seconds()))
    
WORDS = [
    "SOL", "LUNA", "ESTRELLA", "CIELO", "NUBE", "AIRE", "VIENTO", "AGUA", "RIO",
    "LAGO", "MAR", "OCEANO", "PLAYA", "ARENA", "MONTAÑA", "BOSQUE", "ARBOL",
    "FLOR", "HOJA", "HIERBA", "FUEGO", "ROCA", "TIERRA", "NIEVE", "HIELO",
    "TRUENO", "RAYO", "LLUVIA", "TORMENTA", "BRUMA", "NOCHE", "DIA",
    "PERRO", "GATO", "PAJARO", "PEZ", "CABALLO", "VACA", "OVEJA", "CABRA",
    "CERDO", "TORTUGA", "RANA", "ZORRO", "OSO", "LOBO", "LEON", "TIGRE",
    "ELEFANTE", "DELFIN", "MARIPOSA", "ABEJA",
    "CASA", "CIUDAD", "PUEBLO", "CAMPO", "CARRETERA", "PUENTE", "ISLA",
    "VALLE", "DESIERTO", "CASCADA", "VOLCAN", "JARDIN", "PARQUE", "PLAYA",
    "MESA", "SILLA", "CAMA", "PUERTA", "VENTANA", "LIBRO", "LAPIZ",
    "RELOJ", "LLAVE", "CELULAR", "BOLSA", "ZAPATO", "SOMBRERO", "PELOTA",
    "CAJA", "LINTERNA", "BOTELLA", "VASO", "PLATO", "TENEDOR",
]



class BingoCard(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    room = models.ForeignKey("Room", on_delete=models.CASCADE)
    words = models.JSONField()  # 25 palabras (5x5)

    @classmethod
    def generate_words(cls):
        return random.sample(WORDS, 25)

    def rows(self):
        w = self.words
        return [w[i*5:(i+1)*5] for i in range(5)]


class GameState(models.Model):
    room = models.OneToOneField("Room", on_delete=models.CASCADE)
    words_order = models.JSONField(default=list)
    called_words = models.JSONField(default=list)
    next_index = models.IntegerField(default=0)

    @classmethod
    def start_new_for_room(cls, room):
        game_state, _ = cls.objects.get_or_create(room=room)
        shuffled = WORDS.copy()
        random.shuffle(shuffled)
        game_state.words_order = shuffled
        game_state.called_words = []
        game_state.next_index = 0
        game_state.save()
        return game_state

    def call_next(self):
        if self.next_index >= len(self.words_order):
            return None
        word = self.words_order[self.next_index]
        self.next_index += 1
        self.called_words.append(word)
        self.save()
        return word

