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
    WRITE_COMMENT = 7
    
class ContentType(Enum):
    POST = 8
    COMMENT = 9
    
class ScoreType(Enum):
    KARMA = 10
    ENGAGEMENT_SCORE = 11
    
_all_scores = {
    ActionType.COMMENT_UNDER_POST: {
      ContentType.POST: {
          ScoreType.ENGAGEMENT_SCORE: 32,
          ScoreType.KARMA: 5,
      },
    },
    ActionType.COMMENT_UNDER_COMMENT: {
      ContentType.POST: {
          ScoreType.ENGAGEMENT_SCORE: 11,
          ScoreType.KARMA: 3,
      },
      ContentType.COMMENT: {
          ScoreType.ENGAGEMENT_SCORE: (20, 17, 8, 3, ),
          ScoreType.KARMA: (4, 3, 2, 1, ),
      },
    },
    ActionType.VOTE_POST: {
        ContentType.POST: {
            ScoreType.ENGAGEMENT_SCORE: 7,
            ScoreType.KARMA: (3, -2, ),
        },
    },
    ActionType.VOTE_COMMENT: {
        ContentType.POST: {
            ScoreType.ENGAGEMENT_SCORE: 3,
        },
        ContentType.COMMENT: {
            ScoreType.ENGAGEMENT_SCORE: (5, 4, 2, 1, ),
            ScoreType.KARMA: (2, -1, ),
        },
    },
    ActionType.WRITE_POST: {
      ContentType.POST: {
          ScoreType.KARMA: 11,
      },
    },
    ActionType.WRITE_COMMENT: {
      ContentType.COMMENT: {
          ScoreType.KARMA: 7,
      },
    },
}

def get_score(action: ActionType, content_type: ContentType, score_type: ScoreType,
              vote: VoteType=None, order_index: int=None):
    
    if (vote and order_index):
        internal_server_error('Invalid request: Cannot pass both "vote" and "order_index" to "get_score"')
        
    action_scores = _all_scores.get(action, None)
    action_content_scores = action_scores.get(content_type, None) if action_scores else None
    scores = action_content_scores.get(score_type, 0) if action_content_scores else 0
    
    if isinstance(scores, int):
        return scores
    
    if vote and order_index:
        internal_server_error('Invalid Request: Both "vote" and "order_index" cannot be passed to "get_score"')
    elif not vote and not order_index:
        internal_server_error('Invalid Request: One of the "vote" or "order_index" must be passed to "get_score"')
            
    index = order_index if order_index else vote.value
    
    if index >= len(scores):
        internal_server_error('Invalid Request: Index is out of bounds')
    
    return scores[index]