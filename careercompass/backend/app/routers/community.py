from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
import base64
import hashlib
import hmac
import time

from app.database import get_db
from app.models import User, CommunityPost, CommunityComment, PostLike
from app.routers.auth import get_current_user
from app.config import settings
from app.schemas import PostCreate, CommentCreate

router = APIRouter(prefix="/api/community", tags=["community"])


def get_optional_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
) -> Optional[User]:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.split(" ")[1].strip()
    try:
        payload, signature = token.split(".", 1)
        expected_signature = hmac.new(settings.secret_key.encode(), payload.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected_signature):
            return None
        decoded_payload = base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)).decode()
        email, expires_at = decoded_payload.rsplit("|", 1)
        if int(expires_at) <= int(time.time()):
            return None
        return db.query(User).filter(User.email == email).first()
    except Exception:
        return None


@router.get("/posts")
def list_posts(current_user: Optional[User] = Depends(get_optional_user), db: Session = Depends(get_db)):
    rows = db.query(CommunityPost, User).join(User, CommunityPost.user_id == User.id).order_by(CommunityPost.created_at.desc()).all()
    user_liked_ids = {
        row[0]
        for row in db.query(PostLike.post_id).filter(PostLike.user_id == current_user.id).all()
    } if current_user else set()

    return [
        {
            "id": post.id,
            "user_id": user.id,
            "author": user.full_name,
            "author_role": user.role,
            "title": post.title,
            "content": post.content,
            "category": post.category,
            "tags": post.tags,
            "created_at": post.created_at,
            "likes_count": db.query(PostLike).filter(PostLike.post_id == post.id).count(),
            "user_liked": post.id in user_liked_ids,
            "comments_count": db.query(CommunityComment).filter(CommunityComment.post_id == post.id).count(),
        }
        for post, user in rows
    ]


@router.get("/posts/{post_id}/comments")
def list_comments(post_id: int, db: Session = Depends(get_db)):
    post = db.query(CommunityPost).filter(CommunityPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    comments = (
        db.query(CommunityComment, User)
        .join(User, CommunityComment.user_id == User.id)
        .filter(CommunityComment.post_id == post_id)
        .order_by(CommunityComment.created_at.asc())
        .all()
    )

    return [
        {
            "id": comment.id,
            "post_id": comment.post_id,
            "user_id": user.id,
            "author": user.full_name,
            "author_role": user.role,
            "content": comment.content,
            "parent_id": comment.parent_id,
            "created_at": comment.created_at,
        }
        for comment, user in comments
    ]


@router.post("/posts")
def create_post(payload: PostCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role not in {"job_seeker", "recruiter"}:
        raise HTTPException(status_code=403, detail="This account cannot create community posts")
    post = CommunityPost(
        user_id=current_user.id,
        title=payload.title,
        content=payload.content,
        category=payload.category,
        tags=payload.tags,
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return {
        "message": "Post created",
        "post": {
            "id": post.id,
            "user_id": current_user.id,
            "author": current_user.full_name,
            "author_role": current_user.role,
            "title": post.title,
            "content": post.content,
            "category": post.category,
            "tags": post.tags,
            "created_at": post.created_at,
            "likes_count": 0,
            "user_liked": False,
            "comments_count": 0,
        }
    }


@router.post("/posts/{post_id}/comments")
def add_comment(post_id: int, payload: CommentCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    post = db.query(CommunityPost).filter(CommunityPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    comment = CommunityComment(post_id=post_id, user_id=current_user.id, content=payload.content, parent_id=payload.parent_id)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return {
        "message": "Comment added",
        "comment": {
            "id": comment.id,
            "post_id": comment.post_id,
            "user_id": current_user.id,
            "author": current_user.full_name,
            "author_role": current_user.role,
            "content": comment.content,
            "parent_id": comment.parent_id,
            "created_at": comment.created_at,
        }
    }


@router.post("/posts/{post_id}/like")
def toggle_like_post(post_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    existing = db.query(PostLike).filter(PostLike.post_id == post_id, PostLike.user_id == current_user.id).first()
    if existing:
        db.delete(existing)
        db.commit()
        return {"message": "Unliked", "liked": False, "likes_count": db.query(PostLike).filter(PostLike.post_id == post_id).count()}

    db.add(PostLike(post_id=post_id, user_id=current_user.id))
    db.commit()
    return {"message": "Liked", "liked": True, "likes_count": db.query(PostLike).filter(PostLike.post_id == post_id).count()}
