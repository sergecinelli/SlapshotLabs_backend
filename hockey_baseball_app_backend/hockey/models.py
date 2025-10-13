from django.db import models
from django.db.models import Case, ExpressionWrapper, When, Value, F

class TeamLevel(models.Model):

    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "team_levels"

class Division(models.Model):

    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "divisions"

class Season(models.Model):

    name = models.CharField(max_length=11)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "seasons"

class Team(models.Model):

    age_group = models.CharField(max_length=3)
    level = models.ForeignKey(TeamLevel, on_delete=models.RESTRICT)
    division = models.ForeignKey(Division, on_delete=models.RESTRICT)
    name = models.CharField(max_length=150)
    logo = models.ImageField(upload_to='team_logo/')
    city = models.CharField(max_length=100)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "teams"

        constraints = [
            models.UniqueConstraint(
                fields=['name', 'city'],
                name='unique_team'
            )
        ]
    
class TeamSeason(models.Model):

    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    season = models.ForeignKey(Season, on_delete=models.RESTRICT)

    games_played = models.IntegerField()
    """Games played in the season."""

    goals_for = models.IntegerField()
    goals_against = models.IntegerField()
    wins = models.IntegerField()
    losses = models.IntegerField()
    ties = models.IntegerField()

    def __str__(self):
        return f'{self.team.name} - {self.season}/{(self.season + 1)}'

    class Meta:
        db_table = "team_seasons"

class PlayerPosition(models.Model):

    name = models.CharField(max_length=20)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "player_positions"

class Goalie(models.Model):

    team = models.ForeignKey(Team, null=True, on_delete=models.SET_NULL)
    position = models.ForeignKey(PlayerPosition, on_delete=models.RESTRICT)
    height = models.IntegerField()
    weight = models.IntegerField()
    shoots = models.CharField(max_length=1, choices=[('L', 'Left Shot'), ('R', 'Right Shot')])
    jersey_number = models.IntegerField()
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    birth_year = models.DateField()
    shots_on_goal = models.IntegerField(default=0)
    saves = models.IntegerField(default=0)
    goals_against = models.IntegerField(default=0)
    games_played = models.IntegerField(default=0)
    wins = models.IntegerField()
    losses = models.IntegerField()
    goals = models.IntegerField(default=0)
    assists = models.IntegerField(default=0)

    short_handed_goals_against = models.IntegerField("SHGA", default=0)
    """SHGA field."""

    power_play_goals_against = models.IntegerField("PPGA", default=0)
    """PPGA field."""

    saves_above_avg = models.IntegerField(default=0)    # Not used.

    shots_on_goal_per_game = models.GeneratedField(
        expression=Case(When(games_played__gt=0, then=(F('shots_on_goal') / F('games_played'))),
                        default=Value(0), output_field=models.FloatField()),
        output_field=models.FloatField(),
        db_persist=True)

    points = models.GeneratedField(
        expression=F('goals') + F('assists'),
        output_field=models.IntegerField(),
        db_persist=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    class Meta:
        db_table = "goalies"

class GoalieTransaction(models.Model):

    goalie = models.ForeignKey(Goalie, on_delete=models.CASCADE)
    season = models.ForeignKey(Season, on_delete=models.RESTRICT)
    date = models.DateField()
    team = models.ForeignKey(Team, on_delete=models.RESTRICT)
    number = models.IntegerField()
    description = models.TextField()

    def __str__(self):
        return f"{self.goalie.first_name} {self.goalie.last_name} - {self.season}/{(self.season + 1)}"

    class Meta:
        db_table = "goalie_transactions"

class Player(models.Model):

    team = models.ForeignKey(Team, null=True, on_delete=models.SET_NULL)
    position = models.ForeignKey(PlayerPosition, on_delete=models.RESTRICT)
    height = models.IntegerField()
    weight = models.IntegerField()
    shoots = models.CharField(max_length=1, choices=[('L', 'Left Shot'), ('R', 'Right Shot')])
    number = models.IntegerField()
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    birth_year = models.DateField()
    shots_on_goal = models.IntegerField(default=0)
    games_played = models.IntegerField(default=0)
    goals = models.IntegerField(default=0)
    assists = models.IntegerField(default=0)
    scoring_chances = models.IntegerField(default=0)
    blocked_shots = models.IntegerField(default=0)
    penalties_drawn = models.IntegerField()
    penalties_taken = models.IntegerField()

    power_play_goals_diff = models.IntegerField("PP +/-", default=0)
    """PP +/- field."""

    penalty_kill_diff = models.IntegerField("PK +/-", default=0)
    """PK +/- field."""

    five_on_five_diff = models.IntegerField("5v5 +/-", default=0)
    """5v5 +/- field."""

    overall_diff = models.IntegerField("Overall +/-", default=0)
    """Overall +/- field."""

    shots_on_goal_per_game = models.GeneratedField(
        expression=Case(When(games_played__gt=0, then=(F('shots_on_goal') / F('games_played'))),
                        default=Value(0), output_field=models.FloatField()),
        output_field=models.FloatField(),
        db_persist=True)

    points = models.GeneratedField(
        expression=F('goals') + F('assists'),
        output_field=models.IntegerField(),
        db_persist=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    class Meta:
        db_table = "players"

class PlayerTransaction(models.Model):

    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    season = models.ForeignKey(Season, on_delete=models.RESTRICT)
    date = models.DateField()
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    number = models.IntegerField()
    description = models.TextField()

    def __str__(self):
        return f"{self.player.first_name} {self.player.last_name} - {self.season}/{(self.season + 1)}"

    class Meta:
        db_table = "player_transactions"

class Arena(models.Model):

    name = models.CharField(max_length=150)
    address = models.TextField()

    def __str__(self):
        return self.name

    class Meta:
        db_table = "arenas"
    
class ArenaRink(models.Model):

    name = models.CharField(max_length=150)
    arena = models.ForeignKey(Arena, on_delete=models.CASCADE)

    def __str__(self):
        return f"\"{self.arena.name}\" - \"{self.name}\""

    class Meta:
        db_table = "arena_rinks"

class DefensiveZoneExit(models.Model):

    icing = models.IntegerField()
    skate_out = models.IntegerField()
    so_win = models.IntegerField("SO & Win")
    so_lose = models.IntegerField("SO & Lose")
    passes = models.IntegerField("Pass")

    def __str__(self):
        return f'{str(self.game)} - DefensiveZoneExit'

    class Meta:
        db_table = "defensive_zone_exit"

class OffensiveZoneEntry(models.Model):

    pass_in = models.IntegerField("Pass")
    dump_win = models.IntegerField("Dump/W")
    dump_lose = models.IntegerField("Dump/L")
    skate_in = models.IntegerField()

    def __str__(self):
        return f'{str(self.game)} - OffensiveZoneEntry'

    class Meta:
        db_table = "offensive_zone_entry"

class Shots(models.Model):

    shots_on_goal = models.IntegerField()
    missed_net = models.IntegerField()
    scoring_chance = models.IntegerField()
    blocked = models.IntegerField()

    def __str__(self):
        return f'{str(self.game)} - Shots'

    class Meta:
        db_table = "shots"

class Turnovers(models.Model):

    off_zone = models.IntegerField()
    neutral_zone = models.IntegerField()
    def_zone = models.IntegerField()

    def __str__(self):
        return f'{str(self.game)} - Turnovers'

    class Meta:
        db_table = "turnovers"

class GameType(models.Model):

    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name
    
    class Meta:
        db_table = "game_types"

class GamePeriod(models.Model):

    name = models.CharField(max_length=10)

    def __str__(self):
        return self.name
    
    class Meta:
        db_table = "game_periods"

class Game(models.Model):

    GAME_STATUSES = [
        (1, 'Not Started'),
        (2, 'Game in Progress'),
        (3, 'Game Over'),
    ]

    home_team = models.ForeignKey(Team, related_name='home_games', on_delete=models.RESTRICT)
    home_goals = models.IntegerField()
    home_team_goalie = models.ForeignKey(Goalie, related_name='home_games', on_delete=models.RESTRICT, null=True, blank=True)   # TODO: make not null
    away_team = models.ForeignKey(Team, related_name='away_games', on_delete=models.RESTRICT)
    away_goals = models.IntegerField()
    away_team_goalie = models.ForeignKey(Goalie, related_name='away_games', on_delete=models.RESTRICT, null=True, blank=True)   # TODO: make not null
    game_type = models.ForeignKey(GameType, on_delete=models.RESTRICT)
    tournament_name = models.CharField(max_length=150, null=True, blank=True)
    status = models.IntegerField(choices=GAME_STATUSES)
    date = models.DateField()
    time = models.TimeField()
    rink = models.ForeignKey(ArenaRink, on_delete=models.RESTRICT)

    # Dashboard fields.

    game_period = models.ForeignKey(GamePeriod, on_delete=models.RESTRICT)
    game_type_group = models.CharField(max_length=10)

    home_faceoff_win = models.IntegerField("Home Faceoff Win %")
    home_defensive_zone_exit = models.OneToOneField(DefensiveZoneExit, related_name='home_game', on_delete=models.RESTRICT)
    home_offensive_zone_entry = models.OneToOneField(OffensiveZoneEntry, related_name='home_game', on_delete=models.RESTRICT)
    home_shots = models.OneToOneField(Shots, related_name='home_game', on_delete=models.RESTRICT)
    home_turnovers = models.OneToOneField(Turnovers, related_name='home_game', on_delete=models.RESTRICT)

    away_faceoff_win = models.IntegerField("Away Faceoff Win %")
    away_defensive_zone_exit = models.OneToOneField(DefensiveZoneExit, related_name='away_game', on_delete=models.RESTRICT)
    away_offensive_zone_entry = models.OneToOneField(OffensiveZoneEntry, related_name='away_game', on_delete=models.RESTRICT)
    away_shots = models.OneToOneField(Shots, related_name='away_game', on_delete=models.RESTRICT)
    away_turnovers = models.OneToOneField(Turnovers, related_name='away_game', on_delete=models.RESTRICT)

    def __str__(self):
        return f'"{self.home_team.name}" - "{self.away_team.name}" - {str(self.date)} {str(self.time)}'

    class Meta:
        db_table = "games"

class GamePlayer(models.Model):

    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    player = models.ForeignKey(Player, on_delete=models.RESTRICT)
    goals = models.IntegerField()
    assists = models.IntegerField()
    shots = models.IntegerField()

    def __str__(self):
        return f'{str(self.game)} - {self.player.first_name} {self.player.last_name}'

    class Meta:
        db_table = "game_players"

class GameGoalie(models.Model):

    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    goalie = models.ForeignKey(Goalie, on_delete=models.RESTRICT)
    goals_against = models.IntegerField()
    saves = models.IntegerField()

    def __str__(self):
        return f'{str(self.game)} - {self.goalie.first_name} {self.goalie.last_name}'

    class Meta:
        db_table = "game_goalies"
    
class GameEventName(models.Model):

    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "game_event_names"

class GameEvents(models.Model):

    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    number = models.IntegerField()
    event_name = models.ForeignKey(GameEventName, on_delete=models.CASCADE)
    time = models.TimeField(auto_now=False, auto_now_add=False)
    period = models.ForeignKey(GamePeriod, on_delete=models.RESTRICT)
    team = models.ForeignKey(Team, on_delete=models.RESTRICT)
    players = models.ManyToManyField(Player)
    goalie = models.ForeignKey(Goalie, on_delete=models.RESTRICT)
    ice_top_offset = models.IntegerField()
    ice_left_offset = models.IntegerField()
    net_top_offset = models.IntegerField()
    net_left_offset = models.IntegerField()
    youtube_link = models.CharField("YouTube Link", max_length=150, null=True, blank=True)

    def __str__(self):
        return f'{str(self.game)} - {self.time}'

    class Meta:
        db_table = "game_events"
