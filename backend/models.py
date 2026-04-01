"""
DynamoDB models and CRUD operations for PokerFX.

Tables:
- Videos: video_id (PK), filename, status, clip_count, detected_count, verified_count, created_at, s3_key
- DetectedHands: hand_id (PK), video_id (SK), clip_number, cards, confidence, status, thumbnail_key, frame_timestamp, detected_at

GSIs:
- VideosByStatus: status → Videos (for listing by status)
"""
