# from src.init import *

# # internal imports
# from src.db import db
# from src.models.event import EventParticipant
# from src.repository.event import (
#                         EventRepository,
#                         EventPaticipationRepository, 
#                         EventJoiningRepository)

# from src.repository.user import UserRepository
# from src.services.v1 import (EmailService, 
#                              EventService, 
#                              UserService)

# class Container(containers.DeclarativeContainer):

#     db = providers.Resource(db.get_db)

#     singleton_email_service = providers.Singleton(EmailService)

#     user_repo = providers.Factory(UserRepository, db=db)
#     event_repo = providers.Factory(EventRepository, db=db)
#     event_participant_repo = providers.Factory(EventPaticipationRepository, db=db)
#     event_joining_repo = providers.Factory(EventJoiningRepository, db=db)

#     user_service = providers.Factory(
#         UserService,
#         user_repo=user_repo,
#         email_service=singleton_email_service
#     )

#     event_service = providers.Factory(
#         EventService,
#         event_repo=event_repo,
#         event_participant_repo=event_participant_repo,
#         event_joining_repo=event_joining_repo
#     )

# container = Container()