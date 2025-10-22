import datetime
from django.db import models
from django.db.models import Case, ExpressionWrapper, When, Value, F

class PlayerPersonalInformationMixin(models.Model):

    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    birth_year = models.DateField()
    player_bio = models.TextField(null=True, blank=True)

    birthplace_country = models.CharField(max_length=150)

    address_country = models.CharField(max_length=150)
    address_region = models.CharField(max_length=150)
    address_city = models.CharField(max_length=150)
    address_street = models.TextField()
    address_postal_code = models.CharField(max_length=50)

    height = models.IntegerField("Height, inches")
    weight = models.IntegerField("Weight, lbs")
    shoots = models.CharField(max_length=1, choices=[('L', 'Left Shot'), ('R', 'Right Shot')])

    class Meta:
        abstract = True

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

    name = models.CharField(max_length=11, unique=True)

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
        return f'{self.team.name} - {self.season.name}'

    class Meta:
        db_table = "team_seasons"

class PlayerPosition(models.Model):

    name = models.CharField(max_length=20)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "player_positions"

class Goalie(PlayerPersonalInformationMixin, models.Model):

    team = models.ForeignKey(Team, null=True, on_delete=models.SET_NULL)
    jersey_number = models.IntegerField()
    photo = models.ImageField(upload_to='goalie_photo/', null=True, blank=True)
    analysis = models.TextField(null=True, blank=True)

    saves_above_avg = models.IntegerField(default=0)    # Not used.

    shots_on_goal = models.IntegerField(default=0)
    saves = models.IntegerField(default=0)
    goals_against = models.IntegerField(default=0)
    games_played = models.IntegerField(default=0)
    wins = models.IntegerField(default=0)
    losses = models.IntegerField(default=0)
    goals = models.IntegerField(default=0)
    assists = models.IntegerField(default=0)
    penalty_minutes = models.DurationField(default=datetime.timedelta(0))

    short_handed_goals_against = models.IntegerField("SHGA", default=0)
    """SHGA field."""

    power_play_goals_against = models.IntegerField("PPGA", default=0)
    """PPGA field."""

    save_percents = models.GeneratedField(
        expression=Case(When(games_played__gt=0, then=((F('saves') / (F('saves') + F('goals_against'))) * 100)),
                        default=Value(0), output_field=models.FloatField()),
        output_field=models.FloatField(),
        db_persist=True,
        verbose_name="Save %")

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

class GoalieSeason(models.Model):

    goalie = models.ForeignKey(Goalie, on_delete=models.CASCADE)
    season = models.ForeignKey(Season, on_delete=models.RESTRICT)

    shots_on_goal = models.IntegerField(default=0)
    saves = models.IntegerField(default=0)
    goals_against = models.IntegerField(default=0)
    games_played = models.IntegerField(default=0)
    wins = models.IntegerField(default=0)
    losses = models.IntegerField(default=0)
    goals = models.IntegerField(default=0)
    assists = models.IntegerField(default=0)
    penalty_minutes = models.DurationField(default=datetime.timedelta(0))

    short_handed_goals_against = models.IntegerField("SHGA", default=0)
    """SHGA field."""

    power_play_goals_against = models.IntegerField("PPGA", default=0)
    """PPGA field."""

    save_percents = models.GeneratedField(
        expression=Case(When(games_played__gt=0, then=((F('saves') / (F('saves') + F('goals_against'))) * 100)),
                        default=Value(0), output_field=models.FloatField()),
        output_field=models.FloatField(),
        db_persist=True,
        verbose_name="Save %")

    shots_on_goal_per_game = models.GeneratedField(
        expression=Case(When(games_played__gt=0, then=(F('shots_on_goal') / F('games_played'))),
                        default=Value(0), output_field=models.FloatField()),
        output_field=models.FloatField(),
        db_persist=True)

    points = models.GeneratedField(
        expression=F('goals') + F('assists'),
        output_field=models.IntegerField(),
        db_persist=True)

    class Meta:
        db_table = "goalie_seasons"

    def __str__(self):
        return f'{str(self.goalie)} - {self.season.name}'

class GoalieTransaction(models.Model):

    goalie = models.ForeignKey(Goalie, on_delete=models.CASCADE)
    season = models.ForeignKey(Season, on_delete=models.RESTRICT)
    date = models.DateField()
    team = models.ForeignKey(Team, on_delete=models.RESTRICT)
    number = models.IntegerField()
    description = models.TextField()

    def __str__(self):
        return f"{self.goalie.first_name} {self.goalie.last_name} - {self.season.name}"

    class Meta:
        db_table = "goalie_transactions"

class Player(PlayerPersonalInformationMixin, models.Model):

    team = models.ForeignKey(Team, null=True, on_delete=models.SET_NULL)
    position = models.ForeignKey(PlayerPosition, on_delete=models.RESTRICT)
    number = models.IntegerField()
    photo = models.ImageField(upload_to='player_photo/', null=True, blank=True)
    analysis = models.TextField(null=True, blank=True)

    shots_on_goal = models.IntegerField(default=0)
    games_played = models.IntegerField(default=0)
    goals = models.IntegerField(default=0)
    assists = models.IntegerField(default=0)
    scoring_chances = models.IntegerField(default=0)
    blocked_shots = models.IntegerField(default=0)
    penalties_drawn = models.DurationField(default=datetime.timedelta(0))
    penalty_minutes = models.DurationField(default=datetime.timedelta(0))

    power_play_goals_diff = models.IntegerField("PP +/-", default=0)
    """PP +/- field."""

    penalty_kill_diff = models.IntegerField("PK +/-", default=0)
    """PK +/- field."""

    five_on_five_diff = models.IntegerField("5v5 +/-", default=0)
    """5v5 +/- field."""

    overall_diff = models.IntegerField("Overall +/-", default=0)
    """Overall +/- field."""

    short_handed_goals = models.IntegerField("SHG", default=0)
    """SHG field."""

    power_play_goals = models.IntegerField("PPG", default=0)
    """PPG field."""

    faceoffs = models.IntegerField(default=0)
    faceoffs_won = models.IntegerField(default=0)

    turnovers = models.IntegerField(default=0)

    faceoff_win_percents = models.GeneratedField(
        expression=Case(When(games_played__gt=0, then=((F('faceoffs_won') / F('faceoffs'))* 100)),
                        default=Value(0), output_field=models.FloatField()),
        output_field=models.FloatField(),
        db_persist=True,
        verbose_name="Faceoff Win %")

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

class PlayerSeason(models.Model):

    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    season = models.ForeignKey(Season, on_delete=models.RESTRICT)

    shots_on_goal = models.IntegerField(default=0)
    games_played = models.IntegerField(default=0)
    goals = models.IntegerField(default=0)
    assists = models.IntegerField(default=0)
    scoring_chances = models.IntegerField(default=0)
    blocked_shots = models.IntegerField(default=0)
    penalties_drawn = models.DurationField(default=datetime.timedelta(0))
    penalty_minutes = models.DurationField(default=datetime.timedelta(0))

    power_play_goals_diff = models.IntegerField("PP +/-", default=0)
    """PP +/- field."""

    penalty_kill_diff = models.IntegerField("PK +/-", default=0)
    """PK +/- field."""

    five_on_five_diff = models.IntegerField("5v5 +/-", default=0)
    """5v5 +/- field."""

    overall_diff = models.IntegerField("Overall +/-", default=0)
    """Overall +/- field."""

    short_handed_goals = models.IntegerField("SHG", default=0)
    """SHG field."""

    power_play_goals = models.IntegerField("PPG", default=0)
    """PPG field."""

    faceoffs = models.IntegerField(default=0)
    faceoffs_won = models.IntegerField(default=0)

    turnovers = models.IntegerField(default=0)

    faceoff_win_percents = models.GeneratedField(
        expression=Case(When(games_played__gt=0, then=((F('faceoffs_won') / F('faceoffs'))* 100)),
                        default=Value(0), output_field=models.FloatField()),
        output_field=models.FloatField(),
        db_persist=True,
        verbose_name="Faceoff Win %")

    shots_on_goal_per_game = models.GeneratedField(
        expression=Case(When(games_played__gt=0, then=(F('shots_on_goal') / F('games_played'))),
                        default=Value(0), output_field=models.FloatField()),
        output_field=models.FloatField(),
        db_persist=True)

    points = models.GeneratedField(
        expression=F('goals') + F('assists'),
        output_field=models.IntegerField(),
        db_persist=True)

    class Meta:
        db_table = "player_seasons"

    def __str__(self):
        return f'{str(self.player)} - {self.season.name}'

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

    icing = models.IntegerField(default=0)
    skate_out = models.IntegerField(default=0)
    so_win = models.IntegerField("SO & Win", default=0)
    so_lose = models.IntegerField("SO & Lose", default=0)
    passes = models.IntegerField("Pass", default=0)

    def __str__(self):
        return f'{str(self.game)} - DefensiveZoneExit'

    class Meta:
        db_table = "defensive_zone_exit"

class OffensiveZoneEntry(models.Model):

    pass_in = models.IntegerField("Pass", default=0)
    dump_win = models.IntegerField("Dump/W", default=0)
    dump_lose = models.IntegerField("Dump/L", default=0)
    skate_in = models.IntegerField(default=0)

    def __str__(self):
        return f'{str(self.game)} - OffensiveZoneEntry'

    class Meta:
        db_table = "offensive_zone_entry"

class Shots(models.Model):

    shots_on_goal = models.IntegerField(default=0)
    missed_net = models.IntegerField(default=0)
    scoring_chance = models.IntegerField(default=0)
    blocked = models.IntegerField(default=0)

    def __str__(self):
        return f'{str(self.game)} - Shots'

    class Meta:
        db_table = "shots"

class Turnovers(models.Model):

    off_zone = models.IntegerField(default=0)
    neutral_zone = models.IntegerField(default=0)
    def_zone = models.IntegerField(default=0)

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
    home_goals = models.IntegerField(default=0)
    home_team_goalie = models.ForeignKey(Goalie, related_name='home_games', on_delete=models.RESTRICT, null=True, blank=True)   # TODO: make not null
    away_team = models.ForeignKey(Team, related_name='away_games', on_delete=models.RESTRICT)
    away_goals = models.IntegerField(default=0)
    away_team_goalie = models.ForeignKey(Goalie, related_name='away_games', on_delete=models.RESTRICT, null=True, blank=True)   # TODO: make not null
    game_type = models.ForeignKey(GameType, on_delete=models.RESTRICT)
    tournament_name = models.CharField(max_length=150, null=True, blank=True)
    status = models.IntegerField(choices=GAME_STATUSES)
    season = models.ForeignKey(Season, on_delete=models.RESTRICT, null=True, blank=True)
    date = models.DateField()
    time = models.TimeField()
    rink = models.ForeignKey(ArenaRink, on_delete=models.RESTRICT)

    # Dashboard fields.

    game_period = models.ForeignKey(GamePeriod, on_delete=models.RESTRICT, null=True, blank=True)
    game_type_group = models.CharField(max_length=10)

    home_faceoff_win = models.IntegerField("Home Faceoff Win %", null=True, blank=True)
    home_defensive_zone_exit = models.OneToOneField(DefensiveZoneExit, related_name='home_game', on_delete=models.RESTRICT)
    home_offensive_zone_entry = models.OneToOneField(OffensiveZoneEntry, related_name='home_game', on_delete=models.RESTRICT)
    home_shots = models.OneToOneField(Shots, related_name='home_game', on_delete=models.RESTRICT)
    home_turnovers = models.OneToOneField(Turnovers, related_name='home_game', on_delete=models.RESTRICT)

    away_faceoff_win = models.IntegerField("Away Faceoff Win %", null=True, blank=True)
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
    goals = models.IntegerField(default=0)
    assists = models.IntegerField(default=0)
    shots = models.IntegerField(default=0)

    def __str__(self):
        return f'{str(self.game)} - {self.player.first_name} {self.player.last_name}'

    class Meta:
        db_table = "game_players"

class GameGoalie(models.Model):

    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    goalie = models.ForeignKey(Goalie, on_delete=models.RESTRICT)
    goals_against = models.IntegerField(default=0)
    saves = models.IntegerField(default=0)

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
    event_name = models.ForeignKey(GameEventName, on_delete=models.RESTRICT)
    time = models.TimeField(auto_now=False, auto_now_add=False)
    period = models.ForeignKey(GamePeriod, on_delete=models.RESTRICT)
    team = models.ForeignKey(Team, on_delete=models.RESTRICT)
    player = models.ForeignKey(Player, on_delete=models.RESTRICT, null=True, related_name='player')
    player_2 = models.ForeignKey(Player, on_delete=models.RESTRICT, null=True, related_name='player_2')
    goalie = models.ForeignKey(Goalie, on_delete=models.RESTRICT, null=True)

    # Spray chart points.
    ice_top_offset = models.IntegerField(null=True, blank=True)
    ice_left_offset = models.IntegerField(null=True, blank=True)
    net_top_offset = models.IntegerField(null=True, blank=True)
    net_left_offset = models.IntegerField(null=True, blank=True)

    youtube_link = models.CharField("YouTube Link", max_length=1000, null=True, blank=True)

    note = models.TextField(null=True, blank=True)
    time_length = models.DurationField(null=True, blank=True)
    is_faceoff_won = models.BooleanField(null=True, blank=True)

    is_deprecated = models.BooleanField(default=False)

    def __str__(self):
        return f'{str(self.game)} - {self.time}'

    class Meta:
        db_table = "game_events"

class GameEventsAnalysisQueue(models.Model):

    pk = models.CompositePrimaryKey("game_event_id", "date_time")
    game_event = models.ForeignKey(GameEvents, on_delete=models.RESTRICT)
    date_time = models.DateTimeField(auto_now=True)
    
    action = models.IntegerField()
    """1 - added, 2 - updated, 3 - deleted."""

    class Meta:
        db_table = "game_events_analysis_queue"
