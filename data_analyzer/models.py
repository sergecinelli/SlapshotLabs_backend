import datetime
from sqlalchemy import create_engine, select
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.orm.session import Session

class Models:
    def __init__(self, db_conn_str: str):
        self._dbbase = automap_base()
        self._dbengine = create_engine(db_conn_str)
        self._dbbase.prepare(self._dbengine)
        
        self.Goalie = self._dbbase.classes.goalies
        self.Player = self._dbbase.classes.players
        self.Team = self._dbbase.classes.teams

        self.Game = self._dbbase.classes.games

        # Game-players many-to-many tables.
        self.GameHomeGoalie = self._dbbase.classes.games_home_goalies
        self.GameHomePlayer = self._dbbase.classes.games_home_players
        self.GameAwayGoalie = self._dbbase.classes.games_away_goalies
        self.GameAwayPlayer = self._dbbase.classes.games_away_players

        self.GoalieSeason = self._dbbase.classes.goalie_seasons
        self.GoalieTeamSeason = self._dbbase.classes.goalie_team_seasons
        self.PlayerSeason = self._dbbase.classes.player_seasons
        self.PlayerTeamSeason = self._dbbase.classes.player_team_seasons
        self.TeamSeason = self._dbbase.classes.team_seasons

        self.GamePlayer = self._dbbase.classes.game_players
        self.GameGoalie = self._dbbase.classes.game_goalies

        self.GameEvents = self._dbbase.classes.game_events
        self.GameEventsAnalysisQueue = self._dbbase.classes.game_events_analysis_queue

        self.ProcessStatus = self._dbbase.classes.processes_status

        self.session_factory = sessionmaker(autocommit=False, autoflush=False, bind=self._dbengine)

    def new_session(self) -> tuple[Session, scoped_session[Session]]:
        """Creates a new scoped session.
        
        :returns: Session to use in queries and the scoped session object to pass to the `remove_session()` function.
        """
        
        dbsession = scoped_session(self.session_factory)
        session = dbsession()
        return session, dbsession
    
    def remove_session(self, session: Session, dbsession: scoped_session):
        """Closes and removes the scoped session.
        
        :param session: Session which was used in queries.
        :param dbsession: Scoped session to remove.
        """
        
        session.close()
        dbsession.remove()

    def init_player_season(self, season_id: int, player_id: int):
        return self.PlayerSeason(season_id=season_id, player_id=player_id,
            shots_on_goal=0, games_played=0, goals=0, assists=0, scoring_chances=0,
            blocked_shots=0, penalties_drawn=datetime.timedelta(seconds=0), penalty_minutes=datetime.timedelta(seconds=0),
            power_play_goals_diff=0, penalty_kill_diff=0, five_on_five_diff=0,
            overall_diff=0, short_handed_goals=0, power_play_goals=0,
            turnovers=0, faceoffs=0, faceoffs_won=0)

    def init_player_team_season(self, season_id: int, player_id: int, team_id: int):
        return self.PlayerTeamSeason(season_id=season_id, team_id=team_id, player_id=player_id,
            shots_on_goal=0, games_played=0, goals=0, assists=0, scoring_chances=0,
            blocked_shots=0, penalties_drawn=datetime.timedelta(seconds=0), penalty_minutes=datetime.timedelta(seconds=0),
            power_play_goals_diff=0, penalty_kill_diff=0, five_on_five_diff=0,
            overall_diff=0, short_handed_goals=0, power_play_goals=0,
            turnovers=0, faceoffs=0, faceoffs_won=0)

    def init_game_player(self, game_id: int, player_id: int):
        return self.GamePlayer(game_id=game_id, player_id=player_id,
            goals=0, assists=0, shots_on_goal=0, scoring_chances=0, blocked_shots=0,
            short_handed_goals=0, power_play_goals=0, penalties_drawn=datetime.timedelta(seconds=0),
            penalty_minutes=datetime.timedelta(seconds=0), turnovers=0, faceoffs=0, faceoffs_won=0)

    def init_goalie_season(self, season_id: int, goalie_id: int):
        return self.GoalieSeason(season_id=season_id, goalie_id=goalie_id,
            shots_on_goal=0, saves=0, goals_against=0, games_played=0,
            wins=0, losses=0, goals=0, assists=0, penalty_minutes=datetime.timedelta(seconds=0),
            short_handed_goals_against=0, power_play_goals_against=0)

    def init_goalie_team_season(self, season_id: int, goalie_id: int, team_id: int):
        return self.GoalieTeamSeason(season_id=season_id, goalie_id=goalie_id, team_id=team_id,
            shots_on_goal=0, saves=0, goals_against=0, games_played=0,
            wins=0, losses=0, goals=0, assists=0, penalty_minutes=datetime.timedelta(seconds=0),
            short_handed_goals_against=0, power_play_goals_against=0)

    def init_game_goalie(self, game_id: int, goalie_id: int):
        return self.GameGoalie(game_id=game_id, goalie_id=goalie_id, shots_on_goal=0,
            goals_against=0, saves=0, penalty_minutes=datetime.timedelta(seconds=0),
            short_handed_goals_against=0, power_play_goals_against=0)

    def init_team_season(self, season_id: int, team_id: int):
        return self.TeamSeason(season_id=season_id, team_id=team_id,
            games_played=0, wins=0, losses=0, ties=0, goals_for=0, goals_against=0)
