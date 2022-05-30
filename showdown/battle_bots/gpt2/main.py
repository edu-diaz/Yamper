from showdown.battle import Battle

from ..helpers import format_decision
from ..helpers import pick_yamper_move

from transformers import pipeline

class BattleBot(Battle):
    def __init__(self, *args, **kwargs):
        super(BattleBot, self).__init__(*args, **kwargs)

    def find_best_move(self):
        battles = self.prepare_battles(join_moves_together=True)
        yamper_move = pick_yamper_move(battles)
        return format_decision(self, yamper_move)

    @staticmethod
    def call_model(request):
        generator = pipeline('text-generation', model='gpt2')
        return generator(request, max_length=15, num_return_sequences=1)[0]['generated_text'].lower().strip()
