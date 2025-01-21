from enum import Enum
from core.custom_errors import internal_server_error

class VoteType(Enum):
    UPVOTE = 0,
    DOWNVOTE = 1,

class ActionType(Enum):
    COMMENT_UNDER_POST = 2
    COMMENT_UNDER_COMMENT = 3
    VOTE_POST = 4
    VOTE_COMMENT = 5
    WRITE_POST = 6
    
class OwnerType(Enum):
    POST_OWNER = 7
    COMMENT_OWNER = 8
    ACTOR = 9
    
class ScoreType(Enum):
    KARMA = 10
    ENGAGEMENT_SCORE = 11
    ACTIVITY_SCORE = 12
    
_all_scores = {
    ActionType.COMMENT_UNDER_POST: {
      OwnerType.POST_OWNER: {
          ScoreType.ENGAGEMENT_SCORE: 32,
          ScoreType.KARMA: 5,
      },
      OwnerType.ACTOR: {
          ScoreType.KARMA: 7,
          ScoreType.ACTIVITY_SCORE: 3,
      },
    },
    ActionType.COMMENT_UNDER_COMMENT: {
      OwnerType.POST_OWNER: {
          ScoreType.ENGAGEMENT_SCORE: 11,
          ScoreType.KARMA: 3,
      },
      OwnerType.COMMENT_OWNER: {
          ScoreType.ENGAGEMENT_SCORE: 20,
          ScoreType.KARMA: 4,
      },
      OwnerType.ACTOR: {
          ScoreType.KARMA: 11,
          ScoreType.ACTIVITY_SCORE: 4,
      },
    },
    ActionType.VOTE_POST: {
        OwnerType.POST_OWNER: {
            ScoreType.ENGAGEMENT_SCORE: 7,
            ScoreType.KARMA: (3, -2, ),
        },
        OwnerType.ACTOR: {
            ScoreType.ACTIVITY_SCORE: 1,
        },
    },
    ActionType.VOTE_COMMENT: {
        OwnerType.POST_OWNER: {
            ScoreType.ENGAGEMENT_SCORE: 3,
        },
        OwnerType.COMMENT_OWNER: {
            ScoreType.ENGAGEMENT_SCORE: 5,
            ScoreType.KARMA: (2, -1, ),
        },
        OwnerType.ACTOR: {
            ScoreType.ACTIVITY_SCORE: 2,
        },
    },
    ActionType.WRITE_POST: {
      OwnerType.ACTOR: {
          ScoreType.KARMA: 13,
          ScoreType.ACTIVITY_SCORE: 5,
      },
    },
}

def get_score(action: ActionType, owner_type: OwnerType, score_type: ScoreType):
    action_scores = _all_scores.get(action, None)
    action_owner_scores = action_scores.get(owner_type, None) if action_scores else None
    scores = action_owner_scores.get(score_type, 0) if action_owner_scores else 0
    return scores