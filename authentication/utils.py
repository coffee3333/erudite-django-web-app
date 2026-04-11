def safe_photo_url(user):
    """
    Returns the user's photo URL, or None if the photo is absent or uses
    the stale default-avatar Cloudinary path that returns 404.
    """
    if not user.photo:
        return None
    url = user.photo.url
    if 'default_mdlthc' in url:
        return None
    return url
