import logging

import config
import constants
import banana_dev as banana
import os

from showdown.engine.objects import StateMutator
from showdown.engine.select_best_move import pick_safest
from showdown.engine.select_best_move import get_payoff_matrix

from difflib import SequenceMatcher


logger = logging.getLogger(__name__)


def format_decision(battle, decision):
    # Formats a decision for communication with Pokemon-Showdown
    # If the pokemon can mega-evolve, it will
    # If the move can be used as a Z-Move, it will be

    if decision.startswith(constants.SWITCH_STRING + " "):
        switch_pokemon = decision.split("switch ")[-1]
        for pkmn in battle.user.reserve:
            if pkmn.name == switch_pokemon:
                message = "/switch {}".format(pkmn.index)
                break
        else:
            raise ValueError("Tried to switch to: {}".format(switch_pokemon))
    else:
        message = "/choose move {}".format(decision)
        if battle.user.active.can_mega_evo:
            message = "{} {}".format(message, constants.MEGA)
        elif battle.user.active.can_ultra_burst:
            message = "{} {}".format(message, constants.ULTRA_BURST)

        # only dynamax on last pokemon
        if battle.user.active.can_dynamax and all(p.hp == 0 for p in battle.user.reserve):
            message = "{} {}".format(message, constants.DYNAMAX)

        if battle.user.active.get_move(decision).can_z:
            message = "{} {}".format(message, constants.ZMOVE)

    return [message, str(battle.rqid)]


def prefix_opponent_move(score_lookup, prefix):
    new_score_lookup = dict()
    for k, v in score_lookup.items():
        bot_move, opponent_move = k
        new_opponent_move = "{}_{}".format(opponent_move, prefix)
        new_score_lookup[(bot_move, new_opponent_move)] = v

    return new_score_lookup


def pick_safest_move_from_battles(battles):
    all_scores = dict()
    for i, b in enumerate(battles):
        state = b.create_state()
        mutator = StateMutator(state)
        user_options, opponent_options = b.get_all_options()
        logger.debug("Searching through the state: {}".format(mutator.state))
        scores = get_payoff_matrix(mutator, user_options, opponent_options, depth=config.search_depth, prune=True)

        prefixed_scores = prefix_opponent_move(scores, str(i))
        all_scores = {**all_scores, **prefixed_scores}

    decision, payoff = pick_safest(all_scores, remove_guaranteed=True)
    bot_choice = decision[0]
    logger.debug("Safest: {}, {}".format(bot_choice, payoff))
    return bot_choice


def pick_yamper_move(battles):
    bot_choice = None
    for _, b in enumerate(battles):
        state = b.create_state()
        mutator = StateMutator(state)
        user_options, _ = b.get_all_options()
        logger.debug("Searching through the state: {}".format(mutator.state))
        bot_choice = ask_yamper(user_options, b.opponent.active.base_name)

    return bot_choice


def ask_yamper(user_options, opponent_pokemon):

    attack = False
    switch = False
    switch_options = [s for s in [a for a in user_options if "switch" in a]]
    attack_options = [a for a in user_options if "switch" not in a]
    bot_choice = None
    logger.info("User options: " + ", ".join(user_options))

    # If I can both switch or attack then I let decide Yamper
    if switch_options and attack_options:
        request = f"Oponent is a {opponent_pokemon}. Do you prefer attack or switch Pokemon?"
        logger.info("Request: " + request)
        model_parameters = {"text": request, "length": 24, "temperature": 0.3, "topK": 50, "topP": 0.9}

        valid = False
        while (not valid):
            response = banana.run(os.environ['BANANA_API_KEY'], "gptj", model_parameters)["modelOutputs"][0]["output"].lower().strip()
            logger.debug(response)
            attack = "attack" in response
            switch = "switch" in response
            valid = attack ^ switch
        logger.info(f"Response: {response}")
        logger.debug(f"Attack = {attack}; Switch = {switch}")

    
    if attack or not switch_options:
        request = "Pick one of the following: " + ", ".join(attack_options)
        request = request.replace(request[request.rindex(','):], " or" + request[request.rindex(',')+1:]) if "," in request else request
        bot_choice, response = get_valid_response(request, attack_options)
            
    if switch or not attack_options:
        request = "Pick one of the following: " + ", ".join(s.replace("switch ", "") for s in switch_options)
        request = request.replace(request[request.rindex(','):], " or" + request[request.rindex(',')+1:]) if "," in request else request
        bot_choice, response = get_valid_response(request, switch_options)

    return bot_choice


def get_valid_response(request, options):
    logger.info("Request: " + request)
    model_parameters = {"text": request, "length": 30, "temperature": 0.3, "topK": 50, "topP": 0.8}
    response = None
    bot_choice = None
    while (bot_choice is None):
        logger.debug("Request: " + request)
        response = banana.run(os.environ['BANANA_API_KEY'], "gptj", model_parameters)["modelOutputs"][0]["output"].lower().strip()
        logger.debug("Request: " + response)
        choice = [a for a in options if a.replace("switch ", "") in response]
        bot_choice = choice[0] if len(choice) == 1 else bot_choice
    logger.info("Response: " + response)
    logger.info("Bot choice: " + bot_choice)
    return bot_choice, response


def pick_safest_move_using_dynamic_search_depth(battles):
    """
    Dynamically decides how far to look into the game.

    This requires a strong computer to be able to search 3/4 turns ahead.
    Using a pypy interpreter will also result in better performance.

    """
    all_scores = dict()
    num_battles = len(battles)

    if num_battles > 1:
        search_depth = 2

        for i, b in enumerate(battles):
            state = b.create_state()
            mutator = StateMutator(state)
            user_options, opponent_options = b.get_all_options()
            logger.debug("Searching through the state: {}".format(mutator.state))
            scores = get_payoff_matrix(mutator, user_options, opponent_options, depth=search_depth, prune=True)
            prefixed_scores = prefix_opponent_move(scores, str(i))
            all_scores = {**all_scores, **prefixed_scores}

    elif num_battles == 1:
        search_depth = 3

        b = battles[0]
        state = b.create_state()
        mutator = StateMutator(state)
        user_options, opponent_options = b.get_all_options()

        num_user_options = len(user_options)
        num_opponent_options = len(opponent_options)
        options_product = num_user_options * num_opponent_options
        if options_product < 20 and num_user_options > 1 and num_opponent_options > 1:
            logger.debug("Low options product, looking an additional depth")
            search_depth += 1

        logger.debug("Searching through the state: {}".format(mutator.state))
        logger.debug("Options Product: {}".format(options_product))
        logger.debug("My Options: {}".format(user_options))
        logger.debug("Opponent Options: {}".format(opponent_options))
        logger.debug("Search depth: {}".format(search_depth))
        all_scores = get_payoff_matrix(mutator, user_options, opponent_options, depth=search_depth, prune=True)

    else:
        raise ValueError("less than 1 battle?: {}".format(battles))

    decision, payoff = pick_safest(all_scores, remove_guaranteed=True)
    bot_choice = decision[0]
    logger.debug("Safest: {}, {}".format(bot_choice, payoff))
    logger.debug("Depth: {}".format(search_depth))
    return bot_choice


if config.dynamic_search_depth:
    pick_safest_move_from_battles = pick_safest_move_using_dynamic_search_depth
