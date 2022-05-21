from showdown.battle import Battle

from ..helpers import format_decision
from ..helpers import pick_safest_move_from_battles
import banana_dev as banana


class BattleBot(Battle):
    def __init__(self, *args, **kwargs):
        super(BattleBot, self).__init__(*args, **kwargs)

    def find_best_move(self):
        battles = self.prepare_battles(join_moves_together=True)
        safest_move = pick_safest_move_from_battles(battles)
        return format_decision(self, safest_move)

    def call_nlp(self):
        api_key={your key here}
        model_key="gptj"
        model_parameters = { "text": "Hey GPTJ! How are you?", "length": 50, "temperature": 0.9, "topK": 50, "topP": 0.9}

        out = banana.run(api_key, model_key, model_parameters)
        print(out)