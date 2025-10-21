from django.contrib import admin
from django.apps import apps

from .models import Arena, ArenaRink, DefensiveZoneExit, Division, Game, GameEventName, GameEvents, GameGoalie, GamePeriod, GamePlayer, GameType, Goalie, GoalieTransaction, OffensiveZoneEntry, Player, PlayerPosition, PlayerTransaction, Season, Shots, Team, TeamLevel, TeamSeason, Turnovers

class HasNameAdmin(admin.ModelAdmin):
    list_display = ['name']
    ordering = ['name']
    search_fields = ['name']

@admin.register(Arena)
class ArenaAdmin(admin.ModelAdmin):
    list_display = ['name', 'address']
    ordering = ['name']
    search_fields = ['name', 'address']

@admin.register(ArenaRink)
class ArenaRinkAdmin(admin.ModelAdmin):
    list_display = ['arena__name', 'name']
    ordering = ['arena__name', 'name']
    search_fields = ['arena__name', 'name']

@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ['date', 'home_team__name', 'away_team__name']
    ordering = ['-date']
    search_fields = ['date', 'home_team__name', 'away_team__name']

@admin.register(GameEvents)
class GameEventsAdmin(admin.ModelAdmin):
    list_display = ['game__date', 'game__home_team__name', 'game__away_team__name', 'time', 'event_name__name']
    ordering = ['-game__date', 'game__home_team__name', 'time']
    search_fields = ['game__date', 'game__home_team__name', 'game__away_team__name', 'time', 'event_name__name']

@admin.register(GameGoalie)
class GameGoalieAdmin(admin.ModelAdmin):
    list_display = ['game__date', 'game__home_team__name', 'game__away_team__name', 'goalie__last_name', 'goalie__first_name']
    ordering = ['-game__date']
    search_fields = ['game__date', 'game__home_team__name', 'game__away_team__name', 'goalie__last_name', 'goalie__first_name']

@admin.register(GamePlayer)
class GamePlayerAdmin(admin.ModelAdmin):
    list_display = ['game__date', 'game__home_team__name', 'game__away_team__name', 'player__last_name', 'player__first_name']
    ordering = ['-game__date']
    search_fields = ['game__date', 'game__home_team__name', 'game__away_team__name', 'player__last_name', 'player__first_name']

@admin.register(Goalie)
class GoalieAdmin(admin.ModelAdmin):
    list_display = ['last_name', 'first_name', 'team__name', 'jersey_number']
    ordering = ['last_name']
    search_fields = ['last_name', 'first_name', 'team__name', 'jersey_number']

@admin.register(GoalieTransaction)
class GoalieTransactionAdmin(admin.ModelAdmin):
    list_display = ['date', 'goalie__last_name', 'goalie__first_name', 'team__name']
    ordering = ['-date', 'goalie__last_name']
    search_fields = ['date', 'goalie__last_name', 'goalie__first_name', 'team__name']

@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ['last_name', 'first_name', 'team__name', 'number']
    ordering = ['last_name']
    search_fields = ['last_name', 'first_name', 'team__name', 'number']

@admin.register(PlayerTransaction)
class PlayerTransactionAdmin(admin.ModelAdmin):
    list_display = ['date', 'player__last_name', 'player__first_name', 'team__name']
    ordering = ['-date', 'player__last_name']
    search_fields = ['date', 'player__last_name', 'player__first_name', 'team__name']

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ['name', 'age_group', 'level', 'division']
    ordering = ['name']
    search_fields = ['name', 'age_group', 'level', 'division']

@admin.register(TeamSeason)
class TeamSeasonAdmin(admin.ModelAdmin):
    list_display = ['team__name', 'season__name']
    ordering = ['team__name', 'season__name']
    search_fields = ['team__name', 'season__name']

app = apps.get_app_config('hockey')

for _, model in app.models.items():

    if model in [Division, GameEventName, GamePeriod, GameType, PlayerPosition, Season, TeamLevel]:
        admin.site.register(model, HasNameAdmin)
    # elif model not in [DefensiveZoneExit, OffensiveZoneEntry, Shots, Turnovers, Arena, ArenaRink, Game, GameEvents, GameGoalie, GamePlayer, Goalie, GoalieTransaction, Player, PlayerTransaction, Team, TeamSeason]:
    #     admin.site.register(model)
