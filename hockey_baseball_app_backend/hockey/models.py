import datetime
import inspect
import uuid
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q, Case, DateField, ExpressionWrapper, UniqueConstraint, When, Value, F
from django.db.models.functions import Concat

from hockey.utils.constants import GOALIE_POSITION_NAME, GameStatus, GoalType, IdName, RinkZone, get_constant_class_int_choices, get_constant_class_str_choices

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
    start_date = DateField()

    def __str__(self):
        return self.name

    class Meta:
        db_table = "seasons"

class Team(models.Model):

    age_group = models.CharField(max_length=3)
    level = models.ForeignKey(TeamLevel, on_delete=models.RESTRICT)
    division = models.ForeignKey(Division, on_delete=models.RESTRICT)
    name = models.CharField(max_length=150)
    abbreviation = models.CharField(max_length=10, null=True, blank=True)
    logo = models.ImageField(upload_to='team_logo/')
    city = models.CharField(max_length=100)

    is_archived = models.BooleanField(default=False)

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

    name = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "player_positions"

class Player(models.Model):

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

    team = models.ForeignKey(Team, null=True, blank=True, on_delete=models.SET_NULL)
    position = models.ForeignKey(PlayerPosition, on_delete=models.RESTRICT)
    number = models.IntegerField()
    photo = models.ImageField(upload_to='player_photo/', null=True, blank=True)
    analysis = models.TextField(null=True, blank=True)

    is_archived = models.BooleanField(default=False)

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
        expression=Case(When(faceoffs__gt=0, then=((F('faceoffs_won') / F('faceoffs'))* 100)),
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
    team = models.ForeignKey(Team, on_delete=models.CASCADE, null=True, blank=True)
    number = models.IntegerField()
    description = models.TextField()

    def __str__(self):
        return f"{self.player.first_name} {self.player.last_name} - {self.season}/{(self.season + 1)}"

    class Meta:
        db_table = "player_transactions"

class Goalie(models.Model):

    player = models.OneToOneField(Player, on_delete=models.CASCADE, primary_key=True)

    def clean(self) -> None:
        if self.player.position.name != GOALIE_POSITION_NAME:
            raise ValidationError("A goalie must have the \"Goalie\" player position.")
        return super().clean()

    def __str__(self):
        return f"{self.player.first_name} {self.player.last_name}"

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
        expression=Case(When(Q(saves__gt=0) | Q(goals_against__gt=0), then=((F('saves') / (F('saves') + F('goals_against'))) * 100)),
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
        return f'{str(self.id)} - DefensiveZoneExit'

    class Meta:
        db_table = "defensive_zone_exit"

class OffensiveZoneEntry(models.Model):

    pass_in = models.IntegerField("Pass", default=0)
    dump_win = models.IntegerField("Dump/W", default=0)
    dump_lose = models.IntegerField("Dump/L", default=0)
    skate_in = models.IntegerField(default=0)

    def __str__(self):
        return f'{str(self.id)} - OffensiveZoneEntry'

    class Meta:
        db_table = "offensive_zone_entry"

class Shots(models.Model):

    shots_on_goal = models.IntegerField(default=0)
    scoring_chance = models.IntegerField(default=0)
    saves = models.IntegerField(default=0)
    missed_net = models.IntegerField(default=0)
    blocked = models.IntegerField(default=0)

    def __str__(self):
        return f'{str(self.id)} - Shots'

    class Meta:
        db_table = "shots"

class Turnovers(models.Model):

    off_zone = models.IntegerField(default=0)
    neutral_zone = models.IntegerField(default=0)
    def_zone = models.IntegerField(default=0)

    def __str__(self):
        return f'{str(self.id)} - Turnovers'

    class Meta:
        db_table = "turnovers"

class GameType(models.Model):

    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name
    
    class Meta:
        db_table = "game_types"

class GameTypeName(models.Model):
    name = models.CharField(max_length=150)
    is_actual = models.BooleanField(default=True)
    game_type = models.ForeignKey(GameType, on_delete=models.RESTRICT)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "game_type_names"

        constraints = [
            UniqueConstraint(fields=['game_type', 'name'], name='unique_game_type_name')
        ]

class GamePeriod(models.Model):

    name = models.CharField(max_length=10)
    order = models.IntegerField(unique=True)

    def __str__(self):
        return self.name
    
    class Meta:
        db_table = "game_periods"

class Game(models.Model):

    home_team = models.ForeignKey(Team, related_name='home_games', on_delete=models.RESTRICT)
    home_goals = models.IntegerField(default=0)
    home_goalies = models.ManyToManyField(Goalie, related_name='home_games')
    home_players = models.ManyToManyField(Player, related_name='home_games')
    home_start_goalie = models.ForeignKey(Goalie, related_name='home_start_games', on_delete=models.RESTRICT, null=True, blank=True)   # TODO: make not null
    away_team = models.ForeignKey(Team, related_name='away_games', on_delete=models.RESTRICT)
    away_goals = models.IntegerField(default=0)
    away_goalies = models.ManyToManyField(Goalie, related_name='away_games')
    away_players = models.ManyToManyField(Player, related_name='away_games')
    away_start_goalie = models.ForeignKey(Goalie, related_name='away_start_games', on_delete=models.RESTRICT, null=True, blank=True)   # TODO: make not null
    game_type = models.ForeignKey(GameType, on_delete=models.RESTRICT)
    game_type_name = models.ForeignKey(GameTypeName, on_delete=models.RESTRICT, null=True, blank=True)
    status = models.IntegerField(choices=get_constant_class_int_choices(GameStatus), default=GameStatus.NOT_STARTED.id)
    season = models.ForeignKey(Season, on_delete=models.RESTRICT, null=True, blank=True)
    date = models.DateField()
    time = models.TimeField()
    rink = models.ForeignKey(ArenaRink, on_delete=models.RESTRICT)
    analysis = models.TextField(null=True, blank=True)

    # Dashboard fields.

    # game_type_group = models.CharField(max_length=10)

    game_period = models.ForeignKey(GamePeriod, on_delete=models.RESTRICT, null=True, blank=True)

    faceoffs_count = models.IntegerField(default=0)
    """Cache field for the number of faceoffs in the game."""
    home_faceoffs_won_count = models.IntegerField(default=0)
    """Cache field for the number of faceoffs won by the home team."""

    home_defensive_zone_exit = models.OneToOneField(DefensiveZoneExit, related_name='home_game', on_delete=models.RESTRICT)
    home_offensive_zone_entry = models.OneToOneField(OffensiveZoneEntry, related_name='home_game', on_delete=models.RESTRICT)
    home_shots = models.OneToOneField(Shots, related_name='home_game', on_delete=models.RESTRICT)
    home_turnovers = models.OneToOneField(Turnovers, related_name='home_game', on_delete=models.RESTRICT)

    away_defensive_zone_exit = models.OneToOneField(DefensiveZoneExit, related_name='away_game', on_delete=models.RESTRICT)
    away_offensive_zone_entry = models.OneToOneField(OffensiveZoneEntry, related_name='away_game', on_delete=models.RESTRICT)
    away_shots = models.OneToOneField(Shots, related_name='away_game', on_delete=models.RESTRICT)
    away_turnovers = models.OneToOneField(Turnovers, related_name='away_game', on_delete=models.RESTRICT)

    def clean(self):
        if self.home_team == self.away_team:
            raise ValidationError("Home team and away team cannot be the same.")
        if self.home_start_goalie == self.away_start_goalie and self.home_start_goalie is not None:
            raise ValidationError("Home start goalie and away start goalie cannot be the same.")
        if self.game_type.name == "Tournament" and self.game_type_name is None:
            raise ValidationError("Tournament game must have a tournament name.")
        if self.game_type.name != "Tournament" and self.game_type_name is not None:
            raise ValidationError("Non-tournament game cannot have a tournament name.")
        return super().clean()

    @property
    def arena_id(self) -> int | None:
        """Returns the arena_id from the related rink, or None if rink is not set."""
        if self.rink is not None:
            return self.rink.arena_id
        return None

    @property
    def game_type_name_str(self) -> str | None:
        """Returns the name of the related game_type_name, or None if game_type_name is not set."""
        if self.game_type_name is not None:
            return self.game_type_name.name
        return None

    def __str__(self):
        return f'"{self.home_team.name}" - "{self.away_team.name}" - {str(self.date)} {str(self.time)}'

    class Meta:
        db_table = "games"

class GamePlayer(models.Model):

    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    player = models.ForeignKey(Player, on_delete=models.RESTRICT)
    goals = models.IntegerField(default=0)
    assists = models.IntegerField(default=0)
    shots_on_goal = models.IntegerField(default=0)
    scoring_chances = models.IntegerField(default=0)
    blocked_shots = models.IntegerField(default=0)
    penalty_minutes = models.DurationField(default=datetime.timedelta(0))
    penalties_drawn = models.DurationField(default=datetime.timedelta(0))
    turnovers = models.IntegerField(default=0)
    faceoffs = models.IntegerField(default=0)
    faceoffs_won = models.IntegerField(default=0)

    short_handed_goals = models.IntegerField("SHG", default=0)
    """SHG field."""

    power_play_goals = models.IntegerField("PPG", default=0)
    """PPG field."""

    points = models.GeneratedField(
        expression=F('goals') + F('assists'),
        output_field=models.IntegerField(),
        db_persist=True)

    def __str__(self):
        return f'{str(self.game)} - {self.player.first_name} {self.player.last_name}'

    class Meta:
        db_table = "game_players"

class GameGoalie(models.Model):

    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    goalie = models.ForeignKey(Goalie, on_delete=models.RESTRICT)
    goals_against = models.IntegerField(default=0)
    saves = models.IntegerField(default=0)

    short_handed_goals_against = models.IntegerField("SHGA", default=0)
    """SHGA field."""

    power_play_goals_against = models.IntegerField("PPGA", default=0)
    """PPGA field."""

    penalty_minutes = models.DurationField(default=datetime.timedelta(0))

    shots_against = models.GeneratedField(
        expression=F('goals_against') + F('saves'),
        output_field=models.IntegerField(),
        db_persist=True)

    save_percents = models.GeneratedField(
        expression=Case(When(goals_against__gt=0, then=((F('saves') / (F('goals_against') + F('saves'))) * 100)),
                        default=Value(0), output_field=models.FloatField()),
        output_field=models.FloatField(),
        db_persist=True,
        verbose_name="Save %")

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

class ShotType(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "shot_types"

class GameEvents(models.Model):

    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    event_name = models.ForeignKey(GameEventName, on_delete=models.RESTRICT)
    time = models.TimeField(auto_now=False, auto_now_add=False)
    period = models.ForeignKey(GamePeriod, on_delete=models.RESTRICT)
    team = models.ForeignKey(Team, on_delete=models.RESTRICT)
    player = models.ForeignKey(Player, on_delete=models.RESTRICT, null=True, blank=True, related_name='player')
    player_2 = models.ForeignKey(Player, on_delete=models.RESTRICT, null=True, blank=True, related_name='player_2')
    goalie = models.ForeignKey(Goalie, on_delete=models.RESTRICT, null=True, blank=True)

    # Shot specific fields.
    shot_type = models.ForeignKey(ShotType, on_delete=models.RESTRICT, null=True, blank=True)
    is_scoring_chance = models.BooleanField(default=False, null=True, blank=True)

    # Shot -> goal specific fields.
    goal_type = models.CharField(choices=get_constant_class_str_choices(GoalType), max_length=20, null=True, blank=True)

    # Turnover specific fields.
    zone = models.CharField(choices=get_constant_class_str_choices(RinkZone), max_length=20, null=True, blank=True)

    # Spray chart points.
    ice_top_offset = models.IntegerField(null=True, blank=True)
    ice_left_offset = models.IntegerField(null=True, blank=True)
    net_top_offset = models.IntegerField(null=True, blank=True)
    net_left_offset = models.IntegerField(null=True, blank=True)

    youtube_link = models.CharField("YouTube Link", max_length=1000, null=True, blank=True)

    note = models.TextField(null=True, blank=True)
    time_length = models.DurationField(null=True, blank=True)

    def __str__(self):
        return f'{str(self.game)} - {self.time}'

    class Meta:
        db_table = "game_events"

class CustomEvents(models.Model):
    event_name = models.CharField(max_length=150)
    note = models.TextField()
    youtube_link = models.CharField("YouTube Link", max_length=1000, null=True, blank=True)
    date = models.DateField(null=True, blank=True)
    time = models.TimeField(null=True, blank=True)

    user_id = models.IntegerField()
    """User ID reference. Not a foreign key because the users database is separate. Use User.objects.using('default').get(id=user_id) to access the user."""

    def __str__(self):
        return f"{self.date} - {self.time} - {self.event_name}"
    
    class Meta:
        db_table = "custom_events"

class HighlightReel(models.Model):
    name = models.CharField(max_length=150)
    description = models.TextField()
    date = models.DateField(auto_now_add=True)

    user_id = models.IntegerField()
    """User ID reference. Not a foreign key because the users database is separate. Use User.objects.using('default').get(id=user_id) to access the user."""

    def __str__(self):
        return f"{self.date} - {self.name}"

    class Meta:
        db_table = "highlight_reels"

class Highlight(models.Model):
    game_event = models.ForeignKey(GameEvents, on_delete=models.RESTRICT, null=True, blank=True)
    custom_event = models.OneToOneField(CustomEvents, on_delete=models.SET_NULL, related_name='highlights', null=True, blank=True)
    highlight_reel = models.ForeignKey(HighlightReel, related_name='highlights', on_delete=models.CASCADE, null=True, blank=True)
    order = models.IntegerField(default=0)

    user_id = models.IntegerField()
    """User ID reference. Not a foreign key because the users database is separate. Use User.objects.using('default').get(id=user_id) to access the user."""

    def clean(self):
        if self.game_event is None and self.custom_event is None:
            raise ValidationError("Either game event or custom event must be set.")
        if self.game_event is not None and self.custom_event is not None:
            raise ValidationError("Only one of game event or custom event can be set.")
        return super().clean()

    def __str__(self):
        return f"{self.pk} - {self.highlight_reel.name if self.highlight_reel is not None else '(No reel)'} - {self.order}"

    class Meta:
        db_table = "highlights"

class VideoLibrary(models.Model):
    name = models.CharField(max_length=150)
    description = models.TextField(null=True, blank=True)
    date = models.DateField(auto_now_add=True)

    youtube_link = models.CharField("YouTube Link", max_length=1000)

    user_id = models.IntegerField()
    """User ID reference. Not a foreign key because the users database is separate. Use User.objects.using('default').get(id=user_id) to access the user."""

    def __str__(self):
        return f"{self.date} - {self.name}"

    class Meta:
        db_table = "video_library"

class GameEventsAnalysisQueue(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    payload = models.TextField()
    status = models.IntegerField(null=True, blank=True)
    """Status of the game or event in the data analyzer.\n
    Values are from the `GameSystemStatus` or `GameEventSystemStatus` classes.
    """

    date_time = models.DateTimeField(auto_now=True)

    error_message = models.TextField(null=True, blank=True)
    """If the analysis failed, this field will be set to the error message."""

    class Meta:
        db_table = "game_events_analysis_queue"

class ProcessStatus(models.Model):
    name = models.CharField(max_length=150, unique=True)
    status = models.CharField(max_length=150, null=True, blank=True)
    last_finished = models.DateTimeField(null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True)
    log = models.TextField(default="")

    def __str__(self):
        return f"{self.name}"

    class Meta:
        db_table = "processes_status"
