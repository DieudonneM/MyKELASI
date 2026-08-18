from django.contrib import admin

from .models import LearningEvent, LearningRequest, MatchResult, Proposal

admin.site.register(LearningRequest)
admin.site.register(MatchResult)
admin.site.register(Proposal)
admin.site.register(LearningEvent)
