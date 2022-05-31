from showdown.battle import Battle

from ..helpers import format_decision
from ..helpers import pick_yamper_move

import requests
import json

class BattleBot(Battle):
    def __init__(self, *args, **kwargs):
        super(BattleBot, self).__init__(*args, **kwargs)

    def find_best_move(self):
        battles = self.prepare_battles(join_moves_together=True)
        yamper_move = pick_yamper_move(battles)
        return format_decision(self, yamper_move)

    @staticmethod
    def call_model(request):
        url = "https://main-gpt2-large-jeong-hyun-su.endpoint.ainize.ai/gpt2-large/long"
        payload={'text': request, 'num_samples': '1', 'length': '15'}
        headers = {'accept': 'application/json'}
        return json.loads(requests.request("POST", url, headers=headers, data=payload).text).get("0")
