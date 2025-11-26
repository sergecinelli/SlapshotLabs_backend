import datetime
import json
import os
import configparser
import time
from typing import Any, Final
from sqlalchemy import select, update
from sqlalchemy.orm import scoped_session
import traceback

from constants import GameEventSystemStatus
from models import Models

app_path = os.path.dirname(os.path.realpath(__file__))
config = configparser.ConfigParser()
session = None
m = None
log = None

class EventAction:
    ADDED = 1
    UPDATED = 2
    DELETED = 3

# region Logging functions.

def write_log(message: str) -> None:
    """Writes a log message to the database."""

    log_msg = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S") + " - " + message
    
    print(log_msg)

    log_arr = []
    process_status = session.scalar(select(m.ProcessStatus).where(m.ProcessStatus.name == "game_events_analyzer"))
    
    log_arr = process_status.log.split("\n")
    
    while len(log_arr) > 10000:
        log_arr.pop()
        
    log_arr.insert(0, log_msg)
    
    process_status.log = "\n".join(log_arr)

def print_console(message: str) -> None:
    """Prints a message to the console."""
    
    print((datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S") + " - " + message))

# endregion

def form_missing_person_message(person: str, event: dict[str, Any]) -> str:
    """Forms a message for a missing person.
    
    :param person: The person type (goalie or player).
    :param event: The game event.
    :returns: A message for a missing person.
    """
    
    return f"ERROR: No {person} specified for \"{event['event_name']}\" event {event['id']}."

def analyze_game_event(event: dict[str, Any], is_add: bool) -> str | None:
    """Analyzes a game event and updates the player and goalie season statistics.
    
    :param event: The game event to analyze.
    :returns: An error message if an error occurs, otherwise None.
    """

    # region Get goalie_season, goalie_game, player_season, player_game, player_2_season, player_2_game.

    season_id = event['game_season_id']

    is_add_goalie_season = False
    is_add_goalie_game = False
    if event['goalie_id'] is not None:
        goalie_season = session.scalar(select(m.GoalieSeason).where(
            m.GoalieSeason.season_id == season_id, m.GoalieSeason.goalie_id == event['goalie_id']))
        if goalie_season is None:
            goalie_season = m.init_goalie_season(season_id, event['goalie_id'])
            is_add_goalie_season = True
        goalie_game = session.scalar(select(m.GameGoalie).where(
            m.GameGoalie.game_id == event['game_id'], m.GameGoalie.goalie_id == event['goalie_id']))
        if goalie_game is None:
            goalie_game = m.init_game_goalie(event['game_id'], event['goalie_id'])
            is_add_goalie_game = True
    else:
        goalie_season = None
        goalie_game = None

    is_add_player_season = False
    is_add_player_game = False
    if event['player_id'] is not None:
        player_season = session.scalar(select(m.PlayerSeason).where(
            m.PlayerSeason.season_id == season_id, m.PlayerSeason.player_id == event['player_id']))
        if player_season is None:
            player_season = m.init_player_season(season_id, event['player_id'])
            is_add_player_season = True
        player_game = session.scalar(select(m.GamePlayer).where(
            m.GamePlayer.game_id == event['game_id'], m.GamePlayer.player_id == event['player_id']))
        if player_game is None:
            player_game = m.init_game_player(event['game_id'], event['player_id'])
            is_add_player_game = True
    else:
        player_season = None
        player_game = None

    is_add_player_2_season = False
    is_add_player_2_game = False
    if event['player_2_id'] is not None:
        player_2_season = session.scalar(select(m.PlayerSeason).where(
            m.PlayerSeason.season_id == season_id, m.PlayerSeason.player_id == event['player_2_id']))
        if player_2_season is None:
            player_2_season = m.init_player_season(season_id, event['player_2_id'])
            is_add_player_2_season = True
        player_2_game = session.scalar(select(m.GamePlayer).where(
            m.GamePlayer.game_id == event['game_id'], m.GamePlayer.player_id == event['player_2_id']))
        if player_2_game is None:
            player_2_game = m.init_game_player(event['game_id'], event['player_2_id'])
            is_add_player_2_game = True
    else:
        player_2_season = None
        player_2_game = None

    # endregion

    # region Analyze event

    diff = (1 if is_add else -1)

    if event['event_name'] == "shot on goal":

        if player_season is None:
            return form_missing_person_message("player", event)
        if goalie_season is None:
            return form_missing_person_message("goalie", event)

        goalie_season.shots_on_goal += diff
        # goalie_game.shots_on_goal += diff
        player_season.shots_on_goal += diff
        player_game.shots_on_goal += diff

        if event['is_scoring_chance']:
            player_season.scoring_chances += diff
            player_game.scoring_chances += diff

        if event['shot_type'] == "goal":

            player_season.goals += diff
            player_game.goals += diff

            if player_2_season is not None:
                player_2_season.assists += diff
                player_2_game.assists += diff

            goalie_season.goals_against += diff
            goalie_game.goals_against += diff

            if event['goal_type'] == "Short Handed":
                player_season.short_handed_goals += diff
                player_game.short_handed_goals += diff
                goalie_season.short_handed_goals_against += diff
                goalie_game.short_handed_goals_against += diff
            elif event['goal_type'] == "Power Play":
                player_season.power_play_goals += diff
                player_game.power_play_goals += diff
                goalie_season.power_play_goals_against += diff
                goalie_game.power_play_goals_against += diff

        elif event['shot_type'] == "blocked":

            if player_2_season is None:
                return form_missing_person_message("second player", event)

            player_2_season.blocked_shots += diff
            player_2_game.blocked_shots += diff

        elif event['shot_type'] == "save":

            goalie_season.saves += diff
            goalie_game.saves += diff

    elif event['event_name'] == "turnover":

        if player_season is None:
            return form_missing_person_message("player", event)

        player_season.turnovers += diff
        player_game.turnovers += diff

    elif event['event_name'] == 'faceoff':

        if player_season is None:
            return form_missing_person_message("player", event)

        player_season.faceoffs += diff
        player_game.faceoffs += diff
        player_2_season.faceoffs += diff
        player_2_game.faceoffs += diff

        player_season.faceoffs_won += diff
        player_game.faceoffs_won += diff

    elif event['event_name'] == "penalty":

        if goalie_season is None and player_season is None:
            return form_missing_person_message("goalie or player", event)

        time_length = datetime.timedelta(seconds=event['time_length'])

        penalty_minutes = (-time_length if not is_add else time_length)

        if goalie_season is not None:
            goalie_season.penalty_minutes += penalty_minutes
            goalie_game.penalty_minutes += penalty_minutes

        if player_season is not None:
            player_season.penalty_minutes += penalty_minutes
            player_game.penalty_minutes += penalty_minutes

        if player_2_season is not None:
            player_2_season.penalties_drawn += penalty_minutes
            player_2_game.penalties_drawn += penalty_minutes

    # endregion

    # region Add new entries to the database.

    if is_add_goalie_season:
        session.add(goalie_season)
    if is_add_goalie_game:
        session.add(goalie_game)

    if is_add_player_season:
        session.add(player_season)
    if is_add_player_game:
        session.add(player_game)

    if is_add_player_2_season:
        session.add(player_2_season)
    if is_add_player_2_game:
        session.add(player_2_game)

    # endregion

def analyze_game(game: dict[str, Any], is_add: bool) -> str | None:
    """Analyzes the game scoped events: win/loss/tie.
    
    :param game: The game to analyze.
    :returns: An error message if an error occurs, otherwise None.
    """

    diff = (1 if is_add else -1)
    
    season_id = game['season_id']

    home_team_id = game['home_team_id']
    away_team_id = game['away_team_id']

    home_team_season = session.scalar(select(m.TeamSeason).where(
        m.TeamSeason.season_id == season_id, m.TeamSeason.team_id == home_team_id))
    away_team_season = session.scalar(select(m.TeamSeason).where(
        m.TeamSeason.season_id == season_id, m.TeamSeason.team_id == away_team_id))

    if home_team_season is None:
        home_team_season = m.init_team_season(season_id, home_team_id)
        session.add(home_team_season)
        session.commit()
    if away_team_season is None:
        away_team_season = m.init_team_season(season_id, away_team_id)
        session.add(away_team_season)
        session.commit()

    home_goalies_on_ice = ([game['home_start_goalie_id']] +
        [evt['goalie_id'] for evt in game['events'] if (evt['event_name'] == "goalie change" and evt['team_id'] == game['home_team_id'])])
    away_goalies_on_ice = ([game['away_start_goalie_id']] +
        [evt['goalie_id'] for evt in game['events'] if (evt['event_name'] == "goalie change" and evt['team_id'] == game['away_team_id'])])

    last_home_goalie_id = home_goalies_on_ice[-1]
    last_away_goalie_id = away_goalies_on_ice[-1]

    for game_home_goalie_id in game['home_goalies']:

        # region Get home_goalie_season, home_goalie_game.

        is_add_home_goalie_season = False
        is_add_home_goalie_game = False
        home_goalie_season = session.scalar(select(m.GoalieSeason).where(
            m.GoalieSeason.season_id == season_id, m.GoalieSeason.goalie_id == game_home_goalie_id))
        if home_goalie_season is None:
            home_goalie_season = m.init_goalie_season(season_id, game_home_goalie_id)
            is_add_home_goalie_season = True
        home_goalie_game = session.scalar(select(m.GameGoalie).where(
            m.GameGoalie.game_id == game['id'], m.GameGoalie.goalie_id == game_home_goalie_id))
        if home_goalie_game is None:
            home_goalie_game = m.init_game_goalie(game['id'], game_home_goalie_id)
            is_add_home_goalie_game = True

        # endregion

        if home_goalie_season.goalie_id in home_goalies_on_ice:
            home_goalie_season.games_played += diff

        if game['away_goals'] > game['home_goals'] and home_goalie_season.goalie_id == game['home_start_goalie_id']:
            # The goalie that started the game in net gets the loss if the team loses the game.
            home_goalie_season.losses += diff

        elif game['away_goals'] < game['home_goals'] and home_goalie_season.goalie_id == last_home_goalie_id:
            # The goalie that finishes the game in net gets the win if the team wins the game.
            home_goalie_season.wins += diff

        if is_add_home_goalie_season:
            session.add(home_goalie_season)
        if is_add_home_goalie_game:
            session.add(home_goalie_game)

    for game_away_goalie_id in game['away_goalies']:

        # region Get away_goalie_season, away_goalie_game.

        is_add_away_goalie_season = False
        is_add_away_goalie_game = False
        away_goalie_season = session.scalar(select(m.GoalieSeason).where(
            m.GoalieSeason.season_id == season_id, m.GoalieSeason.goalie_id == game_away_goalie_id))
        if away_goalie_season is None:
            away_goalie_season = m.init_goalie_season(season_id, game_away_goalie_id)
            is_add_away_goalie_season = True
        away_goalie_game = session.scalar(select(m.GameGoalie).where(
            m.GameGoalie.game_id == game['id'], m.GameGoalie.goalie_id == game_away_goalie_id))
        if away_goalie_game is None:
            away_goalie_game = m.init_game_goalie(game['id'], game_away_goalie_id)
            is_add_away_goalie_game = True

        # endregion

        if away_goalie_season.goalie_id in away_goalies_on_ice:
            away_goalie_season.games_played += diff

        if game['home_goals'] > game['away_goals'] and away_goalie_season.goalie_id == game['away_start_goalie_id']:
            # The goalie that started the game in net gets the loss if the team loses the game.
            away_goalie_season.losses += diff

        elif game['home_goals'] < game['away_goals'] and away_goalie_season.goalie_id == last_away_goalie_id:
            # The goalie that finishes the game in net gets the win if the team wins the game.
            away_goalie_season.wins += diff

        if is_add_away_goalie_season:
            session.add(away_goalie_season)
        if is_add_away_goalie_game:
            session.add(away_goalie_game)

    for game_home_player_id in game['home_players']:

        # region Get home_player_season, home_player_game.

        is_add_home_player_season = False
        is_add_home_player_game = False
        home_player_season = session.scalar(select(m.PlayerSeason).where(
            m.PlayerSeason.season_id == season_id, m.PlayerSeason.player_id == game_home_player_id))
        if home_player_season is None:
            home_player_season = m.init_player_season(season_id, game_home_player_id)
            is_add_home_player_season = True
        home_player_game = session.scalar(select(m.GamePlayer).where(
            m.GamePlayer.game_id == game['id'], m.GamePlayer.player_id == game_home_player_id))
        if home_player_game is None:
            home_player_game = m.init_game_player(game['id'], game_home_player_id)
            is_add_home_player_game = True

        # endregion

        home_player_season.games_played += diff

        if is_add_home_player_season:
            session.add(home_player_season)
        if is_add_home_player_game:
            session.add(home_player_game)

    for game_away_player_id in game['away_players']:

        # region Get away_player_season, away_player_game.

        is_add_away_player_season = False
        is_add_away_player_game = False
        away_player_season = session.scalar(select(m.PlayerSeason).where(
            m.PlayerSeason.season_id == season_id, m.PlayerSeason.player_id == game_away_player_id))
        if away_player_season is None:
            away_player_season = m.init_player_season(season_id, game_away_player_id)
            is_add_away_player_season = True
        away_player_game = session.scalar(select(m.GamePlayer).where(
            m.GamePlayer.game_id == game['id'], m.GamePlayer.player_id == game_away_player_id))
        if away_player_game is None:
            away_player_game = m.init_game_player(game['id'], game_away_player_id)
            is_add_away_player_game = True

        # endregion

        away_player_season.games_played += diff

        if is_add_away_player_season:
            session.add(away_player_season)
        if is_add_away_player_game:
            session.add(away_player_game)

    home_team_season.games_played += diff
    away_team_season.games_played += diff

    if game['home_goals'] > game['away_goals']:
        home_team_season.wins += diff
        away_team_season.losses += diff
    elif game['home_goals'] < game['away_goals']:
        home_team_season.losses += diff
        away_team_season.wins += diff
    else:
        home_team_season.ties += diff
        away_team_season.ties += diff
    
    home_team_season.goals_for += game['home_goals']
    away_team_season.goals_for += game['away_goals']
    home_team_season.goals_against += game['away_goals']
    away_team_season.goals_against += game['home_goals']


try:
    warning_msgs = []
    config.read(f"{app_path}/settings.ini")
    m = Models(f'postgresql://{os.getenv("DB_USER")}:{os.getenv("DB_PASSWORD")}@{os.getenv("DB_HOST")}:{os.getenv("DB_PORT")}/{os.getenv("DB_NAME_HOCKEY")}?sslmode={os.getenv("SSLMODE")}')
    session, dbsession = m.new_session()

    process_status = session.scalar(select(m.ProcessStatus).where(m.ProcessStatus.name == "game_events_analyzer"))
    if process_status is None:
        process_status = m.ProcessStatus(name="game_events_analyzer", log="")
        session.add(process_status)
    process_status.status = "RUNNING"
    process_status.last_updated = datetime.datetime.now(datetime.timezone.utc)
    session.commit()

    res = None

    events = session.scalars(select(m.GameEventsAnalysisQueue).where(m.GameEventsAnalysisQueue.error_message == None).\
        order_by(m.GameEventsAnalysisQueue.date_time)).all()
    
    for event in events:
        error_messages = []
        payload = json.loads(event.payload)

        if payload['type'] == 'game':

            if event.status not in [GameEventSystemStatus.NEW, GameEventSystemStatus.DEPRECATED]:
                error_messages.append(f"ERROR: Game {event.id} has an unknown status: {event.status}.")
                continue

            is_add = (event.status == GameEventSystemStatus.NEW)

            for payload_event in payload['events']:
                error_message = analyze_game_event(payload_event, is_add)
                if error_message is not None:
                    error_messages.append(error_message)
                    break
            if len(error_messages) == 0:
                error_message = analyze_game(payload, is_add)
                if error_message is not None:
                    error_messages.append(error_message)

            if len(error_messages) > 0:
                error_message = '\n'.join(error_messages)

        elif payload['type'] == 'game_event':

            if event.status not in [GameEventSystemStatus.NEW, GameEventSystemStatus.DEPRECATED]:
                error_messages.append(f"ERROR: Game event {event.id} has an unknown status: {event.status}.")
                continue

            is_add = (event.status == GameEventSystemStatus.NEW)
            error_message = analyze_game_event(payload, is_add)
                
        else:
            error_message = f"ERROR: Event {event.id} has no game event or game."
        
        if error_message is not None:
            event.error_message = error_message
            write_log(f'ERROR: {error_message}')
        else:
            status_str = "Applied" if event.status == GameEventSystemStatus.NEW else "Deleted"
            session.delete(event)
            write_log(f'INFO: {status_str} {payload["type"]} {payload["id"]}.')
        
        session.commit()

    session.execute(update(m.ProcessStatus).where(m.ProcessStatus.name == "game_events_analyzer").\
        values(status="OK", last_finished=datetime.datetime.now(datetime.timezone.utc)))
    session.commit()

except Exception as e:
    write_log(f"ERROR: {traceback.format_exc()}")
    session.execute(update(m.ProcessStatus).where(m.ProcessStatus.name == "game_events_analyzer").\
        values(status="ERROR", last_finished=datetime.datetime.now(datetime.timezone.utc)))
    session.commit()
finally:
    if session is not None: m.remove_session(session, dbsession)
    time.sleep(3)