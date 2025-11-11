from django.contrib import admin
from django.apps import apps

from hockey.utils.constants import GOALIE_POSITION_NAME, NO_GOALIE_NAME

from .models import (Arena, ArenaRink, DefensiveZoneExit, Division, Game, GameEventName, GameEvents, GameGoalie, GamePeriod,
                     GamePlayer, GameType, Goalie, OffensiveZoneEntry, Player, PlayerPosition, PlayerTransaction,
                     Season, ShotType, Shots, Team, TeamLevel, TeamSeason, GameTypeName, Turnovers)

class ReadOnlyAdminMixin:
    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

class HasNameAdmin(admin.ModelAdmin):
    list_display = ['name']
    ordering = ['name']
    search_fields = ['name']

class HasNameReadOnlyAdmin(ReadOnlyAdminMixin, HasNameAdmin):
    pass

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

@admin.register(GameTypeName)
class GameTypeNameAdmin(admin.ModelAdmin):
    list_display = ['game_type__name', 'name', 'is_actual']
    ordering = ['game_type__name', 'name']
    search_fields = ['game_type__name', 'name', 'is_actual']

@admin.register(GamePeriod)
class GamePeriodAdmin(admin.ModelAdmin):
    list_display = ['order', 'name']
    ordering = ['order', 'name']
    search_fields = ['order', 'name']

@admin.register(Game)
class GameAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ['date', 'home_team__name', 'away_team__name', 'is_deprecated']
    ordering = ['-date']
    search_fields = ['date', 'home_team__name', 'away_team__name', 'is_deprecated']

@admin.register(GameEvents)
class GameEventsAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ['game__date', 'game__home_team__name', 'game__away_team__name', 'time', 'event_name__name']
    ordering = ['-game__date', 'game__home_team__name', 'time']
    search_fields = ['game__date', 'game__home_team__name', 'game__away_team__name', 'time', 'event_name__name']

@admin.register(GameGoalie)
class GameGoalieAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ['game__date', 'game__home_team__name', 'game__away_team__name', 'goalie__player__last_name', 'goalie__player__first_name']
    ordering = ['-game__date']
    search_fields = ['game__date', 'game__home_team__name', 'game__away_team__name', 'goalie__player__last_name', 'goalie__player__first_name']

@admin.register(GamePlayer)
class GamePlayerAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ['game__date', 'game__home_team__name', 'game__away_team__name', 'player__last_name', 'player__first_name']
    ordering = ['-game__date']
    search_fields = ['game__date', 'game__home_team__name', 'game__away_team__name', 'player__last_name', 'player__first_name']

@admin.register(Goalie)
class GoalieAdmin(admin.ModelAdmin):
    list_display = ['player__last_name', 'player__first_name', 'player__team__name', 'player__number', 'player__is_archived']
    ordering = ['player__last_name']
    search_fields = ['player__last_name', 'player__first_name', 'player__team__name', 'player__number', 'player__is_archived']

    def has_delete_permission(self, request, obj=None):
        if obj and obj.player.first_name == NO_GOALIE_NAME:
            return False  # This goalie is used in case of no goalie in net, so it cannot be deleted.
        return super().has_delete_permission(request, obj)

    def has_change_permission(self, request, obj=None):
        if obj and obj.player.first_name == NO_GOALIE_NAME:
            return False  # This goalie is used in case of no goalie in net, so it cannot be changed.
        return super().has_change_permission(request, obj)

@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ['last_name', 'first_name', 'team__name', 'number', 'is_archived']
    ordering = ['last_name']
    search_fields = ['last_name', 'first_name', 'team__name', 'number', 'is_archived']

    def has_delete_permission(self, request, obj=None):
        if obj and obj.first_name == NO_GOALIE_NAME:
            return False  # This goalie is used in case of no goalie in net, so it cannot be deleted.
        return super().has_delete_permission(request, obj)

    def has_change_permission(self, request, obj=None):
        if obj and obj.first_name == NO_GOALIE_NAME:
            return False  # This goalie is used in case of no goalie in net, so it cannot be changed.
        return super().has_change_permission(request, obj)

@admin.register(PlayerPosition)
class PlayerPositionAdmin(admin.ModelAdmin):
    list_display = ['name']
    ordering = ['name']
    search_fields = ['name']

    def has_delete_permission(self, request, obj=None):
        if obj and obj.name == GOALIE_POSITION_NAME:
            return False  # This position is auto applied to goalies, so it cannot be deleted.
        return super().has_delete_permission(request, obj)

    def has_change_permission(self, request, obj=None):
        if obj and obj.name == GOALIE_POSITION_NAME:
            return False  # This position is auto applied to goalies, so it cannot be changed.
        return super().has_change_permission(request, obj)

@admin.register(PlayerTransaction)
class PlayerTransactionAdmin(admin.ModelAdmin):
    list_display = ['date', 'player__last_name', 'player__first_name', 'team__name']
    ordering = ['-date', 'player__last_name']
    search_fields = ['date', 'player__last_name', 'player__first_name', 'team__name']

@admin.register(Season)
class SeasonAdmin(admin.ModelAdmin):
    list_display = ['name', 'start_date']
    ordering = ['-start_date']
    search_fields = ['name', 'start_date']

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ['name', 'age_group', 'level', 'division', 'is_archived']
    ordering = ['name']
    search_fields = ['name', 'age_group', 'level', 'division', 'is_archived']

@admin.register(TeamSeason)
class TeamSeasonAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ['team__name', 'season__name']
    ordering = ['team__name', 'season__name']
    search_fields = ['team__name', 'season__name']

app = apps.get_app_config('hockey')

for _, model in app.models.items():

    if model in [Division, GameType, TeamLevel]:
        admin.site.register(model, HasNameAdmin)
    elif model in [GameEventName, ShotType]:
        admin.site.register(model, HasNameReadOnlyAdmin)
